---
description: Single-pass Email Sync Sub-Agent for BrainClaw - reads sync results, performs intelligent semantic matching, and executes task updates via update_task.py.
---

# Email Sync Sub-Agent (Claude Entry Point)

Before performing any classification, task update, ignore registration, or summary work, read `assistant_brain/agents/claude/email-classifier.md` completely and follow it as the authoritative Claude SOP.

This file exists so that Claude Code / Agent SDK can invoke the `email-classifier` subagent directly when needed. Maintain the core SOP in `assistant_brain/agents/claude/email-classifier.md`, not here.
