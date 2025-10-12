#!/usr/bin/env python3
"""
Import device mapping analysis (grouping + params_meta + sources) into the server.

Usage:
  python3 scripts/import_mapping_analysis.py --file analysis.json
  python3 scripts/import_mapping_analysis.py --signature <SIG> --grouping grouping.json --params params_meta.json

The script calls POST /device_mapping/import on the local server.
"""
import argparse
import json
import sys
import urllib.request

SERVER = "http://127.0.0.1:8722"


def _post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="Combined analysis JSON file")
    ap.add_argument("--signature", help="Signature (if providing separate files)")
    ap.add_argument("--grouping", help="Grouping JSON file")
    ap.add_argument("--params", help="Params meta JSON file")
    ap.add_argument("--status", help="analysis_status value (e.g., partial_fits/analyzed)")
    args = ap.parse_args()

    body = {}
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            body = json.load(f)
        if not body.get("signature"):
            print("analysis.json missing 'signature'", file=sys.stderr)
            sys.exit(2)
    else:
        if not args.signature:
            print("--signature required without --file", file=sys.stderr)
            sys.exit(2)
        body["signature"] = args.signature
        if args.grouping:
            with open(args.grouping, "r", encoding="utf-8") as f:
                body["grouping"] = json.load(f)
        if args.params:
            with open(args.params, "r", encoding="utf-8") as f:
                body["params_meta"] = json.load(f)
    if args.status:
        body["analysis_status"] = args.status

    res = _post(f"{SERVER}/device_mapping/import", body)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()

