# Device Mapping Automation Roadmap

**Current state**: Manual process, 4 hours per device
**Goal**: Automate 80% of the workflow, reduce to 30-60 minutes of human oversight

---

## What We Learned from Reverb

### Time Breakdown (3 days → 4 hours)
- **Manual classification**: 30 min (can automate 90%)
- **Manual fitting**: 2 hours (can automate 80%)
- **Manual boundary detection**: 30 min (can automate 100%)
- **Manual testing**: 1 hour (can automate 95%)
- **Human oversight**: 30 min (always needed)

### Automation Opportunities

#### 1. Auto-Classify Parameters (HIGH PRIORITY)
**Current**: Manual review of each param
**Automation**: Pattern detection

```python
def auto_classify_param(param_info, samples):
    """Auto-classify parameter as binary/quantized/continuous."""

    # Binary detection
    if (param_info["min"] == 0.0 and param_info["max"] == 1.0 and
        "On" in param_info["name"]):
        return "binary", {"labels": ["off", "on"]}

    # Check sample uniqueness
    unique_vals = set(s["value"] for s in samples)
    unique_display = set(s["display_str"] for s in samples)

    # Quantized detection
    if len(unique_vals) <= 5:
        # Check if display values are labels (non-numeric)
        if any(not is_numeric(d) for d in unique_display):
            return "quantized", extract_label_map(samples)

        # Check if evenly spaced (e.g., 0, 1, 2, 3)
        sorted_vals = sorted(unique_vals)
        if is_evenly_spaced(sorted_vals):
            return "quantized", extract_label_map(samples)

    # Default: continuous
    return "continuous", detect_fit_type(samples)

def detect_fit_type(samples):
    """Detect best fit type from sample distribution."""
    xs = [s["value"] for s in samples]
    ys = [s["display_num"] for s in samples]

    # Try linear fit
    r2_linear = compute_r2(fit_linear(xs, ys))

    # Try exponential fit
    r2_exp = compute_r2(fit_exp(xs, ys))

    # Choose best
    if r2_linear > 0.999:
        return "linear"
    elif r2_exp > 0.999:
        return "exp"
    else:
        return "piecewise"  # Fallback
```

**Impact**: Saves 20-25 minutes per device

#### 2. Auto-Detect Boundaries (HIGH PRIORITY)
**Current**: Manual probing or inspection
**Automation**: Parallel probing

```python
def auto_detect_boundaries(return_idx, device_idx, param_idx):
    """Auto-detect min/max display values by probing Live."""

    # Set to 0.0, read back
    udp_request({"op": "set_return_device_param",
                 "return_index": return_idx,
                 "device_index": device_idx,
                 "param_index": param_idx,
                 "value": 0.0})

    params = udp_request({"op": "get_return_device_params",
                          "return_index": return_idx,
                          "device_index": device_idx})

    min_display = params[param_idx]["display_value"]

    # Set to 1.0, read back
    udp_request({"op": "set_return_device_param", ..., "value": 1.0})
    max_display = params[param_idx]["display_value"]

    return float(min_display), float(max_display)

# Run for ALL continuous params in parallel
boundaries = {}
for param in continuous_params:
    boundaries[param["name"]] = auto_detect_boundaries(0, 0, param["index"])
```

**Impact**: Saves 20-30 minutes per device

#### 3. Auto-Fit All Parameters (MEDIUM PRIORITY)
**Current**: `fit_params_from_presets.py` does this, but doesn't add boundaries
**Enhancement**: Integrate boundary detection

```python
def auto_fit_with_boundaries(param_name, samples, min_display, max_display):
    """Fit parameter with auto-detected boundaries."""

    # Extract samples
    xy_pairs = [(s["value"], s["display_num"]) for s in samples]

    # Add boundaries
    xy_pairs.append((0.0, min_display))
    xy_pairs.append((1.0, max_display))

    # Auto-detect fit type
    fit_type = detect_fit_type(xy_pairs)

    # Fit
    if fit_type == "linear":
        result = fit_linear(xy_pairs)
    elif fit_type == "exp":
        result = fit_exp(xy_pairs)
    else:
        result = fit_piecewise(xy_pairs)

    # Verify R²
    if result["r2"] < 0.999 and fit_type != "piecewise":
        # Fall back to piecewise
        result = fit_piecewise(xy_pairs)

    return result
```

