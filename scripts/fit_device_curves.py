#!/usr/bin/env python3
"""
Generic device curve fitting tool - fits curves for continuous parameters using preset data.

Usage:
  python3 fit_device_curves.py --signature <device_sig> [--database dev-display-value]

Examples:
  # Fit Compressor curves from presets
  python3 fit_device_curves.py --signature 9e906e0ab3f18c4688107553744914f9ef6b9ee7

  # Fit Reverb curves (example)
  python3 fit_device_curves.py --signature abc123... --database default
"""
import sys
import os
import argparse
os.environ["FIRESTORE_DATABASE_ID"] = os.environ.get("FIRESTORE_DATABASE_ID", "dev-display-value")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud import firestore
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
import json


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
        dict with keys: type, coeffs, r_squared
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
    except Exception:
        pass  # Exponential often fails, don't spam

    # Try logarithmic
    try:
        fit = fit_logarithmic(x, y)
        fits.append(("logarithmic", fit))
    except Exception:
        pass

    # Try power
    try:
        fit = fit_power(x, y)
        fits.append(("power", fit))
    except Exception:
        pass

    if not fits:
        print(f"  ❌ {param_name}: All fits failed, using fallback linear")
        # Fallback: simple linear from min to max
        a = y.max() - y.min()
        b = y.min()
        return {
            "type": "linear",
            "function": "linear",
            "coeffs": {"a": float(a), "b": float(b)},
            "r_squared": 0.0
        }

    # Choose best fit by R²
    best_name, best_fit = max(fits, key=lambda f: f[1]["r_squared"])

    return best_fit


def fit_linear(x, y):
    """Fit linear: y = a*x + b"""
    popt, _ = curve_fit(linear_fit, x, y)
    a, b = popt
    y_pred = linear_fit(x, a, b)
    r2 = pearsonr(y, y_pred)[0] ** 2

    return {
        "type": "linear",
        "function": "linear",
        "coeffs": {"a": float(a), "b": float(b)},
        "r_squared": float(r2)
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
        "function": "exponential",
        "coeffs": {"a": float(a), "b": float(b), "c": float(c)},
        "r_squared": float(r2)
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
        "function": "logarithmic",
        "coeffs": {"a": float(a), "b": float(b), "c": float(c)},
        "r_squared": float(r2)
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
        "function": "power",
        "coeffs": {"a": float(a), "b": float(b), "c": float(c)},
        "r_squared": float(r2)
    }


def fit_device_curves(device_sig, database="dev-display-value", auto_confirm=False):
    """Extract preset data, fit curves, update device mapping."""

    client = firestore.Client(database=database)

    # Step 1: Get all presets for device
    print("=" * 80)
    print("STEP 1: Loading device presets")
    print("=" * 80)
    print(f"Device signature: {device_sig}")
    print(f"Database: {database}")

    presets_query = client.collection("presets").where("structure_signature", "==", device_sig)
    presets = list(presets_query.stream())

    if not presets:
        print(f"❌ No presets found for signature: {device_sig}")
        return False

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

    device_doc = client.collection("device_mappings").document(device_sig).get()

    if not device_doc.exists:
        print(f"❌ Device mapping not found for signature: {device_sig}")
        return False

    device_data = device_doc.to_dict()
    params_meta = device_data.get("params_meta", [])
    device_name = device_data.get("device_name", "Unknown Device")

    print(f"✓ Loaded {device_name} mapping with {len(params_meta)} parameters")

    # Step 4: Fit curves for continuous parameters
    print("\n" + "=" * 80)
    print("STEP 4: Fitting curves for continuous parameters")
    print("=" * 80)

    fitted_count = 0
    skipped_count = 0

    for param in params_meta:
        param_name = param.get("name")
        control_type = param.get("control_type")

        if control_type != "continuous":
            continue

        if param_name not in param_data:
            print(f"  ⚠️  {param_name}: No preset data available (skipping)")
            skipped_count += 1
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
        param["confidence"] = fit_result["r_squared"]

        print(f"    Best fit: {fit_result['type']} (R² = {fit_result['r_squared']:.4f})")
        print(f"    Coefficients: {fit_result['coeffs']}")

        fitted_count += 1

    print(f"\n✓ Fitted {fitted_count} continuous parameters")
    if skipped_count > 0:
        print(f"⚠️  Skipped {skipped_count} parameters (no preset data)")

    # Step 5: Preview and confirm
    print("\n" + "=" * 80)
    print("PREVIEW")
    print("=" * 80)
    print(f"Device: {device_name}")
    print(f"Signature: {device_sig}")
    print(f"Database: {database}")
    print(f"Parameters fitted: {fitted_count}")
    print(f"Parameters skipped: {skipped_count}")

    if fitted_count == 0:
        print("\n❌ No parameters were fitted - aborting")
        return False

    # Confirm
    print("\n" + "=" * 80)
    if auto_confirm:
        print("Auto-confirming changes...")
        response = 'yes'
    else:
        response = input("Apply curve fits to Firestore? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("❌ Aborted - no changes made")
        return False

    # Step 6: Update Firestore
    print("\n" + "=" * 80)
    print("STEP 5: Updating Firestore")
    print("=" * 80)

    device_data["params_meta"] = params_meta

    doc_ref = client.collection("device_mappings").document(device_sig)
    doc_ref.update({"params_meta": params_meta})

    print(f"\n✅ SUCCESS - {device_name} curves fitted and updated!")
    print(f"   Database: {database}")
    print(f"   Signature: {device_sig}")
    print(f"   Fitted parameters: {fitted_count}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Fit curves for device continuous parameters using preset data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fit Compressor curves
  python3 fit_device_curves.py --signature 9e906e0ab3f18c4688107553744914f9ef6b9ee7

  # Fit using different database
  python3 fit_device_curves.py --signature abc123... --database default

  # Auto-confirm (no prompt)
  python3 fit_device_curves.py --signature abc123... --yes
"""
    )

    parser.add_argument('--signature', '-s', required=True,
                       help='Device structure signature (SHA1 hash)')
    parser.add_argument('--database', '-d', default='dev-display-value',
                       help='Firestore database ID (default: dev-display-value)')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Auto-confirm changes without prompting')

    args = parser.parse_args()

    # Set database env var
    os.environ["FIRESTORE_DATABASE_ID"] = args.database

    success = fit_device_curves(
        device_sig=args.signature,
        database=args.database,
        auto_confirm=args.yes
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
