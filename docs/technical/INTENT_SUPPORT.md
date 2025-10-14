# Intent Support

Status: v1 canonical executor implemented (absolute values, guardrails)

This document tracks what the canonical intent layer supports, how to call it, and the roadmap to richer NL parsing.

Key endpoints
- `POST /intent/execute` — execute canonical intent with guardrails (new)
- `POST /intent/parse` — parse NL to canonical (existing; rules/LLM pipeline to be updated later)

Canonical Intent Schema (v1)

```
{
  "domain": "track|return|master|device|transport",
  "action": "set",
  "track_index": 0,
  "return_index": null,
  "device_index": null,
  "field": "volume|pan|mute|solo|send|tempo",
  "send_index": 0,
  "param_index": 12,
  "param_ref": "Dry/Wet",
  "value": 0.75,
  "unit": "normalized|percent|db|ms|hz|on|off",
  "dry_run": false,
  "clamp": true
}
```

Guardrails
- Clamp to [min,max] for device params; [0,1] for sends/volume; [-1,1] for pan.
- dB → Live float conversion for track/master volume when `unit = db`.
- Auto-enable dependent masters heuristically (e.g., enable "HiFilter On" before setting "HiFilter Freq").
- `dry_run = true` returns a preview payload without applying.

Examples
- Track volume (dB):
```
{ "domain":"track","action":"set","track_index":3,"field":"volume","value":-6.0,"unit":"db" }
```

- Return device param by index:
```
{ "domain":"device","action":"set","return_index":1,"device_index":0,"param_index":12,"value":0.42 }
```

- Return send level (percent):
```
{ "domain":"return","action":"set","return_index":0,"field":"send","send_index":1,"value":25,"unit":"percent" }
```

Roadmap
- Relative and qualitative directives (slight/moderate/large/significant) with unit-aware step tables.
- Lexicon-based token correction and rules-first NL parse; constrained LLM fallback on failure.
- Mapping-driven dependency model (masters → modes → dependents) instead of heuristics.
