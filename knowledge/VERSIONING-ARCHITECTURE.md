# DAW State Versioning and Snapshot Architecture

## Overview
Implement a comprehensive version control system for DAW parameters, allowing users to track changes, create snapshots, and restore previous states through natural language commands.

## Core Concepts

### Change History Tracking
- **Every Parameter Change**: Track all modifications made through Fadebender
- **Atomic Operations**: Each command creates a versioned entry
- **Metadata Storage**: Include timestamp, command used, user intent
- **Reversible Actions**: All changes can be undone/redone

### Snapshot System
- **Automatic Snapshots**: Periodic capture of entire DAW state
- **Manual Snapshots**: User-triggered via chat commands
- **Named Snapshots**: "Save current state as 'before-vocal-processing'"
- **Project Snapshots**: Complete project state including all tracks

### Chat Integration
- **Query History**: "What did I change in the last 5 minutes?"
- **Restore Commands**: "Go back to how track 2 sounded 10 minutes ago"
- **Snapshot Management**: "Create snapshot called 'rough-mix'"
- **Version Browsing**: "Show me all reverb changes on track 1"

## Implementation Architecture

### Change History Data Structure
```json
{
  "change_id": "uuid-v4",
  "timestamp": "2024-09-14T18:30:00Z",
  "user_command": "increase reverb on track 2 by 15%",
  "intent": {
    "intent": "relative_change",
    "targets": [{"track": "Track 2", "plugin": "reverb", "parameter": "wet"}],
    "operation": {"type": "relative", "value": 15, "unit": "%"}
  },
  "before_state": {
    "track": "Track 2",
    "parameter": "reverb.wet",
    "value": 25,
    "unit": "%"
  },
  "after_state": {
    "track": "Track 2",
    "parameter": "reverb.wet",
    "value": 40,
    "unit": "%"
  },
  "execution_result": {
    "success": true,
    "midi_cc_sent": 31,
    "actual_value": 40
  },
  "session_id": "session-uuid",
  "project_context": {
    "daw": "logic-pro",
    "project_name": "New Song",
    "tempo": 120
  }
}
```

### Snapshot Data Structure
```json
{
  "snapshot_id": "snapshot-uuid",
  "name": "rough-mix-v1",
  "timestamp": "2024-09-14T18:30:00Z",
  "type": "manual|automatic|project-milestone",
  "description": "Before adding vocal processing",
  "daw_state": {
    "tracks": [
      {
        "track_number": 1,
        "track_name": "Lead Vocal",
        "parameters": {
          "volume": {"value": -6, "unit": "dB"},
          "pan": {"value": 0, "unit": "%"},
          "reverb.wet": {"value": 25, "unit": "%"},
          "eq.high": {"value": 2, "unit": "dB"}
        },
        "plugins": [
          {
            "name": "ChromaVerb",
            "preset": "Vocal Hall",
            "parameters": {...}
          }
        ]
      }
    ],
    "master": {
      "volume": {"value": -3, "unit": "dB"},
      "parameters": {...}
    }
  },
  "project_metadata": {
    "daw": "logic-pro",
    "project_name": "New Song",
    "tempo": 120,
    "key": "C Major",
    "total_tracks": 8
  }
}
```

## Chat Interface Commands

### History Queries
```
User: "What changes did I make in the last 10 minutes?"
Response: "In the last 10 minutes you:
1. Increased reverb on Track 2 by 15% (3 min ago)
2. Added compression to Track 1 (7 min ago)
3. Panned Track 3 left by 30% (9 min ago)"

User: "Show me all volume changes today"
Response: "Volume changes today:
- Track 1: -3dB → -6dB (2:30 PM)
- Track 2: -8dB → -5dB (1:45 PM)
- Master: 0dB → -3dB (1:20 PM)"
```

### Undo/Redo Operations
```
User: "Undo the last change"
Response: "Undoing: Reverb on Track 2 decreased from 40% back to 25%"

User: "Go back to how track 1 sounded 5 minutes ago"
Response: "Restoring Track 1 to state from 2:25 PM:
- Volume: -3dB (was -6dB)
- Reverb: 15% (was 25%)
- Compression: Off (was On)"

User: "Undo the last 3 changes"
Response: "Undoing 3 changes:
1. Track 2 reverb: 40% → 25%
2. Track 1 compression: On → Off
3. Track 3 pan: -30% → 0%"
```

### Snapshot Management
```
User: "Create a snapshot called 'before-vocals'"
Response: "✅ Snapshot 'before-vocals' created with current project state"

User: "Take a snapshot"
Response: "✅ Auto-snapshot created: 'rough-mix-2024-09-14-18-30'"

User: "Restore snapshot 'before-vocals'"
Response: "Restoring to snapshot 'before-vocals' from 2:15 PM...
- 8 tracks restored
- All parameter changes reverted
- ✅ Project restored successfully"

User: "List all snapshots"
Response: "Available snapshots:
1. 'before-vocals' - 2:15 PM (manual)
2. 'rough-mix-v1' - 1:30 PM (manual)
3. 'auto-save-afternoon' - 1:00 PM (automatic)
4. 'project-start' - 12:00 PM (automatic)"
```