**Impact**: Saves 1-1.5 hours per device

#### 4. Auto-Test All Parameters (HIGH PRIORITY)
**Current**: Manual test script creation
**Automation**: Generic test harness

```python
def auto_test_device(device_signature):
    """Automatically test all parameters for device."""

    # Get params_meta from Firestore
    params_meta = get_params_meta(device_signature)

    results = []

    for param in params_meta:
        name = param["name"]
        control_type = param["control_type"]

        if control_type == "binary":
            # Test on/off
            for label in ["off", "on"]:
                result = test_param(name, label)
                results.append(result)

        elif control_type == "quantized":
            # Test each label
            for label in param["labels"]:
                result = test_param(name, label)
                results.append(result)

        elif control_type == "continuous":
            # Test boundaries and midpoint
            min_val = param["min_display"]
            max_val = param["max_display"]
            mid_val = (min_val + max_val) / 2

            for test_val in [min_val, mid_val, max_val]:
                result = test_param(name, test_val)
                results.append(result)

    # Generate report
    failures = [r for r in results if not r["passed"]]

    return {
        "total_tests": len(results),
        "passed": len([r for r in results if r["passed"]]),
        "failed": len(failures),
        "failures": failures
    }
```

**Impact**: Saves 45-55 minutes per device

#### 5. Auto-Generate Documentation (LOW PRIORITY)
**Current**: Manual commit message and docs
**Automation**: Template generation

```python
def generate_device_docs(device_signature):
    """Generate documentation for device mapping."""

    params_meta = get_params_meta(device_signature)
    device_name = get_device_name(device_signature)

    # Count parameters
    binary = [p for p in params_meta if p["control_type"] == "binary"]
    quantized = [p for p in params_meta if p["control_type"] == "quantized"]
    continuous = [p for p in params_meta if p["control_type"] == "continuous"]

    # Count fit types
    fit_types = {}
    for p in continuous:
        ft = p["fit"]["type"]
        fit_types[ft] = fit_types.get(ft, 0) + 1

    # Generate commit message
    commit_msg = f"""feat(devices): complete {device_name} mapping

- {len(params_meta)} parameters: {len(binary)} binary, {len(quantized)} quantized, {len(continuous)} continuous
- All continuous params have fits ({fit_types.get('linear', 0)} linear, {fit_types.get('exp', 0)} exp, {fit_types.get('piecewise', 0)} piecewise)
- All tested and verified working (< 2% error)
- Signature: {device_signature}
"""

    return commit_msg
```

**Impact**: Saves 5-10 minutes per device

---

## Proposed Workflow with Automation

### New Workflow (Target: 30-60 minutes)

**Phase 1: Automated Setup (5 min, mostly automated)**
```bash
# One command to rule them all
python3 scripts/auto_map_device.py --return 0 --device 0 --learn --capture
```

**What it does:**
- Learns device structure
- Captures all presets
- Auto-classifies all parameters (binary/quantized/continuous)
- Auto-detects boundaries for all continuous params
- Auto-fits all continuous params with boundaries
- Creates complete params_meta in Firestore

**Phase 2: Human Review (15-20 min)**
- Review auto-classification report
- Fix any misclassified parameters (rare)
- Review fit R² values
- Refit any params with R² < 0.999 (rare)
- Check for special parameter behaviors

**Phase 3: Automated Testing (5 min)**
```bash
python3 scripts/auto_test_device.py --signature <sig>
```

**What it does:**
- Tests all parameters at boundaries and midpoints
- Generates pass/fail report
- Highlights any failures

**Phase 4: Human Verification (10-15 min)**
- Review test report
- Manually test any failed parameters
- Fix any issues (refit or reclassify)
- Re-run tests until all pass

**Phase 5: Finalization (5 min)**
```bash
python3 scripts/finalize_device.py --signature <sig>
```

**What it does:**
- Backs up to git
- Generates documentation
- Creates commit message
- Commits and pushes

**Total: 40-50 minutes** (vs 4 hours manual)

---

## Implementation Priority

### Phase 1: Critical Automations (Week 1)
1. **Auto-classify parameters** - Saves 25 min/device
2. **Auto-detect boundaries** - Saves 25 min/device
3. **Auto-fit with boundaries** - Saves 60 min/device
4. **Auto-test harness** - Saves 50 min/device

**Total savings: 2.5 hours per device**

