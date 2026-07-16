# Follow-up Workflow

> Automated stale task detection + follow-up email drafting. Connects process awareness with email skill.

---

## Triggers

| User intent | Operation |
|-------------|-----------|
| "follow up" / "催办" / "chase" / "nudge" / "提醒一下" | Scan all stale tasks |
| "follow up T###" / "催办 T###" | Generate follow-up for specific task |

---

## Flow

### 1. Scan for Stale Tasks

Run scanner:
```
py -3 assistant_brain/scripts/followup.py [--task T###]
```

Script outputs JSON array of stale tasks with: task ID, title, days inactive, priority, threshold, waiting-on info, process step, suggested recipient.

### 2. Present Results

**If no stale tasks:**
```
✅ All tasks are active — nothing needs follow-up.
```

**If stale tasks found:**
```
⚠️ {N} tasks need follow-up:

1. [T###](path) {Title} — {days}d stale ({priority}, threshold {threshold}d)
   📥 Waiting on:
      • {person}: {ask} ({days_waiting}d)
      • {person}: {ask} ({days_waiting}d)
   🔄 Process: {process_step}

2. [T###](path) {Title} — {days}d stale ({priority}, threshold {threshold}d)
   📤 I owe:
      • {person}: {ask} ({days_pending}d)

Draft follow-up emails? [all / pick numbers / skip]
```

**Display rules:**
- `waiting_on` and `owed_by_me` are **arrays** — show ALL items, one bullet per ask
- Show `📥 Waiting on` section only if `waiting_on` array exists and is non-empty
- Show `📤 I owe` section only if `owed_by_me` array exists and is non-empty
- Show `🔄 Process` line only if `process_step` field exists in JSON
- Sort by priority (P1 first), then by days_inactive descending (already sorted by script)
- **Contact attribution:** `suggested_recipient` is context-aware: if `action_type` = "owed_by_me", the recipient is the person I owe an action to (NOT the person I'm waiting on). Draft the email TO that person.
- **Overdue vs stale vs ask age:** These are distinct signals:
  - "overdue" = task's Due date has passed (task-level)
  - "stale" = days since last Timeline entry exceeds threshold (inactivity)
  - "ask age" = days since a specific ask was created (per-ask)
  - When displaying: show stale days for the task, show ask age for specific items. Do NOT apply task-level overdue to individual asks.

### 3. Draft Follow-up Emails

On user selection ("all", specific numbers, or task IDs):

For each selected task:

1. **Determine recipient:** Use `suggested_recipient` from JSON. If email not in JSON, look up in [`contacts.md`](../contacts.md).
2. **Determine tone:** Check recipient's role in task RACI:
   - Decision Maker → brief, outcome-focused, respect seniority
   - Process Contact → direct, reference specific step/PO/ticket number
   - External vendor → polite, reference contract/quotation/order number
   - Peer/Executor → friendly, helpful
3. **Compose email** using outlook-com-skill:
   ```powershell
   py -3 "assistant_brain/skills/outlook-com-skill/scripts/outlook_skill.py" compose --to "{email}" --subject "Re: {task title}" --body "{draft}"
   ```

**Email template guidance:**

```
Subject: Follow-up: {original subject or task title}

Hi {first name},

{Context line — what we're waiting for, referencing specific item}

{Time reference — "It's been {N} days since..." or "Just checking in on..."}

{Specific ask — what action needed}

{Closing — appropriate to tone}

Best regards,
Marlon
```

4. **Present draft** to user:
```
📧 Draft for T### → {recipient}:

Subject: {subject}
To: {email}

{body}

[send / edit / skip]
```

### 4. Send on Approval

- `send` → Use outlook-com-skill `compose` (send directly after user approval)
- `edit` → User modifies, then send
- `skip` → Move to next task

After sending, update task file:
- The `compose` command outputs `EntryID: {ID}` — capture this value
- Add timeline entry with EntryID: `- **{today HH:mm}** [email-out]: Follow-up sent to {person} re: {ask} <!-- email:{EntryID} -->`
- If applicable, update `## Asks > Owed to me` with note about follow-up
- **Rule:** Follow-up emails always meet Key Email Criteria (they contain asks) — always include the EntryID

---

## Single Task Mode

When user says "follow up T###" or "催办 T###":

1. Run `py -3 assistant_brain/scripts/followup.py --task T###`
2. Skip stale threshold check (always generate result)
3. Present single task info + offer to draft email
4. Follow same draft → approve → send flow

---

## Integration Points

| System | Integration |
|--------|-------------|
| Dashboard startup | Shows stale count indicator (e.g., "⚠️ 3 tasks stale") |
| Process Workflow | Reuses process matching for step identification |
| Email Workflow | Follows same tone rules; uses outlook-com-skill for compose/send |
| Task Workflow | Updates task timeline after follow-up sent |
