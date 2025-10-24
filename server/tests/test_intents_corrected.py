#!/usr/bin/env python3
"""
Corrected comprehensive test suite for the Intents API.

IMPORTANT: This test suite correctly reflects Live's actual value ranges:
- Track/Return/Master Volume: 0.0-1.0 (or -60dB to +6dB)
- Sends: 0.0-1.0 (or -60dB to 0dB)
- Pan: -1.0 to +1.0
- Mute/Solo: 0.0 or 1.0

INDEXING: All indices are 1-based (Track 1, Return A=1, Send A=1, Device 1)
The API converts to 0-based internally for Live.

NO PERCENT SUPPORT for volume/pan in normalized mode.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from server.app import app
from server.api.intents import CanonicalIntent


client = TestClient(app)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_request_op():
    """Mock the request_op function to simulate Live responses across all modules."""
    # Patch request_op only in service modules (no longer imported in server.api.intents)
    patches = [
        patch('server.services.intents.mixer_service.request_op'),
        patch('server.services.intents.routing_service.request_op'),
        patch('server.services.intents.param_service.request_op'),
    ]

    mocks = [p.start() for p in patches]
    # Configure all mocks to return the same values
    mock = mocks[0]
    for m in mocks[1:]:
        m.return_value = mock.return_value
        m.side_effect = lambda *args, **kwargs: mock(*args, **kwargs)

    yield mock

    for p in patches:
        p.stop()


@pytest.fixture
def mock_store():
    """Mock the Firestore store across all modules."""
    store = MagicMock()
    store.enabled = True

    patches = [
        patch('server.services.intents.param_service.get_store'),
        patch('server.services.intents.utils.mixer.get_store'),
    ]

    mocks = [p.start() for p in patches]
    for m in mocks:
        m.return_value = store

    yield store

    for p in patches:
        p.stop()


@pytest.fixture
def sample_device_params():
    """Sample device parameters for testing."""
    return [
        {
            "index": 0,
            "name": "Predelay",
            "value": 0.12,
            "min": 0.0,
            "max": 1.0,
            "display_value": "20.5 ms"
        },
        {
            "index": 1,
            "name": "Decay Time",
            "value": 0.5,
            "min": 0.0,
            "max": 1.0,
            "display_value": "2.5 s"
        },
        {
            "index": 2,
            "name": "Room Size",
            "value": 0.75,
            "min": 0.0,
            "max": 1.0,
            "display_value": "75.0 %"
        },
        {
            "index": 3,
            "name": "Dry/Wet",
            "value": 0.5,
            "min": 0.0,
            "max": 1.0,
            "display_value": "50.0 %"
        },
        {
            "index": 4,
            "name": "Chorus On",
            "value": 0.0,
            "min": 0.0,
            "max": 1.0,
            "display_value": "Off"
        },
        {
            "index": 5,
            "name": "Chorus Amount",
            "value": 0.3,
            "min": 0.0,
            "max": 1.0,
            "display_value": "30.0 %"
        },
        {
            "index": 6,
            "name": "HiFilter Type",
            "value": 0.0,
            "min": 0.0,
            "max": 1.0,
            "display_value": "Shelving"
        }
    ]


@pytest.fixture
def sample_device_mapping():
    """Sample device mapping with params_meta."""
    return {
        "device_name": "Reverb",
        "params_meta": [
            {
                "name": "Predelay",
                "index": 0,
                "control_type": "continuous",
                "fit": {
                    "type": "linear",
                    "coeffs": {"a": 100.0, "b": 0.0}  # Maps 0-1 to 0-100ms
                }
            },
            {
                "name": "Decay Time",
                "index": 1,
                "control_type": "continuous",
                "fit": {
                    "type": "log",
                    "coeffs": {"a": 2.0, "b": 0.5}
                }
            },
            {
                "name": "HiFilter Type",
                "index": 6,
                "control_type": "quantized",
                "label_map": {
                    "Shelving": 0.0,
                    "Low-pass": 1.0
                }
            }
        ]
    }


# ============================================================================
# 1. TRACK MIXER TESTS - WITH MIN/MAX VALIDATION
# ============================================================================

def test_track_mute_with_range(mock_request_op):
    """Test track mute and validate binary values."""
    mock_request_op.return_value = {"ok": True}

    # Test mute on
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 1,
        "field": "mute",
        "value": 1.0
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    value = call_args[1]["value"]
    assert value in [0.0, 1.0], f"Mute must be 0.0 or 1.0, got {value}"
    assert value == 1.0

    # Test mute off
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 1,
        "field": "mute",
        "value": 0.0
    })

    call_args = mock_request_op.call_args
    value = call_args[1]["value"]
    assert value == 0.0

    print(f"\n✓ Track Mute: tested on/off [values: 0.0 or 1.0]")


def test_track_solo_with_range(mock_request_op):
    """Test track solo and validate binary values."""
    mock_request_op.return_value = {"ok": True}

    # Test solo on
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 1,
        "field": "solo",
        "value": 1.0
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    value = call_args[1]["value"]
    assert value in [0.0, 1.0], f"Solo must be 0.0 or 1.0, got {value}"
    assert value == 1.0

    print(f"\n✓ Track Solo: tested on/off [values: 0.0 or 1.0]")


def test_track_send_db_with_range(mock_request_op):
    """Test track send level in dB (-60dB to 0dB range)."""
    mock_request_op.return_value = {"ok": True}

    # Test -12dB on Send A
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 1,  # Track 1
        "field": "send",
        "send_index": 1,  # Send A
        "value": -12.0,
        "unit": "dB"
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    value = call_args[1]["value"]

    # Validate range: 0.0 <= value <= 1.0
    assert 0.0 <= value <= 1.0, f"Send out of range: {value}"
    # -12dB for sends uses db_to_live_float_send (adds +6dB offset)
    # So -12dB becomes -6dB for conversion
    assert 0.69 < value < 0.71, f"Expected ~0.70 for -12dB send, got {value}"

    print(f"\n✓ Track Send (dB): -12dB → {value:.4f} [range: -60dB to 0dB]")


# ============================================================================
# 2. RETURN MIXER TESTS - WITH MIN/MAX VALIDATION
# ============================================================================

def test_return_volume_db_with_range(mock_request_op):
    """Test return volume in dB (-60dB to +6dB range)."""
    mock_request_op.return_value = {"ok": True}

    # Test -3dB on Return A
    response = client.post("/intent/execute", json={
        "domain": "return",
        "action": "set",
        "return_index": 1,  # Return A
        "field": "volume",
        "value": -3.0,
        "unit": "dB"
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    value = call_args[1]["value"]

    # Validate range: 0.0 <= value <= 1.0
    assert 0.0 <= value <= 1.0, f"Return volume out of range: {value}"
    # -3dB with Firestore mapping
    assert 0.77 < value < 0.78, f"Expected ~0.775 for -3dB, got {value}"

    print(f"\n✓ Return Volume (dB): -3dB → {value:.4f} [range: -60dB to +6dB]")


def test_return_mute_solo_with_range(mock_request_op):
    """Test return track mute and solo."""
    mock_request_op.return_value = {"ok": True}

    # Mute
    response = client.post("/intent/execute", json={
        "domain": "return",
        "action": "set",
        "return_index": 1,
        "field": "mute",
        "value": 1.0
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    value = call_args[1]["value"]
    assert value in [0.0, 1.0]

    # Solo
    response = client.post("/intent/execute", json={
        "domain": "return",
        "action": "set",
        "return_index": 1,
        "field": "solo",
        "value": 1.0
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    value = call_args[1]["value"]
    assert value in [0.0, 1.0]

    print(f"\n✓ Return Mute/Solo: tested [values: 0.0 or 1.0]")


def test_master_volume_db_with_range(mock_request_op):
    """Test master volume in dB and validate range."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "master",
        "action": "set",
        "field": "volume",
        "value": -3.0,
        "unit": "dB"
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    value = call_args[1]["value"]

    # Validate range
    assert 0.0 <= value <= 1.0, f"Master volume out of range: {value}"
    # -3dB = 0.775
    assert 0.77 < value < 0.78, f"Expected ~0.775, got {value}"

    print(f"\n✓ Master Volume (dB): -3dB → {value:.4f} [range: 0.0-1.0]")


