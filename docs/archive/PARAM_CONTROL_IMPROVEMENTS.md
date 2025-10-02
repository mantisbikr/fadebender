# Parameter Control Issues & Enhancements

## Issues Discovered During Testing

### 1. Binary Parameters with Incomplete Learning
**Issue**: Parameters that weren't toggled during learning can't be set to unlearned states.
- **Example**: "Freeze On" was always 0.0 during learning, so it can't be set to 1.0
- **Impact**: Binary/switch parameters may be stuck in one state
- **Root Cause**: Learning only samples current parameter ranges, doesn't explore all possible states

**Potential Solutions**:
- Enhanced learning: Force toggle all binary parameters during device learning
- Fallback: Direct value setting for binary params when learned mapping fails
- UI warning: Indicate which parameter states are unavailable

### 2. Unit Interpretation Ambiguity
**Issue**: System assumes units that may not match actual parameter behavior.
- **Example**: Room Size was treated as percentage (0-100%) but actually ranges 0-500
- **Impact**: User confusion about parameter ranges and units
- **Root Cause**: Display value parsing doesn't validate against actual parameter ranges

**Potential Solutions**:
- Parameter metadata: Store actual units and ranges in learned mappings
- Smart unit detection: Analyze learned samples to determine actual units
- Better error messages: Warn when requested value is outside learned range

### 3. Parameter State Dependencies
**Issue**: Some parameters only function when related enable/master parameters are active.
- **Example**: "HiFilter Freq" only works when "HiFilter On" is enabled
- **Impact**: Frequency/level controls appear broken when master switches are off
- **Root Cause**: Learning captures parameters in current state, missing dependency relationships

**Parameter Groupings**: Some audio processing modules have parameters that work in unison:
- **Diffusion Network**: Parameters are clubbed together and need coordinated changes
- **Filter Sections**: Enable + Frequency + Type parameters work as a unit
- **EQ Bands**: On/Off + Frequency + Gain + Q work together
- **Effect Modules**: Master Enable + individual effect parameters

**Hierarchical Parameter Dependencies**: Many audio effects have master enable switches that control whether sub-parameters are meaningful:
- **Chorus Group**: "Chorus On" → "Chorus Rate" + "Chorus Amount"
- **Filter Groups**: "HiFilter On" → "HiFilter Freq" + "HiFilter Type"
- **EQ Sections**: "LowShelf On" → "LowShelf Freq" + "LowShelf Gain"
- **Effect Chains**: When master is Off, sub-parameters have no audible effect

**Challenges**:
- Setting sub-parameters when master is Off appears to work but has no audio impact
- Users may not realize their changes are ineffective
- Learning may capture parameters in disabled states, missing active relationships
- Some parameters may only make sense within specific master switch contexts

**Potential Solutions**:
- **Dependency mapping**: Detect enable/disable relationships during learning
- **Automatic enablement**: When setting dependent params, auto-enable master switches
- **Smart learning**: Toggle master switches during learning to capture all states
- **Parameter groups**: Identify and handle parameter clusters that work together
- **Coordinated control**: Provide APIs to set multiple related parameters atomically
- **User feedback**: Warn when dependent parameter changes require enabling other params

**Auto-Detection of Parameter Groups**:
```python
def detect_parameter_groups(params):
    """Detect hierarchical parameter dependencies from naming patterns"""
    groups = {}

    # Find master enable parameters
    masters = [p for p in params if p["name"].endswith(" On")]

    for master in masters:
        prefix = master["name"].replace(" On", "")
        # Find related parameters with same prefix
        related = [p for p in params if p["name"].startswith(prefix) and p != master]

        if related:
            groups[master["name"]] = {
                "master": master,
                "dependents": related,
                "type": "hierarchical"
            }

    return groups

# Example detection results:
# "Chorus On" -> ["Chorus Rate", "Chorus Amount"]
# "HiFilter On" -> ["HiFilter Freq", "HiFilter Type"]
# "LowShelf On" -> ["LowShelf Freq", "LowShelf Gain"]
```

