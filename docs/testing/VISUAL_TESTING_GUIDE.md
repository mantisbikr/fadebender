# Visual Testing Guide - Web UI Features

**What to look for when testing the new UI features**

---

## 1. Compact Chat Messages

### Before (Old UI)
- JSON dropdowns with raw intent data
- Verbose technical details
- Cluttered appearance

### After (New UI - What You Should See)

**User Message:**
```
┌─────────────────────────────────────┐
│ set return A reverb decay to 2 sec  │  You  2:30 PM
└─────────────────────────────────────┘
```
- Right-aligned bubble
- Clean text only
- Timestamp on right

**Success Message:**
```
┌──────────────────────────────────────────────────┐
│ ✅ Executed                            Bot  2:30 PM │
│                                                     │
│ ┌─ Parameters • Reverb ─────────────────────┐   │
│ │                                              │   │
│ │ ▼ Global                                    │   │
│ │   [Dry/Wet] [Decay Time] [Pre-Delay]      │   │
│ │                                              │   │
│ │ ▼ Diffusion Network                         │   │
│ │   [Quality] [Size] [Shape]                  │   │
│ │                                              │   │
│ └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```
- Left-aligned
- Accordion below message
- No JSON visible
- Clean parameter chips

---

## 2. Parameter Accordion

### Layout Elements to Check

**Header:**
- Text: "Parameters • [Device Name]"
- Font: Small, secondary color
- Position: Top of accordion

**Groups:**
- Expandable sections with arrow icon
- Group name in bold
- Border: subtle, 1px
- No drop shadow

**Parameter Chips:**
- Small outlined chips
- Text: parameter name only
- Hover: subtle background change
- Click: triggers read action

**Example:**
```
Parameters • Reverb

┌─ Global ──────────────────────────────────┐
│ [Dry/Wet] [Decay Time] [Pre-Delay]        │
│ [In Filter Freq] [In Filter Res]          │
└─────────────────────────────────────────────┘

┌─ Diffusion Network ───────────────────────┐
│ [Quality] [Size] [Shape] [Stereo Image]   │
└─────────────────────────────────────────────┘

┌─ Other ───────────────────────────────────┐
│ [Chorus Amount] [Chorus Rate]             │
└─────────────────────────────────────────────┘
```

### What Should NOT Appear
- ❌ Raw JSON objects
- ❌ Technical field names like `canonical_intent`
- ❌ Nested dropdowns
- ❌ Stack traces or debug info

---

## 3. Parameter Read Response

### After Clicking a Parameter

**What You Should See:**
```
┌──────────────────────────────────────────────────┐
│ ℹ️ Current value for Decay Time on Return A      │
│    device 0 is 2.00 s                      Bot 2:31 PM │
│                                                     │
│ Try these commands:                                │
│ [set Return A device 0 Decay Time to 25%]        │
│ [set Return A device 0 Decay Time to 50%]        │
│ [set Return A device 0 Decay Time to 75%]        │
└──────────────────────────────────────────────────┘
```

**Key Elements:**
- Info icon (ℹ️)
- Clear current value with unit
- Suggested intents as clickable chips (blue outlined)
- Chips have hover effect

**Timing:**
- Should appear **immediately** (<1 second)
- No loading spinner needed

---

## 4. Context-Aware Help

### Example: "what parameters can I control"

**After device command context established:**
```
┌──────────────────────────────────────────────────┐
│ 🔧 Parameters on Return A • Reverb       Bot 2:32 PM │
│                                                     │
│ Dry/Wet, Decay Time, Pre-Delay, ER Spin On,       │
│ ER Spin Rate, ER Spin Amount, In Filter Type,     │
│ In Filter Freq, In Filter Res, Global Filter On,  │
│ Quality, Size, Shape, Stereo Image, ... (30 total)│
└──────────────────────────────────────────────────┘
```

**Key Elements:**
- Device name and return label shown
- Parameter list (up to 40 shown)
- Total count indicated
- Clean formatting

