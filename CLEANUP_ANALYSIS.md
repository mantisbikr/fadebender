# Root-Level & Knowledge Folder Cleanup Analysis

## Current State

### Root-Level .md Files (6 files)
1. `README.md` ✅ KEEP - Main project README
2. `CHANGELOG.md` ⚠️ STALE - Last update v0.0.1 (2025-09-16), outdated
3. `PROJECT-STATUS.md` ⚠️ STALE - September 14, 2024, superseded by docs/STATUS.md
4. `ROADMAP.md` ⚠️ STALE - Early roadmap, superseded by docs/STATUS.md + docs/technical/NEXT_FEATURES.md
5. `DECISIONS.md` ⚠️ STALE - 2025-09-14 decisions, mostly obsolete
6. `OPEN_QUESTIONS.md` ⚠️ STALE - Old questions (400 errors, Ableton adapter - both resolved)

### Knowledge Folder (42 .md files)

**Root-level docs (4):**
1. `knowledge/README.md` ✅ KEEP - Index for knowledge base
2. `knowledge/CURRENT-STATUS-SUMMARY.md` ⚠️ STALE - September 14, 2024
3. `knowledge/DAW-ROADMAP.md` ⚠️ PARTIAL - Multi-DAW plans (future)
4. `knowledge/VERSIONING-ARCHITECTURE.md` ⚠️ PARTIAL - Undo/redo design (not implemented)

**Ableton Live audio effects (38 .md files):** ✅ KEEP ALL
- Comprehensive device documentation for LLM context
- Used by knowledge-backed help system
- Required for Phase 4 (parameter aliasing, LLM intent mapping)
- Examples: delay.md, reverb.md, compressor.md, eq-eight.md, etc.

**Shared knowledge (3 files):** ✅ KEEP
- `shared/audio-engineering-principles.md` - Audio fundamentals
- `shared/audio_concepts.md` - Concepts reference
- `shared/versioning-integration.md` - Version control design

## Redundancy Analysis

### Root-Level Files vs docs/STATUS.md

| Root File | docs/ Equivalent | Redundant? |
|-----------|-----------------|------------|
| PROJECT-STATUS.md | docs/STATUS.md | ✅ YES - Same purpose, docs/ version newer |
| ROADMAP.md | docs/STATUS.md + docs/technical/NEXT_FEATURES.md | ✅ YES - Superseded |
| CHANGELOG.md | Git history | ⚠️ PARTIAL - Outdated, git is source of truth |
| DECISIONS.md | Git commits + docs | ⚠️ PARTIAL - Historical, mostly obsolete |
| OPEN_QUESTIONS.md | N/A | ✅ YES - Questions resolved |

### Knowledge Folder Status Docs

| Knowledge File | Redundant? | Notes |
|----------------|-----------|-------|
| CURRENT-STATUS-SUMMARY.md | ✅ YES | Sept 14, 2024 - superseded by docs/STATUS.md |
| DAW-ROADMAP.md | ⚠️ NO | Multi-DAW future plans, not covered elsewhere |
| VERSIONING-ARCHITECTURE.md | ⚠️ NO | Undo/redo design, not yet implemented |

## Recommendations

### ROOT-LEVEL FILES

**KEEP (1):**
- `README.md` - Main project entry point

**ARCHIVE to docs/archive/ (5):**
- `CHANGELOG.md` → docs/archive/CHANGELOG.md
- `PROJECT-STATUS.md` → docs/archive/PROJECT-STATUS.md
- `ROADMAP.md` → docs/archive/ROADMAP.md
- `DECISIONS.md` → docs/archive/DECISIONS.md
- `OPEN_QUESTIONS.md` → docs/archive/OPEN_QUESTIONS.md

**Rationale:** Historical value but superseded by:
- docs/STATUS.md (current status)
- docs/technical/NEXT_FEATURES.md (roadmap)
- Git history (changes, decisions)

### KNOWLEDGE FOLDER

**KEEP knowledge/ folder structure:** ✅ YES
- Critical for LLM grounding
- Used by knowledge-backed help system
- Required for Phase 4 implementation

**MOVE to docs/archive/ (1):**
- `knowledge/CURRENT-STATUS-SUMMARY.md` → docs/archive/CURRENT-STATUS-SUMMARY.md

**MOVE to docs/architecture/ (2):**
- `knowledge/DAW-ROADMAP.md` → docs/architecture/DAW-ROADMAP.md
- `knowledge/VERSIONING-ARCHITECTURE.md` → docs/architecture/VERSIONING-ARCHITECTURE.md

**Rationale:**
- Status summary is stale (archive)
- DAW-ROADMAP and VERSIONING are architecture docs, not LLM knowledge
- Keeps knowledge/ focused on device/audio content for LLM

**KEEP in knowledge/ (38 files):**
- All `knowledge/ableton-live/audio-effects/*.md` files
- All `knowledge/shared/*.md` files
- `knowledge/README.md`

## Proposed Actions

```bash
# Archive root-level stale docs
mv CHANGELOG.md docs/archive/
mv PROJECT-STATUS.md docs/archive/
mv ROADMAP.md docs/archive/
mv DECISIONS.md docs/archive/
mv OPEN_QUESTIONS.md docs/archive/

# Move knowledge status to archive
mv knowledge/CURRENT-STATUS-SUMMARY.md docs/archive/

# Move architecture docs to docs/architecture/
mv knowledge/DAW-ROADMAP.md docs/architecture/
mv knowledge/VERSIONING-ARCHITECTURE.md docs/architecture/

# Update knowledge/README.md to remove references to moved files
```

## After Cleanup

**Root folder:**
- `README.md` - Main entry point
- `docs/` - All documentation
- `knowledge/` - Pure LLM knowledge (devices + audio engineering)
- Clean separation of concerns

**knowledge/ folder:**
- Focused on Ableton Live device docs + audio fundamentals
- Ready for LLM injection in Phase 4
- No status/roadmap clutter

**docs/ folder:**
- All status, roadmap, architecture in one place
- Clear active vs archive separation
- Easy to find current vs historical docs
