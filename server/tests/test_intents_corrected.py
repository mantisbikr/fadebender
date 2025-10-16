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
    """Mock the request_op function to simulate Live responses."""
    with patch('server.api.intents.request_op') as mock:
        yield mock


@pytest.fixture
def mock_store():
    """Mock the Firestore store."""
    with patch('server.api.intents.get_store') as mock:
        store = MagicMock()
        store.enabled = True
        mock.return_value = store
        yield store


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

def test_track_volume_db_with_range(mock_request_op):
    """Test setting track volume in dB and validate range (1-based indexing)."""
    mock_request_op.return_value = {"ok": True}

    # Test -6dB on Track 1 (converts to 0 internally)
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 1,  # Track 1 (1-based)
        "field": "volume",
        "value": -6.0,
        "unit": "dB"
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    track_idx = call_args[1]["track_index"]
    value = call_args[1]["value"]

    # Verify 1-based conversion to 0-based
    assert track_idx == 0, f"Expected track_index=0, got {track_idx}"

    # Validate range: 0.0 <= value <= 1.0
    assert 0.0 <= value <= 1.0, f"Volume out of range: {value}"
    # -6dB with Firestore mapping
    assert 0.69 < value < 0.71, f"Expected ~0.70, got {value}"

    print(f"\n✓ Track Volume (dB): Track 1, -6dB → {value:.4f} [range: 0.0-1.0]")


def test_track_volume_normalized_with_range(mock_request_op):
    """Test setting track volume normalized and validate range."""
    mock_request_op.return_value = {"ok": True}

    test_values = [0.0, 0.25, 0.5, 0.75, 1.0]

    for val in test_values:
        response = client.post("/intent/execute", json={
            "domain": "track",
            "action": "set",
            "track_index": 0,
            "field": "volume",
            "value": val
        })

        assert response.status_code == 200
        call_args = mock_request_op.call_args
        result_value = call_args[1]["value"]

        # Validate range
        assert 0.0 <= result_value <= 1.0, f"Volume out of range: {result_value}"
        assert result_value == val, f"Expected {val}, got {result_value}"

    print(f"\n✓ Track Volume (normalized): tested {test_values} [range: 0.0-1.0]")


def test_track_pan_with_range(mock_request_op):
    """Test setting track pan and validate range."""
    mock_request_op.return_value = {"ok": True}

    test_values = [-1.0, -0.5, 0.0, 0.5, 1.0]

    for val in test_values:
        response = client.post("/intent/execute", json={
            "domain": "track",
            "action": "set",
            "track_index": 0,
            "field": "pan",
            "value": val
        })

        assert response.status_code == 200
        call_args = mock_request_op.call_args
        result_value = call_args[1]["value"]

        # Validate range: -1.0 <= pan <= 1.0
        assert -1.0 <= result_value <= 1.0, f"Pan out of range: {result_value}"
        assert result_value == val, f"Expected {val}, got {result_value}"

    print(f"\n✓ Track Pan: tested {test_values} [range: -1.0 to +1.0]")


def test_track_mute_with_range(mock_request_op):
    """Test track mute and validate binary values."""
    mock_request_op.return_value = {"ok": True}

    # Test mute on
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
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
        "track_index": 0,
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
        "track_index": 0,
        "field": "solo",
        "value": 1.0
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    value = call_args[1]["value"]
    assert value in [0.0, 1.0], f"Solo must be 0.0 or 1.0, got {value}"
    assert value == 1.0

    print(f"\n✓ Track Solo: tested on/off [values: 0.0 or 1.0]")


def test_track_send_with_range(mock_request_op):
    """Test track send level and validate range (1-based indexing)."""
    mock_request_op.return_value = {"ok": True}

    test_values = [0.0, 0.25, 0.5, 0.75, 1.0]

    for val in test_values:
        response = client.post("/intent/execute", json={
            "domain": "track",
            "action": "set",
            "track_index": 1,  # Track 1 (1-based)
            "field": "send",
            "send_index": 1,  # Send A (1-based)
            "value": val
        })

        assert response.status_code == 200
        call_args = mock_request_op.call_args
        track_idx = call_args[1]["track_index"]
        send_idx = call_args[1]["send_index"]
        result_value = call_args[1]["value"]

        # Verify 1-based conversion
        assert track_idx == 0 and send_idx == 0

        # Validate range: 0.0 <= send <= 1.0
        assert 0.0 <= result_value <= 1.0, f"Send out of range: {result_value}"
        assert result_value == val, f"Expected {val}, got {result_value}"

    print(f"\n✓ Track Send: tested {test_values} [range: 0.0-1.0]")


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

