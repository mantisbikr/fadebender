# Fadebender Parse Index Architecture

## Overview
This document outlines how to build and load a **Parse Index** for Fadebender that ensures:
- Fast and accurate command parsing
- High reliability for device/parameter identification
- Typo tolerance
- Minimal startup/interaction lag

The parse index is separate from the Live **snapshot** of values. The snapshot stores **state**, while the parse index stores **vocabulary** used in parsing.

---

## Key Principles

| Component | Purpose | Loads When |
|---------|---------|------------|
| **Snapshot** | Current mixer states & parameter values | On Live set load |
| **Parse Index** | Device + parameter vocabulary for fast parsing | On session start (small, local) |
| **Lazy Device Param Loads** | Param lists for devices not currently in the Live set | On first reference |

The Parse Index prevents having to load *every* device and parameter upfront — only what exists in the current Live set.

---

## Data Structure: Parse Index

Example stored as JSON (Firestore or local session store):

```json
{
  "version": "pi-2025-11-10T09:12Z",
  "devices_in_set": [
    {"name": "reverb",    "aliases": ["reverb"],      "ordinals": 2},
    {"name": "8dotball",  "aliases": ["8dotball"]},
    {"name": "amp",       "aliases": ["amp"]},
    {"name": "compressor","aliases": ["compressor"]}
  ],
  "params_by_device": {
    "reverb": {
      "params": ["stereo image", "size smoothing", "feedback", "decay", "mix"],
      "aliases": {"stereo image": ["streo image"]}
    },
    "8dotball": {
      "params": ["feedback", "decay", "mix"],
      "aliases": {"decay": ["decai"]}
    },
    "amp": { "params": ["gain", "bass", "mid", "treble"], "aliases": {} },
    "compressor": { "params": ["threshold", "ratio", "attack", "release"], "aliases": {} }
  },
  "mixer_params": ["volume", "pan", "mute", "solo", "send a", "send b", "send c"],
  "typo_map": { "feedbakc": "feedback", "streo image": "stereo image" }
}
```

---

## Why This Works

- Only loads vocabulary **actually present** in the Live set → super small memory footprint.
- Parameter vocab keyed by **device type** → avoids collisions (e.g., different “Decay” meanings).
- Aliases and typo maps keep interactions fast and reliable.

---

## Compile on Session Start (Fast)

### 1. Normalize Text
- Lowercase, normalize whitespace, strip punctuation except `-` & `'`.

### 2. Build Device Regex
Sort longest → shortest to avoid partial matches:
```python
DEVICE_RE = r"(?i)\b(?:analog triplet dub|4th bandpass|8dotball|reverb|amp|compressor)\b"
```

### 3. Build Parameter Regex Per Device
```python
PARAM_RE["reverb"] = r"(?i)\b(?:stereo image|size smoothing|feedback|decay|mix)\b"
```

### 4. Build Tries (Optional Optimization)
Keeps fuzzy matching fast.

---

## Runtime Parse Flow

1. **Exact Parse (Regex-first)**
2. If missing/ambiguous:
   - Apply **typo_map**
3. If still missing:
   - Perform **Constrained Fuzzy Search** only within:
     - text after scope
     - before value separator (`to`, `by`, `at`)
4. If still unresolved:
   - **Lazy Load** that device's param names from Firestore
5. If still ambiguous → **Fallback to LLM**

---

## Confidence Scoring (LLM Gate)

```
+0.5 if scope parsed
+0.5 if parameter found
+0.3 if device found when expected
+0.2 if RHS value parsed

-0.4 if both device and parameter required fuzzy match
-0.3 if conflicts/overlaps detected

LLM fallback if score < 1.0
```

---

## Benefits

| Feature | Achieved By |
|--------|-------------|
| Fast parsing | Exact-first regex + precompiled vocab |
| Reliable device/param matching | Longest-match & per-device param lists |
| Highly typo tolerant | Constrained fuzzy + typo_map learning |
| Zero noticeable session-start lag | Load only current-set vocab |
| Ability to handle unseen devices | Lazy hydration |

---

## Next Step
Implement three modules:

| File | Purpose |
|-----|---------|
| `parse_index_builder.py` | Create parse index JSON from Firestore + Live set |
| `parser_boot.py` | Compile regex/tries on session start |
| `lazy_hydrator.py` | On-demand fetch/compile for new devices |

---

You can now use this doc inside VS Code to implement the parsing engine.