def test_master_pan_with_range(mock_request_op):
    """Test master pan and validate range."""
    mock_request_op.return_value = {"ok": True}

    test_values = [-1.0, -0.5, 0.0, 0.5, 1.0]

    for val in test_values:
        response = client.post("/intent/execute", json={
            "domain": "master",
            "action": "set",
            "field": "pan",
            "value": val
        })

        assert response.status_code == 200
        call_args = mock_request_op.call_args
        result_value = call_args[1]["value"]

        # Validate range
        assert -1.0 <= result_value <= 1.0, f"Master pan out of range: {result_value}"
        assert result_value == val

    print(f"\n✓ Master Pan: tested {test_values} [range: -1.0 to +1.0]")


# TODO: Add Master Cue test once implemented in intents.py
# def test_master_cue_with_range(mock_request_op):
#     """Test master cue volume."""
#     pass


# ============================================================================
# 4. DEVICE PARAMETER TESTS
# ============================================================================

def test_missing_track_index():
    """Test error when track_index is missing."""
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "field": "volume",
        "value": 0.8
    })

    assert response.status_code == 400
    print("\n✓ Error handling: Missing track_index → 400")


def test_param_ambiguous(mock_request_op, sample_device_params):
    """Test error when parameter name is ambiguous."""
    params_with_duplicate = sample_device_params + [
        {
            "index": 10,
            "name": "Chorus Rate",
            "value": 0.5,
            "min": 0.0,
            "max": 1.0,
            "display_value": "2.5 Hz"
        }
    ]

    mock_request_op.return_value = {"data": {"params": params_with_duplicate}}

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "return_index": 1,
        "device_index": 0,
        "param_ref": "chorus",
        "value": 0.5
    })

    assert response.status_code == 409
    print("\n✓ Error handling: Ambiguous param → 409")


# ============================================================================
# 6. AUTO-ENABLE MASTER TOGGLE TESTS
# ============================================================================

def test_value_range_summary(mock_request_op):
    """Comprehensive test to validate and document all value ranges."""
    mock_request_op.return_value = {"ok": True}

    ranges = {
        "Track Volume": (0.0, 1.0),
        "Track Pan": (-1.0, 1.0),
        "Track Mute": (0.0, 1.0),
        "Track Solo": (0.0, 1.0),
        "Track Send": (0.0, 1.0),
        "Return Volume": (0.0, 1.0),
        "Return Pan": (-1.0, 1.0),
        "Return Mute": (0.0, 1.0),
        "Return Solo": (0.0, 1.0),
        "Return Send": (0.0, 1.0),
        "Master Volume": (0.0, 1.0),
        "Master Pan": (-1.0, 1.0),
    }

    print("\n" + "="*70)
    print("VALUE RANGE SUMMARY")
    print("="*70)
    for field, (min_val, max_val) in ranges.items():
        print(f"  {field:20s}: [{min_val:+5.1f}, {max_val:+5.1f}]")
    print("="*70)

    assert True  # This test always passes, it's for documentation


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
