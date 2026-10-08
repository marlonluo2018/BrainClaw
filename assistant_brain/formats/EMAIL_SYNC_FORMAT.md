# Email Sync Display Format

> Read this file right before writing an email sync or task update summary — the layout is easy to get subtly wrong from memory.

---

## Symbol Convention

- `→` = **email-in** (received)
- `←` = **email-out** (sent)
- `🎯` = **my action** (I need to do/send something)
- `⏳` = **waiting** (someone else needs to act)

---

## Template

```
## Email Sync Summary (Date Range) — N emails

### {flag} Geo Name

**[TID](path) Task Name** | Due: YYYY-MM-DD | Last activity: YYYY-MM-DD
Updated:
- Timeline: `YYYY-MM-DD [Tag]: Description`
- Ask added: `YYYY-MM-DD → Person: description`
- Ask completed: `description`
- Field: `Due: TBD → 2026-10-15`

Emails:
→ #X — Wkd Mon DD HH:MM — Sender: one-line summary
← #Y — Wkd Mon DD HH:MM — to Recipient: one-line summary

Actions:
🎯 [action I need to take] — Contact: {name} | Due in {N}d
⏳ [waiting for someone] — Contact: {name} | expected {date/timeframe}

&nbsp;

**[TID](path) Task Name** | Due: YYYY-MM-DD | Last activity: YYYY-MM-DD
Updated: no changes — already up to date.

Emails:
→ #X — Wkd Mon DD HH:MM — Sender: one-line summary

Actions:
⏳ [what I'm waiting for] — Contact: {name} | expected {date/timeframe}

### {flag} Another Geo

**[TID](path) Task Name** | Due: YYYY-MM-DD | Last activity: YYYY-MM-DD
Updated:
- Timeline: `YYYY-MM-DD [Tag]: Description`

Emails:
→ #X — Wkd Mon DD HH:MM — Sender: one-line summary

Actions:
🎯 [action I need to take] — Contact: {name} | Due in {N}d

---

### ❌ Non-Task Emails

**Action needed (requires user action; some are small one-offs, some are big tasks):**
→ #X — Wkd Mon DD HH:MM — Sender: brief description
  🎯/⏳ Suggested: [suggested response/action or what to wait for]
  💡 Create task? [Yes — big action needing full task tracking / No — small one-off action, handle directly without task file]

&nbsp;

→ #Y — Wkd Mon DD HH:MM — Sender: brief description
  🎯/⏳ Suggested: [suggested response/action or what to wait for]
  💡 Create task? [Yes — big action needing full task tracking / No — small one-off action, handle directly without task file]

---

### 🚫 Ignored / Filtered Emails

**Ignored Emails (Informational — read by AI and judged as requiring no action/task; taken from `latest-applied.json`):**
| # | Sender | Subject | Reason | Entry ID |
|---|--------|---------|--------|----------|
| **#A** | Sender Name | `Subject line` | Reason | `EntryID` |
| **#B** | Sender Name | `Subject line` | Reason | `EntryID` |

*How to restore ("take it back"):* `py -3 assistant_brain/scripts/manage_ignore_candidates.py restore <entry_id>` or tell the assistant "restore email #X".

**Filtered Emails (Silently filtered system noise — auto-replies, OTP passcodes, calendar reminders, generic system noise):**
- Total: {N} emails filtered by script.

---

### 📝 Process Observations (only if new findings)

- T053: "vendor confirms entity" — not in offcycle-budget-approval.md (seen 2nd time)
- T044: No process file for "China vendor training" — 3 tasks followed similar path
  🎯 Say "固化流程" to codify

---

### ⚠️ Stale Tasks (only if any exceed threshold)

- T0XX — Xd no activity | stuck at: "{process step}"
  🎯 Follow up: {contact} ({role})

---

### ✅ Priority Actions

| # | Email | Type | Task | Action | Contact | Urgency |
|---|-------|------|------|--------|---------|---------|
| 1 | #X | 🎯 | [TID](path) Task Name | action I need to take | {name} | {deadline/overdue} |
| 2 | #Y | ⏳ | [TID](path) Task Name | what I'm waiting for | {name} | ask: Xd ago |
| 3 | #Z | 🎯 | (Non-Task) | action description | {name} | {deadline/overdue} |
| 4 | — | ⏳ | [TID](path) Task Name | carryover action (no new email) | {name} | ask: Xd ago |

---

### 📋 Sync Audit — Files Modified

| File | Changes |
|------|---------|
| `tasks/T033-...md` | +Timeline 2026-06-08, +Ask My Actions, ✅ State checkbox #3 |
| `tasks/T044-...md` | +Timeline 2026-06-08 (with email ID) |
| `tasks/T008-...md` | no changes |

Total: X files modified, Y unchanged.
```

---

## Format Rules