---

## 5. Generic Help with Suggestions

### Example: "how do I boost vocals?"

```
┌──────────────────────────────────────────────────┐
│ 💡 To boost vocals, increase track volume or      │
│    reduce compressor threshold to bring up        │
│    quieter parts.                           Bot 2:33 PM │
│                                                     │
│ Try these commands:                                │
│ [increase track 1 volume by 3 dB]                 │
│ [set track 1 volume to -6 dB]                     │
│ [reduce compressor threshold on track 1 by 3 dB]  │
└──────────────────────────────────────────────────┘
```

**Key Elements:**
- Help icon (💡 or 🔧)
- Clear, concise answer
- Relevant suggested intents
- Intents are clickable

---

## 6. Error Messages

### Example: Invalid device index

```
┌──────────────────────────────────────────────────┐
│ ❌ Intent error: Device 99 not found on Return A. │
│    Available devices: 0, 1             Bot 2:34 PM │
└──────────────────────────────────────────────────┘
```

**Key Elements:**
- Error icon (❌)
- Clear error description
- Helpful info (available devices)
- Red/error color theme

---

## 7. Message Alignment

### Expected Layout

```
                                    ┌──────────────┐
                                    │ User message │  You  2:30 PM
                                    └──────────────┘

┌────────────────────────┐
│ Bot response           │  Bot  2:30 PM
└────────────────────────┘

                                    ┌──────────────┐
                                    │ User message │  You  2:31 PM
                                    └──────────────┘

┌────────────────────────┐
│ Bot response           │  Bot  2:31 PM
└────────────────────────┘
```

**Rules:**
- User messages: right-aligned (ml: 'auto')
- Bot messages: left-aligned (mr: 'auto')
- Consistent spacing between messages
- Timestamps on appropriate side

---

## 8. Suggested Intent Chips

### Visual Properties

**Appearance:**
- Border: outlined (not filled)
- Color: primary blue
- Size: small
- Margin: 8px right, 8px bottom
- Border-radius: rounded corners

**States:**
- Default: outlined, white background
- Hover: light blue background, darker text
- Active/Click: slightly darker

**Layout:**
- Wrap to multiple lines if needed
- Aligned left
- Consistent spacing

**Example Visual:**
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ set track 1 ... │  │ increase send A │  │ reduce volume   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## 9. Accordion Expand/Collapse Animation

### Closed State:
```
┌─ Global ──────────────────────────┐
│                                    │  ▶ (arrow right)
└─────────────────────────────────────┘
```

### Open State:
```
┌─ Global ──────────────────────────┐
│                                    │  ▼ (arrow down)
│  [Dry/Wet] [Decay Time]           │
│  [Pre-Delay] [ER Spin On]         │
└─────────────────────────────────────┘
```

**Animation:**
- Smooth expand/collapse
- Arrow rotates 90 degrees
- No lag or janky behavior

---

## 10. Overall Color Scheme

### Message Types

| Type    | Icon | Color           | Alignment |
|---------|------|-----------------|-----------|
| User    | 👤   | Primary blue    | Right     |
| Success | ✅   | Green           | Left      |
| Info    | ℹ️   | Blue            | Left      |
| Help    | 💡   | Blue            | Left      |
| Error   | ❌   | Red             | Left      |
| Question| ❓   | Secondary/purple| Left      |

---

## 11. Responsive Design

### Desktop (>1200px)
- Messages max-width: 'lg' (1200px)
- Accordion fits comfortably
- Chips on single or few lines

### Tablet (768px - 1200px)
- Messages max-width adjusts
- Accordion still functional
- Chips wrap more

### Mobile (<768px)
- Messages stack vertically
- Accordion groups collapse by default
- Chips wrap to multiple lines
- Text remains readable
- No horizontal scroll

---

## 12. Browser DevTools Checks

### Console Tab
**Expected:**
- No red errors during normal operation
- Optional debug logs (green/blue)
- Warnings are OK if not critical

