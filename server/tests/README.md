# Intents API Test Suite

Comprehensive test coverage for the Intents API (`/intent/execute` endpoint).

## Test Categories

### 1. Track Mixer Operations
- Volume control (dB, percent, normalized)
- Pan control (percent, normalized)
- Mute/Solo toggles

### 2. Return Mixer Operations
- Volume, pan, mute, solo on return tracks

### 3. Master Mixer Operations
- Master volume and pan

### 4. Send Operations
- Track sends (to returns)
- Return sends (send chains)

### 5. Device Parameter Control
- **By index**: Direct parameter access
- **By name**: Fuzzy parameter matching
- **Display-value conversion**: Human-readable values (e.g., "50 ms", "Low-pass")
- **Label mapping**: Discrete choice parameters
- **Fit inversion**: Linear, log, exp, and piecewise fits

### 6. Auto-Enable Master Toggles
- Automatic enabling of section toggles (e.g., "Chorus On" when setting "Chorus Amount")
- Heuristic-based dependency resolution

### 7. Unit Conversions
- dB ↔ normalized (0-1)
- Percent ↔ normalized
- Display strings ↔ normalized

### 8. Dry-Run Mode
- Preview operations without applying to Live
- Validation and value computation

### 9. Error Handling
- Missing required fields
- Ambiguous parameter names
- Device/parameter not found
- Live connection timeout
- Unsupported operations

### 10. Edge Cases
- Extreme values (very low dB, hard panning)
- Zero values
- Clamping behavior
- Already-enabled toggles

## Running Tests

### Run all tests:
```bash
cd /Users/sunils/ai-projects/fadebender/server
pytest tests/test_intents.py -v
```

### Run specific test category:
```bash
# Track mixer tests only
pytest tests/test_intents.py -k "track_" -v

# Device parameter tests only
pytest tests/test_intents.py -k "device_param" -v

# Display-value conversion tests
pytest tests/test_intents.py -k "display" -v

# Error handling tests
pytest tests/test_intents.py -k "error" -v
```

### Run with coverage:
```bash
pytest tests/test_intents.py \
  --cov=server.api.intents \
  --cov=server.services.intents.mixer_service \
  --cov=server.services.intents.param_service \
  --cov=server.services.intents.routing_service \
  --cov-report=html
```

### Run in verbose mode with output:
```bash
pytest tests/test_intents.py -v -s
```

## Test Fixtures

- **mock_request_op**: Mocks UDP communication with Live
- **mock_store**: Mocks Firestore device mapping lookups
- **sample_device_params**: Realistic Reverb device parameters
- **sample_device_mapping**: Device mapping with params_meta for display-value conversion

## Coverage Goals

- [x] All mixer operations (track, return, master)
- [x] All send operations
- [x] Device parameter by index and name
- [x] Display-value conversions (fit inversion, labels)
- [x] Auto-enable master toggles
- [x] Unit conversions (dB, %, normalized)
- [x] Dry-run mode
- [x] Error conditions
- [x] Edge cases
- [x] Clamping behavior

## Dependencies

```bash
pip install pytest pytest-cov fastapi httpx
```

## Notes

- Tests use mocked Live communication - no actual Ableton Live connection required
- Display-value conversion tests require Firestore mocking for device mappings
- Auto-enable tests verify heuristic-based dependency resolution
- Integration-style tests verify realistic multi-operation scenarios