### Phase 2: Integration (Week 2)
5. **Unified `auto_map_device.py` script**
6. **Automated reporting and error handling**
7. **Finalization script**

**Total savings: Additional 30 min per device**

### Phase 3: Refinements (Week 3)
8. **Better fit type detection** (handle edge cases)
9. **Dependency detection** (auto-enable relationships)
10. **Special case handling** (unusual parameter types)

---

## Key Automation Script: `auto_map_device.py`

```python
#!/usr/bin/env python3
"""Automatically map a device from scratch."""

import argparse
import sys
import time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--return", type=int, required=True)
    parser.add_argument("--device", type=int, required=True)
    parser.add_argument("--learn", action="store_true")
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()

    print("="*70)
    print("AUTOMATED DEVICE MAPPING")
    print("="*70)

    if args.learn:
        print("\n[1/6] Learning device structure...")
        learn_device(args.return, args.device)
        print("✓ Device learned")

    if args.capture:
        print("\n[2/6] Capturing factory presets...")
        capture_presets(args.return, args.device)
        print("✓ Presets captured")

    print("\n[3/6] Auto-classifying parameters...")
    classifications = auto_classify_all_params(args.return, args.device)
    print(f"✓ Classified {len(classifications)} parameters")
    print(f"  - Binary: {sum(1 for c in classifications if c['type'] == 'binary')}")
    print(f"  - Quantized: {sum(1 for c in classifications if c['type'] == 'quantized')}")
    print(f"  - Continuous: {sum(1 for c in classifications if c['type'] == 'continuous')}")

    print("\n[4/6] Auto-detecting boundaries...")
    boundaries = auto_detect_all_boundaries(args.return, args.device, classifications)
    print(f"✓ Detected boundaries for {len(boundaries)} continuous params")

    print("\n[5/6] Auto-fitting all parameters...")
    fits = auto_fit_all_params(classifications, boundaries)
    print(f"✓ Fitted {len(fits)} continuous parameters")
    avg_r2 = sum(f["r2"] for f in fits) / len(fits)
    print(f"  - Average R²: {avg_r2:.6f}")
    low_r2 = [f for f in fits if f["r2"] < 0.999]
    if low_r2:
        print(f"  - ⚠️  {len(low_r2)} params with R² < 0.999 (need review)")

    print("\n[6/6] Saving to Firestore...")
    save_params_meta(classifications, boundaries, fits)
    print("✓ Saved to Firestore")

    print("\n" + "="*70)
    print("AUTOMATED MAPPING COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. Review auto-classification report above")
    print("2. Run: python3 scripts/auto_test_device.py --signature <sig>")
    print("3. Fix any test failures")
    print("4. Run: python3 scripts/finalize_device.py --signature <sig>")

if __name__ == "__main__":
    sys.exit(main())
```

---

## Success Metrics

### Before Automation
- Time per device: **4 hours**
- Human effort: **4 hours** (100% manual)
- Error rate: ~10% (manual mistakes in fitting/classification)

### After Automation
- Time per device: **45 minutes**
- Human effort: **30 minutes** (oversight only)
- Error rate: ~2% (automation handles most edge cases)

### ROI Calculation
- **Time savings**: 3.25 hours per device
- **100 devices**: 325 hours saved = **8 weeks** of full-time work
- **Reduced errors**: 8% fewer mistakes = less debugging time

---

## Open Questions

1. **Should we use ML for fit type detection?**
   - Current: Rule-based (if R² > 0.999 for linear, use linear)
   - Alternative: Train classifier on Reverb + future devices
   - Trade-off: Complexity vs accuracy

2. **How to handle unusual parameter types?**
   - Example: Parameters that depend on other parameters
   - Solution: Manual override flags in auto_map_device.py

3. **Should we auto-detect dependencies?**
   - Example: ER Spin Rate requires ER Spin On
   - Detection: If setting dependent changes master, mark as dependency
   - Risk: False positives from Live's parameter refresh logic

---

## Next Steps

1. Implement auto_classify_params() function
2. Implement auto_detect_boundaries() function
3. Enhance fit_params_from_presets.py to use boundaries
4. Create auto_test_device.py script
5. Create auto_map_device.py unified script
6. Test on 2-3 simple devices
7. Refine based on learnings
8. Roll out for all devices

**Target: Complete automation scripts in 1 week, validate on 5 devices, then scale to 100+ devices**
