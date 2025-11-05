# Fadebender Ghost-Typing Command Input (Sections-Aware) — Implementation Spec

## Table of Contents
- [Goals & Non-Goals](#goals--non-goals)
- [User Experience (at a glance)](#user-experience-at-a-glance)
- [Command Grammar (concise)](#command-grammar-concise)
- [Data Model (Firestore → DeviceMap)](#data-model-firestore--devicemap)
- [Parser & FSM](#parser--fsm)
- [Suggestion Engine](#suggestion-engine)
- [Ghost Text & Chips UI](#ghost-text--chips-ui)
- [Command Palette (“More…”) UI](#command-palette-more-ui)
- [Validation, Units, Clamping](#validation-units-clamping)
- [Fuzzy Matching & Synonyms](#fuzzy-matching--synonyms)
- [Shortcuts & Power-User Tokens](#shortcuts--power-user-tokens)
- [Execution Contract (Intent Object)](#execution-contract-intent-object)
- [Performance & Caching](#performance--caching)
- [Telemetry & Ranking](#telemetry--ranking)
- [Accessibility](#accessibility)
- [Security & Safety Guards](#security--safety-guards)
- [Testing Plan](#testing-plan)
- [Rollout Plan](#rollout-plan)
- [Code Scaffolds](#code-scaffolds)
- [Developer Checklist](#developer-checklist)

---

## Goals & Non-Goals

### Goals
- Fast, error-proof command entry using regex + FSM, with LLM fallback only when needed.
- Parameter selection guided by Firestore device parameter groups (sections).
- Inline ghost suggestions and suggestion chips to guide users.
- Immediate structured-intent execution when parse succeeds.
- Deterministic latency (<50 ms per keystroke).

### Non-Goals
- Not aiming to interpret full natural language; fallback to LLM only on parse failure.

---

## User Experience (at a glance)

```
User types:   set t2 p
Ghost shows:  set track 2 parameter 
Chips show:   Time | Space | Early | Damping | Mod | EQ | I/O
User picks:   Time
Chips show:   Decay Time | Pre-Delay | Size | (More…)
Ghost shows:  set track 2 parameter Decay Time to 
User types:   5 s
Enter → intent executes
```

---

## Command Grammar (concise)

```
COMMAND     := ACTION TARGET (DEVICE_OR_PARAM)? (PARAM_NAME)? (VALUE_SPEC)?
ACTION      := set | increase | decrease | toggle | bypass | enable
TARGET      := track N | return A | master
DEVICE_OR_PARAM := device DEVICE_ID | parameter
PARAM_NAME  := token resolved via section/param lookup
VALUE_SPEC  := to NUMBER UNIT? | by NUMBER UNIT? | on/off
```

Regex atoms and implementation details should follow the document previously provided.

---

## Data Model (Firestore → DeviceMap)

Expected Firestore structure:

```json
{
  "name": "Reverb",
  "sections": [
    {
      "id": "time",
      "label": "Time",
      "priority": 10,
      "params": [
        {
          "id": "decay_time",
          "label": "Decay Time",
          "kind": "continuous",
          "unit": "s",
          "min": 0.1,
          "max": 60,
          "synonyms": ["decay", "rt60"],
          "abbr": ["dec"]
        }
      ]
    }
  ]
}
```

Refer to the full document for the `DeviceMap` adapter code.

---

## Parser & FSM

The FSM processes user input incrementally:
- START → ACTION → TARGET → DEVICE_OR_PARAM → PARAM_SECTION → PARAM_NAME → VALUE → DONE

Each state determines ghost text and chip suggestions.

---

## Suggestion Engine

- Chips for next possible tokens.
- Ghost text shows a likely continuation.
- Parameter selection uses Firestore **sections**, sorted by priority.

---

## Ghost Text & Chips UI

- Ghost text overlays the input, accepted via Tab/Enter/Right.
- Chips appear below input and can be clicked or selected with keyboard.

---

## Command Palette (“More…”) UI

A modal searchable palette opens when needed for large parameter lists.

---

## Validation, Units, Clamping

- Use parameter metadata (min/max/unit/kind) to check values.
- Clamp values and show correction suggestions.

---

## Fuzzy Matching & Synonyms

- Supports `synonyms` and `abbr` from Firestore.
- Never auto-apply; always show as suggestion first.

---

## Shortcuts & Power-User Tokens

Examples:
- `t2` → `track 2`
- `rA` → `return A`
- `param pd` → matches Pre-Delay

---

## Execution Contract (Intent Object)

See full document for exact TypeScript interface.

---

## Performance & Caching

- Preload Firestore device maps when live set loads.
- Cache locally in memory and optionally indexedDB.
- No LLM needed unless parser fails.

---

## Telemetry & Ranking

- Track user selection frequency and recency.
- Re-rank suggestions over time.

---

## Accessibility

- Full keyboard navigation.
- ARIA labels for ghost suggestions.

---

## Testing Plan

- Unit tests for FSM transitions and value rules.
- Integration tests with real device maps.
- User testing for latency and ergonomics.

---

## Rollout Plan

1. Implement for Reverb first.
2. Add device palette + fuzzy search.
3. Extend to all supported devices.

---

## Developer Checklist

- [ ] Implement FSM
- [ ] Implement ghost overlay & chips
- [ ] Integrate Firestore DeviceMap
- [ ] Add clamping & validation
- [ ] Add fuzzy matching
- [ ] Add palette UI
- [ ] Emit structured intents to dispatcher
