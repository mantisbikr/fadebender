# Device Signature Computation Plan

## Problem Statement

**Current Issues:**
1. `/snapshot` doesn't include parameter names (performance optimization)
2. Cannot compute device signatures without parameter names
3. Some devices report `device_type: "unknown"`
4. Users rename presets → device name lookup fails
5. No reliable way to identify "what parameters does this device support?"

**Why Device Signatures Are Critical:**
- Signature = fingerprint of parameter structure (names, types, ranges)
- Survives user renaming: "Reverb" vs "My Epic Reverb" = same signature
- Works for `device_type: "unknown"`
- Canonical way to identify capabilities

---

## Current Architecture

### What We Already Have
- ✅ `make_device_signature(name, params)` in `server/services/mapping_utils.py`
- ✅ Signatures stored in Firestore `device_mappings` collection
- ✅ `/snapshot` endpoint in `server/api/overview.py`
- ✅ `/snapshot_full` uses single UDP call (`get_full_snapshot`)
- ✅ Signature computation during device learning process

### Existing Signature Function
```python
# server/services/mapping_utils.py
def make_device_signature(name: str, params: List[Dict[str, Any]]) -> str:
    param_names = ",".join([str(p.get("name", "")) for p in params])
    base = f"{len(params)}|{param_names}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()
```

---

## Solution: Lazy Async Signature Computation

### Design Principles
1. **Minimal changes** to existing architecture
2. **Lazy + Async** - return snapshot fast, compute signatures in background
3. **Reuse existing** `make_device_signature` function
4. **Follow existing patterns** from device learning process
5. **Optional** - don't break existing snapshot behavior

---

## Implementation Plan

### **Step 1: Add Background Signature Computation Task**

**File**: `server/api/overview.py`

**Add global task tracker:**
```python
import asyncio
from server.services.mapping_utils import make_device_signature

# Global task tracker
_signature_computation_task = None
```

**Add background computation function:**
```python
async def _compute_signatures_background(tracks, returns):
    """Compute signatures for all devices in background.

    This runs asynchronously after snapshot is returned.
    Fetches params for each device and computes signature.
    Results are stored in _enriched_devices_cache.
    """
    signatures = {}

    # Track devices
    for track in tracks:
        track_idx = track.get("index", 0)
        for dev in track.get("devices", []):
            dev_idx = dev.get("index", 0)
            try:
                # Fetch params (quick UDP call per device)
                params_resp = request_op(
                    "get_track_device_params",
                    track_index=track_idx,
                    device_index=dev_idx,
                    timeout=0.5
                )
                params = (params_resp.get("data") or {}).get("params") or []

                # Compute signature using existing function
                sig = make_device_signature(dev.get("name", ""), params)
                signatures[f"track_{track_idx}_dev_{dev_idx}"] = {
                    "signature": sig,
                    "device_name": dev.get("name", ""),
                    "device_type": dev.get("device_type", "unknown"),
                    "param_count": len(params)
                }

            except Exception as e:
                logger.warning(f"Failed to compute signature for track {track_idx} device {dev_idx}: {e}")

    # Return devices (same pattern)
    for ret in returns:
        ret_idx = ret.get("index", 0)
        for dev in ret.get("devices", []):
            dev_idx = dev.get("index", 0)
            try:
                params_resp = request_op(
                    "get_return_device_params",
                    return_index=ret_idx,
                    device_index=dev_idx,
                    timeout=0.5
                )
                params = (params_resp.get("data") or {}).get("params") or []
                sig = make_device_signature(dev.get("name", ""), params)
                signatures[f"return_{ret_idx}_dev_{dev_idx}"] = {
                    "signature": sig,
                    "device_name": dev.get("name", ""),
                    "device_type": dev.get("device_type", "unknown"),
                    "param_count": len(params)
                }
            except Exception as e:
                logger.warning(f"Failed to compute signature for return {ret_idx} device {dev_idx}: {e}")

    # Store in cache
    _enriched_devices_cache["signatures"] = signatures
    _enriched_devices_cache["signatures_timestamp"] = time.time()

    logger.info(f"Computed {len(signatures)} device signatures in background")

    # Optional: Emit WebSocket event when done
    try:
        from server.websocket_manager import broadcast
        broadcast({
            "event": "signatures_computed",
            "count": len(signatures),
            "timestamp": time.time()
        })
    except Exception:
        pass  # WebSocket optional
```

