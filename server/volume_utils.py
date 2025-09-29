"""
Volume conversion utilities for Ableton Live API.

Ableton Live uses a custom logarithmic curve where:
- 0 dB corresponds to float value ~0.85 (not 1.0)
- The relationship is approximately linear: X ≈ 0.85 - (0.025 × |dB_target|)
"""


def db_to_live_float(db_value: float) -> float:
    """
    Convert dB value to Ableton Live API float value (0.0 to 1.0).

    Formula: X ≈ 0.85 - (0.025 × |dB_target|)

    Args:
        db_value: dB value (typically -60 to +6)

    Returns:
        Float value for Live API (0.0 to 1.0)
    """
    # Clamp dB to valid range
    db_clamped = max(-60.0, min(6.0, float(db_value)))

    # Apply the formula: X ≈ 0.85 - (0.025 × |dB_target|)
    float_value = 0.85 - (0.025 * abs(db_clamped))

    # Clamp to valid Live range
    return max(0.0, min(1.0, float_value))


def live_float_to_db(float_value: float) -> float:
    """
    Convert Ableton Live API float value (0.0 to 1.0) to dB.

    Inverse formula: dB ≈ -(0.85 - X) / 0.025

    Args:
        float_value: Live API float value (0.0 to 1.0)

    Returns:
        dB value (typically -60 to +6)
    """
    # Clamp float to valid range
    float_clamped = max(0.0, min(1.0, float(float_value)))

    # Handle special case for very low values (essentially -infinity dB)
    if float_clamped <= 0.001:
        return -60.0

    # Apply inverse formula: dB = -(0.85 - X) / 0.025
    # This gives us negative dB values as expected
    db_value = -(0.85 - float_clamped) / 0.025

    # Clamp to reasonable dB range
    return max(-60.0, min(6.0, db_value))


# Test the conversion functions
if __name__ == "__main__":
    # Test cases based on your provided data
    test_cases = [
        (0.0, -34.0),      # 0 dB → ~0.85
        (-3.0, 0.7749),    # -3 dB → ~0.7749
        (-6.0, 0.7000),    # -6 dB → ~0.7000
        (-9.0, 0.6249),    # -9 dB → ~0.6249
        (-12.0, 0.5500),   # -12 dB → ~0.5500
        (-15.0, 0.475),    # -15 dB → 0.475
    ]

    print("Testing volume conversions:")
    for db, expected_float in test_cases:
        calculated_float = db_to_live_float(db)
        back_to_db = live_float_to_db(calculated_float)
        print(f"{db:6.1f} dB → {calculated_float:.4f} (expected ~{expected_float:.4f}) → {back_to_db:.1f} dB")