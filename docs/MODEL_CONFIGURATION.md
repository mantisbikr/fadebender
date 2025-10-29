# Model Configuration Guide

## Overview

FadeBender now supports operation-specific model configuration, allowing you to choose optimal models for different tasks.

## Current Configuration

Based on performance testing (see `test_llama_vs_gemini.py`):

| Operation | Model | Reason |
|-----------|-------|--------|
| **intent_parsing** | `gemini-2.5-flash-lite` | 1.55x faster, same accuracy, lower cost |
| **audio_analysis** | `gemini-2.5-flash` | Complex reasoning for audio engineering |
| **context_analysis** | `gemini-2.5-flash` | Deep context understanding |
| **default** | `gemini-2.5-flash` | Fallback for unspecified operations |

## How to Change Models

### Option 1: Edit config file (RECOMMENDED)

Edit `configs/app_config.json` and modify the `models` section:

```json
{
  "models": {
    "intent_parsing": "gemini-2.5-flash-lite",
    "audio_analysis": "gemini-2.5-flash",
    "context_analysis": "gemini-2.5-flash",
    "default": "gemini-2.5-flash"
  }
}
```

After editing, save the config:
```python
from server.config.app_config import save_config
save_config()
```

### Option 2: Programmatic configuration

```python
from server.config.app_config import set_model_for_operation, save_config

# Change model for specific operation
set_model_for_operation("intent_parsing", "gemini-2.5-flash")

# Save changes to disk
save_config()
```

### Option 3: Environment variable override

Environment variables take precedence over config file:

```bash
# Override ALL operations to use this model
export VERTEX_MODEL=gemini-2.5-flash

# OR
export LLM_MODEL=gemini-2.5-flash-lite
```

## Priority Order

When selecting a model for an operation, the system uses this priority:

1. **Explicit preference** - If code passes a specific model name
2. **Environment variables** - `VERTEX_MODEL`, `LLM_MODEL`, or `GEMINI_MODEL`
3. **Operation-specific config** - `models.{operation}` in app_config
4. **Default config** - `models.default` in app_config
5. **Hardcoded fallback** - `gemini-2.5-flash`

## Available Models

### Gemini Models (Vertex AI)

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `gemini-2.5-flash-lite` | Fastest | Lowest | Intent parsing, simple tasks |
| `gemini-2.5-flash` | Fast | Low | General purpose, complex reasoning |
| `gemini-2.5-pro` | Slower | Higher | Very complex reasoning |

### Custom Models

You can also use:
- Llama models from Vertex AI Model Garden (e.g., `meta/llama3-8b-instruct-maas`)
- Custom fine-tuned models
- Any Vertex AI model endpoint

## Verification

Run the verification script to check current configuration:

```bash
python3 scripts/verify_model_config.py
```

Output shows:
- Configured models for each operation
- Environment variable overrides
- Effective model that will be used

## Performance Comparison

From `test_llama_vs_gemini.py`:

**Gemini 2.5 Flash vs Flash-Lite:**
- Flash: 2676ms average latency
- Flash-Lite: 1732ms average latency
- **Speedup: 1.55x faster**
- **Cost savings: ~33% lower**
- **Accuracy: Both 100%**

## Adding New Operations

To add a new operation type:

1. Add to `models` section in app_config:
```python
"models": {
    "my_new_operation": "gemini-2.5-flash",
    ...
}
```

2. Use in your code:
```python
from config.llm_config import get_default_model_name

model = get_default_model_name(None, "my_new_operation")
# Use model for your operation
```

## Examples

### Example 1: Use faster model for all operations

```json
{
  "models": {
    "intent_parsing": "gemini-2.5-flash-lite",
    "audio_analysis": "gemini-2.5-flash-lite",
    "context_analysis": "gemini-2.5-flash-lite",
    "default": "gemini-2.5-flash-lite"
  }
}
```

### Example 2: Use standard model for everything

```bash
export VERTEX_MODEL=gemini-2.5-flash
```

This overrides all operation-specific settings.

### Example 3: Mixed approach

```json
{
  "models": {
    "intent_parsing": "gemini-2.5-flash-lite",  # Fast for intents
    "audio_analysis": "gemini-2.5-pro",         # Pro for audio
    "default": "gemini-2.5-flash"               # Standard fallback
  }
}
```

## Troubleshooting

### "Model not found" error

Check:
1. Model name is correct (run `verify_model_config.py`)
2. Vertex AI API is enabled in your GCP project
3. Model is available in your region (default: us-central1)

### Wrong model being used

Check priority order:
1. Are environment variables set? They override config
2. Is the operation name correct?
3. Run `verify_model_config.py` to see effective configuration

### Performance not improving

1. Verify correct model is being used (`verify_model_config.py`)
2. Check if environment variable is overriding config
3. Run comparison test: `python3 scripts/test_llama_vs_gemini.py`
