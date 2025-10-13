# Future Feature: User-Specific Device Catalog

## Overview
Extension of stock device catalog to support personalized, per-user/per-project preset collections and usage analytics.

## Architecture

### User Catalog Structure
```
users/{user_id}/projects/{project_id}/device_catalog: {
  "{device_name}": {
    base_device: "{signature}",  // Links to stock catalog

    custom_presets: {
      "{preset_name}": {
        tags: ["user", "defined", "tags"],
        mapping_id: "preset_xyz",  // Points to full preset data
        notes: "User's description",
        created_at: timestamp,
        last_modified: timestamp
      }
    },

    usage_stats: {
      usage_count: number,
      last_used: timestamp,
      common_contexts: ["guitar", "vocals"],  // Inferred from track names
      favorite_presets: ["preset_id_1", "preset_id_2"]
    }
  }
}
```

### Smart Features to Implement

1. **Auto-tagging from Parameter Values**
   - High HiFilter Freq → "bright", "airy"
   - Long Decay Time → "ambient", "spacious"
   - Low Dry/Wet → "subtle", "natural"

2. **Context Learning**
   - Track preset used on ("Guitar Lead" → "guitar")
   - Co-occurring effects (Reverb + Delay → "ambient chain")
   - Temporal patterns (Friday night sessions → "experimental")

3. **Scope Levels**
   - Project-level: Presets specific to one Live set
   - User-level: Personal presets available across all projects
   - Team-level: Shared presets for collaborative projects

4. **Usage Analytics for LLM**
   - "You often use long reverb on pads"
   - "This preset works well with your guitar tone"
   - "Based on your project, try these complementary effects"

## Implementation Priority
- Phase 1: Stock catalog (current focus)
- Phase 2: User preset storage and tagging
- Phase 3: Usage analytics and tracking
- Phase 4: Smart recommendations based on history

## Related Work
- Stock catalog: `/docs/technical/stock_device_catalog.json` (to be created)
- Device mappings: `device_mappings/{signature}` in Firestore
- Audio knowledge: `reverb_audio_knowledge.json`