**Smart Group Control**:
```python
async def set_param_with_group_awareness(param_name, target_value):
    """Set parameter with automatic group enablement"""
    groups = get_parameter_groups()

    # Check if this param requires a master to be enabled
    for group_name, group_info in groups.items():
        if param_name in [p["name"] for p in group_info["dependents"]]:
            master = group_info["master"]

            # Auto-enable master if setting dependent parameter
            if master["current_value"] == 0.0:  # Master is off
                print(f"Auto-enabling {master['name']} to control {param_name}")
                await set_parameter(master["name"], 1.0)

    # Now set the target parameter
    return await set_parameter(param_name, target_value)
```

**Methodology: Learning-Time Group Detection**

**1. Static Analysis (Name-Based Grouping)**:
```python
def analyze_parameter_names(params):
    """Detect potential groups from naming patterns"""
    groups = {}

    # Pattern 1: Master/Enable switches
    masters = [p for p in params if p["name"].endswith((" On", " Enable"))]

    for master in masters:
        prefix = master["name"].replace(" On", "").replace(" Enable", "")
        related = [p for p in params if p["name"].startswith(prefix) and p != master]

        if related:
            groups[prefix] = {
                "master": master,
                "dependents": related,
                "confidence": "high" if len(related) >= 2 else "medium"
            }

    # Pattern 2: Common prefixes (e.g., "EQ Band 1", "EQ Band 2")
    prefixes = {}
    for param in params:
        words = param["name"].split()
        if len(words) >= 2:
            prefix = " ".join(words[:-1])
            prefixes.setdefault(prefix, []).append(param)

    for prefix, group_params in prefixes.items():
        if len(group_params) >= 3:  # Minimum for a meaningful group
            groups[prefix] = {
                "type": "parameter_set",
                "members": group_params,
                "confidence": "medium"
            }

    return groups
```

**2. Dynamic Analysis (Learning-Time Behavior)**:
```python
def analyze_parameter_dependencies(device_signature):
    """Analyze actual parameter behavior during learning"""
    dependencies = {}

    # Step 1: Test all binary parameters in both states
    binary_params = get_binary_parameters(device_signature)

    for binary_param in binary_params:
        # Test with binary OFF
        set_parameter(binary_param, 0.0)
        off_state_values = sample_all_parameters()

        # Test with binary ON
        set_parameter(binary_param, 1.0)
        on_state_values = sample_all_parameters()

        # Find parameters that change when this binary toggles
        affected_params = []
        for param_name, (off_val, on_val) in zip(off_state_values.keys(),
                                                zip(off_state_values.values(), on_state_values.values())):
            if abs(off_val - on_val) > 0.01:  # Significant change
                affected_params.append(param_name)

        if affected_params:
            dependencies[binary_param] = {
                "affects": affected_params,
                "type": "hard_dependency",  # Changes other params
                "confidence": "high"
            }

    return dependencies
```

**3. Audio Impact Analysis**:
```python
def analyze_audio_impact(device_signature):
    """Determine which parameters have audible effect in different contexts"""
    impact_analysis = {}

    # For each master switch state
    master_switches = get_master_switches(device_signature)

    for master in master_switches:
        for master_state in [0.0, 1.0]:
            set_parameter(master, master_state)

            # Test each dependent parameter
            dependent_params = get_dependent_parameters(master)
            for param in dependent_params:
                # Test if parameter changes have audio impact
                original_value = get_parameter_value(param)

                # Set to different value
                test_value = 0.8 if original_value < 0.5 else 0.2
                set_parameter(param, test_value)

                # Measure if audio output changed (requires audio analysis)
                audio_changed = measure_audio_difference()

                impact_analysis[param] = {
                    "master_state": master_state,
                    "audio_impact": audio_changed,
                    "dependency_type": "hard" if audio_changed else "soft"
                }

                # Restore original value
                set_parameter(param, original_value)

    return impact_analysis
```

