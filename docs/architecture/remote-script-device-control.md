Sure — here’s the complete markdown file in one copy-ready block. You can save it directly as
docs/remote-script-device-control.md in your VS Code project.

⸻


# Fadebender Remote Script — Device Add/Delete & Capture Timing

**Author:** Sunil Satyamurti  
**Target:** Ableton Live (macOS)  
**Purpose:** Automate adding and deleting devices (presets) via your custom Remote Script, expose simple HTTP/OSC hooks, and include timing controls so Firestore can reliably capture new devices before removal.

---

## 0 · Overview

- **Delete:** fully supported through the Live Object Model (LOM) → `Track.delete_device(index)` / `Chain.delete_device(index)`  
- **Add:**  
  - Live 12.3 + only — `Track.insert_device(index, identifier)` and `Chain.insert_device(index, identifier)` for built-in devices  
  - Older Lives — fallback to **UI automation** (Cmd + F → type → Enter) from your external orchestrator  
- This doc defines both, so your automation can use the LOM path when available and fall back gracefully.

---

## 1 · Structure

FadebenderRemote/
init.py
fadebender_remote.py
api/
http_server.py
osc_server.py
ops/
device_ops.py
timing.py
config.py
README.md

---

## 2 · Config (`config.py`)

```python
HTTP_PORT = 8723
OSC_PORT  = 8724
TARGET = dict(kind="return", index=0)     # Return A
DELETE_MODE = "last"                      # or "selected"

CAPTURE_DELAY_SEC   = 1.25
VERIFY_TIMEOUT_SEC  = 8.0
VERIFY_BACKOFF      = [0.6, 0.8, 1.0, 1.2]

ENABLE_INSERT_DEVICE = True               # guard for Live 12.3+


⸻

3 · Device Operations (ops/device_ops.py)

from _Framework.ControlSurface import ControlSurface

class DeviceOps:
    def __init__(self, cs: ControlSurface):
        self._cs = cs
        self._song = cs.song()

    def _resolve_track(self, kind, index):
        return (self._song.return_tracks if kind=="return" else self._song.tracks)[index]

    def select_track(self, kind, index):
        tr = self._resolve_track(kind, index)
        self._song.view.selected_track = tr
        return tr

    def delete_last_device(self, tr):
        if tr.devices:
            tr.delete_device(len(tr.devices)-1)

    def delete_selected_device(self):
        tr = self._song.view.selected_track
        dev = self._song.view.selected_device
        if not dev: return
        idx = list(tr.devices).index(dev)
        tr.delete_device(idx)

    def has_insert_device(self):
        tr = self._song.view.selected_track
        return hasattr(tr, "insert_device")

    def insert_builtin_device(self, tr, position_index, identifier):
        tr.insert_device(position_index, identifier)

insert_device works only for built-in devices in Live 12.3 +.
Older versions must rely on your UI automation.

⸻

4 · Timing Utilities (ops/timing.py)

import time

def sleep(seconds):
    t0 = time.time()
    while time.time() - t0 < seconds:
        time.sleep(0.02)

def backoff_until(ok_fn, timeout_sec, gaps):
    elapsed = 0
    if ok_fn(): return True
    for g in gaps:
        if elapsed >= timeout_sec: break
        sleep(g); elapsed += g
        if ok_fn(): return True
    return False


⸻

5 · HTTP API

Endpoints

Path	Description
POST /select_track	{kind:"return","index":0}
POST /add_builtin_device	{position:"end","identifier":"Builtin:Reverb"}
POST /delete_device	`{mode:“last”
POST /wait_for_capture	{min_delay:1.25,"verify_url":"http://localhost:8888/presets/exists?slug=..."}

# api/http_server.py
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import json
class FBHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        ln = int(self.headers.getheader('content-length','0'))
        data = json.loads(self.rfile.read(ln) or '{}')
        res = ROUTER.handle(self.path, data)
        out = json.dumps(res or {"ok":True})
        self.send_response(200 if res.get("ok") else 500)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


⸻

6 · ControlSurface Entry (fadebender_remote.py)

import threading, urllib2, json
from _Framework.ControlSurface import ControlSurface
from config import *
from ops.device_ops import DeviceOps
from ops.timing import sleep, backoff_until
from api.http_server import HTTPServer, FBHandler

class Router:
    def __init__(self, cs, ops):
        self.cs, self.ops = cs, ops

    def handle(self, path, data):
        s = self.cs.song()
        if path=="/select_track":
            tr=self.ops.select_track(data.get("kind","return"),int(data.get("index",0)))
            return {"ok":True,"track":tr.name}
        if path=="/add_builtin_device":
            tr=s.view.selected_track
            if ENABLE_INSERT_DEVICE and self.ops.has_insert_device():
                idx=len(tr.devices)
                self.ops.insert_builtin_device(tr,idx,data["identifier"])
                return {"ok":True}
            return {"ok":False,"error":"insert_device unsupported"}
        if path=="/delete_device":
            mode=data.get("mode",DELETE_MODE)
            tr=s.view.selected_track
            (self.ops.delete_selected_device() if mode=="selected"
             else self.ops.delete_last_device(tr))
            return {"ok":True}
        if path=="/wait_for_capture":
            sleep(float(data.get("min_delay",CAPTURE_DELAY_SEC)))
            verify=data.get("verify_url")
            ok=True
            if verify:
                def _chk():
                    try: return urllib2.urlopen(verify,timeout=1.5).getcode()==200
                    except: return False
                ok=backoff_until(_chk,VERIFY_TIMEOUT_SEC,VERIFY_BACKOFF)
            return {"ok":ok}
        return {"ok":False,"error":"unknown"}
        
class FadebenderRemote(ControlSurface):
    def __init__(self, c_instance):
        super(FadebenderRemote,self).__init__(c_instance)
        self._ops=DeviceOps(self)
        self._router=Router(self,self._ops)
        global ROUTER; ROUTER=self._router
        th=threading.Thread(target=self._run_http); th.daemon=True; th.start()
        self._ops.select_track(TARGET["kind"],TARGET["index"])

    def _run_http(self):
        srv=HTTPServer(("127.0.0.1",HTTP_PORT),FBHandler)
        srv.serve_forever()


⸻

7 · External Capture Loop
	1.	POST /select_track
	2.	Add device
	•	Live 12.3 +: /add_builtin_device
	•	Older: trigger UI automation to load preset
	3.	POST /wait_for_capture — waits + optional Firestore verify
	4.	Screenshot the device view
	5.	POST /delete_device
	6.	Next preset → repeat

⸻

8 · Timing for Firestore Lag

Adjust in config.py:

Param	Default	Meaning
CAPTURE_DELAY_SEC	1.25 s	fixed wait before verify/screenshot
VERIFY_TIMEOUT_SEC	8 s	total retry window
VERIFY_BACKOFF	[0.6, 0.8, 1.0, 1.2]	progressive sleeps between checks

If Firestore is slower, raise to 1.8–2.0 s and extend the backoff list.

⸻

9 · Testing Checklist
	1.	Load script in Live → Preferences → Control Surface.
	2.	curl -X POST localhost:8723/select_track -d '{"kind":"return","index":0}'
	3.	Add/delete device calls succeed.
	4.	Verify Firestore capture completes before screenshot.

⸻

10 · Limitations
	•	insert_device works only for built-ins (Live 12.3 +).
	•	Preset or Max devices still require external UI automation.
	•	Live must run on the same machine as the Remote Script.
	•	All sleeps are blocking; keep them under ~2 s to avoid UI freeze.

⸻

11 · Next Steps
	•	Add OSC listener mirroring the HTTP routes (optional).
	•	Expose additional metadata (device name, index, etc.) via JSON responses.
	•	Implement AppleScript fallback for preset insertion in your external orchestrator.

⸻

End of File

---

Now you can copy everything inside the triple backticks into a `.md` file in VS Code.