**Modify existing `/snapshot` endpoint:**
```python
@app.get("/snapshot")
async def snapshot(
    force_refresh: bool = False,
    compute_signatures: bool = False  # NEW optional param
) -> Dict[str, Any]:
    """Return a comprehensive snapshot of the current Live set.

    Includes:
    - Overview: tracks, returns, master (with device names and device_type)
    - Devices: LiveIndex cached device structures (tracks, returns)
    - Mixer: ValueRegistry mixer parameter values (volume, pan, sends, etc.)

    Args:
        force_refresh: Force refresh of enriched device cache
        compute_signatures: Compute device signatures in background (async)
    """
    global _enriched_devices_cache, _signature_computation_task

    # ... existing snapshot code ...

    # Kick off background signature computation if requested
    if compute_signatures and (_signature_computation_task is None or _signature_computation_task.done()):
        _signature_computation_task = asyncio.create_task(
            _compute_signatures_background(tracks, returns)
        )
        logger.info("Started background signature computation")

    # Return immediately (don't wait for signatures)
    return {
        "ok": True,
        "tracks": out_tracks,
        "returns": out_returns,
        "master": master_data,
        "mixer": mixer_data,
        "signatures_computing": compute_signatures  # NEW flag
    }
```

---

### **Step 2: Add Signature Retrieval Endpoint**

**File**: `server/api/overview.py`

**New endpoint to retrieve computed signatures:**
```python
@app.get("/snapshot/signatures")
def get_computed_signatures() -> Dict[str, Any]:
    """Get cached device signatures (computed asynchronously).

    Returns signatures that were computed in background after
    calling /snapshot?compute_signatures=true.

    Returns:
        {
            "ok": true,
            "ready": true,  // false if computation not done
            "signatures": {
                "track_0_dev_0": {
                    "signature": "abc123...",
                    "device_name": "Reverb",
                    "device_type": "reverb",
                    "param_count": 23
                },
                ...
            },
            "count": 42,
            "computed_at": 1234567890.123,
            "age_seconds": 5.2
        }
    """
    sigs = _enriched_devices_cache.get("signatures", {})
    timestamp = _enriched_devices_cache.get("signatures_timestamp", 0)
    age = time.time() - timestamp if timestamp else None

    return {
        "ok": True,
        "ready": len(sigs) > 0,
        "signatures": sigs,
        "count": len(sigs),
        "computed_at": timestamp,
        "age_seconds": age
    }
```

**Optional: Add endpoint to get signature for specific device:**
```python
@app.get("/snapshot/signatures/{domain}/{index}/device/{device_index}")
def get_device_signature(domain: str, index: int, device_index: int) -> Dict[str, Any]:
    """Get signature for a specific device.

    Args:
        domain: "track" or "return"
        index: Track or return index
        device_index: Device index on that track/return

    Returns:
        {
            "ok": true,
            "signature": "abc123...",
            "device_name": "Reverb",
            "device_type": "reverb",
            "param_count": 23
        }
    """
    sigs = _enriched_devices_cache.get("signatures", {})
    key = f"{domain}_{index}_dev_{device_index}"
    sig_data = sigs.get(key)

    if not sig_data:
        return {"ok": False, "error": "signature_not_found"}

    return {"ok": True, **sig_data}
```

---

### **Step 3: Incremental Update on Device Changes (Future)**

**Listen to Live events and update signatures only for changed devices:**

