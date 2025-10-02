# Documentation Organization Analysis

## Current State (21 files)

### 📁 Proposed Structure

```
docs/
├── README.md (new - overview of all docs)
├── setup/
│   ├── QUICKSTART.md ✓ (keep)
│   ├── ABLETON_SETUP.md ✓ (keep)
│   ├── RUNBOOK.md ✓ (keep)
│   ├── USER_ONBOARDING.md ✓ (keep)
│   └── STEP_BY_STEP_LIVE.md ✓ (keep)
├── testing/
│   ├── DELAY_PARAM_TESTING.md ✓ (keep - test plan)
│   ├── DELAY_TEST_RESULTS.md ✓ (keep - results from 2025-10-01)
│   └── RETURN_PARAM_TESTING.md ✓ (keep - test plan)
├── technical/
│   ├── PARAMETER_FITTING_METHODS.md ✓ (keep - technical reference)
│   ├── PARAM_CONTROL_PLAN.md ✓ (keep - implementation plan)
│   ├── PARAM_CONTROL_IMPROVEMENTS.md ✓ (keep - issue tracking)
│   └── INTENT_SUPPORT.md ✓ (keep - feature spec)
├── architecture/
│   ├── ARCHITECTURE_MULTIUSER.md ✓ (keep if multiuser planned)
│   └── volume_map.csv ✓ (keep - reference data)
└── archive/
    ├── CODEX_README.md ⚠️ (stale - Codex scaffold instructions)
    ├── Fadebender_Codex_FirstPrompt.md ⚠️ (stale - initial setup)
    ├── Fadebender_Codex_Handoff.md ⚠️ (stale - scaffold guide)
    ├── Fadebender_MVP.md ⚠️ (duplicate of roadmap.md)
    ├── roadmap.md ⚠️ (stale - early MVP plan, Dec 31 1979 date!)
    └── EXECUTION_PLAN.md ⚠️ (stale - early phase planning)
```

## Status by Category

### ✅ KEEP - Active Documentation (14 files)

**Setup & Operations (5):**
- `QUICKSTART.md` - User quick start guide
- `ABLETON_SETUP.md` - Ableton configuration
- `RUNBOOK.md` - Operations guide
- `USER_ONBOARDING.md` - Onboarding flow
- `STEP_BY_STEP_LIVE.md` - Live usage guide

**Testing (3):**
- `DELAY_PARAM_TESTING.md` - Delay device test plan
- `DELAY_TEST_RESULTS.md` - Test results (2025-10-01)
- `RETURN_PARAM_TESTING.md` - Return device test plan

**Technical Reference (4):**
- `PARAMETER_FITTING_METHODS.md` - Fitting algorithms
- `PARAM_CONTROL_PLAN.md` - Implementation plan
- `PARAM_CONTROL_IMPROVEMENTS.md` - Issues & enhancements
- `INTENT_SUPPORT.md` - Intent feature spec

**Architecture (2):**
- `ARCHITECTURE_MULTIUSER.md` - Multiuser design (if planned)
- `volume_map.csv` - Reference data

### ⚠️ ARCHIVE - Stale/Obsolete (6 files)

**Codex Scaffold Docs (3):**
- `CODEX_README.md` - Initial Codex build instructions (outdated)
- `Fadebender_Codex_FirstPrompt.md` - First setup prompt (done)
- `Fadebender_Codex_Handoff.md` - Scaffold guide (done)

**Early Planning (3):**
- `Fadebender_MVP.md` - Duplicate of roadmap.md
- `roadmap.md` - Early MVP plan (stale, weird date)
- `EXECUTION_PLAN.md` - Early phase plan (superseded)

## Recommendations

### Option 1: Archive (Recommended)
Move stale docs to `docs/archive/` to preserve history without cluttering main docs.

### Option 2: Delete
Delete stale docs entirely if no historical value.

### Questions for User:
1. **Multiuser architecture**: Still planned? If not, archive `ARCHITECTURE_MULTIUSER.md`
2. **Codex docs**: Keep for historical reference or delete?
3. **Early roadmap/MVP docs**: Archive or delete?

## Proposed Actions

```bash
# Create new structure
mkdir -p docs/{setup,testing,technical,architecture,archive}

# Move setup docs
mv docs/QUICKSTART.md docs/setup/
mv docs/ABLETON_SETUP.md docs/setup/
mv docs/RUNBOOK.md docs/setup/
mv docs/USER_ONBOARDING.md docs/setup/
mv docs/STEP_BY_STEP_LIVE.md docs/setup/

# Move testing docs
mv docs/DELAY_PARAM_TESTING.md docs/testing/
mv docs/DELAY_TEST_RESULTS.md docs/testing/
mv docs/RETURN_PARAM_TESTING.md docs/testing/

# Move technical docs
mv docs/PARAMETER_FITTING_METHODS.md docs/technical/
mv docs/PARAM_CONTROL_PLAN.md docs/technical/
mv docs/PARAM_CONTROL_IMPROVEMENTS.md docs/technical/
mv docs/INTENT_SUPPORT.md docs/technical/

# Move architecture docs
mv docs/ARCHITECTURE_MULTIUSER.md docs/architecture/
mv docs/volume_map.csv docs/architecture/

# Archive stale docs
mv docs/CODEX_README.md docs/archive/
mv docs/Fadebender_Codex_FirstPrompt.md docs/archive/
mv docs/Fadebender_Codex_Handoff.md docs/archive/
mv docs/Fadebender_MVP.md docs/archive/
mv docs/roadmap.md docs/archive/
mv docs/EXECUTION_PLAN.md docs/archive/
```

## Summary

- **14 active docs** organized into 4 logical folders
- **6 stale docs** archived for reference
- Clear separation: setup, testing, technical, architecture
- Easier navigation and maintenance
