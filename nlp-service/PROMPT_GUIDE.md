# Prompt Instructions for Actionable Help Responses

## Overview
The Fadebender DAW command interpreter has been enhanced to provide actionable help responses with clickable suggested intents. This guide explains how the prompt system works and how to generate effective help responses.

## Enhanced Prompt Structure

### Question Response Format
For help queries and questions, the system now expects this JSON structure:

```json
{
  "intent": "question_response",
  "answer": "helpful response with actionable suggestions",
  "suggested_intents": [
    "set track 1 volume to -12 dB",
    "increase track 2 volume by 3 dB",
    "set track 3 volume to -6 dB"
  ],
  "meta": {
    "utterance": "original command",
    "confidence": 0.95
  }
}
```

### Key Requirements

1. **Always include suggested_intents**: For every question_response, provide 2-4 specific, actionable commands that users can click to execute.

2. **Make intents specific**: Each suggested intent should be a complete, executable command that follows the supported syntax:
   - `"set track N volume to X dB"` (absolute volume)
   - `"increase track N volume by X dB"` (relative increase)
   - `"decrease track N volume by X dB"` (relative decrease)

3. **Context-aware suggestions**: The suggested intents should be relevant to the user's question:
   - For "vocals too soft" → suggest volume increases for likely vocal tracks
   - For "drums not punchy" → suggest volume/EQ adjustments for drum tracks
   - For general mixing questions → provide diverse track examples

## Examples

### Example 1: Volume Issue
**User Query**: "the vocals are too soft"
**Response**:
```json
{
  "intent": "question_response",
  "answer": "For soft vocals, try increasing the vocal track volume or checking for routing issues. You may also want to adjust compression and EQ settings.",
  "suggested_intents": [
    "set track 1 volume to -6 dB",
    "increase track 1 volume by 6 dB",
    "set track 2 volume to -3 dB"
  ]
}
```

### Example 2: General Mixing Question
**User Query**: "how do I make my drums punchier?"
**Response**:
```json
{
  "intent": "question_response",
  "answer": "To make drums punchier, try boosting the volume, adding compression, or EQ adjustments around 60-80Hz (kick) and 2-5kHz (snare).",
  "suggested_intents": [
    "set track 3 volume to -3 dB",
    "increase track 3 volume by 3 dB",
    "set track 4 volume to -6 dB"
  ]
}
```

## Frontend Integration

The web client automatically parses `suggested_intents` and renders them as clickable chips. When a user clicks a suggested intent, it's automatically executed as if they typed the command.

## Fallback Behavior

When the AI service is unavailable, the fallback system also provides suggested intents with generic but useful volume adjustment commands.

## Best Practices

1. **Vary track numbers**: Use different track numbers (1, 2, 3, 4) to give users options
2. **Include both absolute and relative**: Mix absolute settings like "-6 dB" with relative changes like "by 3 dB"
3. **Stay within bounds**: Keep volume suggestions between -60 dB and +6 dB (system limits)
4. **Be specific**: Avoid vague commands - each suggested intent should be immediately executable
5. **Match context**: Tailor suggestions to the specific problem mentioned in the query

## Technical Notes

- The `suggested_intents` field is checked at both `data.intent.suggested_intents` and `data.suggested_intents` levels
- Each suggested intent is rendered as a Material-UI Chip component with hover effects
- Clicking a suggested intent calls the same handler as typing the command manually
- The system supports both absolute volume settings and relative adjustments