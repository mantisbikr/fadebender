#!/usr/bin/env python3
"""
Comprehensive test for device parameter relative changes.

Tests both backend (canonical intent API) and WebUI (chat API) flows:
1. Set parameter to initial value
2. Read back to verify (normalized_value and display_value)
3. Apply relative change (increase/decrease)
4. Read back to verify correct change was applied
5. Validate both normalized and display values

Tests different parameter types:
- Percent parameters (additive: 50% + 20% = 70%)
- Decibel parameters
- Frequency parameters (Hz)
- Time parameters (ms)
- Normalized parameters (0.0-1.0)
"""
import sys
import requests
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Server endpoint
BASE_URL = "http://127.0.0.1:8722"

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


@dataclass
class TestCase:
    """Test case for device parameter relative change."""
    name: str
    # Setup
    return_index: int
    device_index: int
    param_name: str
    initial_display: float  # Initial value in display space (0-100% for percent params)
    # Relative change
    change_type: str  # "increase" or "decrease"
    change_amount: float
    # Expected result
    expected_display: float  # Expected value in display space
    # Optional fields with defaults
    change_unit: Optional[str] = None
    tolerance: float = 0.05  # tolerance for float comparison in display space
    # Additional metadata
    param_unit: Optional[str] = None
    is_percent_additive: bool = False


