# Intents API - Letter-Based References

This document shows the new letter-based API for sends and returns, which is more intuitive than numeric indices.

## Why Letter-Based?

Live users see "Send A", "Send B", "Return A", "Return B" in the UI.
Using letters in the API matches the user's mental model and makes natural language commands easier.

## Track Sends - Letter-Based (Recommended)

### Using send_ref (NEW - Preferred)
```bash
# Set Send A on Track 1 to -12 dB
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"track","action":"set","track_index":1,"field":"send","send_ref":"A","value":-12,"unit":"dB"}'

# Set Send B on Track 2 to -6 dB
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"track","action":"set","track_index":2,"field":"send","send_ref":"B","value":-6,"unit":"dB"}'

# Set Send C on Track 1 to mute (0 dB = full send)
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"track","action":"set","track_index":1,"field":"send","send_ref":"C","value":-60,"unit":"dB"}'
```

### Using send_index (Legacy - Still Supported)
```bash
# Set Send A (index 0) on Track 1 to -12 dB
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"track","action":"set","track_index":1,"field":"send","send_index":0,"value":-12,"unit":"dB"}'

# Set Send B (index 1) on Track 2 to -6 dB
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"track","action":"set","track_index":2,"field":"send","send_index":1,"value":-6,"unit":"dB"}'
```

## Return Tracks - Letter-Based (Recommended)

### Return Mixer - Using return_ref (NEW - Preferred)
```bash
# Set volume on Return A to -6 dB
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"return","action":"set","return_ref":"A","field":"volume","value":-6,"unit":"dB"}'

# Pan Return B to center
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"return","action":"set","return_ref":"B","field":"pan","display":"center"}'

# Pan Return A 25 left
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"return","action":"set","return_ref":"A","field":"pan","display":"25L"}'

# Mute Return A
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"return","action":"set","return_ref":"A","field":"mute","value":1}'
```

### Return Mixer - Using return_index (Legacy - Still Supported)
```bash
# Set volume on Return A (index 0) to -6 dB
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"return","action":"set","return_index":0,"field":"volume","value":-6,"unit":"dB"}'

# Pan Return B (index 1) to center
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"return","action":"set","return_index":1,"field":"pan","display":"center"}'
```

## Return Sends - Letter-Based (Recommended)

### Using return_ref + send_ref (NEW - Preferred)
```bash
# Set Send A on Return A to -12 dB
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"return","action":"set","return_ref":"A","field":"send","send_ref":"A","value":-12,"unit":"dB"}'

# Set Send B on Return B to -6 dB
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"return","action":"set","return_ref":"B","field":"send","send_ref":"B","value":-6,"unit":"dB"}'
```

### Using numeric indices (Legacy - Still Supported)
```bash
# Set Send A (index 0) on Return A (index 0) to -12 dB
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"return","action":"set","return_index":0,"field":"send","send_index":0,"value":-12,"unit":"dB"}'
```

## Return Device Parameters - Letter-Based (Recommended)

### Using return_ref (NEW - Preferred)
```bash
# Set Reverb Decay Time on Return A to 2.5s
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"decay","display":"2.5 s"}'

# Set Reverb Dry/Wet on Return A to 80%
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"dry/wet","value":80,"unit":"percent"}'
```

### Using return_index (Legacy - Still Supported)
```bash
# Set Reverb Decay Time on Return A (index 0) to 2.5s
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","action":"set","return_index":0,"device_index":0,"param_ref":"decay","display":"2.5 s"}'
```

## Natural Language Examples

With letter-based references, these commands become possible:

```
"Set send A on track 1 to -12 dB"
→ {"domain":"track","track_index":1,"field":"send","send_ref":"A","value":-12,"unit":"dB"}

"Pan return A to center"
→ {"domain":"return","return_ref":"A","field":"pan","display":"center"}

"Set return B volume to unity"
→ {"domain":"return","return_ref":"B","field":"volume","display":"unity"}

"Set send B on return A to -6 dB"
→ {"domain":"return","return_ref":"A","field":"send","send_ref":"B","value":-6,"unit":"dB"}
```

## API Summary

### Tracks
- `track_index: 1` = Track 1 (1-based, matches Live UI)

### Sends
- **Preferred**: `send_ref: "A"` = Send A
- **Legacy**: `send_index: 0` = Send A (0-based)

### Returns
- **Preferred**: `return_ref: "A"` = Return A
- **Legacy**: `return_index: 0` = Return A (0-based)

## Migration Guide

### From Numeric to Letter-Based

**Before (numeric):**
```json
{"domain":"track","track_index":1,"field":"send","send_index":0,"value":-12,"unit":"dB"}
```

**After (letter-based):**
```json
{"domain":"track","track_index":1,"field":"send","send_ref":"A","value":-12,"unit":"dB"}
```

**Key Changes:**
1. `send_index: 0` → `send_ref: "A"`
2. `send_index: 1` → `send_ref: "B"`
3. `return_index: 0` → `return_ref: "A"`
4. `return_index: 1` → `return_ref: "B"`

Both formats are supported, but letter-based is preferred for user-facing APIs and NLP applications.