**4. Combined Group Classification**:
```python
def classify_parameter_groups(static_groups, dynamic_deps, audio_impact):
    """Combine all analysis to create final group classification"""
    final_groups = {}

    for group_name, group_info in static_groups.items():
        master = group_info.get("master")
        dependents = group_info.get("dependents", [])

        # Enhance with dynamic analysis
        group_type = "unknown"
        if master and master["name"] in dynamic_deps:
            dep_info = dynamic_deps[master["name"]]

            if dep_info["type"] == "hard_dependency":
                group_type = "hierarchical_hard"  # Like HiFilter On -> HiFilter Freq
            else:
                group_type = "hierarchical_soft"  # Like ER Spin On -> ER Spin Rate

        # Add audio impact data
        for param in dependents:
            param_name = param["name"]
            if param_name in audio_impact:
                param["audio_dependency"] = audio_impact[param_name]["dependency_type"]

        final_groups[group_name] = {
            "type": group_type,
            "master": master,
            "dependents": dependents,
            "auto_enable": group_type == "hierarchical_hard",
            "confidence": group_info["confidence"]
        }

    return final_groups
```

**5. Learning Integration**:
```python
@app.post("/return/device/learn_with_grouping")
async def learn_device_with_group_analysis(body: LearnStartBody):
    """Enhanced learning that discovers parameter groupings"""

    # Phase 1: Static analysis
    params = get_device_parameters(body.return_index, body.device_index)
    static_groups = analyze_parameter_names(params)

    # Phase 2: Dynamic dependency testing
    dynamic_deps = analyze_parameter_dependencies(device_signature)

    # Phase 3: Audio impact analysis (optional, requires audio processing)
    # audio_impact = analyze_audio_impact(device_signature)

    # Phase 4: Standard parameter learning
    learned_params = await standard_parameter_learning(params)

    # Phase 5: Save with group metadata
    device_map = {
        "device_name": device_name,
        "parameters": learned_params,
        "parameter_groups": classify_parameter_groups(static_groups, dynamic_deps, {}),
        "learning_metadata": {
            "grouping_analysis_performed": True,
            "analysis_timestamp": datetime.now().isoformat()
        }
    }

    return save_enhanced_device_map(device_signature, device_map)
```

**Benefits of This Methodology**:
- **Automatic discovery** of parameter relationships
- **Confidence scoring** for group classifications
- **Multiple detection methods** for robustness
- **Learning-time integration** for immediate usability
- **Metadata preservation** for future improvements

**Organizing and Storing Parameter Groups**:
```python
# Enhanced device mapping storage structure
device_mapping = {
    "device_name": "Reverb",
    "signature": "36f2cd17dff059679947e2efcb14f09c8eab11bb",
    "parameters": [...],  # Individual parameter data with samples/fits
    "parameter_groups": {
        "Chorus": {
            "type": "hierarchical_soft",
            "master": {"name": "Chorus On", "index": 17},
            "dependents": [
                {"name": "Chorus Rate", "index": 18, "audio_dependency": "soft"},
                {"name": "Chorus Amount", "index": 19, "audio_dependency": "soft"}
            ],
            "auto_enable": False,  # Don't auto-enable for soft dependencies
            "confidence": "high"
        },
        "HiFilter": {
            "type": "hierarchical_hard",
            "master": {"name": "HiFilter On", "index": 10},
            "dependents": [
                {"name": "HiFilter Freq", "index": 12, "audio_dependency": "hard"},
                {"name": "HiFilter Type", "index": 11, "audio_dependency": "hard"}
            ],
            "auto_enable": True,  # Auto-enable for hard dependencies
            "confidence": "high"
        },
        "LowShelf": {
            "type": "hierarchical_hard",
            "master": {"name": "LowShelf On", "index": 14},
            "dependents": [
                {"name": "LowShelf Freq", "index": 15, "audio_dependency": "hard"},
                {"name": "LowShelf Gain", "index": 16, "audio_dependency": "hard"}
            ],
            "auto_enable": True,
            "confidence": "high"
        }
    },
    "independent_parameters": [
        {"name": "Scale", "index": 22, "type": "percentage"},
        {"name": "Stereo Image", "index": 28, "type": "percentage"},
        {"name": "Size Smoothing", "index": 27, "type": "special_range", "range": [0, 2]},
        {"name": "Diffusion", "index": 21, "type": "percentage"},
        {"name": "Reflect Level", "index": 30, "type": "normalized"},
        {"name": "Diffuse Level", "index": 31, "type": "normalized"}
    ],
    "learning_metadata": {
        "grouping_analysis_performed": True,
        "groups_detected": 3,
        "independent_params": 6,
        "binary_issues": ["Freeze On", "Chorus On toggle", "ER Spin On toggle"]
    }
}
```

