# Fadebender Prompt Management

This directory contains version-controlled LLM prompts for Fadebender's multi-tier help system.

## Structure

```
prompts/
└── tier2/
    ├── config.json              # Version, classifier patterns, settings
    ├── system_prompt.md         # Global system prompt
    └── templates/               # Query-specific templates
        ├── preset_comparison.md
        ├── parameter_explanation.md
        ├── recommendation.md
        └── general_semantic.md
```

## Versioning

**Current Version:** 1.0.0 (2025-12-01)

### Version Format
- Follows semantic versioning: `MAJOR.MINOR.PATCH`
- `MAJOR`: Breaking changes to prompt structure or classification
- `MINOR`: New templates or significant prompt improvements
- `PATCH`: Minor wording tweaks, bug fixes

### Updating Prompts

1. **Edit the prompt file(s)**
   ```bash
   vim prompts/tier2/templates/recommendation.md
   ```

2. **Update version metadata**
   - Increment version in `config.json`
   - Update `last_updated` date
   - Add entry to `changelog` array
   - Update version comment in edited template file(s)

3. **Commit with clear message**
   ```bash
   git add prompts/
   git commit -m "feat(prompts): improve recommendation clarity for v1.0.1"
   ```

4. **Test before deploying**
   ```bash
   cd /tmp
   python3 test_tier2_prompts.py
   ```

### Rollback

```bash
# Revert to previous version
git log prompts/tier2/  # Find commit hash
git revert <commit-hash>

# Or checkout specific version
git checkout v1.0.0 -- prompts/tier2/
```

## Template Metadata

Each template includes version metadata:

```markdown
<!--
version: 1.0.0
last_updated: 2025-12-01
author: sunil
description: Brief description
changelog: What changed
-->
```

## Query Classification

Queries are classified using regex patterns in `config.json`:

- **PRESET_COMPARISON**: "compare", "vs", "difference between"
- **PARAMETER_EXPLANATION**: "explain parameter", "what does X do"
- **RECOMMENDATION**: "best for", "recommend", "suggest"
- **GENERAL_SEMANTIC**: Fallback for other semantic queries

## Production Workflow

### Development
- Edit prompts locally
- Test with `test_tier2_prompts.py`
- Commit to git

### Staging
- Deploy to staging environment
- Test with real queries
- Monitor quality metrics

### Production
- Tag release: `git tag v1.0.1`
- Deploy to production
- Monitor logs for version confirmation

## Future Enhancements

- **GCS Storage**: Load prompts from Cloud Storage for hot-reload
- **A/B Testing**: Multiple prompt versions for experimentation
- **Per-User Overrides**: Firestore-based custom prompts
- **Analytics**: Track which templates perform best

## See Also

- `/server/services/semantic_search_service.py` - Prompt loader
- `/configs/app_config.json` - Model selection
- `/tmp/test_tier2_prompts.py` - Test suite
