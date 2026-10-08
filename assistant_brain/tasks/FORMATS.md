# Task Formats

> Task data structures, templates, and format specifications

---

## Directory Structure
```
assistant_brain/tasks/
├── T001-xxx.md            # Active task files (scanned by dashboard.py)
└── history/               # Completed task archives
    └── YYYY-Q{n}/T0xx-xxx.md # Completed tasks grouped by quarter
```

---

## File Naming
```
T{ID}-{keyword1}-{keyword2}.md
```
- **ID**: 3-digit incrementing number (T001, T002...)
- **Source**: Auto-incremented from highest existing T-number in task files
- **Keywords**: 2-4 keywords connected with `-`

---

## Status System
|| Symbol | Status | Description |
||--------|--------|-------------|
|| 📋 | Not Started | Needs action |
|| ⏳ | In Progress | Actively working on task |
|| 🔴 | Blocked | Waiting on external dependency / Unable to proceed |
|| ✅ | Completed | Move to history/ |

Flow: `📋 → ⏳ → (🔴 optional) → ✅ → history/`

**Note:** 🔴 Blocked status distinguishes tasks waiting on others (blocked) from tasks being actively worked (in progress).

---

## Priority System
|| Level | Meaning |
||-------|---------|
|| P1 | High |
|| P2 | Medium |
|| P3 | Low |

---

---

## Task Template
```markdown
# T{ID}: {Title}

**Status:** 📋 Not Started
**Created:** {YYYY-MM-DD}
**Completed:** {YYYY-MM-DD or — if still active}
**Priority:** P{1-3}
**Category:** {Email/Slack/Meeting/Other}
**Geo:** {Philippines/India/China/Singapore/APAC/Global}
**Due:** {Date or TBD}
**EPD:** {Plan Row ID or —}
**Scope:** {one-line boundary: what this task covers}
**Exclude:** {what does NOT belong here, or — when there is genuinely no exclusion}
**Recurring Task ID:** {recurring task ID (e.g., R001)} (only if from recurring_tasks.md)

---

## Contacts
- **Requester:** Name (email)
- **Approver:** Name (email)

## Stakeholders

### RACI Matrix
*List stakeholders involved in this task and their role.*

| Stakeholder | Role |
|-------------|------|

**Legend:** R=Responsible, A=Accountable, C=Consulted, I=Informed

### Engagement Log

## Tags
`tag1`, `tag2`

---

## Asks
*Explicit asks/promises in either direction (action planning and commitments). View commands (`owed`, `waiting`) read this directly. Update whenever a new commitment is made or fulfilled.*
*`<!-- email:ENTRY_ID -->` markers belong on `## Timeline` lines only, not on Asks items — Asks stay clean for planning, and the timeline is where email history is looked up.*

### My Actions
- [ ] {Due: Wkd Mon DD, YYYY} 🎯 to {person}: {what}

### Waiting on Others
- {Due: Wkd Mon DD, YYYY} ⏳ {person}: {what}

