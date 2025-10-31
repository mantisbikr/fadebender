"""DAW Intent Parser using Vertex AI.

Migrated from google.generativeai (paid API) to Vertex AI (project-based).
Uses Application Default Credentials - no API key needed.
"""
import json
import re
import os
from typing import Dict, Any, List, Optional

# Vertex AI imports
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False
    print("Warning: Vertex AI SDK not available. Install with: pip install google-cloud-aiplatform")

SYSTEM_PROMPT = """You are an expert DAW (Digital Audio Workstation) command parser with conversational intelligence.
Parse natural language commands into structured JSON intents for controlling music production software.

SUPPORTED OPERATIONS:
- Volume control: "set track X volume to Y dB", "make track X louder/quieter by Y dB", "increase/decrease volume"
- Pan control: "pan track X left/right by Y%", "center track X"
- Effects: "add reverb to track X", "increase reverb wet by Y%"
- Transport: "play", "stop", "start recording", "toggle metronome", "set tempo 120" (BPM)
- Questions and explanations: "what did I just do?", "explain what happened", "what does reverb do?"
- Audio engineering advice: "I want spaciousness to my vocals", "add punch to drums", "position it to the right"

QUESTION HANDLING:
For questions about recent actions or explanations, return a "question_response" intent with a helpful answer:
- "what did I just do?" → Explain the most recent action based on context
- "what does reverb do?" → Explain the effect
- "why did that happened?" → Provide context-aware explanation

AUDIO ENGINEERING ADVICE:
For requests about achieving audio goals, provide expert advice with actionable suggestions based on professional audio engineering principles and common Ableton Live workflows (keep suggestions DAW-agnostic when possible):

VOCAL SPACIOUSNESS AND DEPTH:
- "I want spaciousness to my vocals" → Add a high-quality algorithmic reverb (15-25% wet), consider a hall/plate style, set pre-delay for clarity, gentle high-frequency boost at 10-12kHz for air
- "add depth to my vocals" → Longer reverb decay, pre-delay settings, subtle tape delay for character
- Commands: "add reverb to track X", "increase reverb on track X by 20%", "boost track X highs by 2dB"

DRUM PUNCH AND IMPACT:
- "add punch to my drums" → Use compression on kick (fast attack, ~4:1 ratio), EQ boost at 60-80Hz for weight and 2-5kHz for attack
- "make drums hit harder" → Compression for transient control, vintage EQ for character, gate to reduce bleed
- Commands: "add compression to track X", "boost track X lows by 3dB", "gate track X"

STEREO POSITIONING:
- "position it to the right" → Use pan or mid/side tools for placement; typical positions: hi-hats 30-45° right, guitars ±30-60°
- "widen the stereo image" → Use a stereo widener carefully; check phase/mono compatibility
- Commands: "pan track X right by 30%", "center track X", "widen track X"

WARMTH AND CHARACTER:
- "make it warmer" → Gentle low-mid boost (200-400Hz), tape/analog-style saturation, slight high-frequency roll-off
- "add character" → Multiband compression for frequency-specific control, analog modeling, harmonic enhancement
- Commands: "add warmth to track X", "boost track X at 300Hz"

CLARITY AND PRESENCE:
- "make it brighter" → EQ boost at 8-12kHz for air, 2-5kHz for presence, high-pass unwanted low frequencies
- "add presence" → Mid-range EQ boost (2-5kHz), compression for consistency, reduce muddiness at 200-400Hz
- Commands: "boost track X highs by 3dB", "cut track X at 400Hz", "high-pass track X at 100Hz"

FREQUENCY SPECTRUM KNOWLEDGE:
- Sub-bass (20-60Hz): Kick/bass fundamentals only
- Bass (60-200Hz): Power and weight, cut to tighten
- Low-mids (200-500Hz): Warmth/body, often needs cutting
- Mids (500Hz-2kHz): Vocal presence and intelligibility
- High-mids (2-8kHz): Clarity and attack definition
- Highs (8kHz+): Air and sparkle

COMPRESSION PRINCIPLES:
- Vocals: 3:1-6:1 ratio, medium attack, fast release
- Kick drums: Fast attack (0.1-1ms), 4:1 ratio for punch
- Snare: Medium attack (1-3ms), 3:1 ratio for crack
- Use threshold for 3-6dB gain reduction typically

When suggesting devices, prefer generic names or Ableton Live stock devices (e.g., Reverb, EQ Eight, Compressor) and include actionable command examples like "You can say: 'increase track 2 volume by 3 dB'" or "Try: 'add reverb to track 1 and set wet to 20%'"

AMBIGUOUS COMMAND DETECTION:
When a command is ambiguous (missing critical information), return a "clarification_needed" intent with a question.

COMMON AMBIGUITIES:
- "increase volume" → Ask: "Do you want to increase the master volume or a specific track? If specific track, which one?"
- "add reverb" → Ask: "Which track would you like to add reverb to?"
- "make it louder" → Ask: "Do you want to make the master volume or a specific track louder?"
- "pan left" → Ask: "Which track would you like to pan left?"
- When user mentions instrument/sound but not track number → Ask: "Which track is the [instrument] on?"

CRITICAL: If a COMMAND mentions an instrument but does NOT specify a track number, ask for clarification. However, if it's a QUESTION about audio problems or requests for advice, provide helpful suggestions:

COMMANDS (need track clarification):
- "cut drums at 300Hz" → Ask: "Which track are the drums on?"
- "boost vocals" → Ask: "Which track are the vocals on?"
- "compress the guitar" → Ask: "Which track is the guitar on?"
- "add reverb to piano" → Ask: "Which track is the piano on?"

QUESTIONS/PROBLEMS (provide advice):
- "the vocals are too soft" → Provide volume, compression, EQ suggestions
- "drums sound muddy" → Suggest EQ cuts, compression, gating
- "guitar lacks presence" → Recommend frequency boosts, positioning
- "how to make vocals louder" → Explain volume, compression, EQ techniques

NEVER proceed with track: null - always ask for track clarification when the track is not specified.

CONTEXT HANDLING:
When processing clarification responses, be intelligent about understanding the user's intent:
- If user says "track 3" or "it's on track 3", treat as track specification
- If user mentions amounts like "by 5%" or "to -6dB", treat as value specification
- If user mentions instrument names, map them to track numbers if track info is provided

RELATIVE VOLUME INTERPRETATION:
- "a little bit" = 2 dB
- "a bit" = 2 dB
- "slightly" = 1 dB
- "much" = 5 dB
- "a lot" = 6 dB

OUTPUT FORMATS:

For CLEAR commands (JSON only, no explanation):
{
  "intent": "set_parameter" | "relative_change",
  "targets": [{"track": "Track 1", "plugin": null, "parameter": "volume"}],
  "operation": {"type": "absolute|relative", "value": 2, "unit": "dB"},
  "meta": {"utterance": "original command", "confidence": 0.95}
}

For QUESTIONS (JSON only, no explanation):
{
  "intent": "question_response",
  "answer": "You just increased the reverb on Track 2 by 2%, which adds more spaciousness and depth to that audio channel.",
  "meta": {"utterance": "original command", "confidence": 0.95}
}

For AMBIGUOUS commands (JSON only, no explanation):
{
  "intent": "clarification_needed",
  "question": "Do you want to increase the master volume or a specific track? If specific track, which one?",
  "context": {"action": "increase", "parameter": "volume", "partial_intent": "relative_change"},
  "meta": {"utterance": "original command", "confidence": 0.9}
}

EXAMPLES:
"increase track 2 volume a little bit" → {"intent": "relative_change", "targets": [{"track": "Track 2", "plugin": null, "parameter": "volume"}], "operation": {"type": "relative", "value": 2, "unit": "dB"}}
"what did I just do?" → {"intent": "question_response", "answer": "You increased the reverb on Track 2 by 2%, which adds more spaciousness to that audio channel."}
"I want spaciousness to my vocals" → {"intent": "question_response", "answer": "For vocal spaciousness, try adding reverb or delay. You can say: 'add reverb to track 1' or 'increase reverb on track 1 by 15%'. You could also try subtle panning or widening effects."}
"add punch to my drums" → {"intent": "question_response", "answer": "For drum punch, try compression and volume adjustments. You can say: 'increase track 3 volume by 3 dB' for the kick drum, or add compression. EQ boosts around 60-80Hz (low end) and 2-5kHz (attack) also help."}
"the vocals are too soft" → {"intent": "question_response", "answer": "For soft vocals, try: 1) Increase volume: 'increase track X volume by 3 dB', 2) Add compression for consistency: 'add compression to track X', 3) Boost presence frequencies: 'boost track X at 3kHz by 2 dB', 4) Cut competing frequencies in other instruments. Which track are the vocals on?"}
"increase volume" → {"intent": "clarification_needed", "question": "Do you want to increase the master volume or a specific track? If specific track, which one?", "context": {"action": "increase", "parameter": "volume", "partial_intent": "relative_change"}}

RULES:
- Always return valid JSON only
- Use "Track 1", "Track 2" format for track names
- Convert text numbers to integers ("one" -> 1, "two" -> 2)
- Default volume range: -60dB to +6dB
- For relative changes, use positive values for "increase/louder", negative for "decrease/quieter"
- For questions, provide helpful, context-aware answers
- If command is ambiguous, ALWAYS ask for clarification rather than assuming defaults"""

