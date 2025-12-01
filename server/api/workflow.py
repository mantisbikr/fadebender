from typing import List, Optional, Dict, Any, Literal
from fastapi import APIRouter, HTTPException, Query, Body
import time
import uuid
import math
from google.cloud import firestore

from server.models.workflow import Marker, Task, TaskRef
from server.services.firestore import get_db
from server.services.ableton_client import request_op, get_transport

router = APIRouter()

# Default context constants for V1 (single user/project)
DEFAULT_WORKSPACE = "default"
DEFAULT_PROJECT = "p1"

def _get_markers_ref():
    db = get_db()
    if not db:
        return None
    return db.collection("workspaces").document(DEFAULT_WORKSPACE)\
             .collection("projects").document(DEFAULT_PROJECT)\
             .collection("markers")

def _get_tasks_ref():
    db = get_db()
    if not db:
        return None
    return db.collection("workspaces").document(DEFAULT_WORKSPACE)\
             .collection("projects").document(DEFAULT_PROJECT)\
             .collection("tasks")

def _beats_to_timecode(beats: float, signature_numerator: int = 4, signature_denominator: int = 4) -> str:
    # Approximate timecode assuming 4/4 or using provided signature
    # Live uses 1-based bars.beats.sixteenths
    # Example: 0.0 -> 1.1.1
    # 4.0 (end of bar 1) -> 2.1.1
    
    # Beats per bar = numerator * (4 / denominator)
    # e.g. 4/4 -> 4 * 1 = 4 beats per bar
    # e.g. 3/4 -> 3 * 1 = 3 beats per bar
    # e.g. 6/8 -> 6 * 0.5 = 3 beats per bar
    beats_per_bar = signature_numerator * (4 / signature_denominator)
    
    bar = int(beats // beats_per_bar) + 1
    remainder = beats % beats_per_bar
    
    # Beat within bar (1-based)
    # Note: This simplifies complex meters but works for standard ones
    beat = int(remainder) + 1
    sub_beat_remainder = remainder - int(remainder)
    
    sixteenth = int(sub_beat_remainder * 4) + 1
    
    return f"{bar}.{beat}.{sixteenth}"

# --- Markers ---

@router.get("/markers", response_model=List[Marker])
def get_markers(layer: Optional[str] = None):
    """Get merged list of Live locators and Fadebender virtual markers."""
    markers = []
    
    # Fetch transport for time signature
    t_state = get_transport(timeout=1.0)
    sig_num = 4
    sig_den = 4
    if t_state and t_state.get("ok"):
        data = t_state.get("data", {})
        sig_num = int(data.get("time_signature_numerator", 4))
        sig_den = int(data.get("time_signature_denominator", 4))

    # 1. Fetch from Live
    try:
        r = request_op("get_cue_points", timeout=1.5)
        if r and r.get("ok"):
            cues = r.get("data", {}).get("cue_points", [])
            for cue in cues:
                # Live cue: {index: 1, name: "Intro", time: 16.0}
                beats = float(cue.get("time", 0))
                markers.append(Marker(
                    markerId=f"live_cue_{cue.get('index')}",
                    source="live",
                    name=cue.get("name", "Untitled"),
                    timecode=_beats_to_timecode(beats, sig_num, sig_den),
                    beats=beats,
                    private=False,
                    layer="structure" # Live markers are usually structure
                ))
    except Exception as e:
        print(f"Error fetching live cues: {e}")

    # 2. Fetch from Firestore
    ref = _get_markers_ref()
    if ref:
        try:
            query = ref
            if layer:
                query = query.where("layer", "==", layer)
            
            docs = query.stream()
            for doc in docs:
                data = doc.to_dict()
                if "markerId" not in data:
                    data["markerId"] = doc.id
                try:
                    # Recalculate timecode if signature changed (optional but good for consistency)
                    if "beats" in data:
                        data["timecode"] = _beats_to_timecode(data["beats"], sig_num, sig_den)
                    markers.append(Marker(**data))
                except Exception as e:
                    print(f"Skipping invalid marker {doc.id}: {e}")
        except Exception as e:
            print(f"Error fetching firestore markers: {e}")
    
    # Sort by position (beats)
    markers.sort(key=lambda m: m.beats)
    return markers

@router.post("/markers", response_model=Marker)
def create_marker(marker: Marker):
    """Create a new virtual marker."""
    if marker.source == "live":
        raise HTTPException(400, "Cannot create 'live' markers directly via API. Use Ableton UI.")

    ref = _get_markers_ref()
    if not ref:
        raise HTTPException(503, "Database not available")

    if not marker.markerId:
        marker.markerId = f"marker_{uuid.uuid4().hex[:8]}"
        
    # Fetch transport for time signature
    t_state = get_transport(timeout=1.0)
    sig_num = 4
    sig_den = 4
    if t_state and t_state.get("ok"):
        data = t_state.get("data", {})
        sig_num = int(data.get("time_signature_numerator", 4))
        sig_den = int(data.get("time_signature_denominator", 4))

    # Auto-calc timecode if missing or update it based on current signature
    if marker.beats is not None:
         marker.timecode = _beats_to_timecode(marker.beats, sig_num, sig_den)

    doc_ref = ref.document(marker.markerId)
    doc_ref.set(marker.model_dump(by_alias=True))
    
    return marker

@router.put("/markers/{marker_id}", response_model=Marker)
def update_marker(marker_id: str, update: Dict[str, Any] = Body(...)):
    """Update an existing marker (Virtual or Live)."""
    
    # Fetch transport for time signature (needed for return object)
    t_state = get_transport(timeout=1.0)
    sig_num = 4
    sig_den = 4
    if t_state and t_state.get("ok"):
        data = t_state.get("data", {})
        sig_num = int(data.get("time_signature_numerator", 4))
        sig_den = int(data.get("time_signature_denominator", 4))
    
    # 1. Check if it's a Live marker
    if marker_id.startswith("live_cue_"):
        try:
            cue_index = int(marker_id.replace("live_cue_", ""))
            
            # We only support renaming Live markers via API
            if "name" in update:
                r = request_op("set_cue_name", timeout=1.5, cue_index=cue_index, name=update["name"])
                if not r or not r.get("ok"):
                    raise HTTPException(500, f"Failed to rename Live marker: {r.get('error')}")
            
            # Construct a transient Marker object to return
            # We'd ideally re-fetch, but let's return the patched state
            r_info = request_op("get_cue_points", timeout=1.5)
            if r_info and r_info.get("ok"):
                cues = r_info.get("data", {}).get("cue_points", [])
                cue = next((c for c in cues if c["index"] == cue_index), None)
                if cue:
                    return Marker(
                        markerId=marker_id,
                        source="live",
                        name=cue.get("name"),
                        timecode=_beats_to_timecode(float(cue.get("time", 0)), sig_num, sig_den),
                        beats=float(cue.get("time", 0)),
                        private=False,
                        layer="structure"
                    )
            raise HTTPException(404, "Live marker not found after update")

        except ValueError:
             raise HTTPException(400, "Invalid Live marker ID")
    
    # 2. It's a Virtual Marker (Firestore)
    ref = _get_markers_ref()
    if not ref:
        raise HTTPException(503, "Database not available")

    doc_ref = ref.document(marker_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(404, "Marker not found")
        
    current_data = doc.to_dict()
    current_data.update(update)
    
    # Re-calc timecode if beats changed
    if "beats" in update:
        current_data["timecode"] = _beats_to_timecode(current_data["beats"], sig_num, sig_den)

    doc_ref.set(current_data)
    return Marker(**current_data)

@router.delete("/markers/{marker_id}")
def delete_marker(marker_id: str):
    """Delete a marker."""
    if marker_id.startswith("live_cue_"):
        # Live API Limitation: Cannot delete cues reliably via Remote Script in some versions
        # But we can try `delete_cue` op if supported, otherwise fail.
        # For now, following design doc: "Creating/deleting locators not supported"
        raise HTTPException(400, "Deleting Live locators is not supported by the API.")

    ref = _get_markers_ref()
    if not ref:
        raise HTTPException(503, "Database not available")
        
    ref.document(marker_id).delete()
    return {"ok": True, "id": marker_id}

# --- Tasks ---

@router.get("/tasks", response_model=List[Task])
def get_tasks(status: Optional[str] = None, ref_type: Optional[str] = None, ref_id: Optional[str] = None):
    """List tasks, optionally filtered by status or reference."""
    ref = _get_tasks_ref()
    if not ref:
        raise HTTPException(503, "Database not available")
    
    query = ref
    if status:
        query = query.where("status", "==", status)
        
    tasks = []
    try:
        for doc in query.stream():
            data = doc.to_dict()
            if "taskId" not in data:
                data["taskId"] = doc.id
            
            task = Task(**data)
            
            # Manual filter for refs (Firestore array-contains is limited for objects)
            if ref_type or ref_id:
                match = False
                for r in task.refs:
                    if ref_type and r.type != ref_type: continue
                    if ref_id and r.id != ref_id: continue
                    match = True
                    break
                if not match:
                    continue
            
            tasks.append(task)
    except Exception as e:
        raise HTTPException(500, f"Error fetching tasks: {e}")
        
    return tasks

@router.post("/tasks", response_model=Task)
def create_task(task: Task):
    """Create a new task."""
    ref = _get_tasks_ref()
    if not ref:
        raise HTTPException(503, "Database not available")
        
    if not task.taskId:
        task.taskId = f"task_{uuid.uuid4().hex[:8]}"
        
    now = time.time()
    if not task.createdAt:
        task.createdAt = now
    task.updatedAt = now
    
    doc_ref = ref.document(task.taskId)
    doc_ref.set(task.model_dump())
    
    return task

@router.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, update: Dict[str, Any]):
    """Update task fields."""
    ref = _get_tasks_ref()
    if not ref:
        raise HTTPException(503, "Database not available")
        
    doc_ref = ref.document(task_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(404, "Task not found")
        
    current_data = doc.to_dict()
    current_data.update(update)
    current_data["updatedAt"] = time.time()
    
    doc_ref.set(current_data)
    return Task(**current_data)

@router.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a task."""
    ref = _get_tasks_ref()
    if not ref:
        raise HTTPException(503, "Database not available")
    
    ref.document(task_id).delete()
    return {"ok": True, "id": task_id}

# --- Resolution Tools ---

@router.get("/tools/nearest_marker")
def get_nearest_marker(beats: float, layer: Optional[str] = None) -> Dict[str, Any]:
    """Find the marker nearest to the given beat time."""
    markers = get_markers(layer=layer)
    if not markers:
        return {"found": False}
    
    nearest = min(markers, key=lambda m: abs(m.beats - beats))
    distance = abs(nearest.beats - beats)
    
    return {
        "found": True,
        "marker": nearest,
        "distance_beats": distance
    }

@router.get("/tools/navigate_marker")
def navigate_marker(current_beats: float, direction: Literal["next", "prev"], layer: Optional[str] = None) -> Dict[str, Any]:
    """Find the next or previous marker relative to current_beats."""
    markers = get_markers(layer=layer)
    if not markers:
        return {"found": False}
    
    target = None
    if direction == "next":
        # Find smallest beat > current_beats
        candidates = [m for m in markers if m.beats > current_beats + 0.01] # small epsilon
        if candidates:
            target = min(candidates, key=lambda m: m.beats)
    else:
        # Find largest beat < current_beats
        candidates = [m for m in markers if m.beats < current_beats - 0.01]
        if candidates:
            target = max(candidates, key=lambda m: m.beats)
            
    if target:
        return {"found": True, "marker": target}
    return {"found": False}

@router.get("/tools/convert_time")
def convert_time(value: float, from_unit: Literal["beats", "ms", "bars"], to_unit: Literal["beats", "ms", "bars"]) -> Dict[str, Any]:
    """Convert time values using current Live tempo."""
    
    # 1. Get Tempo & Signature
    t_state = get_transport(timeout=1.0)
    if not t_state or not t_state.get("ok"):
         raise HTTPException(503, "Live transport unavailable")
    
    data = t_state.get("data", {})
    tempo = float(data.get("tempo", 120.0))
    sig_num = int(data.get("time_signature_numerator", 4))
    sig_den = int(data.get("time_signature_denominator", 4))
    
    if tempo <= 0: tempo = 120.0
    
    # 2. Normalize to Beats
    beats = 0.0
    if from_unit == "beats":
        beats = value
    elif from_unit == "ms":
        # beats = (ms / 1000 / 60) * bpm
        beats = (value / 60000.0) * tempo
    elif from_unit == "bars":
        # beats = bars * beats_per_bar
        # e.g. 4/4 -> 4 beats/bar. 3/4 -> 3 beats/bar. 6/8 -> 3 beats/bar? 
        # Formula: sig_num * (4 / sig_den)
        beats_per_bar = sig_num * (4 / sig_den)
        beats = value * beats_per_bar
        
    # 3. Convert to Target
    result = 0.0
    if to_unit == "beats":
        result = beats
    elif to_unit == "ms":
        result = (beats / tempo) * 60000.0
    elif to_unit == "bars":
        beats_per_bar = sig_num * (4 / sig_den)
        result = beats / beats_per_bar
        
    return {
        "input": value,
        "input_unit": from_unit,
        "output": result,
        "output_unit": to_unit,
        "tempo": tempo,
        "time_signature": [sig_num, sig_den]
    }