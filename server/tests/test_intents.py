#!/usr/bin/env python3
"""
Comprehensive test suite for the Intents API.

Tests cover:
1. Track mixer operations (volume, pan, mute, solo)
2. Return mixer operations
3. Master mixer operations
4. Track sends
5. Return sends
6. Device parameters (track and return)
7. Display-value conversions
8. Label-based parameter setting
9. Auto-enable master toggles
10. Parameter resolution (by index and name)
11. Unit conversions (dB, %, normalized)
12. Dry-run mode
13. Error handling
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
# 1. TRACK MIXER TESTS
# ============================================================================

def test_track_volume_db(mock_request_op):
    """Test setting track volume in dB."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "volume",
        "value": -6.0,
        "unit": "dB"
    })

    assert response.status_code == 200
    assert response.json()["ok"] is True

    # Check that db_to_live_float was applied
    mock_request_op.assert_called_once()
    call_args = mock_request_op.call_args
    assert call_args[0][0] == "set_mixer"
    # -6dB = 0.70 in Live (using fallback formula: 0.85 - 0.025*6)
    assert 0.69 < call_args[1]["value"] < 0.71


def test_track_volume_percent(mock_request_op):
    """Test setting track volume in percent."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 1,
        "field": "volume",
        "value": 75.0,
        "unit": "%"
    })

    assert response.status_code == 200
    mock_request_op.assert_called_once()
    call_args = mock_request_op.call_args
    assert call_args[1]["value"] == 0.75


def test_track_volume_normalized(mock_request_op):
    """Test setting track volume with normalized value."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "volume",
        "value": 0.85
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[1]["value"] == 0.85


def test_track_pan_percent(mock_request_op):
    """Test setting track pan in percent."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "pan",
        "value": 50.0,
        "unit": "%"
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[1]["value"] == 0.5  # 50% -> 0.5


def test_track_pan_normalized(mock_request_op):
    """Test setting track pan with normalized value (-1 to +1)."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "pan",
        "value": -0.75
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[1]["value"] == -0.75


def test_track_mute(mock_request_op):
    """Test muting a track."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 2,
        "field": "mute",
        "value": 1.0
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[1]["value"] == 1.0


def test_track_solo(mock_request_op):
    """Test soloing a track."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 1,
        "field": "solo",
        "value": 1.0
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[1]["value"] == 1.0


# ============================================================================
# 2. RETURN MIXER TESTS
# ============================================================================

def test_return_volume_percent(mock_request_op):
    """Test setting return track volume in percent."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "return",
        "action": "set",
        "return_index": 0,
        "field": "volume",
        "value": 80.0,
        "unit": "%"
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[0][0] == "set_return_mixer"
    assert call_args[1]["value"] == 0.8


def test_return_pan(mock_request_op):
    """Test setting return track pan."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "return",
        "action": "set",
        "return_index": 1,
        "field": "pan",
        "value": -25.0,
        "unit": "%"
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[1]["value"] == -0.25


def test_return_mute(mock_request_op):
    """Test muting a return track."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "return",
        "action": "set",
        "return_index": 0,
        "field": "mute",
        "value": 1.0
    })

    assert response.status_code == 200


# ============================================================================
# 3. MASTER MIXER TESTS
# ============================================================================

def test_master_volume_db(mock_request_op):
    """Test setting master volume in dB."""
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
    assert call_args[0][0] == "set_master_mixer"
    # -3dB = 0.775 in Live (using fallback formula: 0.85 - 0.025*3)
    assert 0.77 < call_args[1]["value"] < 0.78


def test_master_pan(mock_request_op):
    """Test setting master pan."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "master",
        "action": "set",
        "field": "pan",
        "value": 0.0
    })

    assert response.status_code == 200


# ============================================================================
# 4. TRACK SENDS TESTS
# ============================================================================

def test_track_send_percent(mock_request_op):
    """Test setting track send level in percent."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "send",
        "send_index": 0,
        "value": 65.0,
        "unit": "%"
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[0][0] == "set_send"
    assert call_args[1]["value"] == 0.65


def test_track_send_normalized(mock_request_op):
    """Test setting track send with normalized value."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 1,
        "field": "send",
        "send_index": 1,
        "value": 0.45
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[1]["value"] == 0.45


# ============================================================================
# 5. RETURN SENDS TESTS
# ============================================================================

