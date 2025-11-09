#!/usr/bin/env python3
"""
Fit curves for Compressor continuous parameters using preset data.
Phase 4 of device mapping standardization.
"""
import sys
import os
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
import json

COMPRESSOR_SIG = "9e906e0ab3f18c4688107553744914f9ef6b9ee7"

# Fitting functions
def linear_fit(x, a, b):
    """y = a*x + b"""
    return a * x + b

def exponential_fit(x, a, b, c):
    """y = a * exp(b*x) + c"""
    return a * np.exp(b * x) + c

def logarithmic_fit(x, a, b, c):
    """y = a * log(b*x + 1) + c"""
    return a * np.log(b * x + 1) + c

def power_fit(x, a, b, c):
    """y = a * x^b + c"""
    return a * np.power(x, b) + c


def fit_parameter(norm_values, display_values, param_name):
    """
    Try multiple curve types and return the best fit.

    Returns:
        dict with keys: type, coeffs, r2
    """
    x = np.array(norm_values)
    y = np.array(display_values)

    if len(x) < 3:
        print(f"  ⚠️  {param_name}: Not enough data points ({len(x)}), using linear")
        return fit_linear(x, y)

    fits = []

    # Try linear
    try:
        fit = fit_linear(x, y)
        fits.append(("linear", fit))
    except Exception as e:
        print(f"  ⚠️  {param_name}: Linear fit failed: {e}")

    # Try exponential
    try:
        fit = fit_exponential(x, y)
        fits.append(("exponential", fit))
    except Exception as e:
        pass  # Exponential often fails, don't spam

    # Try logarithmic
    try:
        fit = fit_logarithmic(x, y)
        fits.append(("logarithmic", fit))
    except Exception as e:
        pass

    # Try power
    try:
        fit = fit_power(x, y)
        fits.append(("power", fit))
    except Exception as e:
        pass

    if not fits:
        print(f"  ❌ {param_name}: All fits failed, using fallback linear")
        # Fallback: simple linear from min to max
        a = y.max() - y.min()
        b = y.min()
        return {
            "type": "linear",
            "coeffs": {"a": float(a), "b": float(b)},
            "r2": 0.0
        }

    # Choose best fit by R²
    best_name, best_fit = max(fits, key=lambda f: f[1]["r2"])

    return best_fit


def fit_linear(x, y):
    """Fit linear: y = a*x + b"""
    popt, _ = curve_fit(linear_fit, x, y)
    a, b = popt
    y_pred = linear_fit(x, a, b)
    r2 = pearsonr(y, y_pred)[0] ** 2

    return {
        "type": "linear",
        "coeffs": {"a": float(a), "b": float(b)},
        "r2": float(r2)
    }


def fit_exponential(x, y):
    """Fit exponential: y = a * exp(b*x) + c"""
    # Initial guess
    p0 = [y.max() - y.min(), 1.0, y.min()]
    popt, _ = curve_fit(exponential_fit, x, y, p0=p0, maxfev=5000)
    a, b, c = popt
    y_pred = exponential_fit(x, a, b, c)
    r2 = pearsonr(y, y_pred)[0] ** 2

    return {
        "type": "exponential",
        "coeffs": {"a": float(a), "b": float(b), "c": float(c)},
        "r2": float(r2)
    }


def fit_logarithmic(x, y):
    """Fit logarithmic: y = a * log(b*x + 1) + c"""
    # Initial guess
    p0 = [y.max() - y.min(), 1.0, y.min()]
    popt, _ = curve_fit(logarithmic_fit, x, y, p0=p0, maxfev=5000)
    a, b, c = popt
    y_pred = logarithmic_fit(x, a, b, c)
    r2 = pearsonr(y, y_pred)[0] ** 2

    return {
        "type": "logarithmic",
        "coeffs": {"a": float(a), "b": float(b), "c": float(c)},
        "r2": float(r2)
    }