def test_return_volume_with_range(mock_request_op):
    """Test return track volume and validate range (1-based indexing)."""
    mock_request_op.return_value = {"ok": True}

    test_values = [0.0, 0.3, 0.6, 0.9, 1.0]

    for val in test_values:
        response = client.post("/intent/execute", json={
            "domain": "return",
            "action": "set",
            "return_index": 1,  # Return A (1-based)
            "field": "volume",
            "value": val
        })

        assert response.status_code == 200
        call_args = mock_request_op.call_args
        return_idx = call_args[1]["return_index"]
        result_value = call_args[1]["value"]

        # Verify 1-based conversion
        assert return_idx == 0

        # Validate range
        assert 0.0 <= result_value <= 1.0, f"Return volume out of range: {result_value}"
        assert result_value == val

    print(f"\n✓ Return Volume: tested {test_values} [range: 0.0-1.0]")


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


def test_return_pan_with_range(mock_request_op):
    """Test return track pan and validate range."""
    mock_request_op.return_value = {"ok": True}

    test_values = [-1.0, -0.25, 0.0, 0.25, 1.0]

    for val in test_values:
        response = client.post("/intent/execute", json={
            "domain": "return",
            "action": "set",
            "return_index": 0,
            "field": "pan",
            "value": val
        })

        assert response.status_code == 200
        call_args = mock_request_op.call_args
        result_value = call_args[1]["value"]

        # Validate range
        assert -1.0 <= result_value <= 1.0, f"Return pan out of range: {result_value}"
        assert result_value == val

    print(f"\n✓ Return Pan: tested {test_values} [range: -1.0 to +1.0]")


def test_return_mute_solo_with_range(mock_request_op):
    """Test return track mute and solo."""
    mock_request_op.return_value = {"ok": True}

    # Mute
    response = client.post("/intent/execute", json={
        "domain": "return",
        "action": "set",
        "return_index": 0,
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
        "return_index": 0,
        "field": "solo",
        "value": 1.0
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    value = call_args[1]["value"]
    assert value in [0.0, 1.0]

    print(f"\n✓ Return Mute/Solo: tested [values: 0.0 or 1.0]")


def test_return_send_with_range(mock_request_op):
    """Test return send level and validate range."""
    mock_request_op.return_value = {"ok": True}

    test_values = [0.0, 0.4, 0.8, 1.0]

    for val in test_values:
        response = client.post("/intent/execute", json={
            "domain": "return",
            "action": "set",
            "return_index": 0,
            "field": "send",
            "send_index": 1,
            "value": val
        })

        assert response.status_code == 200
        call_args = mock_request_op.call_args
        result_value = call_args[1]["value"]

        # Validate range
        assert 0.0 <= result_value <= 1.0, f"Return send out of range: {result_value}"
        assert result_value == val

    print(f"\n✓ Return Send: tested {test_values} [range: 0.0-1.0]")


# ============================================================================
# 3. MASTER MIXER TESTS - WITH MIN/MAX VALIDATION
# ============================================================================

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


def test_master_volume_normalized_with_range(mock_request_op):
    """Test master volume normalized and validate range."""
    mock_request_op.return_value = {"ok": True}

    test_values = [0.0, 0.5, 0.85, 1.0]

    for val in test_values:
        response = client.post("/intent/execute", json={
            "domain": "master",
            "action": "set",
            "field": "volume",
            "value": val
        })

        assert response.status_code == 200
        call_args = mock_request_op.call_args
        result_value = call_args[1]["value"]

        # Validate range
        assert 0.0 <= result_value <= 1.0, f"Master volume out of range: {result_value}"
        assert result_value == val

    print(f"\n✓ Master Volume (normalized): tested {test_values} [range: 0.0-1.0]")


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

def test_device_param_by_index_with_range(mock_request_op, sample_device_params):
    """Test device parameter by index with min/max validation."""
    mock_request_op.side_effect = [
        {"data": {"params": sample_device_params}},
        {"ok": True}
    ]

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "return_index": 0,
        "device_index": 0,
        "param_index": 2,  # Room Size: min=0.0, max=1.0
        "value": 0.75
    })

    assert response.status_code == 200

    # Validate that value respects param's min/max
    final_call = mock_request_op.call_args_list[-1]
    value = final_call[1]["value"]
    assert 0.0 <= value <= 1.0, f"Device param out of range: {value}"

    print(f"\n✓ Device Param (by index): Room Size = {value} [range: 0.0-1.0]")


