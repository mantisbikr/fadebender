# Preset System Architecture - Universal Display-Value Based Approach

**Status:** Design Document
**Date:** 2025-10-11
**Purpose:** Comprehensive guide for LLM-based implementation of universal display-value preset system for ALL device types (Delay, Reverb, Compressor, EQ, etc.)
**Scope:** Device-agnostic architecture applicable to any Ableton Live device

**Key Innovation:** Leverages LLM analysis of device manuals + stock presets to automatically discover:
- Master/dependent parameter relationships (grouping rules)
- Parameter types (binary, quantized, continuous)
- Suggested curve fit types (linear, exponential, logarithmic)
- Unit hints and value labels

**Critical Workflow Change:** Enrichment is delayed until AFTER device analysis is complete:
1. **Capture Phase:** All stock presets captured with status="captured" (NO enrichment)
2. **Analysis Phase:** Device analyzed by LLM, device mapping updated with metadata
3. **Enrichment Phase:** Bulk enrichment triggered for all captured presets
4. **Result:** All presets enriched with accurate, grouping-aware metadata

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Current Approach Issues](#current-approach-issues)
3. [New Approach Overview](#new-approach-overview)
4. [Core Concepts](#core-concepts)
5. [System Components](#system-components)
6. [Data Structures](#data-structures)
7. [Workflows](#workflows)
8. [Grouping Rules](#grouping-rules)
9. [Parameter Application Order](#parameter-application-order)
10. [Implementation Phases](#implementation-phases)
11. [Examples](#examples)

---

## 1. Problem Statement

### Current Issues

**Inaccurate Conversions:**
- Display values in Ableton don't match stored/converted values
- Manual curve fitting (linear/exponential) often fails
- Requires extensive learning process with parameter sweeps
- Example: Delay shows 245ms in UI, but converted value is 120ms

**Stale Parameter Values:**
- When master switches are ON/OFF, dependent params retain stale values
- System stores ALL parameters regardless of active state
- Enrichment uses these stale values, generating incorrect metadata
- Examples:
  - Delay: When Link is ON, R channel params are stale
  - Reverb: When Chorus On is OFF, Chorus Rate/Amount are stale
  - EQ: When Band 3 is OFF, Band 3 Freq/Gain/Q are stale

**Complex Learning Process:**
- Must sweep parameters multiple times
- Fit curves (R² optimization)
- Detect parameter types (linear/exp)
- Time-consuming and error-prone
- Needs separate learning for each device type

**Missing Grouping Awareness:**
- System doesn't know which params control others (master/dependent relationships)
- Doesn't know mode toggles that switch between parameter sets
- Results in contradictory data sent to LLM
- Examples:
  - Delay: Link controls R params, Sync toggles Time/16th modes
  - Reverb: Feature switches control processing sections
  - Compressor: Sidechain On controls sidechain params

### What We Need

1. **Accurate parameter values** - What you see is what you get
2. **No curve fitting for reading** - Use Ableton's display values directly
3. **Grouping awareness** - Filter inactive parameters
4. **Smart preset switching** - Load entire presets or modify select parameters
5. **Minimal learning** - Auto-discover device structures
6. **Future: Intelligent parameter manipulation** - Change parameters by display value

---

## 2. Current Approach Issues

### Learning Process
```
1. Detect device
2. Sweep each parameter (0%, 25%, 50%, 75%, 100%)
3. Record (normalized_value, display_value) pairs
4. Fit curve (linear/exp/log)
5. Calculate R² to validate fit
6. Store curve coefficients
7. Use curves to convert normalized ↔ display
```

**Problems:**
- ❌ Curves are often inaccurate (L Time: 0.547 → 120ms, should be 245ms)
- ❌ Time-consuming (21 params × 5 points × delay = significant time)
- ❌ Needs refinement passes when R² is poor
- ❌ Breaks when device behavior is non-standard

### Preset Capture
```
1. Read all parameter normalized values (0.0-1.0)
2. Store normalized values in Firestore
3. (Optionally) Generate metadata with LLM
```

**Problems:**
- ❌ Stores ALL parameters including stale ones
- ❌ No grouping awareness
- ❌ Normalized values need conversion to understand

### Preset Enrichment
```
1. Load normalized values from Firestore
2. Convert using curves to display values
3. Send to LLM for metadata generation
4. Store enriched metadata
```

**Problems:**
- ❌ Conversions are inaccurate (curve errors)
- ❌ Includes stale parameters (R Sync=1.0 when Link=ON)
- ❌ LLM sees contradictory data

---

## 3. New Approach Overview

### Key Insight: Ableton Sends Display Values

Every parameter returned by Ableton includes:
```json
{
  "name": "L Time",
  "value": 0.5467743873596191,        // Normalized (0.0-1.0)
  "display_value": "245.0",            // Actual display string
  "min": 0.0,
  "max": 1.0
}
```

**The `display_value` field gives us exactly what the UI shows!**

### Three-Pillar Strategy

#### Pillar 1: Display-Value Reading (Enrichment)
- ✅ Use `display_value` directly - no conversion needed
- ✅ Apply grouping rules to filter inactive params
- ✅ Send accurate values to LLM
- ✅ Perfect accuracy for reading/understanding

#### Pillar 2: Normalized-Value Storage (Future Manipulation)
- ✅ Store `value` (normalized) for future manipulation
- ✅ Use for preset switching (direct value application)
- ✅ Enable parameter modification later

#### Pillar 3: Smart Curve Fitting (On-Demand)
- ✅ When user wants to SET "500ms", use 3-tier fallback:
  1. Try curve from 32-preset analysis (if confident)
  2. Try parameter type heuristic (Time → exp curve)
  3. Just-in-time probing (probe 3-5 values, fit curve, use it)
- ✅ System gets smarter over time as probing enriches database

---

## 4. Core Concepts

### Device Types

This architecture applies to ALL Ableton device types:
- **Audio Effects:** Delay, Reverb, Compressor, EQ Eight, Auto Filter, Saturator, etc.
- **MIDI Effects:** Arpeggiator, Chord, Scale, etc.
- **Instruments:** (Future scope)

Each device type has unique:
- Parameter structure
- Grouping rules
- Parameter types
- Audio engineering characteristics

### Parameter Classification

Each parameter is classified by the LLM during device discovery:

#### Parameter Types
1. **Binary (On/Off)**
   - Values: 0.0 or 1.0
   - Examples: "Device On", "Filter On", "Chorus On", "Link"
   - Display: "0.0" / "1.0" or visual toggle
   - Fit: None needed (discrete)

2. **Quantized (Discrete Steps)**
   - Values: Integer steps (e.g., 0-7, 0-2)
   - Examples: "L 16th" (0-7 = 1-8 sixteenths), "Delay Mode" (0-2 = 3 modes)
   - Display: May show as integers or labels
   - Fit: None needed (discrete) or lookup table

3. **Continuous Linear**
   - Values: 0.0-1.0, linear mapping
   - Examples: "Dry/Wet", "Mix", "Level", "Amount", "Diffusion"
   - Display: Usually percentage or dB
   - Fit: Linear (y = a*x + b)

4. **Continuous Exponential**
   - Values: 0.0-1.0, exponential mapping
   - Examples: "Time" (ms), "Frequency" (Hz), "Decay", "Rate"
   - Display: Time/frequency units
   - Fit: Exponential (y = a*e^(b*x) + c)

5. **Continuous Logarithmic**
   - Values: 0.0-1.0, logarithmic mapping
   - Examples: Less common, some frequency ranges
   - Display: Varies
   - Fit: Logarithmic (y = a*log(b*x) + c)

#### Parameter Roles
1. **Master** - Controls visibility/behavior of other params
2. **Dependent** - Only active when master has specific value
3. **Independent** - Always active, no dependencies

### Device Signature

A hash identifying device structure (NOT values):

```python
def compute_signature(params):
    """
    Signature includes:
    - Parameter names (ordered)
    - Parameter indices
    - Min/max ranges

    Does NOT include:
    - Current values
    - Display values
    """
    structure = [
        {
            "index": p["index"],
            "name": p["name"],
            "min": p["min"],
            "max": p["max"]
        }
        for p in params
    ]
    return hashlib.sha1(json.dumps(structure, sort_keys=True).encode()).hexdigest()
```

**Purpose:** Match presets to compatible devices

### Grouping Rules

Define master/dependent parameter relationships:

```json
{
  "delay": {
    "masters": ["Link", "L Sync", "R Sync", "Filter On"],
    "dependents": {
      "L Time": "L Sync",        // L Time active when L Sync = 0.0
      "L 16th": "L Sync",        // L 16th active when L Sync = 1.0
      "R Sync": "Link",          // R Sync active when Link = 0.0
      "R Time": "Link",          // R Time active when Link = 0.0
      "R 16th": "Link",          // R 16th active when Link = 0.0
      "R Offset": "Link",
      "Filter Freq": "Filter On",
      "Filter Width": "Filter On"
    },
    "dependent_master_values": {
      "L Time": 0.0,    // Active when master = 0.0
      "L 16th": 1.0,    // Active when master = 1.0
      "R Sync": 0.0,    // Active when Link = 0.0
      "R Time": 0.0,
      "R 16th": 0.0,
      "R Offset": 0.0
    }
  }
}
```

**Purpose:** Filter inactive/stale parameters before enrichment or display

### Display Value Types

Parameters have different display formats across device types:

| Type | Example | Device Context | Notes |
|------|---------|----------------|-------|
| Time (ms/s) | "245.0", "2.3 s" | Delay, Reverb, Compressor | Exponential curve |
| Time (sync) | "3.0", "4 sixteenths" | Delay, Arpeggiator | Quantized (tempo-synced) |
| Frequency (Hz/kHz) | "1725.0", "8.5 kHz" | Filter, EQ, Reverb | Exponential curve |
| Percentage | "58.0", "33.0" | Mix, Level, Feedback | Linear |
| Decibels (dB) | "+3.5 dB", "-12.0 dB" | Gain, EQ bands | Linear or logarithmic |
| On/Off | "1.0" / "0.0" | All devices | Binary toggle |
| Mode/Type | "LP12", "BandPass" | Filter, EQ | Quantized (discrete modes) |
| Ratio | "4:1", "8:1" | Compressor | Quantized or continuous |
| Note/Pitch | "C3", "+7 st" | Pitch, Transpose | Quantized (semitones) |

---

## 5. System Components

### 5.1 Device Mapping Store

**Location:** `device_mappings/` collection in Firestore

**Structure:**
```json
{
  "signature": "9bfcc8b6e739d9675c03f6fe0664cfada9ef7df1",
  "device_name": "Delay",
  "device_type": "audio_effect",
  "category": "delay",
  "manufacturer": "Ableton",
  "param_count": 21,
  "discovered_at": "2025-10-11T00:00:00Z",

  "param_structure": [
    {
      "index": 0,
      "name": "Device On",
      "min": 0.0,
      "max": 1.0,
      "param_type": "binary",
      "param_role": "independent",
      "suggested_fit": null
    },
    {
      "index": 4,
      "name": "L Sync",
      "min": 0.0,
      "max": 1.0,
      "param_type": "binary",
      "param_role": "master",
      "suggested_fit": null,
      "controls": ["L Time", "L 16th"]
    },
    {
      "index": 6,
      "name": "L Time",
      "min": 0.0,
      "max": 1.0,
      "param_type": "continuous_exponential",
      "param_role": "dependent",
      "suggested_fit": "exponential",
      "master": "L Sync",
      "active_when": 0.0,
      "unit_hint": "ms"
    },
    {
      "index": 8,
      "name": "L 16th",
      "min": 0.0,
      "max": 7.0,
      "param_type": "quantized",
      "param_role": "dependent",
      "suggested_fit": null,
      "master": "L Sync",
      "active_when": 1.0,
      "unit_hint": "sixteenths",
      "value_labels": {
        "0": "1 16th",
        "1": "2 16ths",
        "2": "3 16ths",
        "3": "4 16ths",
        "4": "5 16ths",
        "5": "6 16ths",
        "6": "7 16ths",
        "7": "8 16ths"
      }
    },
    {
      "index": 12,
      "name": "Feedback",
      "min": 0.0,
      "max": 1.0,
      "param_type": "continuous_linear",
      "param_role": "independent",
      "suggested_fit": "linear",
      "unit_hint": "%"
    }
    // ... remaining params with metadata
  ],

  "grouping_rules": {
    "masters": ["Link", "L Sync", "R Sync", "Filter On"],
    "dependents": {
      "L Time": "L Sync",
      "L 16th": "L Sync",
      "R Sync": "Link",
      "R Time": "Link",
      "R 16th": "Link",
      "Filter Freq": "Filter On",
      "Filter Width": "Filter On"
    },
    "dependent_master_values": {
      "L Time": 0.0,
      "L 16th": 1.0,
      "R Sync": 0.0,
      "R Time": 0.0,
      "R 16th": 0.0,
      "Filter Freq": 1.0,
      "Filter Width": 1.0
    }
  },

  "llm_analysis": {
    "analyzed_at": "2025-10-11T00:15:00Z",
    "preset_count": 32,
    "confidence": 0.92,
    "notes": "Clear master/dependent patterns observed in all 32 stock presets"
  }
}
```

**Key Additions:**
- ✅ `param_type` - Binary, quantized, continuous (linear/exp/log)
- ✅ `param_role` - Master, dependent, or independent
- ✅ `suggested_fit` - For continuous params, suggested curve type
- ✅ `unit_hint` - Display unit (ms, Hz, %, dB)
- ✅ `value_labels` - For quantized params, label mapping
- ✅ `grouping_rules` - Embedded in device mapping
- ✅ `llm_analysis` - Metadata about discovery process

**NO curve coefficients stored** - those come from multi-preset analysis or just-in-time probing

### 5.2 Preset Store

**Location:** `presets/` collection in Firestore

**Structure:**
```json
{
  "preset_id": "delay_4th_bandpass",
  "name": "4th Bandpass",
  "device_name": "Delay",
  "manufacturer": "Ableton",
  "category": "delay",
  "preset_type": "stock",
  "structure_signature": "9bfcc8b6e739d9675c03f6fe0664cfada9ef7df1",

  "parameter_values": {
    "Device On": 1.0,
    "Link": 1.0,
    "L Sync": 1.0,
    "L Time": 0.0,
    "L 16th": 3.0,
    // ... normalized values for ALL params
  },

  "parameter_display_values": {
    "Device On": "1.0",
    "Link": "1.0",
    "L Sync": "1.0",
    "L Time": "1.0",
    "L 16th": "3.0",
    // ... display values for ALL params
  },

  "audio_engineering": {
    "delay_time": "Left: 3 sixteenths (tempo-synced)",
    "feedback_character": "58% regeneration, moderate tail",
    "sync_mode": "Tempo-synced to project BPM",
    // ... enriched metadata
  },

  "metadata_version": 2,
  "metadata_status": "enriched",
  "enriched_at": "2025-10-11T02:29:26Z"
}
```

**Key Changes:**
- ✅ Store BOTH `parameter_values` (normalized) AND `parameter_display_values`
- ✅ Enrichment uses `parameter_display_values` exclusively
- ✅ Preset switching uses `parameter_values` (normalized)

### 5.3 Grouping Configuration

**Location:** `configs/param_learn.json` (synced to GCS)

**Loaded by:**
- Cloud Run worker (for enrichment filtering)
- Local server (for capture validation, future manipulation)

**Discovery Method:**
- Manual configuration (device-specific)
- Assisted by LLM analysis of Ableton manual + 32 stock presets

### 5.4 Stock Preset Database

**Purpose:** Reference library for preset switching and parameter suggestions

**Contents:**
- All 32 Ableton Delay stock presets
- All 32 Ableton Reverb stock presets
- Etc. for each device type

**Usage:**
- User asks "make it darker" → analyze stock presets for "dark" characteristics
- User asks "turn into slapback" → find closest stock preset, load it
- User asks "more feedback" → check what stock presets do for feedback values

---

## 6. Data Structures

### 6.1 Parameter Structure (from Ableton)

```typescript
interface AbletonParameter {
  index: number;          // Position in parameter list
  name: string;           // "L Time", "Feedback", etc.
  value: number;          // Normalized 0.0-1.0 (or 0-7 for quantized)
  display_value: string;  // "245.0", "58.0", "1725.0"
  min: number;            // Usually 0.0
  max: number;            // Usually 1.0 (or 7.0 for quantized)
}
```

### 6.2 Device Signature Structure

```typescript
interface DeviceSignature {
  signature: string;      // SHA1 hash
  device_name: string;
  manufacturer: string;
  param_count: number;
  param_structure: Array<{
    index: number;
    name: string;
    min: number;
    max: number;
  }>;
}
```

### 6.3 Preset Structure

```typescript
interface Preset {
  preset_id: string;
  name: string;
  device_name: string;
  category: string;
  structure_signature: string;

  parameter_values: Record<string, number>;           // Normalized
  parameter_display_values: Record<string, string>;   // Display strings

  audio_engineering?: {
    // Device-specific enriched metadata
    [key: string]: any;
  };

  metadata_version: number;
  metadata_status: "pending" | "enriched";
  enriched_at?: string;
}
```

### 6.4 Grouping Rule Structure

```typescript
interface GroupingRules {
  [deviceType: string]: {
    masters: string[];                           // Master parameter names
    dependents: Record<string, string>;          // Dependent → Master mapping
    dependent_master_values: Record<string, number>; // Required master value
    skip_auto_enable?: string[];                 // Don't auto-enable these masters
  };
}
```

---

## 7. Workflows

### 7.1 Device Discovery & Mapping

**Trigger:** User loads a device on a return track, opens device tray in UI

**Process:**
```
1. Read device params via API
   GET /return/device/params?index=1&device=0

2. Strip values, compute signature
   signature = compute_signature(params)

3. Check if signature exists in device_mappings

4. IF NOT EXISTS:
   a. Create new device mapping entry
      - Store signature → device_name
      - Store param structure (no values)
   b. Mark as "new device discovered"

5. IF EXISTS:
   a. Validate param count matches
   b. Return existing mapping
```

**No learning process needed!**

### 7.1.1 Offline Manual Device Analysis (Developer Workflow)

**Purpose:** One-time manual process per device type to generate comprehensive device mapping with grouping rules and parameter metadata

**Trigger:** New device type needs to be fully analyzed (e.g., first time analyzing Delay, Reverb, Compressor, etc.)

**Process:**

```
STEP 1: Capture All Stock Presets to Firestore
-----------------------------------------------
1. In Ableton Live, load device on a return track
2. For each stock preset available (typically 20-40 presets per device):
   a. Load preset in Ableton
   b. Use capture API or web UI to save to Firestore
   c. Ensures both parameter_values AND parameter_display_values are stored
3. Result: All preset documents in Firestore presets/ collection
   - Each with structure_signature matching device
   - Each with full param values and display values
   - Note the actual count (varies by device type)

STEP 2: Export All Presets to Analysis Document
------------------------------------------------
1. Query Firestore for all presets matching device signature:
   ```
   presets.where('structure_signature', '==', signature)
         .where('device_name', '==', 'Delay')
         .get()
   ```

2. Generate THREE separate analysis documents:

   **Document 1:** /tmp/device_structure_{device_name}.md
   ```markdown
   # Device Parameter Structure: {Device Name}

   ## Device Information
   - Signature: {signature}
   - Device Name: {device_name}
   - Manufacturer: {manufacturer}
   - Total Parameters: {param_count}
   - Stock Preset Count: {count}

   ## Parameter Structure
   | Index | Name | Min | Max |
   |-------|------|-----|-----|
   | 0 | Device On | 0.0 | 1.0 |
   | 1 | Delay Mode | 0.0 | 2.0 |
   | ... | ... | ... | ... |
   ```

   **Document 2:** /tmp/device_presets_{device_name}.md
   ```markdown
   # Stock Preset Dumps: {Device Name}

   Total Presets: {count}

   ## Preset 1: {preset_name}
   ```json
   {
     "parameter_values": {...},
     "parameter_display_values": {...}
   }
   ```

   ## Preset 2: {preset_name}
   ```json
   {
     "parameter_values": {...},
     "parameter_display_values": {...}
   }
   ```

   (repeat for all available presets)
   ```

   **Document 3:** /tmp/device_manual_{device_name}.md
   ```markdown
   # Device Manual Excerpts: {Device Name}

   Source: Ableton Live Reference Manual

   ## Parameter Descriptions
   [Copy relevant sections from manual]

   ## Relationships and Behaviors
   [Note any master/dependent relationships mentioned]

   ## Usage Notes
   [Any special behaviors or quirks]
   ```


STEP 3: Feed to External LLM (ChatGPT/Claude)
----------------------------------------------
1. Open ChatGPT or Claude in browser
2. Upload or paste the analysis document
3. Use the detailed prompt below (copy-paste ready)

### Complete LLM Analysis Prompt (Copy-Paste This)

```
# Ableton Device Parameter Analysis Task

You are a parameter analysis expert for an audio engineering preset management system. Your task is to analyze an Ableton device's parameter structure and stock presets to generate comprehensive metadata that will enable intelligent preset management, grouping-aware filtering, and smart parameter manipulation.

## Context

I'm building a system that manages Ableton device presets. The system needs to:
1. Filter out "stale" or inactive parameters before generating descriptions
2. Apply parameters in the correct order when loading presets
3. Classify parameters by type to enable future curve fitting
4. Understand master/dependent relationships between parameters

## Input Data Provided

I will provide THREE separate documents:

**Document 1: Device Parameter Structure**
- Device name, signature, manufacturer
- Complete list of parameters with names, indices, min/max values
- Basic structure information

**Document 2: Stock Preset Dumps**
- All available stock presets for this device (typically 20-40 presets)
- Each preset includes both normalized values (0.0-1.0) and display_values (what the UI shows)
- Preset names and categories

**Document 3: Device Manual Excerpts** (if available)
- Relevant sections from Ableton's device reference manual
- Parameter descriptions and relationships
- Usage notes and behavior explanations

## Your Analysis Tasks

### Task 1: Identify Grouping Rules (Master/Dependent Relationships)

**Master Parameters:** Parameters that control the visibility, behavior, or relevance of other parameters.

Common patterns to detect:
- **On/Off Switches**: When OFF, dependent params are inactive (e.g., "Filter On" controls "Filter Freq", "Filter Width")
- **Mode Toggles**: Switch between alternate parameter sets (e.g., "Sync" toggles between "Time" mode and "16th" mode)
- **Stereo Link**: When ON, right channel params are stale/ignored (e.g., "Link" controls all "R" params)
- **Enable Sections**: Enable/disable entire processing sections (e.g., "Chorus On" controls "Chorus Rate", "Chorus Amount")

**How to detect:**
1. Look for binary (0.0/1.0) parameters with names like "On", "Enable", "Link", "Sync"
2. Check if certain parameters only vary meaningfully when a switch is in a specific state
3. Example: If "Chorus On" = 0.0 in some presets, check if "Chorus Rate" and "Chorus Amount" are always the same default value in those presets
4. Example: If "Link" = 1.0 in many presets, check if "R Sync", "R Time", "R 16th" don't vary much in those presets (they're stale)

**Output:**
- List of master parameter names
- Map of dependent parameters to their masters
- Required master values for each dependent to be "active"

### Task 2: Classify Each Parameter Type

For EVERY parameter, determine its type:

**Binary (On/Off):**
- Only two values appear across all presets: 0.0 and 1.0
- Usually toggle switches
- Examples: "Device On", "Link", "Filter On", "Sync"

**Quantized (Discrete Steps):**
- Limited set of discrete integer values (e.g., 0, 1, 2, 3)
- Often mode selectors or stepped controls
- May display as numbers or labels
- Examples: "Delay Mode" (0.0, 1.0, 2.0), "L 16th" (0-7 for 1-8 sixteenths)
- Check if display_value shows labels or if it's numeric but adds offset (e.g., value=3.0 displays as "4 sixteenths")

**Continuous Linear:**
- Full range of values 0.0-1.0 appearing across presets
- Display value scales proportionally with normalized value
- Check pattern: If normalized doubles, display_value roughly doubles
- Examples: "Dry/Wet" (0.5 → 50%), "Mix", "Amount", "Level"
- Often displays as percentage or dB

**Continuous Exponential:**
- Full range of values 0.0-1.0 appearing across presets
- Display value scales exponentially with normalized value
- Check pattern: Small changes in normalized value near 0 cause tiny display changes, near 1.0 cause huge changes
- Examples: "Time" (0.5 → 245ms, 0.6 → 450ms), "Frequency", "Decay"
- Time/frequency parameters are almost always exponential

**Continuous Logarithmic:**
- Full range of values 0.0-1.0 appearing across presets
- Display value scales logarithmically (opposite of exponential)
- Less common, some resonance/Q parameters
- Check pattern: Large changes at low normalized values, small changes at high values

**How to determine continuous type:**
1. Look at several presets with different normalized values for the parameter
2. Plot (roughly in your head): normalized_value vs display_value
3. If roughly straight line → Linear
4. If curve that grows faster → Exponential
5. If curve that grows slower → Logarithmic

### Task 3: Assign Parameter Roles

For each parameter:

**Master:** Controls other parameters (identified in Task 1)
- Binary parameters that enable/disable sections
- Mode toggles that switch between parameter sets

**Dependent:** Controlled by a master, only active when master has specific value
- Only meaningful when master is ON or in specific mode
- May have stale/default values when master is OFF

**Independent:** Always active, not controlled by any master
- Core parameters that always matter
- Examples: "Dry/Wet", "Feedback", "Device On"

### Task 4: Determine Metadata

For each parameter, provide:

**suggested_fit:** (for continuous params only)
- "linear", "exponential", or "logarithmic"
- Based on your analysis in Task 2
- null for binary/quantized

**unit_hint:** What unit the display_value represents
- "ms" (milliseconds), "s" (seconds)
- "Hz" (Hertz), "kHz" (kilohertz)
- "%" (percentage)
- "dB" (decibels)
- "st" (semitones)
- null if no clear unit (just numbers)

**value_labels:** (for quantized params only)
- Map of normalized values to their display labels
- Example: {"0": "Mode A", "1": "Mode B", "2": "Mode C"}
- Example: {"0": "1 sixteenth", "1": "2 sixteenths", ...}
- Check if display adds offset (value=3.0 shows as "4")
- null for non-quantized

**controls:** (for master params only)
- List of dependent parameter names this master controls
- Example: "Link" controls ["R Sync", "R Time", "R 16th", "R Offset"]

**master / active_when:** (for dependent params only)
- master: Name of the controlling parameter
- active_when: Required master value (0.0 or 1.0) for this param to be active
- Example: "L Time" has master="L Sync", active_when=0.0

### Task 5: Provide Confidence Scores

For each parameter classification, provide:
- confidence: 0.0 to 1.0
- 1.0 = Absolutely certain (e.g., only 0.0 and 1.0 appear → binary)
- 0.9-0.99 = Very confident (clear pattern)
- 0.8-0.89 = Confident (pattern mostly consistent)
- 0.5-0.79 = Uncertain (mixed signals, needs review)
- <0.5 = Very uncertain (ambiguous)

### Task 6: Document Observations

Provide high-level observations about patterns you detected:
- Stereo link behavior (if applicable)
- Mode toggle patterns (if applicable)
- Section enable/disable patterns
- Any quirks (e.g., display adds 1 to value, parameters use 0-indexing)
- Consistent default values when params are inactive

## Output Format

Respond with ONLY valid JSON in this exact structure:

```json
{
  "device_info": {
    "signature": "<copy from input>",
    "device_name": "<copy from input>",
    "analyzed_preset_count": 32,
    "analysis_date": "<today's date YYYY-MM-DD>",
    "confidence_overall": <your overall confidence 0.0-1.0>
  },

  "grouping_rules": {
    "masters": [
      "Master1",
      "Master2"
    ],
    "dependents": {
      "Dependent1": "Master1",
      "Dependent2": "Master1",
      "Dependent3": "Master2"
    },
    "dependent_master_values": {
      "Dependent1": 1.0,
      "Dependent2": 1.0,
      "Dependent3": 0.0
    }
  },

  "parameter_metadata": {
    "ParameterName1": {
      "index": 0,
      "param_type": "binary",
      "param_role": "independent",
      "suggested_fit": null,
      "unit_hint": null,
      "value_labels": null,
      "confidence": 1.0,
      "notes": "Brief explanation"
    },
    "ParameterName2": {
      "index": 2,
      "param_type": "binary",
      "param_role": "master",
      "suggested_fit": null,
      "unit_hint": null,
      "value_labels": null,
      "controls": ["Dependent1", "Dependent2"],
      "confidence": 0.98,
      "notes": "Brief explanation"
    },
    "Dependent1": {
      "index": 4,
      "param_type": "continuous_exponential",
      "param_role": "dependent",
      "master": "ParameterName2",
      "active_when": 1.0,
      "suggested_fit": "exponential",
      "unit_hint": "ms",
      "value_labels": null,
      "confidence": 0.95,
      "notes": "Brief explanation"
    },
    "QuantizedParam": {
      "index": 8,
      "param_type": "quantized",
      "param_role": "dependent",
      "master": "SomeSwitch",
      "active_when": 1.0,
      "suggested_fit": null,
      "unit_hint": "sixteenths",
      "value_labels": {
        "0": "1 sixteenth",
        "1": "2 sixteenths",
        "2": "3 sixteenths"
      },
      "confidence": 1.0,
      "notes": "Display adds 1 to value"
    }
  },

  "observations": {
    "pattern1": "Description of pattern observed",
    "pattern2": "Description of another pattern",
    "quirks": "Any unusual behaviors or offsets"
  }
}
```

## Important Notes

1. **Be thorough:** Analyze ALL parameters, not just a subset
2. **Use actual parameter names:** Copy exact names from the input data
3. **Validate against all presets:** Don't base conclusions on just a few examples - use the full set
4. **Note ambiguities:** If uncertain, say so in confidence scores and notes
5. **Check for stale values:** Look for params that don't vary when masters are OFF
6. **Verify display_value patterns:** Essential for determining linear vs exponential
7. **Document quirks:** Note any display offsets, 0-indexing, or unusual behaviors
8. **Preset count varies:** Different devices have different numbers of stock presets (typically 20-40)

## Ready?

I'll now provide the THREE documents:
1. Device parameter structure
2. Stock preset dumps (all available presets)
3. Device manual excerpts (if available)

Please analyze thoroughly and respond with the JSON output.

---

[PASTE DOCUMENT 1: DEVICE PARAMETER STRUCTURE HERE]

---

[PASTE DOCUMENT 2: STOCK PRESET DUMPS HERE]

---

[PASTE DOCUMENT 3: DEVICE MANUAL EXCERPTS HERE (if available)]
```

**Usage Instructions:**
1. Copy entire prompt above (from "# Ableton Device Parameter Analysis Task" to the end)
2. Paste into ChatGPT or Claude
3. Paste your three documents in the indicated sections
4. LLM will respond with the JSON output

**Note:** If device manual is not available, you can skip Document 3 or write "Manual not available"

STEP 4: LLM Generates Analysis JSON
------------------------------------
Expected output format:

```json
{
  "device_info": {
    "signature": "<copy from input>",
    "device_name": "<copy from input>",
    "analyzed_preset_count": <actual number of presets analyzed>,
    "analysis_date": "<today's date YYYY-MM-DD>",
    "confidence_overall": <your overall confidence 0.0-1.0>
  },

  "grouping_rules": {
    "masters": ["Link", "L Sync", "R Sync", "Filter On"],
    "dependents": {
      "L Time": "L Sync",
      "L 16th": "L Sync",
      "R Sync": "Link",
      "R Time": "Link",
      "R 16th": "Link",
      "R Offset": "Link",
      "Filter Freq": "Filter On",
      "Filter Width": "Filter On"
    },
    "dependent_master_values": {
      "L Time": 0.0,
      "L 16th": 1.0,
      "R Sync": 0.0,
      "R Time": 0.0,
      "R 16th": 0.0,
      "R Offset": 0.0,
      "Filter Freq": 1.0,
      "Filter Width": 1.0
    }
  },

  "parameter_metadata": {
    "Device On": {
      "index": 0,
      "param_type": "binary",
      "param_role": "independent",
      "suggested_fit": null,
      "unit_hint": null,
      "confidence": 1.0,
      "notes": "Standard on/off toggle"
    },
    "Link": {
      "index": 2,
      "param_type": "binary",
      "param_role": "master",
      "suggested_fit": null,
      "unit_hint": null,
      "controls": ["R Sync", "R Time", "R 16th", "R Offset"],
      "confidence": 0.98,
      "notes": "When ON, right channel follows left (R params stale)"
    },
    "L Sync": {
      "index": 4,
      "param_type": "binary",
      "param_role": "master",
      "suggested_fit": null,
      "unit_hint": null,
      "controls": ["L Time", "L 16th"],
      "confidence": 1.0,
      "notes": "Toggles between TIME mode (0.0) and SYNC mode (1.0)"
    },
    "L Time": {
      "index": 6,
      "param_type": "continuous_exponential",
      "param_role": "dependent",
      "master": "L Sync",
      "active_when": 0.0,
      "suggested_fit": "exponential",
      "unit_hint": "ms",
      "confidence": 0.95,
      "notes": "Active when L Sync OFF, displays delay time in milliseconds"
    },
    "L 16th": {
      "index": 8,
      "param_type": "quantized",
      "param_role": "dependent",
      "master": "L Sync",
      "active_when": 1.0,
      "suggested_fit": null,
      "unit_hint": "sixteenths",
      "value_labels": {
        "0": "1 sixteenth",
        "1": "2 sixteenths",
        "2": "3 sixteenths",
        "3": "4 sixteenths",
        "4": "5 sixteenths",
        "5": "6 sixteenths",
        "6": "7 sixteenths",
        "7": "8 sixteenths"
      },
      "confidence": 1.0,
      "notes": "Active when L Sync ON, quantized to 8 values"
    },
    "Feedback": {
      "index": 12,
      "param_type": "continuous_linear",
      "param_role": "independent",
      "suggested_fit": "linear",
      "unit_hint": "%",
      "confidence": 0.99,
      "notes": "Linear mapping, displays as percentage"
    }
    // ... remaining parameters
  },

  "observations": {
    "stereo_link_pattern": "When Link=1.0, all R channel params (R Sync, R Time, R 16th, R Offset) retain stale values from when Link was OFF. Observed consistently across all analyzed presets.",
    "sync_mode_pattern": "L Sync and R Sync toggle between TIME mode (value=0.0, use L/R Time) and SYNC mode (value=1.0, use L/R 16th). Never both params active simultaneously.",
    "filter_section": "Filter On enables Filter Freq and Filter Width. When OFF, these params present but values are default/stale.",
    "quantized_offset": "L 16th displays as '4 sixteenths' but value=3.0 (0-indexed). Display adds 1 to value."
  }
}
```

STEP 5: Manual Review and Validation
-------------------------------------
1. Review LLM output for accuracy:
   - Check grouping rules make sense
   - Verify parameter classifications
   - Test against a few presets manually

2. Adjust confidence thresholds:
   - Low confidence (<0.8) items need manual verification
   - Check ambiguous cases in Ableton Live

3. Test grouping filter:
   - Apply filter to one preset
   - Verify correct params excluded
   - Compare against Live UI

STEP 6: Update Device Mapping in Firestore
-------------------------------------------
1. Load device mapping document:
   ```python
   device_doc = db.collection('device_mappings').document(signature).get()
   ```

2. Update param_structure with metadata:
   ```python
   for param in param_structure:
       param_name = param['name']
       metadata = llm_output['parameter_metadata'][param_name]
       param.update({
           'param_type': metadata['param_type'],
           'param_role': metadata['param_role'],
           'suggested_fit': metadata.get('suggested_fit'),
           'unit_hint': metadata.get('unit_hint'),
           'value_labels': metadata.get('value_labels'),
           'master': metadata.get('master'),
           'active_when': metadata.get('active_when'),
           'controls': metadata.get('controls')
       })
   ```

3. Embed grouping_rules:
   ```python
   device_doc['grouping_rules'] = llm_output['grouping_rules']
   ```

4. Add LLM analysis metadata:
   ```python
   device_doc['llm_analysis'] = {
       'analyzed_at': datetime.now().isoformat(),
       'preset_count': 32,
       'confidence': llm_output['device_info']['confidence_overall'],
       'notes': llm_output['observations']
   }
   ```

5. Save to Firestore:
   ```python
   db.collection('device_mappings').document(signature).set(device_doc)
   ```

STEP 7: Update Grouping Config File
------------------------------------
1. Extract grouping rules from LLM output
2. Add to configs/param_learn.json:
   ```json
   {
     "grouping": {
       "delay": { ... },
       "reverb": { ... },
       "new_device": {
         "masters": [...],
         "dependents": {...},
         "dependent_master_values": {...}
       }
     }
   }
   ```

3. Commit and deploy config to GCS
4. Cloud Run worker will use updated rules

STEP 8: Bulk Preset Enrichment via ChatGPT
--------------------------------------------
**NEW APPROACH:** Use ChatGPT to enrich all presets in one batch instead of Cloud Run

1. Device mapping is now fully enriched with parameter metadata
2. Run bulk enrichment export script:
   ```python
   python scripts/export_for_enrichment.py --signature <signature>
   ```

   This script:
   - Queries all presets with status "captured" for this device
   - Loads device mapping with grouping rules
   - Filters each preset using grouping rules (remove stale params)
   - Generates enrichment request document

   Output: /tmp/enrichment_request_{device_name}.md

3. Feed enrichment request to ChatGPT:
   - Open ChatGPT
   - Paste the enrichment prompt (see STEP 8.1 below)
   - Paste the enrichment request document
   - ChatGPT generates enriched metadata for ALL presets

4. Save ChatGPT output:
   - Copy JSON response
   - Save to /tmp/enrichment_output_{device_name}.json

5. Apply enrichments back to Firestore:
   ```python
   python scripts/apply_enrichments.py \
     --input /tmp/enrichment_output_{device_name}.json
   ```

   This script:
   - Loads enrichment output JSON
   - Updates each preset in Firestore
   - Sets metadata_status = "enriched"
   - Sets enriched_at timestamp

6. Verify results:
   - Check Firestore - all presets should have status="enriched"
   - Spot-check 3-5 presets for accuracy
   - Verify no stale parameters mentioned

**Advantages:**
- ✅ No Cloud Run / Vertex AI costs
- ✅ All presets enriched in one ChatGPT conversation (better context)
- ✅ Can review and edit before applying to Firestore
- ✅ Faster (one batch vs individual jobs)

STEP 8.1: ChatGPT Enrichment Prompt
------------------------------------
Use this prompt for batch enrichment:

```
# Batch Preset Enrichment Task

You are an audio engineering expert specializing in {DEVICE_NAME} effects. I need you to generate professional, accurate audio engineering metadata for multiple presets of this device.

## Context

I have {N} presets that need enrichment. For each preset, I've already:
1. Filtered out stale/inactive parameters using grouping rules
2. Provided only the ACTIVE parameters with their display values
3. Included preset name and any category information

## Your Task

For each preset, analyze the active parameter values and generate comprehensive audio engineering metadata following the schema below.

Focus on:
- **Sound Character**: How this preset sounds (bright/dark, tight/spacious, subtle/aggressive)
- **Timing/Rhythm**: Delay times, sync settings, decay characteristics
- **Frequency Response**: Filter settings, EQ characteristics, brightness
- **Modulation**: Any modulation effects (chorus, rate, depth)
- **Use Cases**: When/where to use this preset (genres, instruments, mix positions)
- **Technical Details**: Specific parameter settings that define the sound

## Output Format

Respond with ONLY valid JSON in this structure:

```json
{
  "device_name": "{DEVICE_NAME}",
  "enrichment_date": "{TODAY_DATE}",
  "presets": {
    "preset_id_1": {
      "audio_engineering": {
        // Device-specific metadata schema here
        // See examples below for each device type
      }
    },
    "preset_id_2": {
      "audio_engineering": {
        // ...
      }
    }
    // ... all presets
  }
}
```

## Device-Specific Schemas

### For Delay:
```json
{
  "audio_engineering": {
    "sound_character": "Brief description of overall sound",
    "delay_time": "Timing details (ms, sync, tempo-locked)",
    "feedback_character": "Regeneration amount and decay",
    "filter_character": "Frequency shaping details",
    "modulation": "Any modulation effects active",
    "stereo_behavior": "Mono/stereo/ping-pong characteristics",
    "use_cases": ["genre1", "genre2", "technique"],
    "musical_context": "When to use this preset"
  }
}
```

### For Reverb:
```json
{
  "audio_engineering": {
    "sound_character": "Brief description of reverb character",
    "space_type": "Room/hall/plate/spring characteristics",
    "decay_character": "Decay time and tail behavior",
    "predelay": "Pre-delay amount and effect",
    "diffusion": "Diffusion characteristics",
    "tone": "Frequency response (bright/dark/neutral)",
    "modulation": "Chorus/spin effects if active",
    "use_cases": ["application1", "application2"],
    "musical_context": "Best use scenarios"
  }
}
```

### For Compressor:
```json
{
  "audio_engineering": {
    "sound_character": "Compression character (transparent/colored/aggressive)",
    "compression_type": "Style (peak/RMS, fast/slow)",
    "ratio_character": "Compression ratio and behavior",
    "attack_release": "Timing characteristics",
    "sidechain_character": "Sidechain settings if active",
    "tonal_impact": "How it colors the sound",
    "use_cases": ["instrument1", "instrument2", "application"],
    "musical_context": "When and how to use"
  }
}
```

## Important Guidelines

1. **Be specific**: Use actual parameter values in descriptions
2. **Be professional**: Use proper audio engineering terminology
3. **Be concise**: Each field 1-3 sentences maximum
4. **Be accurate**: Base descriptions on actual parameter values
5. **No stale params**: Only describe parameters that are provided (already filtered)
6. **Consistency**: Use similar language/tone across all presets
7. **Context-aware**: Consider how parameters interact

## Ready?

I'll now provide the enrichment request document with all preset data.

[PASTE ENRICHMENT REQUEST DOCUMENT HERE]
```

**Usage:**
1. Copy prompt above
2. Paste into ChatGPT
3. Paste enrichment request document
4. ChatGPT returns complete JSON with all preset enrichments

STEP 9: Test End-to-End
------------------------
1. Capture a NEW preset of this device type (not one of the stock presets)
2. Manually trigger enrichment for this one preset
3. Verify:
   - Grouping filter excludes correct params
   - LLM receives only active params
   - Enrichment metadata is accurate
4. Test preset switching with smart ordering
5. Validate parameter application works correctly
```

**Tools Needed:**
- `scripts/export_device_presets.py` - Query Firestore, generate 3 analysis docs
- `scripts/update_device_mapping.py` - Apply LLM output to Firestore
- `scripts/export_for_enrichment.py` - **NEW: Generate enrichment request for ChatGPT**
- `scripts/apply_enrichments.py` - **NEW: Apply ChatGPT enrichments to Firestore**
- `scripts/validate_grouping.py` - Test grouping filter against presets
- External LLM access (ChatGPT Plus or Claude Pro) - **Used for both analysis AND enrichment**

**Output Files:**
- `/tmp/device_structure_{device_name}.md` - Device parameter structure (LLM input doc 1)
- `/tmp/device_presets_{device_name}.md` - Stock preset dumps (LLM input doc 2)
- `/tmp/device_manual_{device_name}.md` - Manual excerpts (LLM input doc 3, optional)
- `/tmp/device_metadata_{device_name}.json` - LLM device analysis output
- `/tmp/enrichment_request_{device_name}.md` - **NEW: Preset enrichment request for ChatGPT**
- `/tmp/enrichment_output_{device_name}.json` - **NEW: ChatGPT enrichment output**
- `configs/param_learn.json` - Updated grouping config

**Frequency:** One-time per device type (Delay, Reverb, Compressor, EQ, etc.)

**Preset Count Notes:**
- Varies by device (typically 20-40 presets)
- Delay: ~32 presets
- Reverb: ~32 presets
- Compressor: ~25 presets
- EQ Eight: ~15 presets
- Auto Filter: ~30 presets

**Future Automation:** This manual process can be automated later with:
- Automatic preset export script
- Direct LLM API integration (Vertex AI, OpenAI API)
- Automated validation against test cases
- CI/CD pipeline for device mapping updates

### 7.1.2 Automated Device Mapping Enrichment (Future)

**Trigger:** New device discovered, manual + 32 stock presets captured

**Process:**

```
1. Capture all 32 stock presets
   - Load each stock preset in Ableton
   - Capture full parameter dump (with display_values)
   - Store in temporary analysis collection

2. Gather device manual/documentation
   - Ableton device reference manual (PDF/HTML)
   - Extract parameter descriptions
   - Note master/dependent relationships mentioned

3. Prepare LLM analysis prompt
   Input:
   - Device name and type
   - Manual excerpts (parameter descriptions)
   - All 32 preset parameter dumps
   - Instructions for pattern detection

4. LLM analyzes and generates:
   a. Grouping rules:
      - Master parameters (controls others)
      - Dependent parameters (controlled by masters)
      - Required master values for activation

   b. Parameter classification:
      - Binary (on/off toggles)
      - Quantized (discrete steps with labels)
      - Continuous (linear/exp/log)

   c. Metadata for each parameter:
      - param_type
      - param_role (master/dependent/independent)
      - suggested_fit (for continuous params)
      - unit_hint (ms, Hz, %, dB, etc.)
      - value_labels (for quantized params)
      - confidence scores

5. Human validation
   - Review LLM output for accuracy
   - Test grouping rules against presets
   - Verify parameter classifications
   - Adjust confidence thresholds

6. Update device mapping in Firestore
   - Add parameter metadata to param_structure
   - Embed grouping_rules in device mapping
   - Add llm_analysis metadata
   - Mark device as "fully analyzed"

7. Enable features
   - Grouping-aware enrichment
   - Smart parameter application
   - Parameter type-aware manipulation
```

**Benefits:**
- One-time analysis per device type
- Automated discovery of complex relationships
- High-quality metadata for all parameters
- Enables all advanced features

**Output Example:** See section 5.1 for enriched device mapping structure

### 7.2 Preset Capture (During Analysis Phase)

**Trigger:** Developer loads stock presets during device analysis (Phase 0)

**Process:**
```
1. Read device params (with values)
   params = GET /return/device/params?index=1&device=0

2. Compute signature
   signature = compute_signature(params)

3. Check/create basic device mapping (structure only)
   - Store signature → device_name
   - Store param structure (no metadata yet)

4. Extract values
   parameter_values = {p.name: p.value for p in params}
   parameter_display_values = {p.name: p.display_value for p in params}

5. Generate preset_id
   preset_id = f"{device_type}_{preset_name.lower().replace(' ', '_')}"

6. Store preset in Firestore
   presets/{preset_id} = {
     parameter_values,
     parameter_display_values,
     structure_signature,
     metadata_status: "captured",  // NOT "pending_enrichment" yet!
     captured_at: timestamp,
     preset_type: "stock"
   }

7. DO NOT enqueue enrichment yet
   - Wait until ALL presets captured
   - Wait until device analysis complete
   - Wait until device mapping enriched with parameter metadata
```

**Key Differences from Old Workflow:**
- ❌ NO immediate enrichment trigger
- ✅ Status = "captured" (not "pending_enrichment")
- ✅ Batch enrichment happens AFTER device analysis complete

### 7.2.1 Bulk Enrichment Trigger (After Device Analysis)

**Trigger:** Device mapping updated with LLM analysis results (Phase 0 Step 6 complete)

**Process:**
```
1. Device mapping now has:
   - Full parameter metadata (param_type, param_role, suggested_fit)
   - Grouping rules embedded
   - LLM analysis metadata

2. Query all presets for this device that need enrichment:
   presets_to_enrich = db.collection('presets')
     .where('structure_signature', '==', signature)
     .where('metadata_status', 'in', ['captured', 'pending_enrichment'])
     .get()

3. For each preset, enqueue enrichment:
   for preset in presets_to_enrich:
     publish("preset_enrich_requested", {
       preset_id: preset.id,
       device_signature: signature,
       force_reenrich: true  // Use updated device mapping
     })

4. Update preset status:
   preset.metadata_status = "pending_enrichment"
   preset.enrichment_queued_at = timestamp

5. Monitor enrichment progress:
   - Track completion via Cloud Run logs
   - Update dashboard with progress
```

**Timing:** After STEP 6 of Phase 0 workflow (device mapping updated)

**Result:** All presets for a device enriched with accurate, grouping-aware metadata

### 7.3 Preset Enrichment

**Trigger:** Pub/Sub message `preset_enrich_requested`

**Process:**
```
1. Load preset from Firestore
   preset = get_preset(preset_id)

2. Load grouping config for device type
   grouping = load_grouping_config(device_type)

3. Filter inactive parameters
   active_params = filter_inactive_parameters(
     parameter_values,
     grouping
   )

4. Build context for LLM using DISPLAY VALUES
   context = {
     param_name: parameter_display_values[param_name]
     for param_name in active_params.keys()
   }

5. Load knowledge base (device-specific + general audio engineering)
   kb = load_knowledge_base(device_type)

6. Generate metadata via LLM
   metadata = llm.generate(
     device_type,
     device_name,
     context,  // Uses display_values!
     kb
   )

7. Update Firestore
   preset.audio_engineering = metadata
   preset.metadata_version = 2
   preset.metadata_status = "enriched"
   preset.enriched_at = now()
```

**Key:** Use `parameter_display_values` for enrichment, not normalized values

### 7.4 Parameter Filtering (Grouping-Aware)

**Function:**
```python
def filter_inactive_parameters(
    parameter_values: Dict[str, float],
    grouping_config: Dict[str, Any]
) -> Dict[str, float]:
    """
    Filter out inactive parameters based on master switch states.

    Universal logic applicable to all device types:
    - If master=required_value → include dependent
    - Otherwise → exclude dependent (stale/inactive)
    """
    dependents = grouping_config.get("dependents", {})
    dependent_master_values = grouping_config.get("dependent_master_values", {})

    filtered = {}

    for param_name, param_value in parameter_values.items():
        # Check if this param is a dependent
        if param_name in dependents:
            master_name = dependents[param_name]
            master_value = parameter_values.get(master_name)

            if master_value is None:
                # Master not found, include by default
                filtered[param_name] = param_value
                continue

            # Check if dependent should be active
            required_value = dependent_master_values.get(param_name)
            if required_value is not None:
                # Exact match required
                if abs(master_value - required_value) < 0.01:
                    filtered[param_name] = param_value
                # else: skip (inactive)
            else:
                # No specific value, use threshold
                if master_value > 0.5:
                    filtered[param_name] = param_value
        else:
            # Not a dependent, always include
            filtered[param_name] = param_value

    return filtered
```

**Example 1: Delay** with Link=1.0, L Sync=0.0

```
Input:  {Link: 1.0, L Sync: 0.0, R Sync: 1.0, L Time: 0.547, L 16th: 2.0, R Time: 0.337, R 16th: 5.0}
Output: {Link: 1.0, L Sync: 0.0, L Time: 0.547}
        // Excluded: R Sync, R Time, R 16th, R Offset (Link=1.0)
        // Excluded: L 16th (L Sync=0.0, needs 1.0)
```

**Example 2: Reverb** with Chorus On=0.0, ER Spin On=1.0

```
Input:  {Chorus On: 0.0, Chorus Rate: 0.3, ER Spin On: 1.0, ER Spin Rate: 0.6}
Output: {Chorus On: 0.0, ER Spin On: 1.0, ER Spin Rate: 0.6}
        // Excluded: Chorus Rate (Chorus On=0.0, needs 1.0)
```

**Example 3: EQ Eight** with Band 2 On=0.0

```
Input:  {Band 2 On: 0.0, Band 2 Freq: 0.4, Band 2 Gain: 0.5, Band 2 Q: 0.6}
Output: {Band 2 On: 0.0}
        // Excluded: Band 2 Freq, Gain, Q (Band 2 On=0.0, needs 1.0)
```

### 7.5 Preset Switching (Loading Different Preset)

**Trigger:** User asks "make this sound like [preset_name]" or dramatic change request

**Process:**
```
1. Identify target preset
   - LLM analyzes request
   - Searches stock presets by metadata
   - Finds best match

2. Verify signature compatibility
   current_sig = get_current_device_signature()
   target_sig = target_preset.structure_signature
   if current_sig != target_sig:
     ERROR: "Incompatible device structure"

3. Load grouping config
   grouping = load_grouping_config(device_type)

4. Apply parameters in SMART ORDER (see section 9)
   a. Set all master switches FIRST
      - Link, Sync toggles, Filter On, etc.
   b. Wait briefly (10-50ms)
   c. Set dependent parameters
      - Time/16th values, Filter Freq/Width, etc.
   d. If needed: Toggle masters OFF→ON to force refresh

5. Verify application
   - Read back parameters
   - Confirm values match target
```

**Key:** Use normalized `parameter_values` directly, apply in correct order

### 7.6 Parameter Tweaking (Modify Current Preset)

**Trigger:** User asks for minor adjustments to current preset

**Process:**

```
1. LLM analyzes request
   - Determine which parameters to modify
   - Determine magnitude of change
   - Identify device type and current state

2. Identify high-impact parameters (device-specific)
   Delay: Feedback, Dry/Wet, Filter Freq, Delay Time
   Reverb: Decay Time, Dry/Wet, Pre-Delay, Diffusion
   Compressor: Threshold, Ratio, Attack, Release
   EQ: Band Gain, Band Freq, Band Q
   Filter: Cutoff Freq, Resonance, Filter Type

3. Determine target values
   Option A: Relative change
     "more [param]" → current + 10-20%
     "less [param]" → current - 10-20%

   Option B: Borrow from stock presets
     "darker" → analyze stock presets for "dark" characteristics
     Find common param ranges for desired quality
     Suggest specific values

   Option C: Audio engineering knowledge
     "punchier" (Compressor) → faster attack, moderate release
     "warmer" (EQ) → boost low-mids, cut highs
     "spacious" (Reverb) → longer decay, higher diffusion

4. Convert display value to normalized (if needed)
   Use 3-tier fallback (see section 7.7)

5. Apply changes
   Use smart ordering (masters first if changing modes)
```

**Example Requests by Device Type:**

| Device | User Request | Parameters Modified | Strategy |
|--------|-------------|---------------------|----------|
| Delay | "darker tone" | Filter Freq ↓ | Relative change |
| Reverb | "more spacious" | Decay Time ↑, Diffusion ↑ | Preset analysis |
| Compressor | "punchier" | Attack ↓, Ratio ↑ | Audio eng knowledge |
| EQ | "boost bass" | Band 1 Gain ↑ | Direct manipulation |
| Filter | "more resonant" | Resonance ↑ | Relative change |

### 7.7 Display-to-Normalized Conversion (3-Tier Fallback)

**Needed for:** User wants to SET a parameter to specific display value

**Tier 1: Multi-Preset Curve Fitting**
```
1. Load all stock presets for this device
2. Extract (normalized, display) pairs for target param
3. Fit curve (linear, exp, log) with best R²
4. If R² > 0.95: Use curve to convert
```

**Tier 2: Parameter Type Heuristic**
```
1. Identify parameter type:
   - "Time" → exponential
   - "Freq" → exponential
   - "Mix", "Level", "Feedback" → linear
   - "On/Off" → binary

2. Use generic curve for that type
3. If confidence > 80%: Use generic curve
```

**Tier 3: Just-In-Time Probing**
```
1. Binary search or probe 3-5 values around target
   Example: Want 500ms
   - Try normalized 0.5 → read back → 450ms
   - Try normalized 0.55 → read back → 520ms
   - Try normalized 0.52 → read back → 495ms

2. Interpolate to find exact normalized value
3. Store this point in curve database
4. Use for immediate application
5. After 5-10 probed points, refit curve → improves Tier 1
```

**System Self-Improvement:** Tier 3 probing enriches the database, making Tier 1 more accurate over time!

### 7.8 User Variation Detection & On-Demand Enrichment

**Context:** User presets are project-specific variations of stock presets that need enrichment on-demand, not batch-processed offline.

#### 7.8.1 The Problem

When a user tweaks a stock preset (e.g., increases Feedback on "4th Bandpass" delay), the system should:
1. **Recognize** it as a variation of a known preset
2. **Store** relationship to stock preset
3. **Enrich** it differently than a completely novel preset
4. **Show** context: "Based on '4th Bandpass' (+2 tweaks)" instead of "Custom Delay #47"

**Without variation detection:**
- ❌ Every user tweak creates "new" preset with no context
- ❌ Enrichment treats it as completely novel (expensive, slower)
- ❌ User loses connection to original preset
- ❌ Search/organization becomes difficult

**With variation detection:**
- ✅ System knows "this is 4th Bandpass with higher feedback"
- ✅ Enrichment uses differential approach (cheaper, better quality)
- ✅ Better UX: "Based on 4th Bandpass"
- ✅ Better organization: group variations by stock parent

#### 7.8.2 Detection Strategy: Distance Calculation

**Active Parameter Distance** (Recommended approach):

```python
def calculate_preset_distance(user_preset, stock_preset, grouping_rules):
    """
    Calculate distance between two presets using only ACTIVE parameters.
    Ignores stale dependent params when masters are OFF.

    Returns normalized distance: 0.0 = identical, 1.0 = completely different
    """
    # Step 1: Filter to active params only
    user_active = filter_active_params(user_preset, grouping_rules)
    stock_active = filter_active_params(stock_preset, grouping_rules)

    # Step 2: Calculate squared differences for common params
    total_distance = 0.0
    param_count = 0

    for param_name in user_active.keys():
        if param_name in stock_active:
            diff = user_active[param_name] - stock_active[param_name]
            total_distance += diff ** 2
            param_count += 1

    # Step 3: Normalize by parameter count
    if param_count == 0:
        return 1.0  # No common params = completely different

    normalized_distance = sqrt(total_distance / param_count)
    return normalized_distance


def find_closest_stock_preset(user_preset, device_signature):
    """
    Find closest stock preset and return variation info if match is good.
    """
    # Get all stock presets for this device
    stock_presets = db.collection('presets')\
        .where('device_signature', '==', device_signature)\
        .where('preset_type', '==', 'stock')\
        .stream()

    closest = None
    min_distance = float('inf')

    for stock in stock_presets:
        distance = calculate_preset_distance(user_preset, stock, grouping_rules)
        if distance < min_distance:
            min_distance = distance
            closest = stock

    # Classification thresholds
    if min_distance < 0.15:
        confidence = "high"  # Very likely a variation
    elif min_distance < 0.30:
        confidence = "medium"  # Probably a variation
    else:
        return None  # Too different, treat as novel preset

    # Calculate which params changed
    changed_params = []
    user_active = filter_active_params(user_preset, grouping_rules)
    stock_active = filter_active_params(closest, grouping_rules)

    for param_name in user_active.keys():
        if param_name in stock_active:
            user_val = user_active[param_name]
            stock_val = stock_active[param_name]
            if abs(user_val - stock_val) > 0.01:  # Threshold for "changed"
                changed_params.append({
                    'name': param_name,
                    'stock_value': stock_val,
                    'user_value': user_val,
                    'change_percent': ((user_val - stock_val) / stock_val * 100) if stock_val != 0 else 0
                })

    return {
        'stock_preset_id': closest.id,
        'stock_preset_name': closest.get('name'),
        'distance': min_distance,
        'confidence': confidence,
        'changed_params': changed_params,
        'num_changed_params': len(changed_params),
        'similarity_percent': round((1 - min_distance) * 100, 1)
    }
```

**Distance Thresholds:**
- **< 0.15**: High confidence variation (1-3 params changed slightly)
- **0.15-0.30**: Medium confidence variation (3-5 params changed or larger changes)
- **> 0.30**: Novel preset (treat as completely new)

#### 7.8.3 Data Structure for User Variations

```json
{
  "preset_id": "user_delay_custom_001",
  "name": "My Tweaked 4th BP",
  "preset_type": "user",
  "device_signature": "a1b2c3d4e5...",

  "parameter_values": { /* normalized values */ },
  "parameter_display_values": { /* display values */ },

  "variation_of": {
    "stock_preset_id": "delay_4th_bandpass",
    "stock_preset_name": "4th Bandpass",
    "distance": 0.12,
    "confidence": "high",
    "changed_params": [
      {
        "name": "Feedback",
        "stock_value": 0.61,
        "user_value": 0.75,
        "change_percent": 23.0
      },
      {
        "name": "Dry/Wet",
        "stock_value": 0.33,
        "user_value": 0.50,
        "change_percent": 51.5
      }
    ],
    "num_changed_params": 2,
    "similarity_percent": 88.0
  },

  "metadata_status": "captured",  // or "enriched"
  "enrichment": { /* see 7.8.5 */ },
  "enrichment_method": "differential",  // or "full"

  "captured_at": "2025-10-11T15:30:00Z",
  "enriched_at": "2025-10-11T15:30:05Z"
}
```

#### 7.8.4 Capture Workflow with Variation Detection

```python
# server/services/preset_store.py

def capture_user_preset(params, display_values, device_signature):
    """
    Capture user preset with automatic variation detection.
    """
    # Step 1: Basic preset structure
    preset_doc = {
        'parameter_values': params,
        'parameter_display_values': display_values,
        'device_signature': device_signature,
        'preset_type': 'user',
        'metadata_status': 'captured',
        'captured_at': firestore.SERVER_TIMESTAMP
    }

    # Step 2: Detect if this is a variation of a stock preset
    variation_info = find_closest_stock_preset(params, device_signature)

    if variation_info:
        preset_doc['variation_of'] = variation_info
        print(f"Detected variation of '{variation_info['stock_preset_name']}' "
              f"({variation_info['similarity_percent']}% similar, "
              f"{variation_info['num_changed_params']} params changed)")

    # Step 3: Save to Firestore
    preset_ref = db.collection('presets').add(preset_doc)

    # Step 4: Optionally trigger enrichment (see 7.8.5)
    # enrich_preset_async(preset_ref.id)

    return preset_ref.id
```

#### 7.8.5 On-Demand Enrichment Strategies

**Two-Tier Enrichment Architecture:**

| Preset Type | Enrichment Method | Cost per Preset | Quality | When |
|-------------|------------------|-----------------|---------|------|
| **Stock presets** | ChatGPT batch (offline) | ~$0.05 | Excellent | One-time setup |
| **User variations** | ChatGPT differential (on-demand) | ~$0.001 | Very Good | Project-specific |
| **Novel user presets** | ChatGPT full (on-demand) | ~$0.01 | Good | Rare cases |
| **Hybrid variations** | Rules + LLM polish (on-demand) | ~$0.0003 | Good | Cost-optimized |

**Option A: Differential Enrichment (Recommended)**

Use ChatGPT API with stock preset as context for quick, cheap, high-quality enrichment:

```python
def enrich_user_variation(preset_id):
    """
    Enrich a user variation using differential approach.
    Leverages stock preset enrichment for context.
    """
    # Load user preset
    preset = db.collection('presets').document(preset_id).get()
    preset_data = preset.to_dict()

    if not preset_data.get('variation_of'):
        # Not a variation, use full enrichment
        return enrich_full_preset(preset_id)

    # Load stock preset and its enrichment
    stock_id = preset_data['variation_of']['stock_preset_id']
    stock_preset = db.collection('presets').document(stock_id).get()
    stock_data = stock_preset.to_dict()
    stock_enrichment = stock_data.get('enrichment', {})

    # Get changed parameters
    changed_params = preset_data['variation_of']['changed_params']

    # Build differential enrichment prompt
    prompt = f"""
You are enriching a user's CUSTOM VARIATION of a stock Ableton preset.

STOCK PRESET: {preset_data['variation_of']['stock_preset_name']}
STOCK DESCRIPTION: {stock_enrichment.get('sound_character', 'N/A')}

CHANGED PARAMETERS ({len(changed_params)} changes):
{format_changed_params(changed_params)}

Provide a BRIEF enrichment focusing on:
1. How these specific changes modify the sound relative to the stock preset
2. Updated sound character description (2-3 sentences max)
3. What musical contexts this variation suits better/worse than original

Keep it concise - this is a variation, not a completely new preset.

Output JSON only:
{{
  "audio_engineering": {{
    "sound_character": "Brief description of how sound differs from stock",
    "variation_notes": "Specific impact of parameter changes",
    "use_cases": ["context1", "context2"],
    "relative_to_stock": "Comparison to original preset"
  }}
}}
"""

    # Call ChatGPT API
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # Cheaper model for variations
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500  # Keep it brief
    )

    enrichment = json.loads(response.choices[0].message.content)

    # Update Firestore
    db.collection('presets').document(preset_id).update({
        'enrichment': enrichment,
        'metadata_status': 'enriched',
        'enrichment_method': 'differential',
        'enriched_at': firestore.SERVER_TIMESTAMP
    })

    return enrichment


def format_changed_params(changed_params):
    """Format changed params for LLM prompt."""
    lines = []
    for param in changed_params:
        direction = "increased" if param['change_percent'] > 0 else "decreased"
        lines.append(
            f"- {param['name']}: {param['stock_value']:.2f} → {param['user_value']:.2f} "
            f"({direction} by {abs(param['change_percent']):.1f}%)"
        )
    return "\n".join(lines)
```

**Option B: Hybrid Enrichment (Cost-Optimized)**

Use heuristics for basic enrichment, LLM only for natural language polish:

```python
def enrich_user_variation_hybrid(preset_id):
    """
    Hybrid enrichment: Rules + optional LLM polish.
    Most cost-effective approach.
    """
    preset = db.collection('presets').document(preset_id).get()
    preset_data = preset.to_dict()

    if not preset_data.get('variation_of'):
        return enrich_full_preset(preset_id)

    # Step 1: Rule-based description generation
    stock_name = preset_data['variation_of']['stock_preset_name']
    changed_params = preset_data['variation_of']['changed_params']

    # Generate mechanical description
    param_descriptions = []
    for param in changed_params:
        impact = analyze_parameter_impact(param['name'], param['change_percent'])
        param_descriptions.append(impact)

    base_description = (
        f"Based on '{stock_name}' preset with {len(changed_params)} modifications: "
        + ", ".join(param_descriptions)
    )

    # Step 2: Optional LLM polish (skip if user disabled rich enrichment)
    if user_settings.get('rich_enrichment_enabled', True):
        polished = polish_description_with_llm(base_description, changed_params)
        enrichment_method = "hybrid"
    else:
        polished = base_description
        enrichment_method = "rules_only"

    enrichment = {
        "audio_engineering": {
            "sound_character": polished,
            "variation_of": stock_name,
            "changed_parameters": [p['name'] for p in changed_params]
        }
    }

    # Update Firestore
    db.collection('presets').document(preset_id).update({
        'enrichment': enrichment,
        'metadata_status': 'enriched',
        'enrichment_method': enrichment_method,
        'enriched_at': firestore.SERVER_TIMESTAMP
    })

    return enrichment


def analyze_parameter_impact(param_name, change_percent):
    """Heuristic rules for parameter impact descriptions."""

    impact_rules = {
        'Feedback': {
            'increase': "longer decay and more regeneration",
            'decrease': "shorter decay and less regeneration"
        },
        'Dry/Wet': {
            'increase': "more prominent effect",
            'decrease': "more subtle effect"
        },
        'Filter Freq': {
            'increase': "brighter tone",
            'decrease': "darker tone"
        },
        # Add more parameter-specific rules
    }

    direction = 'increase' if change_percent > 0 else 'decrease'

    if param_name in impact_rules:
        return impact_rules[param_name][direction]
    else:
        return f"{param_name} {direction}d by {abs(change_percent):.0f}%"
```

#### 7.8.6 Enrichment Trigger Strategies

**Option A: Lazy (User-Initiated) - Recommended**
```python
# Enrich only when user views preset details
@app.get("/api/preset/{preset_id}")
def get_preset(preset_id: str):
    preset = db.collection('presets').document(preset_id).get()
    data = preset.to_dict()

    # Trigger enrichment if not done yet
    if data.get('metadata_status') == 'captured':
        enrichment = enrich_user_variation(preset_id)
        data['enrichment'] = enrichment
        data['metadata_status'] = 'enriched'

    return data
```

**Benefits:**
- ✅ Only enrich presets user actually views
- ✅ No wasted API calls on unused presets
- ✅ Fast response after first view (cached)
- ✅ User controls costs implicitly

**Option B: Background (Automatic)**
```python
# Enqueue enrichment job after capture
def capture_user_preset(params, display_values, device_signature):
    preset_id = save_preset_to_firestore(...)

    # Enqueue low-priority background job
    enqueue_enrichment_job(preset_id, priority='low')

    return preset_id


# Worker processes jobs during idle time
def process_enrichment_queue():
    while True:
        job = dequeue_enrichment_job()
        if job:
            enrich_user_variation(job['preset_id'])
        else:
            time.sleep(60)  # Wait for more jobs
```

**Benefits:**
- ✅ Enrichment done before user needs it
- ✅ Smoother UX (no wait time)
- ✅ Can rate-limit to control costs

**Option C: Hybrid (Recommended) - Best of Both**
```python
def capture_user_preset(params, display_values, device_signature):
    preset_id = save_preset_to_firestore(...)
    variation_info = preset_data.get('variation_of')

    if variation_info and variation_info['confidence'] == 'high':
        # High confidence variation = cheap enrichment
        # Do it immediately (< 1 second, < $0.001)
        enrich_user_variation(preset_id)
    else:
        # Low confidence or novel preset = expensive enrichment
        # Defer to background or user-initiated
        # (user will see "Enrichment pending..." until they view it)
        pass

    return preset_id
```

**Benefits:**
- ✅ Common case (variations) enriched immediately
- ✅ Expensive cases deferred
- ✅ Best UX + cost balance

#### 7.8.7 Cost Analysis

**Example Project:** 50 user presets saved
- 40 variations of stock presets
- 10 novel presets

**Cost Breakdown:**

| Method | Variations (40) | Novel (10) | Total |
|--------|----------------|------------|-------|
| **Differential (gpt-4o-mini)** | 40 × $0.001 = $0.04 | 10 × $0.01 = $0.10 | **$0.14** |
| **Hybrid (rules + polish)** | 40 × $0.0003 = $0.012 | 10 × $0.01 = $0.10 | **$0.112** |
| **Rules only** | 40 × $0 = $0 | 10 × $0.01 = $0.10 | **$0.10** |

**Comparison to Old Approach:**
- Old: 50 presets × Cloud Run + Vertex AI = ~$2.50
- New (differential): $0.14 = **94% cost savings**
- New (hybrid): $0.11 = **96% cost savings**

#### 7.8.8 UI/UX Enhancements

**Preset Browser:**
```
┌─────────────────────────────────────────┐
│ Delay Presets                           │
├─────────────────────────────────────────┤
│ 📦 Stock Presets (32)                   │
│   ├─ 4th Bandpass                       │
│   ├─ Dotted 8th                         │
│   └─ ...                                │
│                                         │
│ 🎨 My Variations (12)                   │
│   ├─ Based on "4th Bandpass" (+2)      │
│   ├─ Based on "Dotted 8th" (+1)        │
│   └─ ...                                │
│                                         │
│ ✨ Custom Presets (3)                   │
│   └─ My Weird Delay                    │
└─────────────────────────────────────────┘
```

**Preset Detail View:**
```
┌─────────────────────────────────────────┐
│ My Tweaked 4th BP                       │
├─────────────────────────────────────────┤
│ 🔗 Based on: 4th Bandpass (88% similar) │
│                                         │
│ Changed Parameters:                     │
│   • Feedback: 58% → 75% (+29%)         │
│   • Dry/Wet: 33% → 50% (+52%)          │
│                                         │
│ Sound Character:                        │
│ "Longer decay with more prominent      │
│  effect compared to stock 4th Bandpass.│
│  Suitable for creating deeper rhythmic │
│  textures."                             │
│                                         │
│ [Load Preset] [Compare to Stock]       │
└─────────────────────────────────────────┘
```

**Search/Filter:**
- "Show variations of 4th Bandpass"
- "Find presets similar to current"
- "Group by stock parent"

---

## 8. Grouping Rules

### 8.1 Discovery Process (Universal)

**Input:**
- Ableton device manual (PDF/HTML)
- 32 stock preset dumps (with all parameter values)

**LLM Analysis Task:**

```
Analyze the Ableton {DEVICE_NAME} manual and 32 preset examples.

For each parameter, determine:
1. Is it a master switch? (controls visibility/behavior of other params)
2. Is it a dependent? (only active when master has specific value)
3. What is the relationship?
4. What is the parameter type? (binary, quantized, continuous)
5. What is the suggested fit type? (linear, exponential, logarithmic)

Common patterns to detect:
- On/Off switches that enable/disable groups of params
- Mode toggles that switch between alternate parameter sets
- Link/stereo switches that affect channel independence
- Enable/disable controls for processing sections

For parameter type classification:
- Binary: Only two values (0.0 and 1.0), typically On/Off
- Quantized: Discrete integer steps, may have value labels
- Continuous: Full range 0.0-1.0, determine if linear/exp/log

For suggested fit heuristics:
- Time-related params (Delay, Decay, Attack, Release): exponential
- Frequency-related params (Freq, Cutoff, Pitch): exponential
- Mix/Level/Amount/Gain params: linear
- Resonance/Q/Width params: linear or logarithmic

Output format:
{
  "masters": ["Master1", "Master2", "ModeSwitch"],
  "dependents": {
    "Param1": "Master1",
    "Param2": "Master1",
    "Param3": "ModeSwitch"
  },
  "dependent_master_values": {
    "Param1": 1.0,  // Active when Master1 = 1.0 (ON)
    "Param2": 1.0,
    "Param3": 0.0   // Active when ModeSwitch = 0.0 (Mode A)
  },
  "parameter_types": {
    "Master1": "binary",
    "Param1": "continuous_linear",
    "Param2": "continuous_exponential",
    "Param3": "quantized"
  },
  "suggested_fits": {
    "Param1": "linear",
    "Param2": "exponential"
  },
  "unit_hints": {
    "Param2": "ms",
    "Param4": "Hz",
    "Param5": "%"
  },
  "value_labels": {
    "Param3": {
      "0": "Mode A",
      "1": "Mode B",
      "2": "Mode C"
    }
  },
  "confidence": {
    "Param1": 0.95,
    "Param2": 0.87
  },
  "notes": {
    "Param1": "Observed: present in 32/32 presets, always when Master1=1.0"
  }
}
```

**Validation:**
- Check patterns against all 32 presets
- Verify master/dependent relationships hold consistently
- Detect outliers and edge cases
- Calculate confidence scores based on pattern consistency

### 8.2 Example: Delay Grouping

```json
{
  "delay": {
    "masters": ["Link", "L Sync", "R Sync", "Filter On"],

    "dependents": {
      "L Time": "L Sync",      // Active when L Sync = 0.0 (TIME mode)
      "L 16th": "L Sync",      // Active when L Sync = 1.0 (SYNC mode)
      "R Sync": "Link",        // Active when Link = 0.0 (unlinked)
      "R Time": "Link",        // Active when Link = 0.0
      "R 16th": "Link",        // Active when Link = 0.0
      "R Offset": "Link",      // Active when Link = 0.0
      "Filter Freq": "Filter On",  // Active when Filter On = 1.0
      "Filter Width": "Filter On"  // Active when Filter On = 1.0
    },

    "dependent_master_values": {
      "L Time": 0.0,    // L Time active when L Sync = 0.0
      "L 16th": 1.0,    // L 16th active when L Sync = 1.0
      "R Sync": 0.0,    // R Sync active when Link = 0.0
      "R Time": 0.0,    // R Time active when Link = 0.0
      "R 16th": 0.0,    // R 16th active when Link = 0.0
      "R Offset": 0.0   // R Offset active when Link = 0.0
    },

    "skip_auto_enable": []
  }
}
```

### 8.3 Example: Reverb Grouping

```json
{
  "reverb": {
    "masters": [
      "Chorus On",
      "ER Spin On",
      "LowShelf On",
      "HiFilter On",
      "HiShelf On"
    ],

    "dependents": {
      "Chorus Rate": "Chorus On",
      "Chorus Amount": "Chorus On",
      "ER Spin Rate": "ER Spin On",
      "ER Spin Amount": "ER Spin On",
      "LowShelf Freq": "LowShelf On",
      "LowShelf Gain": "LowShelf On",
      "HiFilter Freq": "HiFilter On",
      "HiFilter Type": "HiFilter On",
      "HiShelf Gain": "HiShelf On"
    },

    "dependent_master_values": {
      // All require master = 1.0 (ON)
      "Chorus Rate": 1.0,
      "Chorus Amount": 1.0,
      "ER Spin Rate": 1.0,
      "ER Spin Amount": 1.0,
      "LowShelf Freq": 1.0,
      "LowShelf Gain": 1.0,
      "HiFilter Freq": 1.0,
      "HiFilter Type": 1.0,
      "HiShelf Gain": 1.0
    },

    "skip_auto_enable": ["Freeze On"]
  }
}
```

### 8.4 Example: Compressor Grouping

```json
{
  "compressor": {
    "masters": [
      "Sidechain On"
    ],

    "dependents": {
      "Sidechain Gain": "Sidechain On",
      "Sidechain Mix": "Sidechain On",
      "Sidechain EQ On": "Sidechain On",
      "Sidechain Filter Freq": "Sidechain On",
      "Sidechain Filter Q": "Sidechain On"
    },

    "dependent_master_values": {
      "Sidechain Gain": 1.0,
      "Sidechain Mix": 1.0,
      "Sidechain EQ On": 1.0,
      "Sidechain Filter Freq": 1.0,
      "Sidechain Filter Q": 1.0
    },

    "skip_auto_enable": []
  }
}
```

### 8.5 Example: EQ Eight Grouping

```json
{
  "eq_eight": {
    "masters": [
      "Band 1 On",
      "Band 2 On",
      "Band 3 On",
      "Band 4 On",
      "Band 5 On",
      "Band 6 On",
      "Band 7 On",
      "Band 8 On"
    ],

    "dependents": {
      "Band 1 Freq": "Band 1 On",
      "Band 1 Gain": "Band 1 On",
      "Band 1 Q": "Band 1 On",
      "Band 2 Freq": "Band 2 On",
      "Band 2 Gain": "Band 2 On",
      "Band 2 Q": "Band 2 On"
      // ... similar for bands 3-8
    },

    "dependent_master_values": {
      "Band 1 Freq": 1.0,
      "Band 1 Gain": 1.0,
      "Band 1 Q": 1.0
      // ... all bands require master = 1.0 (ON)
    },

    "skip_auto_enable": []
  }
}
```

**Note:** These examples show the diversity of grouping patterns across device types. The LLM analysis should discover these patterns automatically from manuals and presets.

---

## 9. Parameter Application Order

### 9.1 The Problem

When applying multiple parameters, **order matters**:

**Observed Issue:**
```
Bulk apply all 21 parameters in index order:
- Link=1.0 (index 2) ✓
- L Sync=1.0 (index 4) ✓ but ignored because Link already ON
- L 16th=3.0 (index 8) ✗ applied while Sync not properly set
Result: Wrong values displayed in Ableton
```

**What Worked:**
```
1. Set Link=0.0 (unlock)
2. Set L Sync=1.0, R Sync=1.0
3. Set Link=1.0 (lock in)
4. Set L 16th=3.0
Result: Correct values!
```

### 9.2 Smart Application Algorithm

```python
def apply_preset_smart(target_params: Dict[str, float], grouping: Dict) -> None:
    """
    Apply parameters in dependency-aware order.
    """
    masters = grouping.get("masters", [])
    dependents_map = grouping.get("dependents", {})

    # Step 1: Identify which params are masters vs dependents
    master_params = {name: val for name, val in target_params.items() if name in masters}
    dependent_params = {name: val for name, val in target_params.items() if name in dependents_map}
    regular_params = {name: val for name, val in target_params.items()
                     if name not in masters and name not in dependents_map}

    # Step 2: For masters that control multiple dependents, toggle OFF first
    lockable_masters = ["Link"]  # Masters that "lock" other params
    for master_name in lockable_masters:
        if master_name in master_params:
            set_param(master_name, 0.0)  # Unlock
            time.sleep(0.01)

    # Step 3: Set all master switches to target values
    for master_name, master_value in master_params.items():
        set_param(master_name, master_value)
        time.sleep(0.01)

    # Step 4: Set regular (non-dependent) parameters
    for param_name, param_value in regular_params.items():
        set_param(param_name, param_value)
        time.sleep(0.01)

    # Step 5: Set dependent parameters
    for param_name, param_value in dependent_params.items():
        set_param(param_name, param_value)
        time.sleep(0.01)

    # Step 6: Re-toggle lockable masters if needed (force refresh)
    for master_name in lockable_masters:
        if master_name in master_params:
            final_value = master_params[master_name]
            if final_value > 0.5:  # If target is ON
                set_param(master_name, 0.0)  # Toggle OFF
                time.sleep(0.01)
                set_param(master_name, final_value)  # Back to ON
                time.sleep(0.01)
```

### 9.3 Application Order Summary

**Order of Operations:**
1. **Unlock** lockable masters (Link → 0.0)
2. **Set** all master switches to target values
3. **Set** regular parameters (Device On, Ping Pong, Feedback, etc.)
4. **Set** dependent parameters (Time/16th values, Filter Freq/Width)
5. **Re-lock** lockable masters (Link → 1.0) to force refresh

**Timing:**
- Small delays (10-50ms) between parameter sets
- Especially important between master and dependent changes
- Allows Ableton to process parameter relationships

**Master Types:**
- **Simple masters**: Just set to target value (Filter On, Chorus On)
- **Lockable masters**: Temporarily set to 0.0, then to target (Link)
- **Toggle masters**: May need OFF→ON cycle to refresh (Sync modes)

---

## 10. Implementation Phases

### Phase 0: Device Analysis (Manual, One-Time Per Device)

**Goal:** Generate comprehensive device mapping with grouping rules and parameter metadata, then enrich all stock presets

**Prerequisites:**
- Ableton Live with device loaded
- Firestore access
- ChatGPT Plus or Claude Pro access
- ~~Cloud Run preset enricher deployed~~ **NOT NEEDED - using ChatGPT for enrichment!**

**Tasks:**
1. Capture all stock presets to Firestore with status="captured" (count varies: 20-40 per device)
2. Export to three analysis documents (structure, presets, manual)
3. Feed to ChatGPT with device analysis prompt
4. Review and validate ChatGPT output
5. Update device mapping in Firestore with parameter metadata
6. Update `configs/param_learn.json` with grouping rules
7. Deploy updated config to GCS
8. **Generate enrichment request document for ChatGPT**
9. **Feed to ChatGPT with enrichment prompt**
10. **Apply enrichment output to Firestore**
11. Spot-check enriched presets
12. Test end-to-end with a new preset

**Scripts Needed:**
- `scripts/export_device_presets.py` - Query Firestore, generate 3 analysis docs
- `scripts/update_device_mapping.py` - Apply LLM output to Firestore
- `scripts/export_for_enrichment.py` - **NEW: Generate enrichment request for ChatGPT**
- `scripts/apply_enrichments.py` - **NEW: Apply ChatGPT enrichments to Firestore**
- `scripts/validate_grouping.py` - Test grouping filter against presets

**Key Workflow Changes:**
- ❌ OLD: Each preset triggers Cloud Run enrichment immediately on capture
- ✅ NEW: All presets captured first, device analyzed, then ChatGPT batch enrichment
- ✅ **COST SAVINGS:** No Cloud Run / Vertex AI API calls for enrichment
- ✅ **BETTER QUALITY:** ChatGPT sees all presets in context, more consistent output

**Deliverables:**
- Device mapping with full parameter metadata
- Grouping rules in config file
- LLM analysis documentation with confidence scores
- **All stock presets enriched with accurate metadata (via ChatGPT)**

**Repeat for each device type:** Delay (~32 presets), Reverb (~32), Compressor (~25), EQ Eight (~15), Auto Filter (~30), etc.

**Timeline per device:** ~2-4 hours (mostly manual steps, 2 ChatGPT interactions)

### Phase 0.1: Code Changes Required for New Workflow

**Goal:** Implement the ChatGPT-based enrichment workflow

**Changes Needed:**

**1. Server Preset Capture (server/app.py)**
```python
# OLD behavior (remove):
# After saving preset, immediately publish enrichment event

# NEW behavior:
@app.route('/return/device/capture_preset', methods=['POST'])
def capture_preset():
    # ... capture logic ...

    preset_doc = {
        'parameter_values': parameter_values,
        'parameter_display_values': parameter_display_values,
        'structure_signature': signature,
        'metadata_status': 'captured',  # Changed from 'pending_enrichment'
        'captured_at': firestore.SERVER_TIMESTAMP,
        'preset_type': data.get('preset_type', 'user')  # 'stock' or 'user'
    }

    db.collection('presets').document(preset_id).set(preset_doc)

    # DO NOT publish enrichment event here anymore
    # Return success without triggering enrichment
    return jsonify({'ok': True, 'preset_id': preset_id, 'status': 'captured'})
```

**2. New Enrichment Export Script (scripts/export_for_enrichment.py)**
```python
#!/usr/bin/env python3
"""
Generate enrichment request document for ChatGPT batch enrichment.
Usage: python export_for_enrichment.py --signature <device_signature>
"""

import argparse
import json
from google.cloud import firestore

def export_for_enrichment(signature: str):
    db = firestore.Client()

    # Load device mapping with grouping rules
    device_doc = db.collection('device_mappings').document(signature).get()
    device_data = device_doc.to_dict()
    device_name = device_data['device_name']
    grouping_rules = device_data.get('grouping_rules', {})

    # Query all captured presets
    presets = db.collection('presets') \
        .where('structure_signature', '==', signature) \
        .where('metadata_status', '==', 'captured') \
        .get()

    print(f"Found {len(presets)} presets to enrich for {device_name}")

    # Generate enrichment request document
    output = f"# Enrichment Request: {device_name}\n\n"
    output += f"Total Presets: {len(presets)}\n\n"

    for preset in presets:
        data = preset.to_dict()
        preset_name = data.get('name', preset.id)

        # Filter parameters using grouping rules
        filtered = filter_inactive_parameters(
            data['parameter_values'],
            grouping_rules
        )

        # Get display values for filtered params
        display_vals = {
            k: data['parameter_display_values'][k]
            for k in filtered.keys()
            if k in data['parameter_display_values']
        }

        output += f"## Preset: {preset_name}\n"
        output += f"ID: {preset.id}\n\n"
        output += "```json\n"
        output += json.dumps(display_vals, indent=2)
        output += "\n```\n\n"

    # Write to file
    filename = f"/tmp/enrichment_request_{device_name.lower()}.md"
    with open(filename, 'w') as f:
        f.write(output)

    print(f"\n✓ Enrichment request written to: {filename}")
    print(f"\nNext steps:")
    print(f"1. Copy ChatGPT enrichment prompt from docs")
    print(f"2. Paste into ChatGPT")
    print(f"3. Paste {filename} content")
    print(f"4. Save ChatGPT output to /tmp/enrichment_output_{device_name.lower()}.json")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--signature', required=True, help='Device signature')
    args = parser.parse_args()

    export_for_enrichment(args.signature)
```

**3. New Enrichment Application Script (scripts/apply_enrichments.py)**
```python
#!/usr/bin/env python3
"""
Apply ChatGPT enrichment output to Firestore presets.
Usage: python apply_enrichments.py --input <enrichment_output.json>
"""

import argparse
import json
from google.cloud import firestore
from datetime import datetime

def apply_enrichments(input_file: str, dry_run: bool = False):
    db = firestore.Client()

    # Load enrichment output
    with open(input_file, 'r') as f:
        data = json.load(f)

    presets = data['presets']
    print(f"Found enrichments for {len(presets)} presets")

    # Apply to Firestore
    for preset_id, enrichment in presets.items():
        print(f"Processing: {preset_id}")

        if dry_run:
            print(f"  Would update with: {enrichment['audio_engineering']}")
            continue

        # Update preset in Firestore
        db.collection('presets').document(preset_id).update({
            'audio_engineering': enrichment['audio_engineering'],
            'metadata_status': 'enriched',
            'metadata_version': 2,
            'enriched_at': firestore.SERVER_TIMESTAMP
        })

    print(f"\n✓ Applied enrichments to {len(presets)} presets")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='ChatGPT enrichment output JSON')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    args = parser.parse_args()

    apply_enrichments(args.input, args.dry_run)
```

**4. Cloud Run Worker (Optional - for future auto-enrichment)**
```python
# Cloud Run worker can remain for user presets if needed
# But stock presets during analysis phase use ChatGPT instead
# This reduces costs significantly
```

**Testing:**
1. Capture 5 stock presets → verify status="captured"
2. Complete device analysis and update device mapping
3. Run `export_for_enrichment.py --signature <sig>` → generates request doc
4. Feed to ChatGPT → get enrichment JSON
5. Run `apply_enrichments.py --input <output.json> --dry-run` → verify
6. Run `apply_enrichments.py --input <output.json>` → apply
7. Check Firestore → verify all 5 presets now status="enriched"

---

### Phase 1: Foundation (No Breaking Changes)

**Goal:** Capture display values alongside normalized values

**Changes:**
1. Update preset capture to store `parameter_display_values`
2. Update Firestore schema to include new field
3. Backfill existing presets with display values (re-capture)
4. Update API responses to include both fields

**Testing:**
- Verify display values match Ableton UI
- Confirm normalized values unchanged
- Check Firestore storage size impact

**No disruption** to existing enrichment or preset loading

### Phase 2: Enrichment Migration

**Goal:** Use display values for enrichment

**Changes:**
1. Update Cloud Run worker to use `parameter_display_values`
2. Remove curve conversion from enrichment path
3. Update filtering to work with display values
4. Re-enrich all presets with accurate values

**Testing:**
- Compare old vs new enrichments
- Verify accuracy improvements (245ms vs 120ms)
- Check grouping filter effectiveness

**Result:** More accurate metadata

### Phase 3: Device Mapping Simplification

**Goal:** Remove curve fitting from device mapping

**Changes:**
1. Remove learning/sweep code
2. Simplify device mapping to structure-only
3. Auto-create mappings on first preset capture
4. Remove curve storage from Firestore

**Testing:**
- Verify new devices auto-discovered
- Confirm signature matching works
- Check preset compatibility validation

**Result:** No manual learning needed

### Phase 4: Smart Preset Loading

**Goal:** Implement dependency-aware parameter application

**Changes:**
1. Implement smart application algorithm (section 9.2)
2. Add grouping-aware ordering
3. Add toggle/refresh logic for lockable masters
4. Update preset switching to use new logic

**Testing:**
- Test with 32 delay presets (all combinations)
- Verify Sync modes apply correctly
- Confirm Link behavior works

**Result:** Reliable preset switching

### Phase 5: Stock Preset Database

**Goal:** Load and analyze all stock presets

**Changes:**
1. Capture all 32 Delay stock presets
2. Capture all 32 Reverb stock presets
3. Store with rich metadata
4. Create preset similarity search

**Testing:**
- Verify all presets captured accurately
- Confirm metadata quality
- Test preset recommendations

**Result:** Full reference library

### Phase 6: Grouping Discovery (LLM-Assisted)

**Goal:** Auto-generate grouping rules

**Changes:**
1. Create LLM analysis pipeline
2. Feed manual + 32 presets
3. Generate grouping rules
4. Validate against presets
5. Human review and approval

**Testing:**
- Compare LLM-generated vs manual rules
- Check accuracy on test presets
- Validate edge cases

**Result:** Automated grouping discovery

### Phase 7: Parameter Manipulation (Future)

**Goal:** Enable intelligent parameter changes

**Changes:**
1. Implement 3-tier curve fitting fallback
2. Add just-in-time probing
3. Store probed points for learning
4. Enable "set to 500ms" requests

**Testing:**
- Test with various display value targets
- Verify probing accuracy
- Confirm database enrichment

**Result:** Full parameter control

---

## 11. Examples

### Example 1: Capturing a Preset (Generic)

**Scenario:** User loads a stock preset on a return track

**API Call:**
```bash
curl "http://127.0.0.1:8722/return/device/params?index=1&device=0"
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "return_index": 1,
    "device_index": 0,
    "params": [
      {"index": 4, "name": "L Sync", "value": 1.0, "display_value": "1.0"},
      {"index": 8, "name": "L 16th", "value": 3.0, "display_value": "3.0"},
      {"index": 12, "name": "Feedback", "value": 0.6105, "display_value": "58.0"},
      // ... 18 more params
    ]
  }
}
```

**Capture Process:**
```python
# 1. Compute signature
signature = compute_signature(params)
# → "9bfcc8b6e739d9675c03f6fe0664cfada9ef7df1"

# 2. Check device mapping
if not device_mapping_exists(signature):
    create_device_mapping(signature, "Delay", param_structure)

# 3. Store preset
preset = {
    "preset_id": "delay_4th_bandpass",
    "name": "4th Bandpass",
    "structure_signature": signature,
    "parameter_values": {
        "L Sync": 1.0,
        "L 16th": 3.0,
        "Feedback": 0.6105,
        # ...
    },
    "parameter_display_values": {
        "L Sync": "1.0",
        "L 16th": "3.0",
        "Feedback": "58.0",
        # ...
    },
    "metadata_status": "pending_enrichment"
}
save_preset(preset)

# 4. Enqueue enrichment
publish_pubsub("preset_enrich_requested", {"preset_id": "delay_4th_bandpass"})
```

### Example 2: Enriching with Grouping Filter

**Scenario:** Cloud Run worker enriches "4th Bandpass" preset

**Stored Values:**
```json
{
  "parameter_values": {
    "Link": 1.0,
    "L Sync": 1.0,
    "R Sync": 1.0,
    "L Time": 0.0,
    "L 16th": 3.0,
    "R Time": 0.0,
    "R 16th": 0.0
  },
  "parameter_display_values": {
    "Link": "1.0",
    "L Sync": "1.0",
    "R Sync": "1.0",
    "L Time": "1.0",
    "L 16th": "3.0",
    "R Time": "1.0",
    "R 16th": "0.0"
  }
}
```

**Filtering Process:**
```python
# Load grouping rules
grouping = {
    "masters": ["Link", "L Sync", "R Sync"],
    "dependents": {
        "L Time": "L Sync",   # Active when L Sync = 0.0
        "L 16th": "L Sync",   # Active when L Sync = 1.0
        "R Sync": "Link",     # Active when Link = 0.0
        "R Time": "Link",
        "R 16th": "Link"
    },
    "dependent_master_values": {
        "L Time": 0.0,
        "L 16th": 1.0,
        "R Sync": 0.0,
        "R Time": 0.0,
        "R 16th": 0.0
    }
}

# Apply filter
filtered = filter_inactive_parameters(parameter_values, grouping)

# Result:
# {
#   "Link": 1.0,        ✓ Master, always included
#   "L Sync": 1.0,      ✓ Master, always included
#   "L 16th": 3.0       ✓ Active (L Sync = 1.0)
# }
# Excluded:
# - L Time (L Sync = 1.0, needs 0.0)
# - R Sync (Link = 1.0, needs 0.0)
# - R Time (Link = 1.0, needs 0.0)
# - R 16th (Link = 1.0, needs 0.0)

# Build LLM context with DISPLAY VALUES
context = {
    "Link": "1.0",
    "L Sync": "1.0",
    "L 16th": "3.0"
}

# Send to LLM
metadata = llm.generate(
    "This is a delay preset with:\n"
    "- Stereo Link: ON (both channels linked)\n"
    "- L Sync: ON (tempo-synced)\n"
    "- L 16th: 3 sixteenths\n"
    "...\n"
)
```

**Result:**
```json
{
  "audio_engineering": {
    "delay_time": "3 sixteenths (tempo-synced), stereo linked",
    "sync_mode": "Tempo-synced to project BPM",
    "stereo_behavior": "Stereo linked - both channels use same timing"
  }
}
```

**Accuracy:** ✅ No mention of stale R parameters or L Time!

### Example 3: Loading Preset with Smart Ordering

**Scenario:** User asks "make this delay sound like 4th Bandpass"

**Current Device State:**
```json
{
  "Link": 1.0,
  "L Sync": 0.0,  // Currently in TIME mode
  "L Time": 0.547 // 245ms
}
```

**Target Preset:**
```json
{
  "Link": 1.0,
  "L Sync": 1.0,  // Want SYNC mode
  "L 16th": 3.0   // Want 3 sixteenths
}
```

**Application Process:**
```python
# Step 1: Unlock Link
set_param("Link", 0.0)
sleep(0.01)

# Step 2: Set master switches
set_param("L Sync", 1.0)  # Switch to SYNC mode
set_param("R Sync", 1.0)
sleep(0.01)

# Step 3: Set dependent parameters
set_param("L 16th", 3.0)  # Now Sync mode is active
set_param("R 16th", 0.0)
sleep(0.01)

# Step 4: Re-lock Link (force refresh)
set_param("Link", 1.0)
sleep(0.01)

# Step 5: Verify
verify_params()
```

**Result:** ✅ Delay now shows "4 sixteenths" in SYNC mode

### Example 4: Two-Step Modification Strategy

**Scenario:** User asks "make this delay darker"

**Current Preset:** "4th Bandpass"
```json
{
  "Filter Freq": "1725.0",
  "Filter Width": "2.82",
  "Feedback": "58.0"
}
```

**LLM Analysis:**
```
Request: "darker"
Magnitude: Minor tweak
Approach: Adjust Filter Freq (major impact on brightness)

Search stock presets for "dark" characteristics:
- Dark presets typically have Filter Freq: 500-800 Hz
- Current: 1725 Hz (bright)
- Suggestion: Reduce to 700 Hz
```

**Application:**
```python
# Minor tweak - only change Filter Freq
set_param("Filter Freq", target_normalized_value_for_700hz)

# Use 3-tier fallback to convert 700 Hz → normalized:
# Tier 1: Check curve from stock presets
# Tier 2: Use exponential heuristic for frequency
# Tier 3: Probe if needed
```

**Result:** ✅ Darker tone without loading entire different preset

---

**Scenario 2:** User asks "turn this into a slapback delay"

**Current Preset:** "4th Bandpass" (tempo-synced, 3 sixteenths)

**LLM Analysis:**
```
Request: "slapback delay"
Magnitude: Dramatic change
Approach: Load stock preset

Search stock presets:
- Slapback characteristics: 80-140ms, low feedback, mono
- Best match: "Delay" preset (L Time: 245ms, Feedback: 21%)
- Load entire preset
```

**Application:**
```python
# Dramatic change - load entire "delay_delay" preset
apply_preset_smart("delay_delay", grouping_config)

# Applies all 21 parameters in smart order
```

**Result:** ✅ Complete preset switch to slapback character

---

### Example 5: Reverb Preset Enrichment

**Scenario:** Cloud Run worker enriches a Reverb preset with multiple features disabled

**Stored Values:**
```json
{
  "parameter_values": {
    "Chorus On": 0.0,
    "ER Spin On": 1.0,
    "HiFilter On": 0.0,
    "Decay Time": 0.45,
    "ER Spin Rate": 0.6,
    "Chorus Rate": 0.3,
    "HiFilter Freq": 0.8
  },
  "parameter_display_values": {
    "Chorus On": "0.0",
    "ER Spin On": "1.0",
    "HiFilter On": "0.0",
    "Decay Time": "2.3 s",
    "ER Spin Rate": "0.8 Hz",
    "Chorus Rate": "1.2 Hz",
    "HiFilter Freq": "8500.0"
  }
}
```

**Filtering Process:**
```python
# Apply grouping filter
grouping = load_grouping_config("reverb")
filtered = filter_inactive_parameters(parameter_values, grouping)

# Result:
# {
#   "Chorus On": 0.0,      ✓ Master, always included
#   "ER Spin On": 1.0,     ✓ Master, always included
#   "HiFilter On": 0.0,    ✓ Master, always included
#   "Decay Time": 0.45,    ✓ Independent param
#   "ER Spin Rate": 0.6    ✓ Active (ER Spin On = 1.0)
# }
# Excluded:
# - Chorus Rate (Chorus On = 0.0, needs 1.0)
# - HiFilter Freq (HiFilter On = 0.0, needs 1.0)
```

**LLM Context (Display Values Only):**
```json
{
  "Decay Time": "2.3 s",
  "ER Spin On": "1.0",
  "ER Spin Rate": "0.8 Hz"
}
```

**Result:** ✅ Accurate metadata without mentioning disabled Chorus or HiFilter features

---

### Example 6: Compressor Sidechain Discovery

**Scenario:** LLM analyzes Compressor manual + 32 presets to discover sidechain grouping

**Analysis Input:**
- Manual states: "Sidechain On enables external sidechain processing"
- Observed pattern: In 32 presets, when Sidechain On=0.0, Sidechain Gain/Mix/Freq values are always default
- When Sidechain On=1.0, these params vary significantly

**LLM Output:**
```json
{
  "masters": ["Sidechain On"],
  "dependents": {
    "Sidechain Gain": "Sidechain On",
    "Sidechain Mix": "Sidechain On",
    "Sidechain EQ On": "Sidechain On"
  },
  "dependent_master_values": {
    "Sidechain Gain": 1.0,
    "Sidechain Mix": 1.0,
    "Sidechain EQ On": 1.0
  },
  "parameter_types": {
    "Sidechain On": "binary",
    "Sidechain Gain": "continuous_linear",
    "Sidechain Mix": "continuous_linear"
  },
  "suggested_fits": {
    "Sidechain Gain": "linear",
    "Sidechain Mix": "linear"
  },
  "confidence": {
    "Sidechain Gain": 0.98,
    "Sidechain Mix": 0.98
  }
}
```

**Result:** ✅ Automatic discovery of grouping rules + parameter types

---

### Example 7: EQ Eight Multi-Band Configuration

**Scenario:** User loads EQ preset with only bands 1, 3, and 5 enabled

**Grouping Filter:**
```python
# Band structure allows independent enable/disable
grouping = {
  "masters": ["Band 1 On", "Band 2 On", ..., "Band 8 On"],
  "dependents": {
    "Band 1 Freq": "Band 1 On",
    "Band 1 Gain": "Band 1 On",
    // ... etc
  }
}

# Input preset:
preset = {
  "Band 1 On": 1.0, "Band 1 Freq": 0.2, "Band 1 Gain": 0.6,
  "Band 2 On": 0.0, "Band 2 Freq": 0.4, "Band 2 Gain": 0.5,
  "Band 3 On": 1.0, "Band 3 Freq": 0.5, "Band 3 Gain": 0.7,
  // ... bands 4-8
}

# Filtered result (only active bands):
filtered = {
  "Band 1 On": 1.0, "Band 1 Freq": 0.2, "Band 1 Gain": 0.6,
  "Band 3 On": 1.0, "Band 3 Freq": 0.5, "Band 3 Gain": 0.7,
  "Band 5 On": 1.0, "Band 5 Freq": 0.7, "Band 5 Gain": 0.8
}
# Excluded: All params for bands 2, 4, 6, 7, 8 (disabled)
```

**Result:** ✅ Enrichment only describes active EQ bands

---

## Appendices

### Appendix A: API Endpoints Reference

#### Read Device Parameters
```
GET /return/device/params?index={return_index}&device={device_index}

Response:
{
  "ok": true,
  "data": {
    "return_index": 1,
    "device_index": 0,
    "params": [
      {
        "index": 0,
        "name": "Device On",
        "value": 1.0,
        "min": 0.0,
        "max": 1.0,
        "display_value": "1.0"
      },
      // ...
    ]
  }
}
```

#### Set Parameter (Index-Based)
```
POST /op/return/device/param

Body:
{
  "return_index": 1,
  "device_index": 0,
  "param_index": 4,
  "value": 1.0
}

Response:
{"ok": true, "op": "set_return_device_param"}
```

#### Set Parameter (Name-Based)
```
POST /op/return/param_by_name

Body:
{
  "return_ref": "B",           // Return A/B/C or 0/1/2
  "device_ref": "0",           // Device index or name substring
  "param_ref": "L Sync",       // Parameter name
  "target_value": 1.0          // Normalized value
}

Response:
{"ok": true, "op": "set_return_param_by_name"}
```

#### Capture Preset
```
POST /return/device/capture_preset

Body:
{
  "return_index": 1,
  "device_index": 0,
  "preset_name": "My Preset",
  "category": "user"
}

Response:
{
  "ok": true,
  "preset_id": "delay_my_preset",
  "param_count": 21
}
```

#### Apply Preset
```
POST /return/device/apply_preset

Body:
{
  "return_index": 1,
  "device_index": 0,
  "preset_id": "delay_4th_bandpass"
}

Response:
{
  "ok": true,
  "preset_name": "4th Bandpass",
  "applied": 21,
  "total": 21
}
```

### Appendix B: Firestore Schema Reference

#### Device Mappings Collection

**Path:** `device_mappings/{signature}`

**Document Structure:**
```json
{
  "signature": "9bfcc8b6e739d9675c03f6fe0664cfada9ef7df1",
  "device_name": "Delay",
  "manufacturer": "Ableton",
  "param_count": 21,
  "created_at": "2025-10-11T00:00:00Z"
}
```

**Subcollection:** `device_mappings/{signature}/params`

**Param Document:**
```json
{
  "index": 4,
  "name": "L Sync",
  "min": 0.0,
  "max": 1.0
}
```

#### Presets Collection

**Path:** `presets/{preset_id}`

**Document Structure:**
```json
{
  "preset_id": "delay_4th_bandpass",
  "name": "4th Bandpass",
  "device_name": "Delay",
  "manufacturer": "Ableton",
  "category": "delay",
  "preset_type": "stock",
  "structure_signature": "9bfcc8b6e739d9675c03f6fe0664cfada9ef7df1",

  "parameter_values": {
    "Device On": 1.0,
    "Link": 1.0,
    // ... all 21 params (normalized)
  },

  "parameter_display_values": {
    "Device On": "1.0",
    "Link": "1.0",
    // ... all 21 params (display strings)
  },

  "audio_engineering": {
    "delay_time": "...",
    "feedback_character": "...",
    // ... device-specific metadata
  },

  "metadata_version": 2,
  "metadata_status": "enriched",
  "enriched_at": "2025-10-11T02:29:26Z",
  "created_at": "2025-10-10T12:00:00Z"
}
```

### Appendix C: Grouping Configuration File

**Location:** `configs/param_learn.json`

**Structure:**
```json
{
  "grouping": {
    "delay": {
      "masters": ["Link", "L Sync", "R Sync", "Filter On"],
      "dependents": {
        "L Time": "L Sync",
        "L 16th": "L Sync",
        "R Sync": "Link",
        "R Time": "Link",
        "R 16th": "Link",
        "R Offset": "Link",
        "Filter Freq": "Filter On",
        "Filter Width": "Filter On"
      },
      "dependent_master_values": {
        "L Time": 0.0,
        "L 16th": 1.0,
        "R Sync": 0.0,
        "R Time": 0.0,
        "R 16th": 0.0,
        "R Offset": 0.0
      },
      "skip_auto_enable": []
    },

    "reverb": {
      "masters": [
        "Chorus On",
        "ER Spin On",
        "LowShelf On",
        "HiFilter On",
        "HiShelf On"
      ],
      "dependents": {
        "Chorus Rate": "Chorus On",
        "Chorus Amount": "Chorus On",
        "ER Spin Rate": "ER Spin On",
        "ER Spin Amount": "ER Spin On",
        "LowShelf Freq": "LowShelf On",
        "LowShelf Gain": "LowShelf On",
        "HiFilter Freq": "HiFilter On",
        "HiFilter Type": "HiFilter On",
        "HiShelf Gain": "HiShelf On"
      },
      "dependent_master_values": {
        "Chorus Rate": 1.0,
        "Chorus Amount": 1.0,
        "ER Spin Rate": 1.0,
        "ER Spin Amount": 1.0,
        "LowShelf Freq": 1.0,
        "LowShelf Gain": 1.0,
        "HiFilter Freq": 1.0,
        "HiFilter Type": 1.0,
        "HiShelf Gain": 1.0
      },
      "skip_auto_enable": ["Freeze On"]
    },

    "default": {
      "masters": [],
      "dependents": {},
      "dependent_master_values": {},
      "skip_auto_enable": []
    }
  }
}
```

### Appendix D: LLM Prompts for Grouping Discovery

**Prompt Template:**
```
You are analyzing the Ableton {device_name} device to discover parameter grouping rules.

# Input Data

## Device Manual Excerpt
{manual_text}

## 32 Stock Preset Examples
{preset_examples}

# Task

Analyze the manual and presets to identify:

1. **Master Parameters** - Parameters that control visibility or behavior of other parameters
   - Look for: On/Off switches, mode toggles, enable/disable controls
   - Examples: "Link", "Sync", "Filter On", "Chorus On"

2. **Dependent Parameters** - Parameters that are only active/visible when a master has a specific value
   - Look for: Parameters that only appear in certain modes
   - Examples: "L Time" only when "L Sync" is OFF, "Filter Freq" only when "Filter On" is ON

3. **Dependency Relationships** - Which dependent requires which master at what value
   - Format: dependent_param → master_param @ required_value

# Analysis Process

For each parameter:
1. Check if it appears in all 32 presets or only in some
2. When it appears, check what other parameters are present
3. Look for patterns: "When X=1, Y and Z are always present; when X=0, they're absent"
4. Cross-reference with manual descriptions

# Output Format

Return JSON:
{
  "masters": ["param1", "param2"],
  "dependents": {
    "dependent1": "master1",
    "dependent2": "master1"
  },
  "dependent_master_values": {
    "dependent1": 0.0,  // Active when master1 = 0.0
    "dependent2": 1.0   // Active when master2 = 1.0
  },
  "confidence": {
    "dependent1": 0.95,  // How confident (0-1)
    "dependent2": 0.87
  },
  "notes": {
    "dependent1": "Observed: present in 16/32 presets, always when master1=0.0"
  }
}

# Validation

For each discovered rule:
- Count how many presets follow the pattern
- Flag exceptions/outliers
- Note confidence level
```

---

## Summary

This architecture document provides a comprehensive guide for implementing a **universal display-value-based preset system** applicable to **all Ableton device types**.

### Key Features

1. **Eliminates curve fitting** for reading/enrichment
   - Uses Ableton's `display_value` field directly
   - Perfect accuracy for all parameter types

2. **Universal grouping awareness**
   - Filters inactive parameters across all device types
   - Master/dependent relationships discovered via LLM

3. **Smart preset switching**
   - Dependency-aware parameter application order
   - Works for Delay, Reverb, Compressor, EQ, and all other devices

4. **Automatic parameter classification**
   - LLM identifies: binary, quantized, continuous (linear/exp/log)
   - Suggested fit types stored in device mappings
   - Unit hints and value labels for quantized params

5. **Auto-discovery without manual learning**
   - Device signatures computed from structure
   - LLM analyzes manual + 32 presets to discover grouping rules
   - No curve sweeping needed for initial capture

6. **Future: Intelligent parameter manipulation**
   - 3-tier fallback (multi-preset curves, heuristics, just-in-time probing)
   - System self-improves with each probing operation
   - Supports setting parameters by display value ("set delay to 500ms")

7. **Device-agnostic architecture**
   - Same workflows for all device types
   - Device-specific logic isolated to grouping rules and parameter metadata
   - Extensible to future device types

### Design Principles

- **Accurate**: Display values match Ableton UI exactly
- **Maintainable**: Clear separation of concerns, minimal device-specific code
- **Self-improving**: Just-in-time probing enriches curve database over time
- **Universal**: Works for any Ableton device with master/dependent parameter patterns

### Next Steps

1. Review this document for completeness and accuracy
2. Validate approach with stakeholders
3. Begin Phase 1 implementation (capture display values)
4. Test with multiple device types (Delay, Reverb, Compressor, EQ)
5. Prepare LLM prompts for parameter classification and grouping discovery

---

**Document Version:** 1.0
**Last Updated:** 2025-10-11
**Author:** Architecture discussion between user and Claude
**Review Status:** Pending user review