**Not Expected:**
- ❌ Uncaught errors
- ❌ Failed network requests (except intentional tests)
- ❌ React render warnings

### Network Tab
**Expected Requests:**
1. `/config` - on page load
2. `/snapshot` - on page load (optional)
3. `/intent/parse` - after user input
4. `/intent/execute` - if use_intents_for_chat enabled
5. `/return/device/capabilities` - after device command
6. `/intent/read` - after clicking parameter
7. `/help` - after help query

**Request Timing:**
- `/intent/parse`: < 2 seconds
- `/intent/execute`: < 2 seconds
- `/return/device/capabilities`: < 2 seconds
- `/intent/read`: < 1 second (fast path)

### Elements Tab
**Check for:**
- `<ParamAccordion>` component rendered
- Accordion groups expand properly
- Chips are `<Chip>` MUI components
- No inline style warnings

---

## 13. Accessibility

### Keyboard Navigation
- Tab through chips
- Enter to click chip
- Tab to accordion headers
- Enter/Space to expand accordion

### Screen Readers
- Icons have aria-labels
- Buttons are labeled
- Semantic HTML used

---

## 14. Edge Cases to Visually Verify

### Empty Accordion
- No parameters: accordion doesn't render
- No errors shown

### Long Device Names
- Name truncates or wraps gracefully
- UI doesn't break

### Many Parameters (50+)
- Accordion handles large lists
- No performance issues
- Scrollable if needed

### Rapid Clicking
- Click multiple chips quickly
- Messages stack correctly
- No duplicate responses

---

## Common Visual Bugs to Watch For

❌ **JSON blobs visible** - Should never see raw JSON in chat
❌ **Misaligned messages** - User messages must be right-aligned
❌ **Overlapping text** - Chips should wrap, not overlap
❌ **No hover effect** - Chips must show hover state
❌ **Accordion doesn't expand** - Arrow should rotate, content show
❌ **Timestamp missing** - Every message needs timestamp
❌ **Icon missing** - Every message needs appropriate icon
❌ **Suggested intents not clickable** - Must be interactive
❌ **Parameters cut off** - Full parameter name should be visible
❌ **Stale values** - Parameter reads must show current value

---

## Screenshot Checklist

When documenting tests, capture screenshots of:

1. ✅ Clean user message (right-aligned)
2. ✅ Success message with accordion
3. ✅ Expanded accordion with grouped parameters
4. ✅ Parameter read response with suggested intents
5. ✅ Context-aware help response
6. ✅ Generic help with suggestions
7. ✅ Error message (clear and helpful)
8. ✅ Multiple messages in sequence (alignment check)
9. ✅ Hover state on chips
10. ✅ Mobile/responsive view

---

## Testing Flow Visualization

```
User Input
    ↓
[Processing]
    ↓
Success Message (left-aligned)
    ↓
Parameter Accordion Appears
    ↓
User Clicks Parameter Chip
    ↓
[Fast Read - No LLM]
    ↓
Info Message: "Current value is X"
    ↓
Suggested Intents (clickable chips)
    ↓
User Clicks Suggestion
    ↓
[Execute Command]
    ↓
New Success Message + Accordion
```

---

## Final Visual Checklist

Before signing off, verify:

- ☐ No JSON visible anywhere
- ☐ Messages aligned correctly (user right, bot left)
- ☐ Accordions render and expand smoothly
- ☐ Parameter chips clickable with hover effect
- ☐ Suggested intents appear and work
- ☐ Icons match message types
- ☐ Timestamps visible on all messages
- ☐ Colors match expected scheme
- ☐ No layout breaks on resize
- ☐ No console errors
- ☐ Network requests complete successfully
- ☐ Animations smooth (no jank)
- ☐ Text readable at all sizes
- ☐ Interactive elements respond to input

---

**Tester:** _______________
**Date:** _______________
**Browser:** _______________
**Screen Size:** _______________
**Result:** ☐ PASS  ☐ FAIL

**Visual Issues Found:**
