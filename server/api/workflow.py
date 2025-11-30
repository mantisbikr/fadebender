from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
import time
import uuid
from google.cloud import firestore

from server.models.workflow import Marker, Task, TaskRef
from server.services.firestore import get_db
from server.services.ableton_client import request_op

router = APIRouter()

# Default context constants for V1 (single user/project)
DEFAULT_WORKSPACE = "default"
DEFAULT_PROJECT = "p1"
DEFAULT_USER = "local-owner"

def _get_markers_ref():
    db = get_db()
    if not db:
        return None
    # /workspaces/{w}/projects/{p}/markers
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

@router.get("/markers", response_model=List[Marker])
def get_markers():
    """Get merged list of Live locators and Fadebender virtual markers."""
    markers = []

    # 1. Fetch from Live
    try:
        r = request_op("get_cue_points", timeout=1.5)
        if r and r.get("ok"):
            cues = r.get("data", {}).get("cue_points", [])
            for cue in cues:
                # Live cue: {index: 1, name: "Intro", time: 16.0}
                markers.append(Marker(
                    markerId=f"live_cue_{cue.get('index')}",
                    source="live",
                    name=cue.get("name", "Untitled"),
                    timecode=f"{cue.get('time'):.1f}", # approximated timecode
                    beats=float(cue.get("time", 0)),
                    private=False
                ))
    except Exception as e:
        print(f"Error fetching live cues: {e}")

    # 2. Fetch from Firestore
    ref = _get_markers_ref()
    if ref:
        try:
            docs = ref.stream()
            for doc in docs:
                data = doc.to_dict()
                # Ensure ID matches
                if "markerId" not in data:
                    data["markerId"] = doc.id
                try:
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
        # We don't support creating live markers yet (API limitation)
        # But we can store it as virtual with source='fadebender'?
        # User asked for virtual locators.
        raise HTTPException(400, "Cannot create 'live' markers directly. Use 'fadebender' source.")

    ref = _get_markers_ref()
    if not ref:
        raise HTTPException(503, "Database not available")

    # Generate ID if needed
    if not marker.markerId:
        marker.markerId = f"marker_{uuid.uuid4().hex[:8]}"

    doc_ref = ref.document(marker.markerId)
    doc_ref.set(marker.model_dump(by_alias=True))
    
    return marker

@router.get("/tasks", response_model=List[Task])
def get_tasks(status: Optional[str] = None):
    """List tasks, optionally filtered by status."""
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
            tasks.append(Task(**data))
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