INSTRUMENT_WORDS = [
    "drums", "drum", "kick", "snare", "hihat", "hi-hat",
    "vocal", "vocals", "voice",
    "guitar", "bass", "piano", "keys", "synth", "pad"
]

NUM_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}

def _track_label(n: int) -> str:
    return f"Track {int(n)}"

def _contains_instrument(text: str) -> Optional[str]:
    for w in INSTRUMENT_WORDS:
        if re.search(rf"\b{re.escape(w)}\b", text):
            return w
    return None

def fallback_parse(text: str) -> Dict[str, Any]:
    """Rule-based parser for when the AI model is not available.
    Produces intents compatible with the controller (targets[], operation, etc.).
    Also performs instrument-based clarification when track is unspecified.
    """
    t = text.strip()
    s = t.lower()

    # Normalize common number words in track references
    for word, num in NUM_WORDS.items():
        s = re.sub(rf"track\s+{word}\b", f"track {num}", s)

    # 0) Transport controls
    # Play / Stop
    if re.search(r"\b(play|start)\b", s) and not re.search(r"\b(stop|record|recording)\b", s):
        return {
            "intent": "transport",
            "targets": [],
            "operation": {"action": "play"},
            "meta": {"utterance": t, "fallback": True}
        }
    if re.search(r"\b(stop|pause)\b", s):
        return {
            "intent": "transport",
            "targets": [],
            "operation": {"action": "stop"},
            "meta": {"utterance": t, "fallback": True}
        }
    # Record on/off (start/stop recording)
    if re.search(r"\b(start\s+record(ing)?|record\b)\b", s) and not re.search(r"stop\s+record", s):
        return {
            "intent": "transport",
            "targets": [],
            "operation": {"action": "record"},
            "meta": {"utterance": t, "fallback": True}
        }
    if re.search(r"\bstop\s+record(ing)?\b", s):
        # Use same toggle behavior on RS side; intent remains 'record'
        return {
            "intent": "transport",
            "targets": [],
            "operation": {"action": "record"},
            "meta": {"utterance": t, "fallback": True}
        }
    # Metronome toggle / on / off
    if re.search(r"\bmetronome\b.*\bon\b", s):
        return {"intent": "transport", "targets": [], "operation": {"action": "metronome"}, "meta": {"utterance": t, "fallback": True}}
    if re.search(r"\bmetronome\b.*\boff\b", s):
        return {"intent": "transport", "targets": [], "operation": {"action": "metronome"}, "meta": {"utterance": t, "fallback": True}}
    if re.search(r"\b(toggle|tap)\s+metronome\b", s):
        return {"intent": "transport", "targets": [], "operation": {"action": "metronome"}, "meta": {"utterance": t, "fallback": True}}
    # Tempo / BPM
    m = re.search(r"\b(set|change)\s+(tempo|bpm)\s*(to)?\s*(\d+(?:\.\d+)?)\b", s)
    if m:
        bpm = float(m.group(4))
        return {
            "intent": "transport",
            "targets": [],
            "operation": {"action": "tempo", "value": bpm},
            "meta": {"utterance": t, "fallback": True}
        }
    m = re.search(r"\b(tempo|bpm)\s*(to)?\s*(\d+(?:\.\d+)?)\b", s)
    if m:
        bpm = float(m.group(3))
        return {
            "intent": "transport",
            "targets": [],
            "operation": {"action": "tempo", "value": bpm},
            "meta": {"utterance": t, "fallback": True}
        }

    # 1) Explicit: set track N volume to X dB
    m = re.search(r"set\s+track\s+(\d+)\s+volume\s+to\s+(-?\d+\.?\d*)\s*d?b\b", s)
    if m:
        n = int(m.group(1)); val = float(m.group(2))
        return {
            "intent": "set_parameter",
            "targets": [{"track": _track_label(n), "plugin": None, "parameter": "volume"}],
            "operation": {"type": "absolute", "value": val, "unit": "dB"},
            "meta": {"utterance": t, "fallback": True}
        }

    # 2) Relative volume: increase/decrease track N by X dB
    m = re.search(r"(increase|decrease|make)\s+(?:track\s+(\d+)\s+)?(?:volume|it)?\s*(?:by\s*)?(-?\d+\.?\d*)\s*d?b\b", s)
    if m:
        op = m.group(1); n = m.group(2); delta = float(m.group(3))
        sign = 1 if op in ("increase", "make") else -1
        track = _track_label(int(n)) if n else _track_label(1)
        return {
            "intent": "relative_change",
            "targets": [{"track": track, "plugin": None, "parameter": "volume"}],
            "operation": {"type": "relative", "value": sign * delta, "unit": "dB"},
            "meta": {"utterance": t, "fallback": True}
        }

    # 2b) Relative volume by percent: increase/decrease track N by X%
    m = re.search(r"(increase|decrease|make)\s+(?:track\s+(\d+)\s+)?(?:volume|it)?\s*(?:by\s*)?(\d+\.?\d*)%\b", s)
    if m:
        op = m.group(1); n = m.group(2); pct = float(m.group(3))
        sign = 1 if op in ("increase", "make") else -1
        track = _track_label(int(n)) if n else _track_label(1)
        return {
            "intent": "relative_change",
            "targets": [{"track": track, "plugin": None, "parameter": "volume"}],
            "operation": {"type": "relative", "value": sign * pct, "unit": "%"},
            "meta": {"utterance": t, "fallback": True}
        }

    # 3) Pan track N left/right X%
    m = re.search(r"pan\s+track\s+(\d+)\s+(left|right)\s+(\d+)%", s)
    if m:
        n = int(m.group(1)); dirn = m.group(2); pct = int(m.group(3))
        val = -pct if dirn == 'left' else pct
        return {
            "intent": "set_parameter",
            "targets": [{"track": _track_label(n), "plugin": None, "parameter": "pan"}],
            "operation": {"type": "absolute", "value": val, "unit": "%"},
            "meta": {"utterance": t, "fallback": True}
        }

    # 3b) Pan master left/right by X (assume percent if no unit)
    m = re.search(r"pan\s+master\s+(left|right)\s+(?:by\s*)?(\d+)(?:%?)\b", s)
    if m:
        dirn = m.group(1); amt = int(m.group(2))
        val = -amt if dirn == 'left' else amt
        return {
            "intent": "relative_change",
            "targets": [{"track": "Master", "plugin": None, "parameter": "pan"}],
            "operation": {"type": "relative", "value": val, "unit": "%"},
            "meta": {"utterance": t, "fallback": True}
        }

    # 1b) Set master volume to X [dB]
    m = re.search(r"set\s+master\s+volume\s+to\s+(-?\d+\.?\d*)\s*(d?b)?\b", s)
    if m:
        val = float(m.group(1))
        has_db = bool(m.group(2))
        return {
            "intent": "set_parameter",
            "targets": [{"track": "Master", "plugin": None, "parameter": "volume"}],
            "operation": {"type": "absolute", "value": val, "unit": "dB" if has_db or True else None},
            "meta": {"utterance": t, "fallback": True}
        }

    # 1c) Set master cue to X [dB]
    m = re.search(r"set\s+master\s+cue\s+to\s+(-?\d+\.?\d*)\s*(d?b)?\b", s)
    if m:
        val = float(m.group(1))
        # default to dB semantics for cue as well
        return {
            "intent": "set_parameter",
            "targets": [{"track": "Master", "plugin": None, "parameter": "cue"}],
            "operation": {"type": "absolute", "value": val, "unit": "dB"},
            "meta": {"utterance": t, "fallback": True}
        }

    # 4) Reverb wet change: increase/decrease reverb on track N by X%
    m = re.search(r"(increase|decrease).*reverb.*track\s+(\d+).*?(\d+)%", s)
    if m:
        op = m.group(1); n = int(m.group(2)); pct = int(m.group(3))
        delta = pct if op == 'increase' else -pct
        return {
            "intent": "relative_change",
            "targets": [{"track": _track_label(n), "plugin": "reverb", "parameter": "wet"}],
            "operation": {"type": "relative", "value": delta, "unit": "%"},
            "meta": {"utterance": t, "fallback": True}
        }

    # 5) Frequency-based EQ: cut/boost (track N | instrument) at X Hz [by Y dB]
    m = re.search(r"\b(cut|boost)\b.*?(?:track\s+(\d+)|\b([a-z-]+)\b)?.*?(\d+)\s*hz(?:\s*by\s*(-?\d+\.?\d*)\s*d?b)?", s)
    if m:
        op = m.group(1)
        track_num = m.group(2)
        instrument = m.group(3)
        freq = float(m.group(4))
        amt = m.group(5)
        # If no explicit track and we matched a likely instrument, ask for clarification
        if not track_num:
            inst = _contains_instrument(s)
            if inst:
                return {
                    "intent": "clarification_needed",
                    "question": f"Which track are the {inst} on?",
                    "context": {
                        "action": op,
                        "parameter": f"eq @ {int(freq)}Hz",
                        "instrument": inst,
                        "utterance": t
                    }
                }
            # If no instrument either, default to track 1
            track_num = "1"
        val = float(amt) if amt is not None else 2.0
        if op == 'cut' and val > 0:
            val = -val
        return {
            "intent": "relative_change",
            "targets": [{"track": _track_label(int(track_num)), "plugin": "Channel EQ", "parameter": op}],
            "operation": {"type": "relative", "value": val, "unit": "dB", "frequency": freq},
            "meta": {"utterance": t, "fallback": True}
        }

    # 6) Instrument-only commands without track → clarification
    inst = _contains_instrument(s)
    if inst and not re.search(r"track\s+\d+", s):
        return {
            "intent": "clarification_needed",
            "question": f"Which track are the {inst} on?",
            "context": {"instrument": inst, "utterance": t}
        }

    # Default conservative fallback
    return {
        "intent": "set_parameter",
        "targets": [{"track": _track_label(1), "plugin": None, "parameter": "volume"}],
        "operation": {"type": "absolute", "value": -6, "unit": "dB"},
        "meta": {"utterance": t, "fallback": True}
    }


