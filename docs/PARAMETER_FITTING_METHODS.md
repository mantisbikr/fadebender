# Parameter Fitting Methods Analysis

## Overview
This document summarizes the mathematical fitting approaches used for Ableton Live device parameters, based on analysis of the Reverb device parameter mappings. These patterns provide guidance for parameter learning and model selection.

## Fitting Method Distribution (Most to Least Frequent)

### 1. **LINEAR** (9/22 parameters - 41%)
**Best for:** Level controls, percentages, gain parameters, mix ratios

**Characteristics:**
- Model: `y = a*x + b`
- Excellent accuracy (R² > 0.999 for most parameters)
- Used for parameters with direct proportional relationships

**Parameter Types:**
- **Mix/Level Controls:** Dry/Wet (99.99%), Chorus Amount (99.99%)
- **Gain Controls:** HiShelf Gain (100%), LowShelf Gain (100%)
- **Spatial Controls:** Stereo Image (100%), Diffusion (99.99%)
- **Shape Controls:** ER Shape (99.99%), Scale (99.99%)
- **Filter Controls:** In Filter Width (99.99%)

### 2. **EXPONENTIAL** (9/22 parameters - 41%)
**Best for:** Time-based controls, frequency parameters, rate controls

**Characteristics:**
- Model: `y = a * e^(b*x)`
- Near-perfect accuracy for time/frequency domains
- Natural for parameters with logarithmic human perception

**Parameter Types:**
- **Time Controls:** Decay Time (100%), Predelay (99.99%)
- **Frequency Controls:** In Filter Freq (100%), LowShelf Freq (100%), HiFilter Freq (100%)
- **Spatial Controls:** Room Size (99.99%)
- **Modulation Controls:** ER Spin Rate (99.96%), ER Spin Amount (100%), Chorus Rate (99.87%)

### 3. **PIECEWISE** (4/22 parameters - 18%)
**Best for:** Complex parameters, quantized controls, non-monotonic relationships

**Characteristics:**
- Model: Series of connected linear segments
- Lower accuracy (R² 0.76-0.89) due to complex underlying relationships
- Used when simple mathematical functions fail

**Parameter Types:**
- **Complex Controls:** Density (89.09%), Size Smoothing (75.57%)
- **Level Controls:** Reflect Level (80.67%), Diffuse Level (80.67%)

## Parameter Classification Guidelines

### Use **LINEAR** fitting for:
- Percentage controls (0-100%)
- dB gain controls
- Mix ratios and blend controls
- Stereo width/imaging
- Filter bandwidth/width parameters

### Use **EXPONENTIAL** fitting for:
- Time parameters (ms, seconds)
- Frequency parameters (Hz, kHz)
- Rate/speed controls
- Room/space simulation parameters
- Parameters with logarithmic scaling

### Use **PIECEWISE** fitting for:
- Quantized parameters with complex stepping
- Parameters with plateau regions
- Controls with non-monotonic behavior
- Complex algorithmic parameters where simple math fails

## Quality Thresholds

### Excellent Fit (R² ≥ 0.999)
- **Linear:** 7/9 parameters
- **Exponential:** 7/9 parameters
- Ready for production use

### Good Fit (R² ≥ 0.99)
- **Linear:** 9/9 parameters
- **Exponential:** 8/9 parameters
- Acceptable for most use cases

### Acceptable Fit (R² ≥ 0.75)
- **Piecewise:** 4/4 parameters
- May require refinement or additional samples

## Implementation Notes

1. **Binary Parameters:** Device switches (On/Off) use `"fit": null` - no curve fitting needed
2. **Fitting Selection:** The system automatically selects the best-fitting model type based on R² scores
3. **Confidence Scoring:** R² values indicate fitting quality and prediction reliability
4. **Parameter Groups:** Fitting methods often correlate with parameter functional groups (Global, Input, Early, Tail, Chorus)

## Future Enhancements

- **Template-based Learning:** Use fitting method patterns to predict optimal approaches for new devices
- **Hybrid Models:** Combine multiple fitting approaches for complex parameters
- **Adaptive Sampling:** Increase sample density in regions where piecewise fits show low confidence