**Group-Aware Parameter Control**:
```python
async def set_parameter_with_groups(device_signature, param_name, target_value):
    """Enhanced parameter setting with group awareness"""
    mapping = get_device_mapping(device_signature)
    groups = mapping.get("parameter_groups", {})

    # Check if parameter belongs to a hierarchical group
    for group_name, group_info in groups.items():
        if group_info["type"].startswith("hierarchical"):
            dependent_names = [d["name"] for d in group_info["dependents"]]

            if param_name in dependent_names:
                master = group_info["master"]

                # Check if master is enabled
                current_master_value = await get_parameter_value(master["name"])

                if current_master_value == 0.0 and group_info.get("auto_enable", False):
                    print(f"Auto-enabling {master['name']} for {param_name}")
                    await set_parameter_direct(master["name"], 1.0)
                elif current_master_value == 0.0:
                    print(f"Warning: {param_name} may have no audio effect while {master['name']} is disabled")

    # Set the target parameter
    return await set_parameter_direct(param_name, target_value)
```

### 4. Label Matching Inconsistencies
**Issue**: Quantized parameter labels may not match expected mappings.
- **Example**: "High" for Density mapped to 0.0 instead of 3.0
- **Impact**: Unreliable label-based parameter setting
- **Root Cause**: Possible mislabeled samples or case-sensitive matching

**Potential Solutions**:
- Label validation: Check learned labels during fit process
- Fuzzy matching: More robust label matching (case-insensitive, partial matches)
- Manual label correction: UI to fix mislabeled samples

## Enhancement 1: Smart Learning with Parameter Pattern Recognition

### Proposed Feature: Template-Based Fast Learning
**Goal**: Dramatically reduce learning time by recognizing common parameter patterns and applying known curve templates.

**Concept**:
Many audio parameters follow predictable mathematical patterns:
- **Frequency parameters**: Often logarithmic (20Hz-20kHz)
- **Time parameters**: Usually linear or exponential (ms, seconds)
- **Gain/Level parameters**: Typically logarithmic (dB scale)
- **Binary toggles**: Always 0/1 or On/Off
- **Quantized enums**: Discrete steps (Low/Med/High, Filter types)

**Algorithm**:
1. **Parameter Classification**: Analyze parameter name, units, range to classify type
   ```python
   def classify_parameter(name, min_val, max_val, current_samples):
       if max_val == 1.0 and min_val == 0.0:
           return classify_binary_or_continuous(name, current_samples)
       elif "freq" in name.lower() or "hz" in name.lower():
           return "frequency_log"
       elif "time" in name.lower() or "delay" in name.lower() or "ms" in name.lower():
           return "time_linear"
       elif "gain" in name.lower() or "db" in name.lower():
           return "gain_log"
       # ... more patterns
   ```

2. **Quick Template Testing**: For recognized patterns, test minimal points
   - **Binary**: Test 0.0, 0.5, 1.0 (3 points vs 41)
   - **Frequency**: Test log-spaced points (5-7 points vs 41)
   - **Linear**: Test min, mid, max (3 points vs 41)
   - **Quantized**: Test boundary values to find steps

3. **Template Fitting**: Apply known curve templates and validate R²
   ```python
   templates = {
       "frequency_log": lambda x: A * log(B * x + C),
       "time_linear": lambda x: A * x + B,
       "gain_log": lambda x: A * 20 * log10(B * x + C),
       "binary": lambda x: round(x),
   }
   ```

4. **Fallback to Full Learning**: If template doesn't fit well (R² < 0.95), fall back to traditional 41-point sampling

**Benefits**:
- **Speed**: 3-7 samples vs 41 samples = 85-90% time reduction
- **Reliability**: Templates based on audio engineering principles
- **Server Stability**: Shorter learning sessions reduce crash risk
- **User Experience**: Sub-minute learning vs 15+ minutes

**Implementation**:
```python
@app.post("/return/device/learn_smart")
async def smart_learn_device(body: LearnStartBody):
    # Get device params
    params = get_device_params(ri, di)

    learned_params = []
    for param in params:
        param_type = classify_parameter(param.name, param.min, param.max)

        if param_type in KNOWN_TEMPLATES:
            # Fast template-based learning
            samples = quick_sample_for_type(param, param_type)
            fit = apply_template(samples, param_type)

            if fit.r2 >= 0.95:  # Good fit
                learned_params.append(create_param_with_fit(param, samples, fit))
                continue

        # Fallback to traditional learning
        learned_params.append(traditional_sample_param(param))
```

