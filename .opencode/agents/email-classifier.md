---
description: Single-pass BrainClaw email-sync classifier - reads latest-candidates.json, semantically matches every review item to active tasks, writes latest-plan.json, and applies it once via email_sync_apply.py. Never fetches mail and never edits task files directly.
mode: subagent
---

# Email Classifier (OpenCode entrypoint)

Read `assistant_brain/agents/email-classifier.md` completely and follow it as the single authoritative SOP. Do not maintain instructions here.
