# Issue: Tracks — eliminate slider wiggle after mute/solo

Status: Open
Priority: Post‑MVP polish
Owner: TBD

## Summary
After toggling mute or solo on a track, volume/pan sliders sometimes move briefly before settling. Icon colors update promptly, but the visible slider “wiggle” is distracting.

## Environment
- Ableton Live 12 (macOS) with Remote Script
- Backend server (SSE) + Web UI (React)

## Reproduction
1) Open Tracks tab
2) Click mute/solo on any track
3) Observe: within ~1s, volume/pan sliders may briefly change before settling

## Expected
- Icon updates immediately (<100 ms)
- Sliders remain stable for ~500–800 ms after the toggle, then reflect the final Live values
- Continuous slider drags remain smooth (no snap‑back)

## Likely Cause
Live may emit near‑simultaneous mixer updates (volume/pan) during a toggle transition. Applying these continuous updates mid‑transition causes UI jitter.

## Proposed Fixes (in order of preference)
1. Remote Script coalescing (preferred)
   - When a track’s mute/solo toggles, open a 400–800 ms gate for that track.
   - Suppress value_changed callbacks for volume/pan within the gate unless |Δ| > epsilon (e.g., >0.005).
   - On gate close, emit a single snapshot for volume/pan.

2. Server‑side coalescing
   - Track last toggle timestamp per track.
   - Drop volume/pan SSE within the gate; on gate close, perform one `get_track_status` and emit synth events.

3. UI‑only state machine (backup)
   - Current suppression window prevents refresh/jitter.
   - Enhance: ignore volume/pan SSE entirely within gate and fire one `refreshTrack(idx)` at gate end.

## Acceptance Criteria
- No visible slider movement for 500 ms after toggles
- Icon flips immediately; sliders match Live after gate closes
- Continuous drag behavior remains unchanged

## Links
- Commit: 193d28f (mixer stability)
- Files: `clients/web-chat/src/components/Sidebar.jsx`, `clients/web-chat/src/components/TrackRow.jsx`

