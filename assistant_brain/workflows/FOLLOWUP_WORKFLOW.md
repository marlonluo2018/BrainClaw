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
   📥 Waiting on {person}: {ask} ({days_waiting}d)
   🔄 Process: {process_step}

2. [T###](path) {Title} — {days}d stale ({priority}, threshold {threshold}d)
   📥 Waiting on {person}: {ask} ({days_waiting}d)

Draft follow-up emails? [all / pick numbers / skip]
```

**Display rules:**
- Show `📥 Waiting on` line only if `waiting_on` field exists in JSON
- Show `🔄 Process` line only if `process_step` field exists in JSON
- Sort by priority (P1 first), then by days_inactive descending (already sorted by script)

### 3. Draft Follow-up Emails

On user selection ("all", specific numbers, or task IDs):

For each selected task:

1. **Determine recipient:** Use `suggested_recipient` from JSON. If email not in JSON, look up in [`contacts.md`](../contacts.md).
2. **Determine tone:** Check recipient's role in task RACI:
   - Decision Maker → brief, outcome-focused, respect seniority
   - Process Contact → direct, reference specific step/PO/ticket number
   - External vendor → polite, reference contract/quotation/order number
   - Peer/Executor → friendly, helpful
3. **Compose email** using outlook-skill:
   ```
   py -3 "assistant_brain/skills/outlook-skill/scripts/compose.py" --to "{email}" --subject "Re: {task title}" --body "{draft}"
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

- `send` → Use outlook-skill `send-draft`
- `edit` → User modifies, then send
- `skip` → Move to next task

After sending, update task file:
- Add timeline entry: `- **{today}** [email-out] Follow-up sent to {person} re: {ask}`
- If applicable, update `## Asks > Owed to me` with note about follow-up

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
| Email Workflow | Follows same tone rules; uses outlook-skill for compose/send |
| Task Workflow | Updates task timeline after follow-up sent |
