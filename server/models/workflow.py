from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union, Dict, Any

class MarkerLink(BaseModel):
    taskId: Optional[str] = None
    snapshotId: Optional[str] = None

class Marker(BaseModel):
    markerId: str
    source: Literal["fadebender", "live"]
    name: str
    timecode: str  # "57.3.0" or similar display format
    beats: float   # Absolute beats
    barsFromHere: int = 4
    is_private: bool = Field(False, alias="private")
    layer: str = "default"  # e.g. "structure", "notes", "automation"
    links: MarkerLink = Field(default_factory=MarkerLink)
    color: Optional[str] = None
    
class TaskRef(BaseModel):
    type: Literal["track", "device", "marker"]
    id: str

class Task(BaseModel):
    taskId: str
    title: str
    status: Literal["todo", "in_progress", "done"] = "todo"
    priority: Literal["low", "medium", "high"] = "medium"
    refs: List[TaskRef] = []
    labels: List[str] = []
    playhead: Optional[float] = None
    description: Optional[str] = None
    createdAt: Optional[float] = None
    updatedAt: Optional[float] = None