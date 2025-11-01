Instructions to Claude:
Always build in a modular fashion wherever possible
Do not build monolithic code
Do not hardcode values etc. in code. We should always use app_config or some way of configuring outside of code so we can add/modify/update without having to change the code.
Always back up the database before doing any major udpating operationa of the database.

**Multi-layer Testing Required:**
    - If a feature spans multiple layers (parser → intent_mapper → service → Live), 
    test EACH layer, not just the first one
    - Parsing tests passing ≠ feature working
    - Always trace through the full execution path manually before claiming success