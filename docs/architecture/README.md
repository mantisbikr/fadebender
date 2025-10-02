# Architecture Documentation

System architecture, multi-user design, and future planning.

## Files

### Multi-User & Cloud
- **[ARCHITECTURE_MULTIUSER.md](ARCHITECTURE_MULTIUSER.md)** - Multi-user architecture with cloud services
  - Cloud: Web UI, API Gateway, NLP Service, Session/Auth
  - Local: Fadebender Agent + Remote Script
  - WebSocket/WebRTC for secure connectivity
  - **Status:** Design only, Phases 3-9 not started

### Multi-DAW Support
- **[DAW-ROADMAP.md](DAW-ROADMAP.md)** - Multi-DAW support strategy
  - Current: Ableton Live focus
  - Planned: Cubase, other DAWs
  - Auto-detection and context switching
  - **Status:** Future work

### Version Control System
- **[VERSIONING-ARCHITECTURE.md](VERSIONING-ARCHITECTURE.md)** - Undo/redo and snapshot design
  - Change history tracking
  - Natural language version control
  - Snapshot management
  - **Status:** Design complete, not implemented

### Reference Data
- **[volume_map.csv](volume_map.csv)** - Volume mapping reference data

---

See [../STATUS.md](../STATUS.md) for current implementation status.
