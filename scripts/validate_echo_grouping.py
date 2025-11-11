#!/usr/bin/env python3
"""
Validate Echo device master/dependent grouping structure.
Phase 3: Master/Dependent Analysis
"""
import os
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
import sys
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore

ECHO_SIGNATURE = "9bd78001e088fcbde50e2ead80ef01e393f3d0ba"

def validate_grouping():
    """Validate Echo grouping structure."""

    client = firestore.Client(database="dev-display-value")
    doc = client.collection("device_mappings").document(ECHO_SIGNATURE).get()

    if not doc.exists:
        print("❌ Echo device not found")
        return False

    data = doc.to_dict()
    params_meta = data.get("params_meta", [])
    grouping = data.get("grouping", {})

    # Get all parameter names
    param_names = {p.get("name") for p in params_meta}

    print("=" * 80)
    print("ECHO GROUPING VALIDATION")
    print("=" * 80)
    print(f"Total parameters: {len(param_names)}")
    print(f"Device: {data.get('device_name', 'Unknown')}")
    print(f"Signature: {ECHO_SIGNATURE}\n")

    # Extract grouping components
    masters = grouping.get("masters", [])
    dependents = grouping.get("dependents", {})
    dependent_master_values = grouping.get("dependent_master_values", {})

    errors = []
    warnings = []

    # Check 1: All masters are valid parameters
    print("Check 1: Validating master parameters")
    print("-" * 80)
    for master in masters:
        if master not in param_names:
            errors.append(f"Master '{master}' not found in params_meta")
            print(f"  ❌ {master} - NOT FOUND")
        else:
            # Check that master is binary (should be on/off switch)
            param = next(p for p in params_meta if p.get("name") == master)
            control_type = param.get("control_type")
            if control_type != "binary":
                warnings.append(f"Master '{master}' is {control_type}, expected binary")
                print(f"  ⚠️  {master} - {control_type} (expected binary)")
            else:
                print(f"  ✓ {master} - valid binary master")

    # Check 2: All dependents reference valid masters
    print(f"\nCheck 2: Validating dependent → master relationships")
    print("-" * 80)
    for dependent, master_list in dependents.items():
        if dependent not in param_names:
            errors.append(f"Dependent '{dependent}' not found in params_meta")
            print(f"  ❌ {dependent} → {master_list} - DEPENDENT NOT FOUND")
            continue

        # master_list should be a list
        if not isinstance(master_list, list):
            errors.append(f"Dependent '{dependent}' master list is not a list: {master_list}")
            print(f"  ❌ {dependent} → {master_list} - NOT A LIST")
            continue

        # Check each master in the list
        for master in master_list:
            if master not in masters:
                errors.append(f"Dependent '{dependent}' references unknown master '{master}'")
                print(f"  ❌ {dependent} → {master} - MASTER NOT IN MASTERS LIST")
            elif master not in param_names:
                errors.append(f"Dependent '{dependent}' references invalid parameter '{master}'")
                print(f"  ❌ {dependent} → {master} - MASTER NOT FOUND")
            else:
                print(f"  ✓ {dependent} → {master}")

    # Check 3: All dependent_master_values match dependents
    print(f"\nCheck 3: Validating dependent_master_values")
    print("-" * 80)
    for dependent, value_spec in dependent_master_values.items():
        if dependent not in dependents:
            errors.append(f"dependent_master_values key '{dependent}' not in dependents")
            print(f"  ❌ {dependent} - NOT IN DEPENDENTS")
            continue

        # value_spec should be a dict mapping master -> [values]
        if not isinstance(value_spec, dict):
            errors.append(f"dependent_master_values['{dependent}'] is not a dict: {value_spec}")
            print(f"  ❌ {dependent} - NOT A DICT")
            continue

        # Check each master in value_spec matches the dependent's masters
        dependent_masters = dependents[dependent]
        for master, values in value_spec.items():
            if master not in dependent_masters:
                errors.append(f"dependent_master_values['{dependent}'] references '{master}' not in dependents['{dependent}']")
                print(f"  ❌ {dependent}: {master} → {values} - MASTER MISMATCH")
            else:
                print(f"  ✓ {dependent}: {master} → {values}")

    # Check 4: All dependents have corresponding dependent_master_values
    print(f"\nCheck 4: Ensuring all dependents have master values defined")
    print("-" * 80)
    for dependent in dependents.keys():
        if dependent not in dependent_master_values:
            warnings.append(f"Dependent '{dependent}' missing from dependent_master_values")
            print(f"  ⚠️  {dependent} - MISSING MASTER VALUES")
        else:
            print(f"  ✓ {dependent} - has master values")

    # Check 5: No circular dependencies
    print(f"\nCheck 5: Checking for circular dependencies")
    print("-" * 80)

    def has_circular_dependency(param, visited=None):
        """Check if param has circular dependency."""
        if visited is None:
            visited = set()

        if param in visited:
            return True

        if param not in dependents:
            return False

        visited.add(param)
        for master in dependents[param]:
            if has_circular_dependency(master, visited.copy()):
                return True

        return False

    circular_found = False
    for param in dependents.keys():
        if has_circular_dependency(param):
            errors.append(f"Circular dependency detected for '{param}'")
            print(f"  ❌ {param} - CIRCULAR DEPENDENCY")
            circular_found = True

    if not circular_found:
        print("  ✓ No circular dependencies found")

    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Masters: {len(masters)}")
    print(f"Dependents: {len(dependents)}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    if errors:
        print("\n❌ VALIDATION FAILED")
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ VALIDATION PASSED")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")

    print("\n" + "=" * 80)
    print("MASTER/DEPENDENT RELATIONSHIPS")
    print("=" * 80)

    # Group dependents by master
    master_dependents = {}
    for dependent, master_list in dependents.items():
        for master in master_list:
            if master not in master_dependents:
                master_dependents[master] = []
            master_dependents[master].append(dependent)

    for master in sorted(masters):
        deps = master_dependents.get(master, [])
        print(f"\n{master} ({len(deps)} dependents):")
        for dep in sorted(deps):
            values = dependent_master_values.get(dep, {}).get(master, [])
            print(f"  → {dep} (when {master} = {values})")

    return len(errors) == 0

if __name__ == "__main__":
    success = validate_grouping()
    sys.exit(0 if success else 1)