def fit_power(x, y):
    """Fit power: y = a * x^b + c"""
    # Initial guess
    p0 = [y.max() - y.min(), 2.0, y.min()]
    popt, _ = curve_fit(power_fit, x, y, p0=p0, maxfev=5000)
    a, b, c = popt
    y_pred = power_fit(x, a, b, c)
    r2 = pearsonr(y, y_pred)[0] ** 2

    return {
        "type": "power",
        "coeffs": {"a": float(a), "b": float(b), "c": float(c)},
        "r2": float(r2)
    }


def main():
    """Extract preset data, fit curves, update device mapping."""

    client = firestore.Client(database="dev-display-value")

    # Step 1: Get all presets for Compressor
    print("=" * 80)
    print("STEP 1: Loading Compressor presets")
    print("=" * 80)

    presets_query = client.collection("presets").where("structure_signature", "==", COMPRESSOR_SIG)
    presets = list(presets_query.stream())

    print(f"✓ Found {len(presets)} presets")

    # Step 2: Extract parameter data
    print("\n" + "=" * 80)
    print("STEP 2: Extracting parameter values")
    print("=" * 80)

    # Collect data: param_name -> [(norm_val, display_val), ...]
    param_data = {}

    for preset_doc in presets:
        preset = preset_doc.to_dict()
        param_values = preset.get("parameter_values", {})
        param_display_values = preset.get("parameter_display_values", {})

        for param_name, norm_val in param_values.items():
            display_val = param_display_values.get(param_name)
            if display_val is not None and norm_val is not None:
                if param_name not in param_data:
                    param_data[param_name] = []
                param_data[param_name].append((float(norm_val), float(display_val)))

    print(f"✓ Collected data for {len(param_data)} parameters")
    for name, points in param_data.items():
        print(f"  - {name}: {len(points)} data points")

    # Step 3: Load device mapping to identify continuous parameters
    print("\n" + "=" * 80)
    print("STEP 3: Loading device mapping")
    print("=" * 80)

    device_doc = client.collection("device_mappings").document(COMPRESSOR_SIG).get()
    device_data = device_doc.to_dict()
    params_meta = device_data.get("params_meta", [])

    print(f"✓ Loaded device mapping with {len(params_meta)} parameters")

    # Step 4: Fit curves for continuous parameters
    print("\n" + "=" * 80)
    print("STEP 4: Fitting curves for continuous parameters")
    print("=" * 80)

    fitted_count = 0
    for param in params_meta:
        param_name = param.get("name")
        control_type = param.get("control_type")

        if control_type != "continuous":
            continue

        if param_name not in param_data:
            print(f"  ⚠️  {param_name}: No preset data available")
            continue

        data_points = param_data[param_name]
        norm_vals = [p[0] for p in data_points]
        disp_vals = [p[1] for p in data_points]

        print(f"\n  {param_name}:")
        print(f"    Data points: {len(data_points)}")
        print(f"    Norm range: [{min(norm_vals):.3f}, {max(norm_vals):.3f}]")
        print(f"    Display range: [{min(disp_vals):.3f}, {max(disp_vals):.3f}]")

        # Fit
        fit_result = fit_parameter(norm_vals, disp_vals, param_name)

        # Update param
        param["fit"] = fit_result
        param["confidence"] = fit_result["r2"]

        print(f"    Best fit: {fit_result['type']} (R² = {fit_result['r2']:.4f})")
        print(f"    Coefficients: {fit_result['coeffs']}")

        fitted_count += 1

    print(f"\n✓ Fitted {fitted_count} continuous parameters")

    # Step 5: Update Firestore
    print("\n" + "=" * 80)
    print("STEP 5: Updating Firestore")
    print("=" * 80)

    device_data["params_meta"] = params_meta

    doc_ref = client.collection("device_mappings").document(COMPRESSOR_SIG)
    doc_ref.update({"params_meta": params_meta})

    print("✅ SUCCESS - Compressor curves fitted and updated!")
    print(f"   Database: dev-display-value")
    print(f"   Signature: {COMPRESSOR_SIG}")
    print(f"   Fitted parameters: {fitted_count}")


if __name__ == "__main__":
    main()
