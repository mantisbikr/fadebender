#!/usr/bin/env python3
"""
Generic parameter calibration tool - works for any device parameter.

Usage:
  # Automatic sweep calibration
  python3 calibrate_parameter.py --device SIGNATURE --param "Parameter Name" \\
    --return-index 2 --device-index 0 --mode auto

  # Manual point capture (for interactive use)
  python3 calibrate_parameter.py --device SIGNATURE --param "Parameter Name" \\
    --return-index 2 --device-index 0 --mode manual --add 50.0

  # Formula-based (e.g., for Ratio)
  python3 calibrate_parameter.py --device SIGNATURE --param "Ratio" \\
    --return-index 2 --device-index 0 --mode formula --formula "1/(1-x)"

  # Apply linear fit
  python3 calibrate_parameter.py --device SIGNATURE --param "S/C Mix" \\
    --return-index 2 --device-index 0 --mode linear --a 100.0 --b 0.0
"""
import os
os.environ["FIRESTORE_DATABASE_ID"] = os.environ.get("FIRESTORE_DATABASE_ID", "dev-display-value")
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud import firestore
from server.services.ableton_client import request_op
import argparse
import json
import time
import numpy as np
from pathlib import Path

CALIBRATION_DIR = Path("/tmp/fadebender_calibrations")
CALIBRATION_DIR.mkdir(exist_ok=True)


