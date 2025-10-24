# Intent Execution Flow

This document shows the end-to-end path for executing intents, from the API layer through the service modules and into the Live bridge, plus where state is updated for snapshots.

## Overview

```mermaid
flowchart LR
  subgraph Client
    A[Web Chat / HTTP Client]
  end

  subgraph API
    B[POST /intent/execute]
    C[POST /intent/query]
  end

  subgraph Services
    D[mixer_service]
    E[param_service]
    F[routing_service]
  end

  subgraph Live Bridge
    G[ableton_remote / UDP bridge]
  end

  subgraph Snapshot
    H[Value Registry]
  end

  A --> B
  A --> C
  B -->|delegate mixer| D
  B -->|delegate device param| E
  B -->|delegate routing| F
  C -->|forward| I[GET /snapshot/query]
  D -->|request_op| G
  E -->|request_op| G
  F -->|request_op| G
  D -->|write-through| H
  E -->|write-through| H
  F -->|write-through (if applicable)| H
```

## Dispatcher Responsibilities
- Minimal validation: ensure domain + field shape are plausible
- Delegate to service modules for all business logic
- Keep `/intent/query` as a forwarder to snapshot query

## Service Responsibilities
- mixer_service: track/return/master mixer + sends
- param_service: track/return device parameters, fits/labels, dependencies
- routing_service: track/return routing semantics and validation
- All services call `request_op` to reach the Live bridge and update `ValueRegistry` on success

## Indexing Policy
- Tracks: 1-based (Track 1 = 1)
- Returns: 0-based numeric or letter refs (A=0)
- Sends: 0-based
- Devices: 0-based

## Testing and Coverage
- Unit tests mock `server.services.intents.*.request_op`
- Coverage should include API dispatcher and all three service modules
```
pytest tests/test_intents.py \
  --cov=server.api.intents \
  --cov=server.services.intents.mixer_service \
  --cov=server.services.intents.param_service \
  --cov=server.services.intents.routing_service \
  --cov-report=html
```
