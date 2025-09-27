import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from server.ableton.client_udp import request as udp_request, send as udp_send
from server.models.ops import MixerOp, SendOp, DeviceParamOp
from server.services.knowledge import search_knowledge


app = FastAPI(title="Fadebender Ableton Server", version="0.1.0")

# Load .env at server startup so Vertex/LLM config can come from file
try:  # optional dependency
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatBody(BaseModel):
    text: str
    confirm: bool = True
    model: Optional[str] = None  # e.g., 'gemini-2.5-flash' or 'llama'
    strict: Optional[bool] = None


class HelpBody(BaseModel):
    query: str


@app.get("/ping")
def ping() -> Dict[str, Any]:
    resp = udp_request({"op": "ping"}, timeout=0.5)
    ok = bool(resp and resp.get("ok", True))
    return {"ok": ok, "remote": resp}


@app.get("/status")
def status() -> Dict[str, Any]:
    resp = udp_request({"op": "get_overview"}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    return resp


@app.post("/op/mixer")
def op_mixer(op: MixerOp) -> Dict[str, Any]:
    msg = {"op": "set_mixer", **op.dict()}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    return resp


@app.post("/op/send")
def op_send(op: SendOp) -> Dict[str, Any]:
    msg = {"op": "set_send", **op.dict()}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    return resp


@app.post("/op/device/param")
def op_device_param(op: DeviceParamOp) -> Dict[str, Any]:
    msg = {"op": "set_device_param", **op.dict()}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    return resp


@app.post("/chat")
def chat(body: ChatBody) -> Dict[str, Any]:
    # Import llm_daw from nlp-service/ dynamically (folder has a hyphen)
    import sys
    import pathlib
    nlp_dir = pathlib.Path(__file__).resolve().parent.parent / "nlp-service"
    if nlp_dir.exists() and str(nlp_dir) not in sys.path:
        sys.path.insert(0, str(nlp_dir))
    try:
        from llm_daw import interpret_daw_command  # type: ignore
    except Exception as e:
        raise HTTPException(500, f"NLP module not available: {e}")

    intent = interpret_daw_command(body.text, model_preference=body.model, strict=body.strict)

    # Very small mapper for MVP: support volume absolute set if provided
    targets = intent.get("targets") or []
    op = intent.get("operation") or {}
    param = None
    if targets:
        param = (targets[0] or {}).get("parameter")
    track_index: Optional[int] = None
    if targets and targets[0].get("track"):
        try:
            label = targets[0]["track"]  # e.g., "Track 2"
            track_index = int(str(label).split()[-1])
        except Exception:
            track_index = None

    if intent.get("intent") == "set_parameter" and param == "volume" and track_index is not None and op.get("type") == "absolute":
        # Map dB -60..+6 to 0..1
        val = float(op.get("value", 0))
        norm = (max(-60.0, min(6.0, val)) + 60.0) / 66.0
        msg = {"op": "set_mixer", "track_index": track_index, "field": "volume", "value": round(norm, 4)}
        summary = f"Set Track {track_index} volume to {val:g} dB"
        if not body.confirm:
            return {"ok": True, "preview": msg, "intent": intent, "summary": summary}
        resp = udp_request(msg, timeout=1.0)
        return {"ok": bool(resp and resp.get("ok", True)), "preview": msg, "resp": resp, "intent": intent, "summary": summary}

    # Fallback: return intent for UI to decide
    return {
        "ok": False,
        "reason": "unsupported_intent_for_auto_execute",
        "intent": intent,
        "summary": "I can auto-execute only absolute track volume right now."
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("SERVER_PORT", "8722"))
    uvicorn.run("server.app:app", host=host, port=port, reload=True)


@app.post("/help")
def help_endpoint(body: HelpBody) -> Dict[str, Any]:
    """Return grounded help snippets from local knowledge notes.

    Response shape:
    { ok, answer, sources: [{source, title}] }
    """
    matches = search_knowledge(body.query)
    if not matches:
        return {"ok": False, "answer": "No relevant notes found. Try rephrasing your question."}
    # Compose a short answer from top matches
    snippets = []
    sources = []
    for src, title, body_text in matches:
        sources.append({"source": src, "title": title})
        snippets.append(f"{title}:\n" + body_text)
    answer = "\n\n".join(snippets[:2])
    return {"ok": True, "answer": answer, "sources": sources}