class ParameterCalibrator:
    """Generic parameter calibration tool."""

    def __init__(self, device_sig, param_name, return_index=None, track_index=None,
                 device_index=0, database="dev-display-value"):
        self.device_sig = device_sig
        self.param_name = param_name
        self.return_index = return_index
        self.track_index = track_index
        self.device_index = device_index
        self.database = database
        self.param_index = None

        # Find parameter index
        self._find_param_index()

    def _find_param_index(self):
        """Find parameter index by name."""
        if self.return_index is not None:
            result = request_op("get_return_device_params",
                              return_index=self.return_index,
                              device_index=self.device_index)
        elif self.track_index is not None:
            result = request_op("get_track_device_params",
                              track_index=self.track_index,
                              device_index=self.device_index)
        else:
            raise ValueError("Must specify either return_index or track_index")

        if result:
            params = result.get('data', {}).get('params', [])
            for p in params:
                if p.get('name') == self.param_name:
                    self.param_index = p['index']
                    print(f"Found '{self.param_name}' at index {self.param_index}")
                    return

        raise ValueError(f"Parameter '{self.param_name}' not found")

    def read_value(self):
        """Read current parameter value."""
        if self.return_index is not None:
            result = request_op("get_return_device_params",
                              return_index=self.return_index,
                              device_index=self.device_index)
        else:
            result = request_op("get_track_device_params",
                              track_index=self.track_index,
                              device_index=self.device_index)

        if result:
            params = result.get('data', {}).get('params', [])
            param = next((p for p in params if p['index'] == self.param_index), None)
            if param:
                try:
                    display = float(param['display_value'])
                    return {
                        'norm': float(param['value']),
                        'display': display
                    }
                except (ValueError, TypeError):
                    return None
        return None

    def set_value(self, norm_value):
        """Set parameter to normalized value."""
        if self.return_index is not None:
            request_op("set_return_device_param",
                      return_index=self.return_index,
                      device_index=self.device_index,
                      param_index=self.param_index,
                      value=norm_value)
        else:
            request_op("set_track_device_param",
                      track_index=self.track_index,
                      device_index=self.device_index,
                      param_index=self.param_index,
                      value=norm_value)
        time.sleep(0.05)

    def calibrate_auto(self, num_points=50, dense_range=None):
        """
        Automatic calibration by sweeping normalized values.

        Args:
            num_points: Number of points to sample
            dense_range: Tuple (start, end) for denser sampling in that range
        """
        print(f"\nAutomatic calibration: {self.param_name}")
        print(f"Sampling {num_points} points...")

        norm_values = np.linspace(0.0, 1.0, num_points)

        # Add dense sampling if requested
        if dense_range:
            start, end = dense_range
            dense_points = np.linspace(start, end, num_points // 2)
            norm_values = np.concatenate([norm_values, dense_points])
            norm_values = np.unique(np.sort(norm_values))

        points = []
        print(f"\n{'Norm':>12s} {'Display':>15s}")
        print("-" * 30)

        for norm in norm_values:
            self.set_value(norm)
            data = self.read_value()
            if data and data['display'] < 1e10:  # Skip infinity
                points.append(data)
                print(f"{data['norm']:>12.6f} {data['display']:>15.2f}")

        return points

    def calibrate_formula(self, formula_str):
        """
        Generate points using a mathematical formula.

        Args:
            formula_str: Formula string like "1/(1-x)" where x is normalized value
        """
        print(f"\nFormula-based calibration: {self.param_name}")
        print(f"Formula: {formula_str}")

        # Generate dense points
        norm_values = []
        norm_values.extend(np.arange(0.0, 0.90, 0.01))
        norm_values.extend(np.arange(0.900, 0.990, 0.001))
        norm_values.extend([0.990, 0.992, 0.994, 0.996, 0.998, 0.999])

        points = []
        for norm in norm_values:
            try:
                x = norm
                display = eval(formula_str)
                if not np.isnan(display) and not np.isinf(display):
                    points.append({'norm': float(norm), 'display': float(display)})
            except:
                pass

        print(f"Generated {len(points)} points")
        return points

    def apply_fit(self, fit_data):
        """Apply fit to Firestore."""
        print(f"\nApplying fit to Firestore...")

        client = firestore.Client(database=self.database)

        # Determine collection
        if self.return_index is not None:
            # Device mapping
            doc_ref = client.collection("device_mappings").document(self.device_sig)
        else:
            # Track device mapping (future support)
            doc_ref = client.collection("device_mappings").document(self.device_sig)

        doc = doc_ref.get()
        if not doc.exists:
            print(f"❌ Device {self.device_sig} not found")
            return False

        data = doc.to_dict()
        params_meta = data.get("params_meta", [])

        # Find parameter
        for param in params_meta:
            if param.get("name") == self.param_name:
                param["fit"] = fit_data
                param["confidence"] = 1.0
                break
        else:
            print(f"❌ Parameter '{self.param_name}' not found in Firestore")
            return False

        # Save
        doc_ref.update({"params_meta": params_meta})
        print(f"✅ Fit applied successfully")
        return True

    def save_points(self, points):
        """Save calibration points to file."""
        filename = CALIBRATION_DIR / f"{self.device_sig}_{self.param_name.replace(' ', '_')}.json"
        with open(filename, 'w') as f:
            json.dump(points, f, indent=2)
        print(f"Points saved to: {filename}")
        return filename

    def load_points(self):
        """Load calibration points from file."""
        filename = CALIBRATION_DIR / f"{self.device_sig}_{self.param_name.replace(' ', '_')}.json"
        if filename.exists():
            with open(filename, 'r') as f:
                return json.load(f)
        return None


def main():
    parser = argparse.ArgumentParser(description="Generic parameter calibration tool")

    # Device identification
    parser.add_argument('--device', required=True, help='Device signature')
    parser.add_argument('--param', required=True, help='Parameter name')
    parser.add_argument('--return-index', type=int, help='Return track index')
    parser.add_argument('--track-index', type=int, help='Track index')
    parser.add_argument('--device-index', type=int, default=0, help='Device index (default: 0)')
    parser.add_argument('--database', default='dev-display-value', help='Firestore database')

    # Calibration mode
    parser.add_argument('--mode', choices=['auto', 'manual', 'formula', 'linear', 'apply'],
                       required=True, help='Calibration mode')

    # Mode-specific options
    parser.add_argument('--num-points', type=int, default=50, help='Number of points for auto mode')
    parser.add_argument('--formula', help='Formula for formula mode (e.g., "1/(1-x)")')
    parser.add_argument('--a', type=float, help='Linear coefficient a (display = a*norm + b)')
    parser.add_argument('--b', type=float, help='Linear coefficient b')
    parser.add_argument('--add', type=float, help='Manual mode: add point at this display value')
    parser.add_argument('--fit-file', help='JSON file with fit data to apply')

    args = parser.parse_args()

    # Create calibrator
    cal = ParameterCalibrator(
        device_sig=args.device,
        param_name=args.param,
        return_index=args.return_index,
        track_index=args.track_index,
        device_index=args.device_index,
        database=args.database
    )

    # Execute calibration
    if args.mode == 'auto':
        points = cal.calibrate_auto(num_points=args.num_points)
        cal.save_points(points)

        # Convert to Firestore format
        points_dict = {f"p{i}": {"norm": p['norm'], "display": p['display']}
                      for i, p in enumerate(sorted(points, key=lambda x: x['display']))}

        fit_data = {
            "type": "point_based",
            "points": points_dict,
            "point_count": len(points),
            "interpolation": "linear"
        }
        cal.apply_fit(fit_data)

    elif args.mode == 'formula':
        if not args.formula:
            print("❌ --formula required for formula mode")
            return 1

        points = cal.calibrate_formula(args.formula)
        cal.save_points(points)

        points_dict = {f"p{i}": {"norm": p['norm'], "display": p['display']}
                      for i, p in enumerate(sorted(points, key=lambda x: x['display']))}

        fit_data = {
            "type": "point_based",
            "points": points_dict,
            "point_count": len(points),
            "interpolation": "linear",
            "formula": args.formula
        }
        cal.apply_fit(fit_data)

    elif args.mode == 'linear':
        if args.a is None or args.b is None:
            print("❌ --a and --b required for linear mode")
            return 1

        fit_data = {
            "type": "linear",
            "function": "linear",
            "coeffs": {"a": args.a, "b": args.b},
            "r_squared": 1.0
        }
        cal.apply_fit(fit_data)

    elif args.mode == 'manual':
        if args.add is not None:
            # Read current normalized value
            data = cal.read_value()
            if data:
                points = cal.load_points() or []
                points.append({'display': args.add, 'norm': data['norm']})
                cal.save_points(points)
                print(f"✓ Point added: {args.add} → {data['norm']:.6f}")
                print(f"Total points: {len(points)}")
        else:
            print("❌ --add required for manual mode")
            return 1

    elif args.mode == 'apply':
        points = cal.load_points()
        if not points:
            print("❌ No saved points found")
            return 1

        points_dict = {f"p{i}": {"norm": p['norm'], "display": p['display']}
                      for i, p in enumerate(sorted(points, key=lambda x: x['display']))}

        fit_data = {
            "type": "point_based",
            "points": points_dict,
            "point_count": len(points),
            "interpolation": "linear"
        }
        cal.apply_fit(fit_data)

    return 0


if __name__ == "__main__":
    sys.exit(main())