def test_return_send(mock_request_op):
    """Test setting return send level."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "return",
        "action": "set",
        "return_index": 0,
        "field": "send",
        "send_index": 1,
        "value": 50.0,
        "unit": "%"
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[0][0] == "set_return_send"
    assert call_args[1]["value"] == 0.5


# ============================================================================
# 6. DEVICE PARAMETER TESTS (BY INDEX)
# ============================================================================

def test_return_device_param_by_index(mock_request_op, sample_device_params):
    """Test setting return device parameter by index."""
    mock_request_op.side_effect = [
        {"data": {"params": sample_device_params}},  # get_return_device_params
        {"ok": True}  # set_return_device_param
    ]

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "return_index": 0,
        "device_index": 0,
        "param_index": 2,
        "value": 0.85
    })

    assert response.status_code == 200
    assert mock_request_op.call_count == 2


def test_return_device_param_percent(mock_request_op, sample_device_params):
    """Test setting device parameter with percent unit."""
    mock_request_op.side_effect = [
        {"data": {"params": sample_device_params}},
        {"ok": True}
    ]

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "return_index": 0,
        "device_index": 0,
        "param_index": 2,
        "value": 80.0,
        "unit": "%"
    })

    assert response.status_code == 200
    # Should map 80% to 0.8 in normalized range [0, 1]
    final_call = mock_request_op.call_args_list[-1]
    assert final_call[1]["value"] == pytest.approx(0.8, abs=0.01)


# ============================================================================
# 7. DEVICE PARAMETER TESTS (BY NAME)
# ============================================================================

def test_return_device_param_by_name(mock_request_op, sample_device_params):
    """Test setting device parameter by name (partial match)."""
    mock_request_op.side_effect = [
        {"data": {"params": sample_device_params}},
        {"ok": True}
    ]

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "return_index": 0,
        "device_index": 0,
        "param_ref": "decay",  # Should match "Decay Time"
        "value": 0.7
    })

    assert response.status_code == 200


def test_return_device_param_ambiguous_name(mock_request_op, sample_device_params):
    """Test error when parameter name is ambiguous."""
    # Add another param with similar name
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
        "param_ref": "chorus",  # Matches "Chorus On" and "Chorus Amount" and "Chorus Rate"
        "value": 0.5
    })

    assert response.status_code == 409  # Conflict - ambiguous


def test_return_device_param_not_found(mock_request_op, sample_device_params):
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


# ============================================================================
# 8. DISPLAY-VALUE CONVERSION TESTS
# ============================================================================

def test_device_param_display_linear_fit(mock_request_op, sample_device_params, sample_device_mapping, mock_store):
    """Test setting device parameter using display value with linear fit."""
    mock_store.get_device_mapping.return_value = sample_device_mapping

    mock_request_op.side_effect = [
        {"data": {"params": sample_device_params}},  # get_return_device_params
        {"data": {"devices": [{"index": 0, "name": "Reverb"}]}},  # get_return_devices
        {"ok": True}  # set_return_device_param
    ]

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "return_index": 0,
        "device_index": 0,
        "param_ref": "predelay",
        "display": "50 ms"  # Should convert to 0.5 via linear fit
    })

    assert response.status_code == 200
    # Linear fit: y = a*x + b => y = 100*x + 0
    # 50ms => x = 50/100 = 0.5
    final_call = mock_request_op.call_args_list[-1]
    assert final_call[1]["value"] == pytest.approx(0.5, abs=0.01)


def test_device_param_display_label_map(mock_request_op, sample_device_params, sample_device_mapping, mock_store):
    """Test setting device parameter using label from label_map."""
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
        "param_ref": "hifilter type",
        "display": "Low-pass"
    })

    assert response.status_code == 200
    # Should map "Low-pass" -> 1.0
    final_call = mock_request_op.call_args_list[-1]
    assert final_call[1]["value"] == 1.0


# ============================================================================
# 9. AUTO-ENABLE MASTER TOGGLE TESTS
# ============================================================================

def test_auto_enable_chorus_on(mock_request_op, sample_device_params):
    """Test auto-enabling 'Chorus On' when setting Chorus Amount."""
    mock_request_op.side_effect = [
        {"data": {"params": sample_device_params}},  # get params (Chorus On is off)
        {"ok": True},  # set Chorus On to 1.0
        {"ok": True}   # set Chorus Amount
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
    # Should have made 3 calls: get_params, set Chorus On, set Chorus Amount
    assert mock_request_op.call_count == 3

    # Check that Chorus On was enabled first
    second_call = mock_request_op.call_args_list[1]
    assert second_call[0][0] == "set_return_device_param"
    assert second_call[1]["param_index"] == 4  # Chorus On index
    assert second_call[1]["value"] == 1.0


def test_no_auto_enable_when_master_already_on(mock_request_op, sample_device_params):
    """Test that master toggle is not enabled if already on."""
    # Set Chorus On to 1.0 (already on)
    params_with_chorus_on = sample_device_params.copy()
    params_with_chorus_on[4]["value"] = 1.0

    mock_request_op.side_effect = [
        {"data": {"params": params_with_chorus_on}},
        {"ok": True}
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
    # Should only make 2 calls: get_params, set Chorus Amount (no enable)
    assert mock_request_op.call_count == 2


# ============================================================================
# 10. DRY-RUN MODE TESTS
# ============================================================================

def test_dry_run_track_volume(mock_request_op):
    """Test dry-run mode for track volume."""
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "volume",
        "value": -6.0,
        "unit": "dB",
        "dry_run": True
    })

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "preview" in data
    assert data["preview"]["op"] == "set_mixer"

    # Should not have called Live
    mock_request_op.assert_not_called()


def test_dry_run_device_param(mock_request_op, sample_device_params):
    """Test dry-run mode for device parameter."""
    mock_request_op.return_value = {"data": {"params": sample_device_params}}

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "return_index": 0,
        "device_index": 0,
        "param_index": 2,
        "value": 0.85,
        "dry_run": True
    })

    assert response.status_code == 200
    data = response.json()
    assert "preview" in data

    # Should only have called get_params, not set
    assert mock_request_op.call_count == 1


# ============================================================================
# 11. ERROR HANDLING TESTS
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


def test_missing_param_selector(mock_request_op, sample_device_params):
    """Test error when neither param_index nor param_ref provided."""
    mock_request_op.return_value = {"data": {"params": sample_device_params}}

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "return_index": 0,
        "device_index": 0,
        "value": 0.5
    })

    assert response.status_code == 400


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


def test_unsupported_intent():
    """Test error for unsupported intent combinations."""
    response = client.post("/intent/execute", json={
        "domain": "transport",
        "action": "set",
        "field": "tempo",
        "value": 120.0
    })

    assert response.status_code == 400


def test_device_params_not_found(mock_request_op):
    """Test error when device parameters cannot be fetched."""
    mock_request_op.return_value = {"data": {"params": []}}

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "return_index": 0,
        "device_index": 0,
        "param_index": 0,
        "value": 0.5
    })

    assert response.status_code == 404


# ============================================================================
# 12. CLAMPING TESTS
# ============================================================================

def test_clamp_volume_above_max(mock_request_op):
    """Test that volume is clamped to max when clamp=True."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "volume",
        "value": 1.5,
        "clamp": True
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[1]["value"] == 1.0


