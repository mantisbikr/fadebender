# Comprehensive RAG Test Queries

Test these queries to validate your Vertex AI Search RAG system.

## 1. Device Parameter Queries

### Basic Parameter Information
```
What does reverb decay do?
Explain compressor ratio
What is delay feedback?
What's the range for reverb predelay?
Tell me about amp gain parameter
```

### Expected Results:
- Should retrieve from device-catalog.html
- Include parameter ranges (e.g., "0.1s to 60s")
- Include audio knowledge explanations
- Mention sonic effects and use cases

---

## 2. Preset Queries

### List Presets
```
What reverb presets are available?
Show me all compressor presets
List delay presets
What amp presets exist?
```

### Specific Preset Information
```
Tell me about the Cathedral reverb preset
What is the Gentle compressor preset?
Explain the Ping Pong delay preset
When should I use the Plate Medium reverb?
```

### Expected Results:
- Should retrieve from preset-catalog.html
- List preset names
- Include when to use each preset
- May include parameter values if available

---

## 3. Audio Engineering Advice

### Problem-Solving Queries
```
My vocals sound weak
My mix sounds muddy
How to make kick punch through
Vocals getting lost in the mix
Too much low end in my mix
Drums sound flat
Need more presence in guitar
Bass and kick clash
```

### Technique Queries
```
How to sidechain in Ableton
Best way to compress vocals
How to use parallel compression
What's the best reverb for drums
How to create space in a mix
Stereo widening techniques
```

### Expected Results:
- Should retrieve from audio-fundamentals + device-catalog
- Provide specific parameter recommendations
- Suggest device/preset combinations
- Include Fadebender commands

---

## 4. Ableton Live Knowledge

### Feature Questions
```
What are sends and returns
How does sidechaining work in Ableton
Explain automation in Ableton Live
What is the difference between audio and MIDI tracks
How to use groups in Ableton
What are return tracks used for
```

### Workflow Questions
```
How to record audio in Ableton
How to arm a track
How to create a scene
How to use session view
```

### Expected Results:
- Should retrieve from ableton-live manual (488 pages)
- Explain Ableton concepts
- May include practical examples

---

## 5. Fadebender Command Help

### Command Syntax
```
How do I control reverb on return A
How to load a device
How to set track volume
How to open device controls
What commands can I use
```

### Workflow Help
```
How to set up a reverb send
How to control multiple devices
How to query my project
How to use the capabilities drawer
```

### Expected Results:
- Should retrieve from user-guide.html
- Show specific Fadebender commands
- Include workflow examples
- Explain capabilities drawer usage

---

## 6. Combined Queries (Multi-Document)

These should pull from multiple sources:

```
How to add reverb to vocals - should retrieve:
  - Device parameters (reverb decay, predelay)
  - Preset recommendations (Vocal Hall, Plate Medium)
  - Audio advice (vocal mixing techniques)
  - Fadebender commands (load reverb, set sends)

How to compress drums - should retrieve:
  - Compressor parameters (ratio, attack, release)
  - Preset recommendations (Punchy, Drum Bus)
  - Audio techniques (parallel compression, transient shaping)
  - Fadebender commands (load compressor, adjust parameters)

Create a delay effect on vocals - should retrieve:
  - Delay parameters (time, feedback, filter)
  - Preset recommendations (Vocal Delay, Slap)
  - Routing in Ableton (send/return setup)
  - Fadebender commands (load delay on return)
```

---

## 7. Context-Aware / Conversational

### Initial Query
```
My vocals sound weak
```

### Follow-up Questions (Conversational)
```
What reverb preset do you recommend?
How much reverb should I add?
Should I compress first or add reverb first?
What about EQ?
Give me the specific commands
```

### Expected Behavior:
- Should remember previous context
- Refine recommendations based on follow-ups
- Provide increasingly specific advice

---

## 8. Response Format Control

### Short Answers
```
What is reverb decay? [keep it brief]
Explain compressor ratio in one sentence
Quick answer: what are sends and returns
```

