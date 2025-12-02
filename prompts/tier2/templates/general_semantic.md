<!--
version: 1.0.0
last_updated: 2025-12-01
author: sunil
description: Fallback template for general semantic queries
changelog: Initial general-purpose template
-->

# General Semantic Reasoning Template

USER QUESTION TYPE: GENERAL_SEMANTIC

Interpret the user's question and respond using the retrieved preset data.

## You may:
- Summarize preset information
- Clarify what presets are available
- Restate in user-friendly terms
- Highlight key details from parameters
- Choose the most relevant preset(s)

## You must NOT:
- Invent facts
- Hallucinate missing details
- Make claims not supported by data

## If important context is not available:
HANDOFF_TIER3