### Advanced Queries
```
User: "What's different between now and the 'before-vocals' snapshot?"
Response: "Changes since 'before-vocals' snapshot:
- Track 1: Added ChromaVerb (Vocal Hall preset)
- Track 1: Volume adjusted -6dB → -4dB
- Track 2: Reverb increased 20% → 35%
- Track 4: New compression added (3:1 ratio)"

User: "Show me the history of track 2 reverb changes"
Response: "Track 2 reverb history:
- 2:45 PM: 35% (increased by 15%)
- 2:30 PM: 20% (decreased by 5%)
- 2:15 PM: 25% (initial setting)
- 2:00 PM: 0% (reverb added)"
```

## Storage and Persistence

### Database Schema
```sql
-- Change history table
CREATE TABLE change_history (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ,
    session_id UUID,
    user_command TEXT,
    intent_json JSONB,
    before_state JSONB,
    after_state JSONB,
    execution_result JSONB,
    project_context JSONB
);

-- Snapshots table
CREATE TABLE snapshots (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    timestamp TIMESTAMPTZ,
    type VARCHAR(50), -- manual, automatic, milestone
    description TEXT,
    daw_state JSONB,
    project_metadata JSONB,
    session_id UUID
);

-- Indexes for efficient querying
CREATE INDEX idx_changes_timestamp ON change_history(timestamp);
CREATE INDEX idx_changes_session ON change_history(session_id);
CREATE INDEX idx_snapshots_name ON snapshots(name);
```

### File System Backup
```
/project-states/
├── sessions/
│   └── session-uuid/
│       ├── changes/
│       │   ├── 001-increase-reverb.json
│       │   ├── 002-add-compression.json
│       │   └── 003-pan-left.json
│       └── snapshots/
│           ├── before-vocals.json
│           ├── rough-mix-v1.json
│           └── auto-save-1430.json
└── projects/
    └── project-name/
        ├── daily-snapshots/
        └── milestone-snapshots/
```

## Automatic Snapshot Triggers

### Time-Based Snapshots
- **Hourly**: Automatic project state capture
- **Session Start**: Initial project state
- **Session End**: Final project state
- **Extended Breaks**: After 30+ minutes of inactivity

### Event-Based Snapshots
- **Major Changes**: Before significant processing (> 5 parameter changes)
- **Milestone Moments**: "Starting vocal processing", "Beginning mix"
- **User Requests**: Manual snapshot creation
- **Error Recovery**: Before attempting complex operations

### Smart Snapshot Logic
- **Detect Significant Changes**: Don't snapshot minor tweaks
- **Compress Similar States**: Avoid redundant snapshots
- **Preserve Important Moments**: Keep user-named snapshots indefinitely
- **Auto-cleanup**: Remove old automatic snapshots after 30 days

## Integration with DAW Services

### Controller Service Updates
```typescript
interface VersioningService {
  // Change tracking
  recordChange(command: string, intent: Intent, beforeState: any, afterState: any): Promise<string>;

  // Undo/Redo
  undoLastChange(): Promise<void>;
  undoLastNChanges(n: number): Promise<void>;
  redoChange(): Promise<void>;

  // Snapshots
  createSnapshot(name?: string, description?: string): Promise<string>;
  restoreSnapshot(snapshotId: string): Promise<void>;
  listSnapshots(): Promise<Snapshot[]>;

  // Queries
  getChangeHistory(timeRange?: string, trackFilter?: string): Promise<Change[]>;
  compareStates(snapshotId1: string, snapshotId2: string): Promise<StateDiff>;
}
```

### NLP Service Integration
```python
# New intent types for versioning
VERSION_CONTROL_INTENTS = [
    "undo_change",           # "undo last change"
    "redo_change",           # "redo that change"
    "create_snapshot",       # "save snapshot as 'rough-mix'"
    "restore_snapshot",      # "restore to 'before-vocals'"
    "query_history",         # "what did I change?"
    "compare_states"         # "what's different since 'snapshot-1'?"
]
```

## Benefits of This Architecture

### For Users
- **Confidence**: Experiment freely knowing changes can be undone
- **Workflow**: Save states at important milestones
- **Learning**: Review what changes improved/worsened the mix
- **Recovery**: Restore from accidental changes or experiments

### For Development
- **Debugging**: Track exact parameter changes for troubleshooting
- **Analytics**: Understand user mixing patterns and workflows
- **Testing**: Compare before/after states for feature validation
- **Backup**: Comprehensive project state preservation

### For Collaboration
- **Sharing**: Export/import snapshots between collaborators
- **Documentation**: Automatic change logs for project notes
- **A/B Testing**: Easy comparison between different mix approaches
- **Teaching**: Show progression of mixing decisions

## Future Enhancements

### Advanced Features
- **Branch Management**: Create alternate mix versions
- **Merge Conflicts**: Handle simultaneous changes intelligently
- **Visual Timeline**: GUI representation of change history
- **Pattern Recognition**: "You often increase reverb after adding compression"

### Integration Possibilities
- **Git-like Commands**: "git diff", "git checkout", "git merge"
- **Cloud Sync**: Backup snapshots to cloud storage
- **Collaboration**: Real-time shared project states
- **AI Suggestions**: "Your mix improved most when you..."