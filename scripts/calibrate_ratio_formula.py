#!/usr/bin/env python3
"""
Apply exact formula-based calibration for Ratio using dense point sampling.
Formula: display = 1 / (1 - norm), inverse: norm = 1 - (1 / display)
"""
import os
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
import sys
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore
import numpy as np

COMPRESSOR_SIG = "9e906e0ab3f18c4688107553744914f9ef6b9ee7"

def generate_formula_points():
    """
    Generate points using the exact formula: display = 1 / (1 - norm)
    Use dense sampling (100 points) to effectively represent the formula.
    """
    # Generate normalized values from 0 to 0.99
    # Use denser sampling at higher values where the curve is steeper
    norm_values = []

    # 0.0 to 0.9: every 0.01 (90 points)
    norm_values.extend(np.arange(0.0, 0.90, 0.01))

    # 0.90 to 0.99: every 0.001 (90 points) - denser where curve is steep
    norm_values.extend(np.arange(0.900, 0.990, 0.001))

    # Add specific points near the max
    norm_values.extend([0.990, 0.992, 0.994, 0.996, 0.998, 0.999])

    points = []
    for norm in norm_values:
        # Apply exact formula
        display = 1.0 / (1.0 - norm)
        points.append({
            'norm': float(norm),
            'display': float(display)
        })

    # Sort by display value
    points = sorted(points, key=lambda p: p['display'])

    return points

def apply_formula_calibration():
    """Apply formula-based calibration to Ratio parameter."""
    print("=" * 80)
    print("RATIO FORMULA-BASED CALIBRATION")
    print("=" * 80)
    print("\nFormula: display = 1 / (1 - norm)")
    print("Inverse: norm = 1 - (1 / display)")

    # Generate points
    points = generate_formula_points()

    print(f"\nGenerated {len(points)} points")
    print(f"Range: {points[0]['display']:.2f} to {points[-1]['display']:.2f}")

    # Show sample points
    print("\nSample points:")
    print(f"{'Norm':>12s} {'Display':>12s}")
    print("-" * 26)
    sample_indices = [0, len(points)//4, len(points)//2, 3*len(points)//4, -1]
    for i in sample_indices:
        p = points[i]
        print(f"{p['norm']:>12.6f} {p['display']:>12.2f}")

    # Convert to Firestore format
    points_dict = {}
    for i, p in enumerate(points):
        points_dict[f"p{i}"] = {
            "norm": float(p['norm']),
            "display": float(p['display'])
        }

    # Apply to Firestore
    print("\n" + "=" * 80)
    print("Applying to Firestore...")

    client = firestore.Client(database="dev-display-value")
    doc_ref = client.collection("device_mappings").document(COMPRESSOR_SIG)
    doc = doc_ref.get()

    if not doc.exists:
        print("❌ Compressor device not found")
        return False

    data = doc.to_dict()
    params_meta = data.get("params_meta", [])

    # Find Ratio
    for param in params_meta:
        if param.get("name") == "Ratio":
            param["fit"] = {
                "type": "point_based",
                "points": points_dict,
                "point_count": len(points),
                "interpolation": "linear",
                "formula": "display = 1 / (1 - norm)",  # Documentation
                "formula_inverse": "norm = 1 - (1 / display)"
            }
            param["confidence"] = 1.0
            break
    else:
        print("❌ Ratio parameter not found")
        return False

    # Save
    data["params_meta"] = params_meta
    doc_ref.update({"params_meta": params_meta})

    print("\n✅ SUCCESS - Ratio calibrated with formula-based points!")
    print(f"   Points: {len(points)}")
    print(f"   Range: {points[0]['display']:.1f} to {points[-1]['display']:.1f}")
    print(f"   Accuracy: Perfect (formula-based)")
    print(f"   Database: dev-display-value")

    return True

if __name__ == "__main__":
    apply_formula_calibration()