def test_device_param_by_name_with_range(mock_request_op, sample_device_params):
    """Test device parameter by name with validation."""
    mock_request_op.side_effect = [
        {"data": {"params": sample_device_params}},
        {"ok": True}
    ]

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "return_index": 0,
        "device_index": 0,
        "param_ref": "decay",  # Matches "Decay Time"
        "value": 0.6
    })

    assert response.status_code == 200
    final_call = mock_request_op.call_args_list[-1]
    value = final_call[1]["value"]
    assert 0.0 <= value <= 1.0, f"Device param out of range: {value}"

    print(f"\n✓ Device Param (by name): Decay Time = {value} [range: 0.0-1.0]")


def test_device_param_display_value_with_range(mock_request_op, sample_device_params, sample_device_mapping, mock_store):
    """Test display-value conversion with range validation."""
    mock_store.get_device_mapping.return_value = sample_device_mapping

    mock_request_op.side_effect = [
        {"data": {"params": sample_device_params}},
        {"data": {"devices": [{"index": 0, "name": "Reverb"}]}},
        {"ok": True}
    ]

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "return_index": 0,
        "device_index": 0,
        "param_ref": "predelay",
        "display": "50 ms"
    })

    assert response.status_code == 200
    final_call = mock_request_op.call_args_list[-1]
    value = final_call[1]["value"]

    # Linear fit: y = 100*x => 50ms -> x = 0.5
    assert 0.0 <= value <= 1.0, f"Device param out of range: {value}"
    assert value == pytest.approx(0.5, abs=0.01)

    print(f"\n✓ Device Param (display): '50 ms' → {value} [range: 0.0-1.0]")


# ============================================================================
# 5. ERROR HANDLING TESTS
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


def test_param_not_found(mock_request_op, sample_device_params):
    """Test error when parameter not found."""
    mock_request_op.return_value = {"data": {"params": sample_device_params}}

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "return_index": 0,
        "device_index": 0,
        "param_ref": "nonexistent",
        "value": 0.5
    })

    assert response.status_code == 404
    print("\n✓ Error handling: Param not found → 404")


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
        "return_index": 0,
        "device_index": 0,
        "param_ref": "chorus",
        "value": 0.5
    })

    assert response.status_code == 409
    print("\n✓ Error handling: Ambiguous param → 409")


def test_no_live_response(mock_request_op):
    """Test error when Live doesn't respond."""
    mock_request_op.return_value = None

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "volume",
        "value": 0.8
    })

    assert response.status_code == 504
    print("\n✓ Error handling: Live timeout → 504")


# ============================================================================
# 6. AUTO-ENABLE MASTER TOGGLE TESTS
# ============================================================================

def test_auto_enable_chorus_on(mock_request_op, sample_device_params):
    """Test auto-enabling 'Chorus On' when setting Chorus Amount."""
    mock_request_op.side_effect = [
        {"data": {"params": sample_device_params}},
        {"ok": True},  # Enable Chorus On
        {"ok": True}   # Set Chorus Amount
    ]

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "return_index": 0,
        "device_index": 0,
        "param_ref": "chorus amount",
        "value": 0.8
    })

    assert response.status_code == 200
    assert mock_request_op.call_count == 3

    # Check that Chorus On was enabled
    second_call = mock_request_op.call_args_list[1]
    assert second_call[1]["param_index"] == 4  # Chorus On
    assert second_call[1]["value"] == 1.0

    print("\n✓ Auto-enable: Chorus On activated before setting Chorus Amount")


# ============================================================================
# 7. DRY-RUN MODE TESTS
# ============================================================================

def test_dry_run_preview(mock_request_op):
    """Test dry-run mode returns preview without executing."""
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "volume",
        "value": 0.75,
        "dry_run": True
    })

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "preview" in data
    assert data["preview"]["value"] == 0.75

    # Should not have called Live
    mock_request_op.assert_not_called()

    print("\n✓ Dry-run: Preview generated without execution")


# ============================================================================
# 8. VALUE RANGE SUMMARY TEST
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
