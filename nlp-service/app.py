import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv
# Legacy import - keeping for fallback if needed
# from intents.parser import DAWIntentParser, fallback_parse

# Load environment-specific configuration
env = os.getenv('ENV', 'development')
env_file = f'.env.{env}'

# Try to load environment-specific file first, fallback to .env
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"✅ Loaded environment config: {env_file}")
else:
    load_dotenv()
    print("✅ Loaded default .env file")

app = FastAPI(title="Fadebender NLP Service", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize lightweight LLM system
from llm_daw import interpret_daw_command
print("✅ Initialized lightweight LLM DAW interpreter")

class ParseRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None

class HowToRequest(BaseModel):
    query: str

@app.post("/parse")
async def parse(request: ParseRequest):
    """Parse natural language DAW commands into structured intents"""
    try:
        # Helper: normalize track labels in-place to "Track N"
        def _normalize_tracks(intent_obj):
            targets = intent_obj.get("targets") or []
            for t in targets:
                tr = t.get("track")
                if tr is None:
                    continue
                # Accept int or string digits
                if isinstance(tr, int) or (isinstance(tr, str) and tr.strip().isdigit()):
                    n = int(tr)
                    t["track"] = f"Track {n}"
                elif isinstance(tr, str) and tr.lower().startswith("track "):
                    # Normalize spacing/case
                    parts = tr.strip().split()
                    if len(parts) == 2 and parts[1].isdigit():
                        t["track"] = f"Track {int(parts[1])}"
            return intent_obj

        # Use lightweight LLM interpreter
        intent = interpret_daw_command(request.text)

        intent = _normalize_tracks(intent)
        return intent

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing error: {str(e)}")

@app.post("/howto")
async def howto(request: HowToRequest):
    """Get help with DAW techniques and workflows"""
    try:
        # Use the same lightweight LLM system for help queries
        help_result = interpret_daw_command(f"help: {request.query}")

        # If it returns a question_response, use that answer
        if help_result.get("intent") == "question_response":
            return {"answer": help_result.get("answer", "No specific advice available.")}
        else:
            # Fallback to generic DAW help
            return {"answer": f"For '{request.query}': Check your DAW documentation or try being more specific about which track and parameter you want to adjust."}

    except Exception as e:
        return {"answer": f"Sorry, I encountered an error while generating help: {str(e)}"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    from config.llm_config import get_llm_project_id, get_llm_api_key
    project_id = get_llm_project_id()
    api_key = get_llm_api_key()
    service_acct = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is not None
    ai_available = bool(api_key) or service_acct

    return {
        "status": "healthy",
        "llm_system": "lightweight_vertex_ai",
        "project_id": project_id,
        "api_key_configured": bool(api_key),
        "service_account_auth": service_acct,
        "ai_parser_available": ai_available,
    }
