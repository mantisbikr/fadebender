# Overnight Investigation Report: Typo Corrections

## Summary

Investigated typo correction system and found issues with bad auto-learned mappings. Applied fixes and created audit tooling.

---

## Issues Found

### 1. **Bad Typo Mappings in Config**
- ❌ `"rack" → "track"` - Too dissimilar (Levenshtein distance 3, only 75% similar)
- ❌ `"mod" → "mode"` - Prevented by adding "mod" to protected words
- ⚠️ Possibly more bad mappings in Firestore (you mentioned "check" → "master")

### 2. **Root Cause: Auto-Learning Without Distance Check at Application Time**

**How the system works:**

```
User Query → Typo Correction → Regex Parser → Intent
                   ↓
              (if fails)
                   ↓
              LLM Fallback → Success?
                   ↓
              Typo Learner → Validate → Save to Firestore
```

**The problem:**
- Learning phase has validation (Levenshtein ≤2 for fuzzy, ≤4 for suspected typos)
- Application phase has NO distance check - just blind word replacement
- Some bad corrections slip through validation and get stored in Firestore

---

## Fixes Applied

### ✅ 1. Added "mod" to Protected Words
**File**: `configs/app_config.json`

Protected words are never typo-corrected. This prevents "mod" → "mode" which breaks preset parameters like "Dly < Mod".

### ✅ 2. Removed Bad Correction
**File**: `configs/app_config.json`

Removed `"rack" → "track"` because:
- Levenshtein distance: 3 (too high)
- "rack" is a valid word (effects rack, rack mount, etc.)
- Only 3/4 letters match

### ✅ 3. Created Audit Tool
**File**: `scripts/audit_typo_corrections.py`

New utility script that:
- Checks Levenshtein distance for all mappings
- Applies validation rules from typo_learner.py:
  - Distance ≤ 3 (configurable)
  - Length ratio ≥ 70% (unless substring)
  - Character overlap ≥ 30%
- Reports suspicious corrections from both:
  - `configs/app_config.json`
  - Firestore `nlp_config/typo_corrections`

**Usage:**
```bash
python scripts/audit_typo_corrections.py
```

Output example:
```
❌ SUSPICIOUS: 'check' → 'master' (distance=6)
   Reason: Distance too large: 6 > 3

⚠️ BORDERLINE: 'paning' → 'pan' (distance=3)
   Status: OK
```

---

## Validation Rules Explained

The typo learner (`nlp-service/learning/typo_learner.py`) uses these rules:

| Check | Threshold | Example Pass | Example Fail |
|-------|-----------|--------------|--------------|
| **Levenshtein Distance** | ≤2 (fuzzy)<br>≤4 (suspected) | "volme"→"volume" (2) | "check"→"master" (6) |
| **Length Ratio** | ≥70% or substring | "paning"→"pan" (50% but substring) | "filter"→"a" (17%) |
| **Character Overlap** | ≥30% shared chars | "reverbb"→"reverb" (86%) | "check"→"master" (20%) |
| **Single Letter/Digit** | Never | ❌ Any | "freq"→"a" |

---

## Action Items for Tomorrow

### 🔴 HIGH PRIORITY

1. **Run the audit tool:**
   ```bash
   python scripts/audit_typo_corrections.py
   ```
   This will show ALL suspicious corrections in both config and Firestore.

2. **Clean Firestore typo corrections:**
   - Access Firestore console
   - Navigate to `nlp_config/typo_corrections`
   - Review the `corrections` field
   - Remove any suspicious mappings found by audit tool
   - Especially look for:
     - "check" → "master" (you mentioned this one)
     - Any distance > 3
     - Any length ratio < 70%

### 🟡 MEDIUM PRIORITY

3. **Add more protected words:**
   Common audio/music terms that should never be corrected:
   - "rack", "mod", "mix", "fx", "aux", "pre", "post"
   - Device-specific terms from your most-used plugins
   - Parameter names that are short and might conflict

4. **Consider stricter validation:**
   Edit `nlp-service/learning/typo_learner.py` line 304:
   ```python
   # Current: distance <= 4 for suspected typos
   if distance <= 4 and distance < best_distance:

   # Stricter: distance <= 2 for all
   if distance <= 2 and distance < best_distance:
   ```

### 🟢 LOW PRIORITY

5. **Monitor typo learning logs:**
   Enable logging to see what's being auto-learned:
   ```bash
   export LOG_TYPO_LEARNING=true
   export DEBUG_TYPO_CORRECTION=true
   ```

6. **Optional: Disable auto-learning temporarily:**
   If you want to manually curate all typos:
   ```bash
   export DISABLE_TYPO_LEARNING=true
   ```

---

## Commits Made

1. ✅ **034d78c** - fix: strip 'as' keyword from scene creation commands
2. ✅ **420fe03** - fix: improve typo correction quality and add audit tool

---

## Tomorrow's Other Task

Remember to investigate: "set return A reverb decay to 100" works from curl but shows "404 not found" from webui.

---

## Files Modified

- `configs/app_config.json` - Added "mod" to protected words, removed "rack"→"track"
- `scripts/audit_typo_corrections.py` - New audit utility (executable)

## Next Steps

1. Run audit tool
2. Clean Firestore based on results
3. Test problematic commands ("mod" params, etc.)
4. Debug webui 404 issue

---

**Good night! 😴**
