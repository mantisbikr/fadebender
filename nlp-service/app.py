import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from intents.parser import DAWIntentParser, fallback_parse

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

# Initialize AI parser
api_key = os.getenv("GOOGLE_API_KEY")
project_id = os.getenv("PROJECT_ID")
if not api_key:
    print("Warning: GOOGLE_API_KEY not set. Using fallback parser only.")
    parser = None
else:
    try:
        parser = DAWIntentParser(api_key=api_key, model_name="gemini-1.5-flash-latest")
        print(f"✅ Initialized Gemini parser with Google AI API")
    except Exception as e:
        print(f"❌ Failed to initialize AI parser: {e}")
        parser = None

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

        if parser:
            # Use AI parser with context
            intent = parser.parse(request.text, request.context)
            intent.setdefault("meta", {})["model_used"] = "gemini-1.5-flash"
        else:
            intent = fallback_parse(request.text)
            intent.setdefault("meta", {})["model_used"] = "fallback"

        intent = _normalize_tracks(intent)
        return intent

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing error: {str(e)}")

@app.post("/howto")
async def howto(request: HowToRequest):
    """Get help with DAW techniques and workflows"""
    if parser:
        try:
            # Create a help prompt for the AI
            help_prompt = f"""You are a helpful DAW (Digital Audio Workstation) assistant. The user is asking: "{request.query}"

If this is about what they just did, provide a helpful summary of recent DAW actions.
If this is a general DAW question, provide clear, actionable advice.

Examples of good responses:
- For "what did I just do?": "You increased the reverb on Track 2 by 2%, which adds more spaciousness to that audio channel."
- For "how to sidechain?": "Sidechaining involves routing one track's signal to control another track's compressor. In most DAWs: 1) Add a compressor to the track you want ducked, 2) Set the sidechain input to the trigger track, 3) Adjust threshold and ratio."

Provide a concise, helpful response:"""

            response = parser.model.generate_content(help_prompt)
            answer = response.text.strip()

            return {"answer": answer}
        except Exception as e:
            return {"answer": f"Sorry, I encountered an error while generating help: {str(e)}"}
    else:
        return {"answer": "Help functionality requires AI model. Please check configuration."}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ai_parser_available": parser is not None,
        "api_configured": api_key is not None,
        "project_id": project_id or "not_configured"
    }