```python
# server/api/overview.py or new file server/services/signature_service.py

async def on_device_added(track_index: int, device_index: int, is_return: bool = False):
    """Compute signature for newly added device."""
    try:
        if is_return:
            params_resp = request_op("get_return_device_params",
                                    return_index=track_index,
                                    device_index=device_index)
            key = f"return_{track_index}_dev_{device_index}"
        else:
            params_resp = request_op("get_track_device_params",
                                    track_index=track_index,
                                    device_index=device_index)
            key = f"track_{track_index}_dev_{device_index}"

        params = (params_resp.get("data") or {}).get("params") or []
        device_name = ...  # Get from device info

        sig = make_device_signature(device_name, params)

        # Update cache
        if "signatures" not in _enriched_devices_cache:
            _enriched_devices_cache["signatures"] = {}

        _enriched_devices_cache["signatures"][key] = {
            "signature": sig,
            "device_name": device_name,
            "param_count": len(params)
        }

        # Broadcast update
        broadcast({
            "event": "device_signature_updated",
            "key": key,
            "signature": sig
        })

    except Exception as e:
        logger.error(f"Failed to compute signature on device_added: {e}")

# Hook into Live event system (implementation depends on your event setup)
# live.on('device_added', on_device_added)
```

---

## Usage Flow

### **Client Request Pattern**

```python
# 1. Request snapshot with background signature computation
GET /snapshot?compute_signatures=true

# Response (immediate, < 200ms):
{
    "ok": true,
    "tracks": [...],
    "returns": [...],
    "signatures_computing": true  // Indicates background task started
}

# 2. Poll for signatures (client choice: poll or listen to WebSocket)
GET /snapshot/signatures

# Response (if not ready yet):
{
    "ok": true,
    "ready": false,
    "count": 0
}

# 3. Wait 2-5 seconds, poll again
GET /snapshot/signatures

# Response (when ready):
{
    "ok": true,
    "ready": true,
    "signatures": {
        "track_0_dev_0": {
            "signature": "a1b2c3d4e5f6...",
            "device_name": "Reverb",
            "device_type": "reverb",
            "param_count": 23
        },
        "track_1_dev_0": {...},
        ...
    },
    "count": 42,
    "computed_at": 1234567890.123,
    "age_seconds": 3.4
}
```

### **WebSocket Pattern (Optional)**

```javascript
// Listen for completion event
ws.on('message', (msg) => {
    if (msg.event === 'signatures_computed') {
        console.log(`${msg.count} signatures ready`);
        fetch('/snapshot/signatures')
            .then(r => r.json())
            .then(data => {
                // Use signatures
            });
    }
});

// Request snapshot
fetch('/snapshot?compute_signatures=true');
```

---

## Performance Characteristics

### **Timing**
- **Snapshot return time**: < 200ms (unchanged from current)
- **Signature computation**: 2-5 seconds in background
  - 40 devices × 50ms UDP call = ~2 seconds
  - Can be parallelized with `asyncio.gather()` for speed
- **Polling overhead**: < 10ms per check

### **Memory**
- ~1KB per signature
- 40 devices = ~40KB total
- Stored in `_enriched_devices_cache` (already in memory)

### **Network**
- Each device requires 1 UDP call to get params
- UDP call timeout: 500ms
- Total: 40 devices = 40 UDP calls (can be parallelized)

---

## Testing Plan

### **Basic Flow Test**
1. Load Live set with 40 devices (mix of tracks and returns)
2. `GET /snapshot?compute_signatures=true`
3. Verify snapshot returns in < 500ms
4. Poll `/snapshot/signatures` every 1 second
5. Verify signatures ready in 2-5 seconds
6. Verify signature format matches existing `make_device_signature`

### **Signature Accuracy Test**
1. Compute signature via `/snapshot/signatures`
2. Rename device in Live
3. Compute signature again
4. Verify signatures match (same param structure)

