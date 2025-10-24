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
# 1. TRACK MIXER TESTS
# ============================================================================

def test_track_volume_db(mock_request_op):
    """Test setting track volume in dB."""
    # Mock overview for validation, then set_mixer operation
    mock_request_op.side_effect = [
        {"data": {"tracks": [{"index": 1, "name": "Track 1"}]}},  # get_overview
        {"ok": True}  # set_mixer
    ]

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 1,
        "field": "volume",
        "value": -6.0,
        "unit": "dB"
    })

    assert response.status_code == 200
    assert response.json()["ok"] is True

    # Check that db_to_live_float was applied
    assert mock_request_op.call_count == 2
    set_mixer_call = mock_request_op.call_args_list[1]
    assert set_mixer_call[0][0] == "set_mixer"
    # -6dB = 0.70 in Live (using fallback formula: 0.85 - 0.025*6)
    assert 0.69 < set_mixer_call[1]["value"] < 0.71


def test_track_volume_percent(mock_request_op):
    """Test setting track volume in percent."""
    mock_request_op.side_effect = [
        {"data": {"tracks": [{"index": 1, "name": "Track 1"}]}},  # get_overview
        {"ok": True}  # set_mixer
    ]

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 1,
        "field": "volume",
        "value": 75.0,
        "unit": "%"
    })

    assert response.status_code == 200
    assert mock_request_op.call_count == 2
    set_mixer_call = mock_request_op.call_args_list[1]
    assert set_mixer_call[1]["value"] == 0.75


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
        "return_index": 1,
        "field": "volume",
        "value": 80.0,
        "unit": "%"
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[0][0] == "set_return_mixer"
    assert call_args[1]["value"] == 0.8


def test_return_mute(mock_request_op):
    """Test muting a return track."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "return",
        "action": "set",
        "return_index": 1,
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
        "track_index": 1,
        "field": "send",
        "send_index": 0,
        "value": 65.0,
        "unit": "%"
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    assert call_args[0][0] == "set_send"
    assert call_args[1]["value"] == 0.65


def test_return_send(mock_request_op):
    """Test setting return send level."""
    mock_request_op.return_value = {"ok": True}

    response = client.post("/intent/execute", json={
        "domain": "return",
        "action": "set",
        "return_index": 1,
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

    mock_request_op.side_effect = [
        {"data": {"devices": [{"index": 0, "name": "Reverb"}]}},  # get_return_devices (validation)
        {"data": {"params": params_with_duplicate}},  # get_return_device_params
    ]

    response = client.post("/intent/execute", json={
        "domain": "device",
        "action": "set",
        "return_index": 1,
        "device_index": 0,
        "param_ref": "chorus",  # Matches "Chorus On" and "Chorus Amount" and "Chorus Rate"
        "value": 0.5
    })

    assert response.status_code == 409  # Conflict - ambiguous


def test_dry_run_track_volume(mock_request_op):
    """Test dry-run mode for track volume."""
    # Even in dry-run mode, validation calls might be made
    mock_request_op.side_effect = [
        {"data": {"tracks": [{"index": 1, "name": "Track 1"}]}},  # get_overview (validation)
    ]

    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 1,
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

    # Should only have called get_overview, not set_mixer
    assert mock_request_op.call_count == 1
    assert mock_request_op.call_args_list[0][0][0] == "get_overview"


def test_missing_track_index():
    """Test error when track_index is missing."""
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "field": "volume",
        "value": 0.8
    })

    assert response.status_code == 400


def test_unsupported_intent():
    """Test error for unsupported intent combinations."""
    response = client.post("/intent/execute", json={
        "domain": "transport",
        "action": "set",
        "field": "tempo",
        "value": 120.0
    })

    assert response.status_code == 400


def test_track_device_param_by_name(mock_request_op, sample_device_params):
    """Test setting track device parameter by name."""
    mock_request_op.side_effect = [
        {"data": {"params": sample_device_params}},  # get_track_device_params
        {"data": {"devices": [{"index": 0, "name": "Reverb"}]}},  # get_track_devices (for mapping)
        {"ok": True}  # set_device_param
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
        "track_index": 1,
        "field": "volume",
        "value": 0.0,
        "unit": "dB"
    })

    assert response.status_code == 200
    call_args = mock_request_op.call_args
    # 0 dB = 0.85 in Live (approximately)
    assert 0.80 < call_args[1]["value"] < 0.90


def test_pan_extremes(mock_request_op):
    """Test panning to extreme left and right."""
    mock_request_op.return_value = {"ok": True}

    # Hard left
    response = client.post("/intent/execute", json={
        "domain": "track",
        "action": "set",
        "track_index": 1,
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
        "track_index": 1,
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