> Mark items `[x]` when fulfilled (don't delete — needed for history).
> If overdue, leave as `[ ]`; the view engine compares the due date with today.

**Asks vs Current State — where does an action go?**

| Test | Goes in |
|------|---------|
| Is there a specific person/role I owe this to? (`🎯 {person}` makes sense) | **Asks > Owed by me** |
| Am I waiting on a specific person/role for this? (`⏳ {person}` makes sense) | **Asks > Owed to me** |
| It's an internal step toward task completion with no external recipient | **Current State** |

**Examples:**
- "Send notification email to I&D Sector Focals" → **Owed by me** (recipients are explicit)
- "Upload report to Box folder" → **Current State** (internal step, no one is waiting for "the upload" itself)
- "Get budget approval from Erda" → **Owed to me** (waiting on Erda)
- "Review draft before sending" → **Current State** (self-action)

**Tie-breaker:** if an action **also has a recipient who is actively waiting for it**, prefer `Owed by me` so views surface it. Current State is for steps that don't show up in cross-task views.

---

## Timeline
- **{Wkd Mon DD, YYYY}** `[tag]` {description} <!-- email:ENTRY_ID --> <!-- conversation:CONVERSATION_ID -->

> See [Timeline Tag Vocabulary](#timeline-tag-vocabulary) below for tag list.
> Email entry_ids are tracked inline via HTML comments — see [Email Tracking in Timeline](#email-tracking-in-timeline).

---

## Current State
- [ ] Todo item 1
- [ ] Todo item 2

## Notes
Notes here
```

---

## Timeline Tag Vocabulary

Timeline entries use a single tag in `[brackets]` to enable synthesis filtering.

| Tag | When to use | Used by synthesis |
|-----|-------------|-------------------|
| `[created]` | Task creation event | history reference |
| `[update]` | Generic progress update from user | digest |
| `[email-in]` | Inbound email logged (append `<!-- email:ID -->`) | digest, email extraction |
| `[email-out]` | Outbound email sent (append `<!-- email:ID -->`) | digest, commitment tracking |
| `[decision]` | Key decision made (述职 material) | digest, achievements extraction |
| `[milestone]` | Significant progress reached (述职 material) | digest, achievements extraction |
| `[delivery]` | Concrete deliverable produced (述职 material) | digest, achievements extraction |
| `[ask]` | New ask logged (mirror to Asks section above) | digest, owed |
| `[waiting]` | Started waiting on something/someone | digest, waiting |
| `[blocker]` | Hard block encountered | digest, brief |
| `[resolved]` | Blocker cleared | digest |
| `[deadline]` | New or revised deadline learned | digest, brief |
| `[slack]` | Slack message (inbound or outbound) | digest |
| `[meeting]` | Call, meeting, or live discussion | digest |

**Rule:** One tag per entry. Choose the most specific applicable tag. Always lowercase-kebab.

**Material for 述职:** `[decision]`, `[milestone]`, `[delivery]` — these are surfaced verbatim during achievement extraction.

**Legacy aliases** (recognised by scripts, do NOT use in new entries):

| Legacy tag | Maps to |
| ---------- | ------- |
| `[Email Sent]`, `[Email Forwarded]`, `[email sent]` | `[email-out]` |
| `[Email Received]`, `[Email-in]`, `[email received]` | `[email-in]` |
| `[Email]` | `[email-in]` (assume inbound unless context says otherwise) |
| `[Slack]`, `[Slack-in]`, `[Slack-out]`, `[slack-in]` | `[slack]` |
| `[Call/Meeting]`, `[Meeting]` | `[meeting]` |
| `[Update]`, `[Action]` | `[update]` |
| `[Task Created]`, `[Created]` | `[created]` |

---

### Email Tracking in Timeline

When a timeline entry corresponds to a specific email, append an HTML comment with the Outlook EntryID. When available, also preserve the Outlook ConversationID for direct thread matching:

```markdown
- **Mon Jun 09, 2026** [email-in] Tao Han → Marlon: subject here <!-- email:00000000EFB4F92F...full_entry_id --> <!-- conversation:AAQk...conversation_id -->
```

- Invisible in rendered markdown, grep-searchable for thread matching
- One `<!-- email:ID -->` per entry; multiple emails on one event = multiple comments
- Add at most one matching `<!-- conversation:ID -->` marker for each tracked email when Outlook provides it
- The email sync workflow greps for `<!-- email:` to detect existing threads (Signal 1)
- To re-read a tracked email: extract the ID, run `get-email "ENTRY_ID"`

---

## Scope & Exclude Guidelines

Two fields define task boundaries:
- **Scope** (required) — what belongs here (positive inclusion)
- **Exclude** (required field) — what does NOT belong here, even if keywords/contacts overlap; use `—` only when none applies

### Rules

- **Scope**: Always required at task creation — never leave empty
- **Exclude**: Always include the field. Record adjacent work, other phases/quarters, or overlapping tasks; use `—` only when no exclusion exists
- One line max each — answers "what emails/events belong here?" and "what doesn't?"
- When a new task overlaps an existing one (same vendor/geo/topic), sharpen BOTH Scopes and add Exclude
- Update Scope/Exclude after a sync mismatch to tighten the boundary

### How email sync uses them

- **Scope** contributes positive retrieval evidence for the semantic classifier.
- **Exclude** contributes boundary warnings and evidence that another task or workstream may own the message.
- Neither field produces a score, threshold, automatic match, or automatic rejection. The classifier reads the complete candidate task before deciding ownership.

### Examples

| Task type | Scope | Exclude |
|-----------|-------|---------|
| Procurement | `RHLS subscription procurement & activation (PO IG291921), India.` | `TU consumption notifications (→ T071); general Red Hat training operations.` |
| Time-bound | `Q3 only (Jul–Sep 2026).` | `June course deliveries (→ T060).` |
| Phase-bound | `RHLS + TU procurement & activation.` | `Course delivery notifications; exam voucher redemptions.` |
| Vendor-specific | `Temenos TLC license procurement & user onboarding, Q2 2026.` | *(none needed — no overlap)* |

### Migration from old format

Old: `**Scope:** ... NOT X. NOT Y.`
New: Split into `**Scope:**` (before NOT) + `**Exclude:**` (the NOT content without "NOT" prefix)

The script supports both formats (parses "NOT" from Scope as fallback), but new/updated tasks should use the two-field format.

---

## Tag Guidelines

- Use SPECIFIC identifiers that discriminate this task from others
- Avoid generic terms (certification, approval, email, training)
- Max 4 tags
- **Good discriminators:** EPD numbers (`1032769`), course codes (`DO288`, `AI267`), vendor names (`Red Hat`, `Temenos`), geo (`FNC India`, `Philippines`), PO numbers (`IG291921`), quarter+scope (`Q3 2026`)
- **Why:** Tags help retrieve plausible tasks for semantic review. They are evidence only and never auto-assign an email to a task.

---

## Validation

Run `py -3 assistant_brain/scripts/validate_tasks.py` to validate active task files against `assistant_brain/formats/task_file.schema.json`. CI validates the sanitized fixture set. Missing required headers/sections, placeholder Scope, invalid tag counts, filename/heading ID mismatch, and malformed contact emails are errors; legacy email timeline entries without ConversationID are warnings.

Every structured update must include a five-part `matching_review` audit for Scope, Exclude, Tags, Contacts, and Identifiers. The deterministic updater accepts `checked-no-change`, `updated`, or `not-applicable` for each part.

---

## Master-Subtask Organization
- **Master task**: Complex task with subtasks → "(Master)" in title
- **Subtask**: Component task → "Parent Task: TXXX" field
- **Listing**: Subtasks appear indented under master in dashboard views