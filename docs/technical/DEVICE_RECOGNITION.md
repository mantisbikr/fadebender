# Device Recognition & Signature System

## How Fadebender Recognizes Learned Devices

### Device Signature Generation

When you learn a device, Fadebender creates a unique "signature" based on:

```python
def _make_device_signature(name: str, params: list[dict]) -> str:
    param_names = ",".join([str(p.get("name", "")) for p in params])
    base = f"{name}|{len(params)}|{param_names}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()
```

**Signature components:**
1. **Device name** (e.g., "Reverb")
2. **Number of parameters** (e.g., 23)
3. **Parameter names in order** (e.g., "Dry/Wet,Predelay,DecayTime,...")

**Example:**
- Input: `"Reverb|23|Dry/Wet,Predelay,DecayTime,HiShelf Freq,..."`
- Output: `"a1b2c3d4e5f6..."`(40-character SHA1 hash)

### Recognition Process

**When you check if a device is learned:**

1. **Fetch current device info** from Ableton via UDP
2. **Compute signature** from device name + parameters
3. **Look up signature** in storage (Firestore + local cache)
4. **Return exists: true** if mapping found with ≥3 samples per param

**Endpoint:** `GET /return/device/map?index=1&device=0`

```json
{
  "ok": true,
  "exists": true,
  "signature": "a1b2c3d4e5...",
  "backend": "firestore"
}
```

## Your Question: Remove & Re-add Reverb

### ✅ YES - It Will Recognize It!

**Scenario:**
1. You learn Reverb on Return A → signature `abc123...`
2. You delete Reverb from Return A
3. You re-add same Reverb to Return A (or any other return)
4. **Recognition:** ✅ Signature matches → uses existing learned mapping!

**Why it works:**
- Signature is based on **device type**, not position
- Same device (Reverb) = same parameters = same signature
- Mapping is **portable across returns and tracks**

### Example

**Initial Learning:**
```bash
# Return A, Device 0 (Reverb)
POST /return/device/learn_quick {"return_index":0,"device_index":0}
# Creates signature: "a1b2c3d4..." and saves mapping
```

**Later - Different Location:**
```bash
# Return B, Device 2 (same Reverb preset)
GET /return/device/map?index=1&device=2
# Returns: exists=true, signature="a1b2c3d4..."
# ✅ Uses same learned mapping!
```

## When Signatures DON'T Match

**Different signature means re-learning needed:**

### 1. Different Device Type
- Reverb vs. Delay → Different names → Different signatures
- **Action:** Learn separately

### 2. Same Device, Different Preset/State
- ⚠️ **Important:** If device has parameter count changes based on mode
- Example: Some devices add/remove parameters dynamically
- **Result:** Different param count → Different signature → Re-learn needed

### 3. Different Ableton Version
- Rare: If Ableton adds/removes parameters in updates
- Parameter names change → Different signature
- **Action:** Re-learn after Ableton update

### 4. Third-Party Plugins
- Different plugin versions may have different parameters
- **Action:** Learn once per version

## Storage & Caching

**Dual Storage System:**

1. **Firestore (Cloud)** - `STORE.get_device_map(signature)`
   - Persistent across machines
   - Shared mappings (future multi-user)
   - Requires `GOOGLE_APPLICATION_CREDENTIALS`

2. **Local Cache** - `~/.fadebender/param_maps/`
   - Fast local access
   - Fallback if Firestore unavailable
   - File: `{signature}.json`

**Lookup Order:**
1. Check Firestore first (if enabled)
2. Fallback to local cache
3. Return `exists: false` if not found

## Quick Reference

| Scenario | Recognized? | Action |
|----------|-------------|--------|
| Same Reverb, different return | ✅ YES | Uses existing mapping |
| Same Reverb, same return, deleted & re-added | ✅ YES | Uses existing mapping |
| Reverb vs. Delay | ❌ NO | Different devices, learn separately |
| Reverb preset A vs. preset B (same param structure) | ✅ YES | Same signature if params identical |
| Reverb after Ableton update (params changed) | ❌ NO | Re-learn if params changed |

## Checking Device Mapping

**Before learning, check if device already mapped:**

```bash
# Check if Reverb on Return B is learned
curl -s "http://127.0.0.1:8722/return/device/map?index=1&device=0" | jq .

# Response if learned:
{
  "ok": true,
  "exists": true,
  "signature": "a1b2c3d4e5f6...",
  "backend": "firestore"
}

# Response if NOT learned:
{
  "ok": true,
  "exists": false,
  "signature": "a1b2c3d4e5f6...",
  "backend": "firestore"
}
```

**Get full mapping details:**

```bash
curl -s "http://127.0.0.1:8722/return/device/map_summary?index=1&device=0" | jq .
```

## Tips

1. **Learn once, use everywhere** - Same device signature = reusable mapping
2. **Check before learning** - Use `/map` endpoint to avoid duplicate work
3. **Signature debugging** - Look at signature in response to verify identity
4. **Local backup** - Check `~/.fadebender/param_maps/` for cached mappings
5. **Re-learning** - If mapping seems wrong, delete via `/mappings/delete` and re-learn

---

See [DELAY_TEST_RESULTS.md](../testing/DELAY_TEST_RESULTS.md) for example of learned device testing.
