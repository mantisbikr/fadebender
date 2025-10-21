#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
from urllib import request

BASE = "http://127.0.0.1:8722"


def http_json(method: str, path: str, body: dict | None = None):
    url = BASE + path
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    with request.urlopen(req, timeout=3.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def expect_caps(resp, label):
    if not isinstance(resp, dict) or not resp.get("ok", False):
        return False, f"{label}: not ok ({resp})"
    data = resp.get("data") or {}
    if not isinstance(data, dict) or not data.get("capabilities"):
        return False, f"{label}: missing capabilities"
    return True, f"{label}: ok"


def main():
    fails = []
    # Track mixer
    r = http_json("POST", "/intent/execute", {
        "domain": "track", "track_index": 1, "field": "volume", "value": -6, "unit": "dB"
    })
    ok, msg = expect_caps(r, "track.volume")
    print(msg)
    if not ok: fails.append(msg)

    # Track send A
    r = http_json("POST", "/intent/execute", {
        "domain": "track", "track_index": 1, "field": "send", "send_ref": "A", "value": -12, "unit": "dB"
    })
    ok, msg = expect_caps(r, "track.sendA")
    print(msg)
    if not ok: fails.append(msg)

    # Return volume (A)
    r = http_json("POST", "/intent/execute", {
        "domain": "return", "return_ref": "A", "field": "volume", "value": -12, "unit": "dB"
    })
    ok, msg = expect_caps(r, "return.volumeA")
    print(msg)
    if not ok: fails.append(msg)

    # Return send B
    r = http_json("POST", "/intent/execute", {
        "domain": "return", "return_ref": "A", "field": "send", "send_ref": "B", "value": -10, "unit": "dB"
    })
    ok, msg = expect_caps(r, "return.sendB")
    print(msg)
    if not ok: fails.append(msg)

    # Master volume
    r = http_json("POST", "/intent/execute", {
        "domain": "master", "field": "volume", "value": -6, "unit": "dB"
    })
    ok, msg = expect_caps(r, "master.volume")
    print(msg)
    if not ok: fails.append(msg)

    if fails:
        print("\nFAILURES:")
        for f in fails:
            print("- ", f)
        sys.exit(1)
    print("\nAll capability checks passed.")


if __name__ == "__main__":
    main()