**Template Library**:
- Start with common Ableton device patterns
- Learn from existing mappings to build template database
- Allow manual template assignment for edge cases

**Auto-Detection of Binary Toggles**:
```python
def is_binary_toggle(param_data):
    """Detect binary toggles from learned data patterns"""
    return (
        param_data.get("quantized") == True and
        len(param_data.get("samples", [])) == 2 and
        param_data.get("min") == 0.0 and
        param_data.get("max") == 1.0 and
        any(keyword in param_data.get("name", "").lower()
            for keyword in ["on", "cut", "flat", "freeze", "enable"])
    )
```

**Common Binary Toggle Patterns**:
- **Device states**: "Device On", "Freeze On", "Flat On"
- **Filter switches**: "LowCut On", "HighCut On", "HiFilter On"
- **Effect enables**: "Chorus On", "ER Spin On", "Cut On"
- **Processing modes**: Quantized=True + 2 samples = binary toggle

**Enhanced Binary Handling**:
When detected as binary toggle, automatically:
1. Map "On"/"1"/"True" → higher sample value
2. Map "Off"/"0"/"False" → lower sample value
3. Handle case-insensitive matching ("on", "ON", "On")
4. Support numeric targets (0, 1) and text targets ("on", "off")

## Enhancement 2: Iterative Value Refinement

### Proposed Feature: Nudge-Based Precision Improvement
**Goal**: Achieve more precise parameter values through iterative refinement.

**Algorithm**:
1. Set initial value using learned mapping/fit model
2. Read back actual display value from Live
3. Compare with target value
4. If not close enough (configurable threshold):
   - Calculate adjustment direction (+/-)
   - Apply small nudge to internal value
   - Set adjusted value
   - Read back again
5. Repeat up to 2 attempts for closer precision

**Implementation**:
```python
def set_param_with_refinement(ri, di, pi, target_display, max_attempts=2):
    for attempt in range(max_attempts + 1):
        # Initial or adjusted set
        value = calculate_value_for_target(target_display, attempt_offset)
        set_param(ri, di, pi, value)

        # Read back
        actual_display = read_param_display(ri, di, pi)

        # Check if close enough
        if is_close_enough(actual_display, target_display):
            return success(actual_display)

        # Calculate nudge for next attempt
        if attempt < max_attempts:
            attempt_offset = calculate_nudge(target_display, actual_display)

    return partial_success(actual_display)
```

**Benefits**:
- Higher precision for critical parameters
- Better user experience with more accurate results
- Adaptive to parameter non-linearities

**Configuration**:
- `precision_threshold`: How close is "close enough" (default: 5%)
- `max_nudge_attempts`: Number of refinement attempts (default: 2)
- `nudge_factor`: Size of adjustment steps (default: 0.1)

**API Addition**:
- Add `precision_mode: "standard" | "high"` to `/op/return/param_by_name`
- High precision mode enables iterative refinement

## Implementation Priority
1. **High**: Binary parameter learning enhancement
2. **Medium**: Iterative value refinement
3. **Medium**: Unit detection and validation
4. **Low**: Label matching improvements

## Comprehensive Testing Summary

**Testing Coverage**: 26 of 33 Reverb parameters tested across 5 functional groups

### ✅ **Fully Working Parameters (23)**:

**Group 1 - Chorus Parameters**:
- ✅ **Chorus Rate**: 0.02 → 0.47 (continuous, soft dependency)
- ✅ **Chorus Amount**: 0.02 → 2.01 (range 0-4, soft dependency)

**Group 2 - ER (Early Reflection) Parameters**:
- ✅ **ER Spin Rate**: 0.25 → 0.51 (continuous, soft dependency)
- ✅ **ER Spin Amount**: 7.53 → varies (continuous, soft dependency)
- ✅ **ER Shape**: 1.0 → 0.30 (independent parameter)