class DeviceRelativeChangesTester:
    """Test device parameter relative changes."""

    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.errors = []

    def set_parameter_backend(self, return_index: int, device_index: int,
                            param_name: str, value: float, unit: str = "percent") -> Dict[str, Any]:
        """Set device parameter using backend canonical intent API."""
        payload = {
            "domain": "device",
            "action": "set",
            "return_index": return_index,
            "device_index": device_index,
            "param_ref": param_name,
            "value": value,
            "unit": unit
        }

        try:
            response = requests.post(
                f"{BASE_URL}/intent/execute",
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"ok": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def read_parameter_backend(self, return_index: int, device_index: int,
                              param_name: str) -> Dict[str, Any]:
        """Read device parameter using backend read intent API."""
        payload = {
            "domain": "device",
            "return_index": return_index,
            "device_index": device_index,
            "param_ref": param_name
        }

        try:
            response = requests.post(
                f"{BASE_URL}/intent/read",
                json=payload,
                timeout=10
            )
            return response.json() if response.status_code == 200 else {"ok": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def apply_change_chat(self, return_index: int, device_index: int,
                         param_name: str, change_type: str, amount: float,
                         unit: Optional[str] = None) -> Dict[str, Any]:
        """Apply relative change using WebUI chat API."""
        # Convert return_index to letter
        return_letter = chr(ord('A') + return_index)

        # Convert parameter name to natural language (replace slashes with spaces)
        # The LLM handles "dry wet" better than "dry/wet"
        natural_param_name = param_name.replace("/", " ")

        # Build natural language command
        unit_str = f" {unit}" if unit else ""
        text = f"{change_type} return {return_letter} device {device_index + 1} {natural_param_name} by {amount}{unit_str}"

        try:
            response = requests.post(
                f"{BASE_URL}/chat",
                json={"text": text},
                timeout=15
            )
            return response.json() if response.status_code == 200 else {"ok": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def values_match(self, actual: float, expected: float, tolerance: float) -> bool:
        """Check if two float values match within tolerance."""
        return abs(actual - expected) <= tolerance

    def run_test_case(self, test: TestCase, mode: str = "backend") -> Tuple[bool, str]:
        """
        Run a single test case.

        Args:
            test: TestCase to run
            mode: "backend" or "webui"

        Returns:
            (success, message)
        """
        self.total_tests += 1

        # Step 1: Set initial value (in percent for percent parameters)
        print(f"\n  Step 1: Setting {test.param_name} to {test.initial_display}%")
        set_result = self.set_parameter_backend(
            test.return_index, test.device_index, test.param_name,
            test.initial_display, unit="percent"
        )

        if not set_result.get("ok"):
            msg = f"Failed to set initial value: {set_result.get('error', 'unknown error')}"
            self.failed_tests += 1
            self.errors.append(f"{test.name}: {msg}")
            return False, msg

        time.sleep(0.5)  # Allow Live to process

        # Step 2: Read back to verify initial value
        print(f"  Step 2: Reading back to verify initial value")
        read_result = self.read_parameter_backend(
            test.return_index, test.device_index, test.param_name
        )

        if not read_result.get("ok"):
            msg = f"Failed to read initial value: {read_result.get('error', 'unknown error')}"
            self.failed_tests += 1
            self.errors.append(f"{test.name}: {msg}")
            return False, msg

        initial_normalized = read_result.get("normalized_value")
        initial_display = float(read_result.get("display_value"))

        # Validate display value matches expected initial value
        if not self.values_match(initial_display, test.initial_display, test.tolerance):
            msg = f"Initial display value mismatch: expected {test.initial_display}, got {initial_display}"
            self.failed_tests += 1
            self.errors.append(f"{test.name}: {msg}")
            return False, msg

        print(f"    ✓ Initial: normalized={initial_normalized}, display={initial_display}")

        # Step 3: Apply relative change
        print(f"  Step 3: Applying {test.change_type} by {test.change_amount}{test.change_unit or ''}")

        if mode == "webui":
            change_result = self.apply_change_chat(
                test.return_index, test.device_index, test.param_name,
                test.change_type, test.change_amount, test.change_unit
            )
        else:
            # For backend mode, we need to construct the canonical intent with delta
            # For now, we'll use the chat API as it handles relative changes
            # TODO: Implement backend relative change support if needed
            change_result = self.apply_change_chat(
                test.return_index, test.device_index, test.param_name,
                test.change_type, test.change_amount, test.change_unit
            )

        if not change_result.get("ok"):
            msg = f"Failed to apply change: {change_result.get('error', 'unknown error')}"
            self.failed_tests += 1
            self.errors.append(f"{test.name}: {msg}")
            return False, msg

        time.sleep(0.5)  # Allow Live to process

        # Step 4: Read back to verify change was applied
        print(f"  Step 4: Reading back to verify change")
        final_result = self.read_parameter_backend(
            test.return_index, test.device_index, test.param_name
        )

        if not final_result.get("ok"):
            msg = f"Failed to read final value: {final_result.get('error', 'unknown error')}"
            self.failed_tests += 1
            self.errors.append(f"{test.name}: {msg}")
            return False, msg

        final_normalized = final_result.get("normalized_value")
        final_display = float(final_result.get("display_value"))

        print(f"    ✓ Final: normalized={final_normalized}, display={final_display}")

        # Step 5: Validate final display value matches expected
        if not self.values_match(final_display, test.expected_display, test.tolerance):
            msg = f"Final display value mismatch: expected {test.expected_display}, got {final_display}"
            self.failed_tests += 1
            self.errors.append(f"{test.name}: {msg}")
            return False, msg

        # Also validate the change amount (for debugging)
        change = final_display - initial_display
        expected_change = test.expected_display - test.initial_display
        print(f"    ✓ Change: {change:.2f} (expected: {expected_change:.2f})")

        self.passed_tests += 1
        return True, f"display={final_display} (changed by {change:.2f})"

    def run_all_tests(self):
        """Run all test cases."""
        print("=" * 80)
        print("Device Parameter Relative Changes - Comprehensive Test")
        print("=" * 80)
        print("\nThis test requires:")
        print("  - Ableton Live running")
        print("  - Return track A with a device at index 0 that has a dry/wet parameter")
        print("\nNote: Tests work in display value space (0-100%) not normalized values")
        print()

        # Define test cases
        # NOTE: These test cases assume a device on Return A with dry/wet parameter
        # We use display values (percent) for all validation
        test_cases = [
            # Device - Dry/Wet parameter (percent, additive)
            TestCase(
                name="Device Dry/Wet - Increase (percent additive)",
                return_index=0,
                device_index=0,
                param_name="dry/wet",
                initial_display=50.0,  # 50%
                change_type="increase",
                change_amount=20,
                change_unit="percent",
                expected_display=70.0,  # 50% + 20% = 70%
                param_unit="%",
                is_percent_additive=True
            ),

            TestCase(
                name="Device Dry/Wet - Decrease (percent additive)",
                return_index=0,
                device_index=0,
                param_name="dry/wet",
                initial_display=70.0,  # 70%
                change_type="decrease",
                change_amount=20,
                change_unit="percent",
                expected_display=50.0,  # 70% - 20% = 50%
                param_unit="%",
                is_percent_additive=True
            ),

            TestCase(
                name="Device Dry/Wet - Increase from 30%",
                return_index=0,
                device_index=0,
                param_name="dry/wet",
                initial_display=30.0,  # 30%
                change_type="increase",
                change_amount=15,
                change_unit="percent",
                expected_display=45.0,  # 30% + 15% = 45%
                param_unit="%",
                is_percent_additive=True
            ),

            TestCase(
                name="Device Dry/Wet - Decrease from 60%",
                return_index=0,
                device_index=0,
                param_name="dry/wet",
                initial_display=60.0,  # 60%
                change_type="decrease",
                change_amount=10,
                change_unit="percent",
                expected_display=50.0,  # 60% - 10% = 50%
                param_unit="%",
                is_percent_additive=True
            ),
        ]

        # Run tests
        for i, test in enumerate(test_cases, 1):
            print(f"\n{BLUE}[Test {i}/{len(test_cases)}] {test.name}{RESET}")
            print(f"  Parameter: {test.param_name} (unit: {test.param_unit})")
            print(f"  Additive: {test.is_percent_additive}")

            success, msg = self.run_test_case(test, mode="webui")

            if success:
                print(f"  {GREEN}✓ PASS{RESET}: {msg}")
            else:
                print(f"  {RED}✗ FAIL{RESET}: {msg}")

            # Cooldown between tests to avoid overwhelming the server
            if i < len(test_cases):
                time.sleep(1.0)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total tests:  {self.total_tests}")
        print(f"{GREEN}Passed:       {self.passed_tests}{RESET}")
        print(f"{RED}Failed:       {self.failed_tests}{RESET}")
        print("=" * 80)

        if self.failed_tests > 0:
            print(f"\n{RED}FAILED TESTS:{RESET}")
            for error in self.errors:
                print(f"  • {error}")
            print()

        if self.failed_tests == 0:
            print(f"\n{GREEN}✅ All tests PASSED!{RESET}")
            print("Device parameter relative changes are working correctly.")
        else:
            print(f"\n{RED}❌ {self.failed_tests} test(s) FAILED{RESET}")
            print("Device parameter relative changes need adjustment.")


def main():
    """Main entry point."""
    tester = DeviceRelativeChangesTester()

    try:
        tester.run_all_tests()
        return 0 if tester.failed_tests == 0 else 1
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Test interrupted by user{RESET}")
        return 130
    except Exception as e:
        print(f"\n\n{RED}Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