class DAWIntentParser:
    """DAW Intent Parser using Vertex AI.

    Args:
        project_id: GCP project ID (defaults to env: GOOGLE_CLOUD_PROJECT or PROJECT_ID)
        location: Vertex AI location (defaults to env: VERTEX_LOCATION or 'us-central1')
        model_name: Model name (defaults to env: VERTEX_MODEL or 'gemini-1.5-flash-002')
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        if not VERTEX_AVAILABLE:
            print("⚠️  Vertex AI not available - using fallback parser only")
            self.model = None
            return

        # Get config from env or params
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID") or "fadebender"
        self.location = location or os.getenv("VERTEX_LOCATION") or "us-central1"
        # Use model name compatible with Vertex AI
        self.model_name = model_name or os.getenv("VERTEX_MODEL") or "gemini-1.5-flash"

        try:
            # Initialize Vertex AI (uses Application Default Credentials)
            vertexai.init(project=self.project_id, location=self.location)

            # Create model with system instruction
            self.model = GenerativeModel(
                self.model_name,
                system_instruction=SYSTEM_PROMPT
            )
            print(f"✅ Vertex AI initialized: {self.model_name} in {self.project_id}/{self.location}")

        except Exception as e:
            print(f"⚠️  Failed to initialize Vertex AI: {e}")
            print("    Using fallback parser only")
            self.model = None

    def parse(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Parse natural language utterance into structured intent"""
        if not self.model:
            print("No AI model available, using fallback")
            return fallback_parse(text)

        try:
            # Build prompt with context and conversation history if available
            if context:
                # Handle clarification responses
                if context.get('action'):  # This is a clarification context
                    context_info = f"\n\nCONTEXT: The user previously wanted to {context.get('action', '')} {context.get('parameter', '')} for {context.get('track', 'unknown track')}. This is their clarification response. Combine the context with this response to create a complete command."
                    prompt = f"ORIGINAL CONTEXT: {json.dumps(context)}\nUSER CLARIFICATION: {text}\n\nCombine the original intent with this clarification to generate the final JSON command.\nJSON:"
                else:
                    # Handle conversation history
                    history_info = ""
                    if context.get('recentHistory'):
                        history_info = "\n\nCONVERSATION HISTORY:\n"
                        for msg in context['recentHistory']:
                            history_info += f"- {msg['type']}: {msg['content']}\n"

                    prompt = f"{history_info}\n\nCURRENT COMMAND: {text}\nJSON:"
            else:
                prompt = f"COMMAND: {text}\nJSON:"

            # Generate content with Vertex AI
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 1024,
                    "top_p": 0.9,
                }
            )

            # Extract JSON from response
            result_text = response.text.strip()

            # Remove markdown formatting if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]  # Remove ```json
            if result_text.startswith("```"):
                result_text = result_text[3:]   # Remove ```
            if result_text.endswith("```"):
                result_text = result_text[:-3]  # Remove trailing ```

            result_text = result_text.strip()

            # Try to parse JSON
            try:
                intent = json.loads(result_text)
                if "meta" not in intent:
                    intent["meta"] = {}
                intent["meta"]["utterance"] = text
                return intent
            except json.JSONDecodeError as e:
                print(f"JSON parsing failed: {e}")
                return fallback_parse(text)

        except Exception as e:
            print(f"AI parsing error: {e}")
            return fallback_parse(text)