1. **Geo grouping:** The `### {flag} Geo Name` sections use the task file's declared `**Geo:**` field. Never infer geo from company/brand names (e.g., PETRONAS task with Geo: China → goes under 🇨🇳 China, not 🇲🇾 ASEAN).
2. Email numbers are mandatory for ALL entries — handles for "check email #XX"
3. **Report every write.** Sync writes to task files without asking the user first, so the `Updated:` block is how the user learns what changed: list each timeline entry, each ask added/completed/removed, each decision/deadline, and each header/Tags/Contacts/RACI/Scope/Exclude/Notes change, with its actual text (from `latest-applied.json`). Never summarize as counts only.
3a. **Missing next step:** If, after apply, an open task has no open item in either `### My Actions` or `### Waiting on Others`, add a line `⚠️ No next step recorded — please tell me what this task is waiting on.` to that task's `Actions:` block. Do not invent an ask to fill the gap.
4. If a matched task required no updates, state "Updated: no changes — already up to date." — still list its Emails section
5. Each task has two sub-sections: **Emails** (→ in / ← out) then **Actions** (🎯 my action / ⏳ waiting). Use one or both action types as appropriate
   - Every task section has an `Actions:` block, including `Updated: no changes — already up to date.` It reflects the task's currently open asks from its `## Asks` section, not only emails received this run. See template lines 38–45.
   - Show only open items: check the task's `## Asks` and `## Current State`, and leave out anything marked `[x]`, `[✅]`, struck through (`~~`), or suffixed `✅`. An email about a completed action is informational; it doesn't reopen it.
6. Separate tasks with `&nbsp;` (blank spacer line) for visual clarity — no `---` horizontal rules between tasks
7. Non-Task "Action needed" items show the email with `→`/`←` prefix, then indented `🎯 Suggested:` line, then `💡 Create task?` recommendation. Separate each "Action needed" email entry with `&nbsp;` (blank spacer line) for visual clarity.
8. Email numbers are sequential across the entire summary (not per-task)
9. **Contact attribution:** The `Contact: {name}` in `🎯`/`⏳` lines is the person relevant to that specific action — NOT the task's generic primary contact. Match the person to the verb.
10. **Overdue vs ask age:** "overdue" refers to the task's Due date. When surfacing a specific ask, show the ask's age (e.g., "ask: 3d ago") separately from task overdue.
11. **Priority Actions (consolidated):** A single table of ALL **verified-open** actions — both 🎯 and ⏳ — from task-linked AND non-task emails. Order by urgency. Include the email number (`#X`) that triggered each action; use `—` for carryover actions not tied to a new email. Non-task actions show `(Non-Task)` instead of TID. **Never include an action that is already completed in the task file** (see rule 5). A new email about a completed action is NOT a new action — it is confirmation/follow-up only.
12. **Section header visibility:** Use `---` horizontal rule before `### ✅ Priority Actions` and `### ❌ Non-Task Emails`. Keep the emoji-prefixed `###` headers so sections stand out.
13. **Task creation suggestion (Non-Task):** For EACH non-task actionable email, include `💡 Create task? [Yes — {reason}]` or `[No — {reason}]`.
14. **Sync Audit:** List EVERY task file evaluated. For modified files include field-level results such as `+Timeline`, `+Ask`, `✅ State`, `Scope`, `Exclude`, `Tags`, `Contacts`, `RACI`, `EPD`, or `Notes`. Unmodified: "no changes". Never omit. The audit is rendered from `latest-applied.json`, not the intended plan.
15. **No rejected emails under tasks:** Only list emails that PASS semantic judgment under a task. Emails rejected during scope validation (wrong task, scope mismatch, irrelevant content) must NOT appear under the matched task. Move actionable or uncertain rejected matches to Non-Task review; list them under Ignored only after semantic ignore is confirmed in `latest-applied.json`. Never silently omit a relevant email or show "❌ Scope mismatch" lines under a task.
16. **Skip empty tasks:** If a task has zero valid emails after semantic judgment (all were rejected or already known with no updates), do NOT show that task in the summary at all.
17. **Ignore metadata awareness:** If `latest-candidates.json` contains items with `review_status: ignored`, treat those emails as already suppressed by `assistant_brain/sync_results/ignore_candidates.json` and do not ask the user about them again unless the user says they may be task-related and wants them restored for review.
18. **Semantic ignore only:** Never equate unmatched with ignored. Add an email to the incremental ignore pool only after the classifier affirmatively determines from its content that it is informational and requires no task or action. Ignore registrations are submitted in `latest-plan.json` and become valid only when confirmed in `latest-applied.json`; do not call the ignore manager separately during sync. List applied ignores with full Entry IDs so the user can review or restore them. Unmatched actionable or uncertain emails belong under Non-Task / unresolved review, not the ignore pool.

19. **Applied-result source of truth:** Task updates and ignored-email tables must be rendered from `assistant_brain/sync_results/latest-applied.json`. If apply failed, was rejected as stale, or the applied report does not match the current snapshot, do not present a successful sync summary.
20. **Unresolved visibility:** Every relevant email that is neither task-updated nor semantically ignored must remain visible under Non-Task Emails with a concrete action/review recommendation. Never silently drop uncertain items.
