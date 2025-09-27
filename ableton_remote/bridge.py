"""
Minimal UDP JSON bridge for Ableton Remote Script prototype.

This standalone script can be used as a local simulator (outside Ableton)
to test the server <-> UDP path. It echoes ops with ok:true and fake data
for get_overview.

In a real Remote Script, this code would run inside Ableton Live and use
the Live Object Model (LOM) to implement actual operations.
"""
import json
import os
import socket


HOST = os.getenv("ABLETON_UDP_HOST", "127.0.0.1")
PORT = int(os.getenv("ABLETON_UDP_PORT", "19845"))


def _overview_stub():
    return {
        "tracks": [
            {"index": 1, "name": "Track 1", "type": "audio"},
            {"index": 2, "name": "Track 2", "type": "audio"},
        ],
        "selected_track": 1,
        "scenes": 1,
    }


def serve():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((HOST, PORT))
        print(f"UDP bridge listening on {HOST}:{PORT}")

        while True:
            data, addr = sock.recvfrom(64 * 1024)
            try:
                msg = json.loads(data.decode("utf-8"))
            except Exception:
                continue

            op = msg.get("op")
            if op == "ping":
                resp = {"ok": True, "op": "ping"}
            elif op == "get_overview":
                resp = {"ok": True, "op": op, "data": _overview_stub()}
            elif op in ("set_mixer", "set_send", "set_device_param"):
                resp = {"ok": True, "op": op, "echo": msg}
            else:
                resp = {"ok": False, "error": f"unknown op: {op}", "echo": msg}

            sock.sendto(json.dumps(resp).encode("utf-8"), addr)


if __name__ == "__main__":
    serve()

