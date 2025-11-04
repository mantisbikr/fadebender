# Ghost-Typing FSM - Modular Architecture

## Overview

This document defines the modular architecture for the ghost-typing FSM feature. **Each module is independent, testable, and replaceable.**

---

## Core Principles

1. **Single Responsibility** - Each module does ONE thing
2. **No Circular Dependencies** - Clean dependency graph
3. **Interface-Driven** - Modules communicate via well-defined interfaces
4. **Testable** - Each module can be unit tested in isolation
5. **Replaceable** - Swap implementations without breaking others

---

## Module Hierarchy

```
┌─────────────────────────────────────────┐
│           UI COMPONENTS                 │
│  (React components, no business logic)  │
└─────────────────────────────────────────┘
              ↓ uses
┌─────────────────────────────────────────┐
│          PRESENTATION LOGIC             │
│   (View models, formatters, hooks)      │
└─────────────────────────────────────────┘
              ↓ uses
┌─────────────────────────────────────────┐
│         APPLICATION LOGIC               │
│  (FSM, parsers, suggestion engines)     │
└─────────────────────────────────────────┘
              ↓ uses
┌─────────────────────────────────────────┐
│          DATA LAYER                     │
│   (API clients, state management)       │
└─────────────────────────────────────────┘
```

---

## Module Definitions

### 1. FSM Engine (`src/fsm/MixerFSM.js`)

**Responsibility:** State machine logic for mixer commands

**Interface:**
```javascript
class MixerFSM {
  constructor()

  // Processes one token, returns new state
  processToken(currentState, token) → { state, error }

  // Gets valid next tokens for current state
  getNextTokens(currentState) → Array<Token>

  // Checks if state is complete (ready to execute)
  isComplete(currentState) → boolean

  // Converts state to intent object
  toIntent(currentState) → Intent
}
```

**Dependencies:** None (pure logic)

**Tests:** `MixerFSM.test.js`

---

### 2. Token Parser (`src/fsm/TokenParser.js`)

**Responsibility:** Parses user input into tokens

**Interface:**
```javascript
class TokenParser {
  // Splits input into tokens
  parse(input) → Array<Token>

  // Normalizes shortcuts (t1 → track 1)
  expandShortcuts(token) → string

  // Detects token type (action, target, param, value)
  detectType(token, context) → TokenType
}
```

**Dependencies:** None

**Tests:** `TokenParser.test.js`

---

### 3. Suggestion Engine (`src/fsm/SuggestionEngine.js`)

**Responsibility:** Generates suggestions based on FSM state

**Interface:**
```javascript
class SuggestionEngine {
  constructor(fsmEngine)

  // Gets suggestions for current input
  getSuggestions(currentState, partialToken) → Array<Suggestion>

  // Filters suggestions by partial match
  filterByPrefix(suggestions, prefix) → Array<Suggestion>

  // Ranks suggestions by relevance
  rankSuggestions(suggestions, context) → Array<Suggestion>
}
```

**Dependencies:** FSM Engine

**Tests:** `SuggestionEngine.test.js`

---

### 4. Ghost Text Generator (`src/fsm/GhostTextGenerator.js`)

**Responsibility:** Produces ghost text from suggestions

**Interface:**
```javascript
class GhostTextGenerator {
  // Gets ghost text for current input
  getGhostText(currentInput, suggestions) → string

  // Gets completion (what Tab would insert)
  getCompletion(currentInput, ghostText) → string
}
```

**Dependencies:** None

**Tests:** `GhostTextGenerator.test.js`

---

### 5. Mode Router (`src/routing/ModeRouter.js`)

**Responsibility:** Routes input to correct mode (/execute, /ask, /help, /learn)

**Modes:**
- `/execute` - Execute mixer/device commands (Phase 1 focus)
- `/ask` - Read-only queries about session state
- `/help` - AI assistant for general questions (future)
- `/learn` - Device parameter learning mode (future - lets users teach system about unknown devices by turning knobs)

**Interface:**
```javascript
class ModeRouter {
  // Detects mode from input
  detectMode(input) → Mode

  // Routes to appropriate handler
  route(input, mode) → Promise<Response>
}
```