def test_no_clamp_volume(mock_request_op):
    """Test that volume is not clamped when clamp=False."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "volume",
        "value": 1.5,
        "clamp": False
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[1]["value"] == 1.5


# ============================================================================
# 13. TRACK DEVICE PARAMETER TESTS
# ============================================================================

def test_track_device_param_by_index(mock_request_op, sample_device_params):
    """Test setting track device parameter by index."""
    mock_request_op.side_effect = [
        {"data": {"params": sample_device_params}},
        {"ok": True}
    ]

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "track_index": 0,
        "device_index": 0,
        "param_index": 1,
        "value": 0.65
    })

    assert response.status_code == 200
    assert mock_request_op.call_count == 2

    # Check the set_device_param call
    final_call = mock_request_op.call_args_list[-1]
    assert final_call[0][0] == "set_device_param"
    assert final_call[1]["track_index"] == 0
    assert final_call[1]["device_index"] == 0
    assert final_call[1]["param_index"] == 1
    assert final_call[1]["value"] == 0.65


def test_track_device_param_by_name(mock_request_op, sample_device_params):
    """Test setting track device parameter by name."""
    mock_request_op.side_effect = [
        {"data": {"params": sample_device_params}},
        {"ok": True}
    ]

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "track_index": 1,
        "device_index": 0,
        "param_ref": "room",
        "value": 0.9
    })

    assert response.status_code == 200


# ============================================================================
# 14. EDGE CASES
# ============================================================================

def test_zero_db_volume(mock_request_op):
    """Test setting volume to 0 dB (unity gain)."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "volume",
        "value": 0.0,
        "unit": "dB"
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    # 0 dB = 0.85 in Live (approximately)
    assert 0.80 < call_args[1]["value"] < 0.90


def test_extreme_negative_db(mock_request_op):
    """Test setting very low volume in dB."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "volume",
        "value": -70.0,
        "unit": "dB"
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    # Very low dB should result in very small value
    assert call_args[1]["value"] < 0.01


def test_pan_extremes(mock_request_op):
    """Test panning to extreme left and right."""
    mock_request_op.return_value = {"ok": True}

    # Hard left
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "pan",
        "value": -100.0,
        "unit": "%"
    })
    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[1]["value"] == -1.0

    # Hard right
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "pan",
        "value": 100.0,
        "unit": "%"
    })
    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[1]["value"] == 1.0


# ============================================================================
# 15. INTEGRATION-STYLE TESTS
# ============================================================================

def test_full_mix_scenario(mock_request_op, sample_device_params):
    """Test a realistic mixing scenario with multiple operations."""
    mock_request_op.return_value = {"ok": True}

    # 1. Set track volume
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "volume",
        "value": -3.0,
        "unit": "dB"
    })
    assert response.status_code == 200

    # 2. Pan track
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "pan",
        "value": 25.0,
        "unit": "%"
    })
    assert response.status_code == 200

    # 3. Set send to reverb
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 0,
        "field": "send",
        "send_index": 0,
        "value": 30.0,
        "unit": "%"
    })
    assert response.status_code == 200

    # 4. Adjust return device parameter
    mock_request_op.side_effect = [
        {"data": {"params": sample_device_params}},
        {"ok": True}
    ]

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "return_index": 0,
        "device_index": 0,
        "param_ref": "decay",
        "value": 0.75
    })
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