### **Unknown Device Test**
1. Load device that reports `device_type: "unknown"`
2. Compute signature
3. Verify signature can be used to look up capabilities in Firestore

### **Performance Test**
1. Load set with 100+ devices
2. Time signature computation
3. Verify it completes in < 10 seconds
4. Verify no impact on snapshot response time

---

## Files to Modify

### **Primary Changes**
1. `server/api/overview.py`
   - Add `_compute_signatures_background()` function (~80 lines)
   - Modify `snapshot()` endpoint (~5 lines)
   - Add `get_computed_signatures()` endpoint (~20 lines)
   - Add `get_device_signature()` endpoint (~20 lines)

### **Optional Changes (Future)**
2. `server/services/signature_service.py` (new file)
   - Extract signature logic into dedicated service
   - Add incremental update handlers
   - Add caching strategies

3. `server/websocket_manager.py`
   - Add event emission for signature completion

---

## Benefits After Implementation

✅ **Renamed devices work**: "Reverb" → "My Epic Reverb" = same signature
✅ **Unknown devices work**: Signature-based lookup doesn't need device_type
✅ **Fast snapshot**: No blocking I/O, signatures computed async
✅ **Reliable parameter detection**: Always know what params are available
✅ **Persistent knowledge**: Firestore remembers signatures across sessions
✅ **Minimal changes**: Reuses existing functions and patterns

---

## Future Enhancements

### **Phase 2: Client Integration**
- Update WebUI to use signature-based lookups
- Update NLP device resolution to use signatures
- Handle renamed devices gracefully

### **Phase 3: Signature Cache Optimization**
- Add in-memory cache with TTL
- Implement cache invalidation on device_added/removed
- Precompute signatures on Live set load

### **Phase 4: Firestore Integration**
- Store computed signatures in Firestore
- Query Firestore by signature for capabilities
- Build signature → device_type mapping database

---

## Open Questions / Decisions

1. **Cache expiration**: How long should signatures stay in cache?
   - **Recommendation**: 1 hour (same as current enriched device cache)

2. **Parallel vs Sequential**: Compute signatures in parallel or sequential?
   - **Recommendation**: Parallel with `asyncio.gather()` for speed

3. **WebSocket required**: Should we require WebSocket or just polling?
   - **Recommendation**: Make WebSocket optional, support both patterns

4. **Firestore writes**: Should we auto-save signatures to Firestore?
   - **Recommendation**: Not initially - keep read-only for safety

---

## Implementation Checklist

### **Milestone 1: Core Async Signature Computation**
- [ ] Add `_compute_signatures_background()` function
- [ ] Modify `/snapshot` endpoint with `compute_signatures` param
- [ ] Add global task tracker
- [ ] Test: signatures compute in background without blocking

### **Milestone 2: Signature Retrieval**
- [ ] Add `/snapshot/signatures` endpoint
- [ ] Add `/snapshot/signatures/{domain}/{index}/device/{device_index}` endpoint
- [ ] Test: polling retrieval works correctly

### **Milestone 3: WebSocket Events (Optional)**
- [ ] Add WebSocket event emission on completion
- [ ] Test: clients receive completion event

### **Milestone 4: Testing & Validation**
- [ ] Test with 40+ devices
- [ ] Test renamed devices (signature stability)
- [ ] Test unknown devices
- [ ] Performance benchmarking

### **Milestone 5: Documentation**
- [ ] Update API docs with new endpoints
- [ ] Add usage examples
- [ ] Document signature format

---

## Branch: `feature/device-signatures`

Create new branch for implementation:
```bash
git checkout -b feature/device-signatures
```

---

## References

- Existing signature function: `server/services/mapping_utils.py:49`
- Existing snapshot endpoint: `server/api/overview.py:275`
- Device learning process: `server/services/param_learning_start.py`
- Firestore device mappings: `device_mappings` collection

---

**Document Version**: 1.0
**Created**: 2025-11-23
**Status**: Ready for Implementation