### Detailed Answers
```
Explain reverb decay in detail
Tell me everything about compressor parameters
Provide a detailed explanation of sidechaining
```

### Bulleted Answers
```
List the steps to set up a reverb send [bulleted]
What are the main compressor parameters [as bullet points]
Give me reverb preset options [bulleted list]
```

### Structured Answers
```
Explain vocal compression [step by step]
How to improve vocal presence [numbered list]
Guide me through setting up parallel compression [step-by-step]
```

---

## 9. Edge Cases

### Ambiguous Queries
```
How to improve my sound
Make it better
Fix my mix
```

### Very Specific Technical
```
What's the exact range for reverb predelay in milliseconds
Compressor ratio formula
Delay time calculation for tempo 120 BPM
```

### Non-Existent Information
```
Tell me about the quantum compressor preset
How to use Fruity Loops in Ableton
Ableton Live 15 new features
```

---

## 10. Performance Tests

### Rapid Fire (Speed)
```
List reverb presets
What's decay
Compress vocals how
```

### Complex Multi-Part
```
I'm mixing a rock song with weak vocals that get lost behind guitars and drums. The vocal track has some harshness in the high end around 3-5kHz. I want to add depth without making it muddy. What combination of EQ, compression, and reverb should I use, with specific preset recommendations and parameter values?
```

---

## Testing Checklist

For each query type, verify:

- [ ] **Relevance**: Results match the query intent
- [ ] **Source**: Correct documents retrieved (device/preset/manual/guide)
- [ ] **Citations**: Sources are attributed
- [ ] **Specificity**: Includes preset names, parameter values, commands
- [ ] **Actionability**: User can implement the advice
- [ ] **Format**: Respects format instructions (brief/detailed/bulleted)
- [ ] **Conversation**: Follow-ups maintain context
- [ ] **Commands**: Fadebender commands are syntactically correct

---

## Expected Response Examples

### Good Response (Audio Advice + Preset + Command)
> **Query**: "My vocals sound weak"
>
> **Response**:
> To strengthen weak vocals, try these techniques:
>
> 1. **EQ Boost**: Add presence at 2-5kHz to bring vocals forward
> 2. **Compression**: Use the **Gentle** compressor preset (3:1 ratio, medium attack) to even out dynamics
> 3. **Reverb**: Add **Vocal Hall** or **Plate Medium** preset with 15-20ms predelay for space without muddiness
>
> **Fadebender Commands**:
> ```
> load compressor preset gentle on track 1
> set track 1 send A to -12 dB
> load reverb preset vocal hall on return A
> ```
>
> *Sources: device-catalog.html, preset-catalog.html, audio-fundamentals*

### Good Response (Parameter Explanation)
> **Query**: "What does reverb decay do?"
>
> **Response**:
> Reverb decay controls the length of the reverb tail - how long the reverb sound continues after the initial sound stops.
>
> - **Short decay (0.5-1.5s)**: Tight, intimate sound; good for fast music or when you want clarity
> - **Medium decay (2-3s)**: Natural room sound; versatile for most applications
> - **Long decay (4-8s)**: Spacious, ambient sound; great for ballads or atmospheric effects
>
> **Range**: 0.1s to 60s
> **Parameter location**: Reverb device → General section
>
> *Source: device-catalog.html*

---

## Quick Test Script

```bash
# Test each category with curl
curl -X POST https://YOUR-REGION-YOUR-PROJECT.cloudfunctions.net/help \
  -H "Content-Type: application/json" \
  -d '{"query": "What reverb presets are available?"}'

curl -X POST https://YOUR-REGION-YOUR-PROJECT.cloudfunctions.net/help \
  -H "Content-Type: application/json" \
  -d '{"query": "My vocals sound weak"}'

curl -X POST https://YOUR-REGION-YOUR-PROJECT.cloudfunctions.net/help \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain reverb decay [keep it brief]"}'
```