**Group 3 - Shelf/Filter Parameters**:
- ✅ **HiFilter Freq**: 965 → 1542 Hz (hard dependency, requires HiFilter On)
- ✅ **HiFilter Type**: 1.0 → 0.0 (quantized, hard dependency)
- ✅ **LowShelf Freq**: 89.6 → 124.0 Hz (hard dependency)
- ✅ **LowShelf Gain**: 0.46 → 0.8 (hard dependency)
- ✅ **In Filter Width**: 7.18 → 4.96 (independent)

**Group 4 - Level Parameters**:
- ✅ **Reflect Level**: 0.0 → 0.5 (independent)
- ✅ **Diffuse Level**: 0.0 → 0.9 (independent)
- ✅ **Diffusion**: 60.0 → 79.0 (independent, 0-100 scale)

**Group 5 - Other Parameters**:
- ✅ **Scale**: 40.0 → 69.0 (independent, 0-100 scale)
- ✅ **Size Smoothing**: 0.0 → 1.0 (independent, special 0-2 range)
- ✅ **Stereo Image**: 100.0 → 75.0 (independent, 0-100 scale)

**Previously Tested**:
- ✅ **Dry/Wet**: 100% → 20% → 100% (percentage with exact fit)
- ✅ **Predelay**: 2.55 → 24.3 ms (time parameter)
- ✅ **Decay Time**: 6128 → 1958 → 6128 ms (large range time parameter)
- ✅ **Room Size**: 100 → 231 → ~107 (raw value 0-500 range)
- ✅ **Density**: 3.0 → 0.0 → 3.0 (quantized 0-3)

### ⚠️ **Limited Binary Parameters (3)**:
- ⚠️ **Freeze On**: Can't enable (binary learning limitation)
- ⚠️ **Chorus On**: Can disable (1→0) but can't re-enable (0→1)
- ⚠️ **ER Spin On**: Can disable (1→0) but can't re-enable (0→1)

### 🔍 **Untested Parameters (7)**:
- **Binary switches**: Cut On, Device On, Flat On, In HighCut On, In LowCut On
- **Gain parameter**: HiShelf Gain
- **Master switch**: LowShelf On

### **Key Discoveries from Testing**:

**1. Parameter Group Types**:
- **Hierarchical Hard**: HiFilter (On → Freq + Type), LowShelf (On → Freq + Gain)
- **Hierarchical Soft**: Chorus (On → Rate + Amount), ER Spin (On → Rate + Amount)
- **Independent**: Scale, Stereo Image, Diffusion, Level parameters

**2. Parameter Range Variations**:
- **Standard 0-100**: Dry/Wet, Scale, Stereo Image, Diffusion
- **Time-based**: Predelay (ms), Decay Time (ms)
- **Frequency-based**: Filter frequencies (Hz)
- **Special ranges**: Chorus Amount (0-4), Size Smoothing (0-2), Room Size (0-500)

**3. Dependency Behavior**:
- **Hard dependencies**: Parameter changes have no audio effect when master disabled
- **Soft dependencies**: Parameter changes can be made but no audio impact when master disabled
- **Independent**: Always functional regardless of other parameter states

**4. Binary Parameter Learning Issues**:
- Many enable/disable switches only learned in one state during sampling
- Can often disable but cannot re-enable (asymmetric learned mappings)
- Suggests need for forced binary state exploration during learning

**5. Name Resolution Success**:
- ✅ **Partial matching**: "HiFilter" → "HiFilter Freq"
- ✅ **Cross-return control**: "B" → Return track 1 (B-Delay)
- ✅ **Device resolution**: "Reverb", "Delay" correctly identified
- ✅ **Parameter lookup**: All tested parameters found successfully

**6. Value Range Validation**:
- System respects learned min/max ranges for each parameter
- Out-of-range requests map to closest available learned value
- Different parameters have different display scales requiring range awareness

### **Testing Methodology Insights**:
This comprehensive testing revealed the importance of:
- **Group-aware learning** to capture parameter relationships
- **Binary state exploration** during learning phase
- **Range validation** before parameter targeting
- **Dependency detection** for hierarchical parameter control
- **Confidence scoring** for parameter group classifications

## Testing Needed
- Remaining 7 untested parameters
- Binary parameter learning enhancement
- Cross-device parameter group detection
- Iterative value refinement validation
- Performance impact of group-aware control
- Edge cases for hierarchical parameter dependencies