**Dependencies:** None (routes to handlers, doesn't execute them)

**Tests:** `ModeRouter.test.js`

---

### 6. Capabilities Data Provider (`src/data/CapabilitiesProvider.js`)

**Responsibility:** Fetches mixer/device data from backend

**Interface:**
```javascript
class CapabilitiesProvider {
  // Gets current session snapshot (tracks, mixer states)
  getSnapshot() → Promise<Snapshot>

  // Gets mixer params for target
  getMixerParams(target) → Promise<MixerParams>

  // Gets device params for target + device
  getDeviceParams(target, device) → Promise<DeviceParams>

  // Caches data (5s TTL)
  invalidateCache()
}
```

**Dependencies:** API client

**Tests:** `CapabilitiesProvider.test.js`

---

### 7. API Client (`src/services/fsmApi.js`)

**Responsibility:** HTTP calls to backend

**Interface:**
```javascript
export const fsmApi = {
  // Session snapshot
  fetchSnapshot: () => Promise<Response>

  // Mixer reads
  fetchTrackStatus: (trackIndex) => Promise<Response>
  fetchReturnStatus: (returnIndex) => Promise<Response>
  fetchMasterStatus: () => Promise<Response>

  // Device reads
  fetchTrackDevices: (trackIndex) => Promise<Response>
  fetchReturnDevices: (returnIndex) => Promise<Response>
}
```

**Dependencies:** None (uses fetch)

**Tests:** `fsmApi.test.js` (with mock fetch)

---

## React Components (UI Layer)

### 8. CapabilitiesPanel (`src/components/fsm/CapabilitiesPanel.jsx`)

**Responsibility:** Displays mixer params or device params

**Props:**
```javascript
{
  mode: 'execute' | 'ask' | 'help',
  context: {
    target?: string,    // "Track 1", "Return A", etc.
    param?: string,     // "volume", "pan", etc.
    device?: string     // For later (Phase 2)
  },
  onParamClick: (param) => void  // Fills input when clicked
}
```

**State:** None (receives data via props)

**Children:**
- `MixerParamDisplay` - Shows single mixer param with current value
- `ParamSection` - Collapsible section for grouped params

---

### 9. GhostInput (`src/components/fsm/GhostInput.jsx`)

**Responsibility:** Input field with ghost text overlay

**Props:**
```javascript
{
  value: string,
  onChange: (value) => void,
  onSubmit: () => void,
  ghostText: string,
  mode: 'execute' | 'ask' | 'help'
}
```

**State:**
- `cursorPosition` (to position ghost text)

**Behavior:**
- Tab/Right Arrow accepts ghost text
- Enter submits if complete
- Esc clears

---

### 10. SuggestionDropdown (`src/components/fsm/SuggestionDropdown.jsx`)

**Responsibility:** Shows suggestions below input

**Props:**
```javascript
{
  suggestions: Array<Suggestion>,
  selectedIndex: number,
  onSelect: (suggestion) => void,
  onClose: () => void
}
```

**State:** None

**Behavior:**
- Arrow keys navigate
- Enter selects
- Click selects
- Esc closes

---

### 11. ModeSelector (`src/components/fsm/ModeSelector.jsx`)

**Responsibility:** Mode chip next to input

**Props:**
```javascript
{
  currentMode: 'execute' | 'ask' | 'help',
  onModeChange: (mode) => void
}
```

**State:**
- `dropdownOpen` (for mode picker)

**Behavior:**
- Click opens dropdown
- Ctrl+M cycles modes
- Shows icon for current mode

---

### 12. CommandHistory (`src/components/fsm/CommandHistory.jsx`)

**Responsibility:** Scrollable command history

**Props:**
```javascript
{
  commands: Array<Command>,
  onCommandClick: (command) => void  // Updates capabilities panel
}
```

**State:**
- `selectedIndex` (highlighted command)

**Behavior:**
- Click command → capabilities panel updates
- Up/Down arrows navigate
- Enter fills input with selected command

---

## Presentation Logic (Hooks)

### 13. useFSM Hook (`src/hooks/useFSM.js`)

**Responsibility:** Manages FSM state and input processing

**Interface:**
```javascript
function useFSM(mode) {
  return {
    currentState: FSMState,
    input: string,
    ghostText: string,
    suggestions: Array<Suggestion>,
    isComplete: boolean,

    handleInput: (value) => void,
    acceptGhostText: () => void,
    selectSuggestion: (suggestion) => void,
    reset: () => void,
    submit: () => Promise<void>
  }
}
```

**Uses:**
- MixerFSM
- TokenParser
- SuggestionEngine
- GhostTextGenerator

---

### 14. useCapabilities Hook (`src/hooks/useCapabilities.js`)

**Responsibility:** Fetches and caches capabilities data

**Interface:**
```javascript
function useCapabilities(context) {
  return {
    data: CapabilitiesData | null,
    loading: boolean,
    error: Error | null,
    refresh: () => void
  }
}
```

**Uses:**
- CapabilitiesProvider

---

### 15. useCommandHistory Hook (`src/hooks/useCommandHistory.js`)

**Responsibility:** Manages command history state

**Interface:**
```javascript
function useCommandHistory() {
  return {
    commands: Array<Command>,
    addCommand: (command) => void,
    selectCommand: (index) => void,
    selectedCommand: Command | null
  }
}
```

**Uses:**
- localStorage for persistence

---

## File Structure

```
clients/web-chat/src/
├── fsm/                          # Core FSM logic (no React)
│   ├── MixerFSM.js              # FSM state machine
│   ├── MixerFSM.test.js
│   ├── TokenParser.js            # Input tokenization
│   ├── TokenParser.test.js
│   ├── SuggestionEngine.js       # Suggestion generation
│   ├── SuggestionEngine.test.js
│   ├── GhostTextGenerator.js     # Ghost text logic
│   ├── GhostTextGenerator.test.js
│   └── types.js                  # TypeScript-style types (JSDoc)
│
├── routing/                      # Mode routing
│   ├── ModeRouter.js
│   └── ModeRouter.test.js
│
├── data/                         # Data layer
│   ├── CapabilitiesProvider.js
│   ├── CapabilitiesProvider.test.js
│   └── cache.js                  # Simple cache utility
│
├── services/                     # API clients
│   ├── fsmApi.js
│   └── fsmApi.test.js
│
├── hooks/                        # React hooks
│   ├── useFSM.js
│   ├── useFSM.test.js
│   ├── useCapabilities.js
│   ├── useCapabilities.test.js
│   ├── useCommandHistory.js
│   └── useCommandHistory.test.js
│
├── components/fsm/               # UI components
│   ├── CapabilitiesPanel.jsx
│   ├── CapabilitiesPanel.test.jsx
│   ├── GhostInput.jsx
│   ├── GhostInput.test.jsx
│   ├── SuggestionDropdown.jsx
│   ├── SuggestionDropdown.test.jsx
│   ├── ModeSelector.jsx
│   ├── ModeSelector.test.jsx
│   ├── CommandHistory.jsx
│   └── CommandHistory.test.jsx
│
└── pages/
    └── FSMChatPage.jsx           # Main page that assembles components
```

---

## Dependency Graph

```
FSMChatPage
  ├─ uses → CapabilitiesPanel
  │           └─ uses → useCapabilities
  │                       └─ uses → CapabilitiesProvider
  │                                   └─ uses → fsmApi
  │
  ├─ uses → GhostInput
  │           └─ uses → useFSM
  │                       ├─ uses → MixerFSM
  │                       ├─ uses → TokenParser
  │                       ├─ uses → SuggestionEngine
  │                       │           └─ uses → MixerFSM
  │                       └─ uses → GhostTextGenerator
  │
  ├─ uses → SuggestionDropdown
  │
  ├─ uses → ModeSelector
  │           └─ uses → ModeRouter
  │
  └─ uses → CommandHistory
                └─ uses → useCommandHistory
```

**No circular dependencies!**

---

## Testing Strategy

### Unit Tests (Jest)

Each module has its own test file:
- Pure logic modules (FSM, parsers, generators) → easy to test
- Hooks → test with `@testing-library/react-hooks`
- Components → test with `@testing-library/react`

### Integration Tests

- `FSMIntegration.test.js` - Full flow from input to intent
- `CapabilitiesIntegration.test.js` - Full flow from context to display

### E2E Tests (Playwright)

- User types command → sees ghost text → accepts → executes
- User clicks history → capabilities panel updates
- Mode switching works

---

## Implementation Order

### Week 1: Core Logic (No UI)

1. `MixerFSM.js` + tests
2. `TokenParser.js` + tests
3. `SuggestionEngine.js` + tests
4. `GhostTextGenerator.js` + tests
5. `ModeRouter.js` + tests

**Deliverable:** Core FSM working, fully tested

---

### Week 2: Data Layer

1. `fsmApi.js` + tests
2. `CapabilitiesProvider.js` + tests
3. Backend: `/snapshot` endpoint

**Deliverable:** Data fetching working

---

### Week 3: Hooks (Presentation Logic)

1. `useFSM.js` + tests
2. `useCapabilities.js` + tests
3. `useCommandHistory.js` + tests

**Deliverable:** React integration layer working

---

### Week 4: UI Components

1. `GhostInput.jsx` + tests
2. `SuggestionDropdown.jsx` + tests
3. `CapabilitiesPanel.jsx` + tests
4. `ModeSelector.jsx` + tests
5. `CommandHistory.jsx` + tests

**Deliverable:** Full UI working

---

### Week 5: Integration & Polish

1. `FSMChatPage.jsx` - Assemble all components
2. Integration tests
3. E2E tests
4. Performance optimization
5. User testing

**Deliverable:** Production-ready feature

---

## Benefits of This Architecture

1. **Easy to test** - Each module isolated
2. **Easy to extend** - Add new FSMs (device FSM, send FSM) without touching existing code
3. **Easy to debug** - Clear boundaries between modules
4. **Easy to optimize** - Profile and optimize individual modules
5. **Easy to maintain** - Single responsibility makes changes localized
6. **Easy to onboard** - New devs can understand one module at a time

---

## Migration Path from Current Code

Current ChatInput.jsx has autocorrect logic. Plan:

1. Extract autocorrect to `TokenParser` module
2. Keep existing ChatInput working
3. Build new FSMChatPage in parallel
4. A/B test both
5. Migrate when stable

**No breaking changes to existing code.**

---

## Success Metrics

- ✅ Each module < 200 lines
- ✅ Each module has 80%+ test coverage
- ✅ No circular dependencies
- ✅ All modules have JSDoc types
- ✅ Build time < 5s
- ✅ Runtime performance < 50ms per keystroke
