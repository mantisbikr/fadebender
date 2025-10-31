# DAW Autocorrect

The WebUI now has **automatic typo correction** - just like your phone! Type a common typo and press **space** or **tab** to auto-correct it.

## How It Works

Type: `set trak 1 volum to -10`
Press **space** after "trak" → automatically becomes "track"
Press **space** after "volum" → automatically becomes "volume"

Result: `set track 1 volume to -10`

## Supported Auto-Corrections

The autocorrect map is defined in `ChatInput.jsx` and includes:

### Track References
- trak, tracj, trk → track

### Volume Terms
- volum, vollume, vol → volume
- loudr → louder
- quiter, quietr → quieter
- incrase, increse, increace → increase

### Pan Terms
- pann → pan
- centre, centr → center

### Effects
- revreb, reverbb, revebr, reverv → reverb
- teh → the

### Returns
- retrun, retun → return

### Stereo
- strereo, streo, stere → stereo

## Adding New Corrections

To add new autocorrections, edit the `AUTOCORRECT_MAP` in `clients/web-chat/src/components/ChatInput.jsx`:

```javascript
const AUTOCORRECT_MAP = {
  'yourtpyo': 'yourtypo',  // Add new corrections here
  // ...
};
```

## Multi-Layer Typo Handling

1. **WebUI Autocorrect** (NEW!) - Instant correction on space/tab
2. **Backend Corrections** - Server-side typo corrections from textProcessor.js
3. **Firestore Learning** - Learned corrections from user patterns

## Benefits

- ✅ **Zero latency** - Corrections happen instantly as you type
- ✅ **Familiar UX** - Works like iPhone/Android autocorrect
- ✅ **No red squiggles** - Clean typing experience
- ✅ **Easy to extend** - Just add to the map
