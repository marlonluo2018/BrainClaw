# Email Sync Display Format

> **⚠️ MANDATORY READ:** Load this file immediately before presenting any email sync or task update summary. Do NOT present from memory.

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

**Ignored Emails (Informational — read by AI, judged as no action/task needed; auto-registered in ignore json, listed for user verification):**
- **#A** — Wkd Mon DD HH:MM — Sender: subject / brief description (Reason: informational / no action or task needed)
- **#B** — Wkd Mon DD HH:MM — Sender: subject / brief description (Reason: informational / no action or task needed)

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

1. **Geo grouping:** The `### {flag} Geo Name` sections MUST use the task file's declared `**Geo:**` field. Never infer geo from company/brand names (e.g., PETRONAS task with Geo: China → goes under 🇨🇳 China, not 🇲🇾 ASEAN).
2. Email numbers are mandatory for ALL entries — handles for "check email #XX"
3. Task File Updates must show what was written to each task file
4. If a matched task required no updates, state "Updated: no changes — already up to date." — **ALWAYS still list their Emails section**
5. Each task has two sub-sections: **Emails** (→ in / ← out) then **Actions** (🎯 my action / ⏳ waiting). Use one or both action types as appropriate
   - **⛔ Completion-Check Gate (before generating ANY 🎯/⏳ action):** READ the task file's `## Asks` section AND `### Action Items` / `## Current State`. If the proposed action corresponds to an ask or item already marked `[x]`, `[✅]`, struck through (`~~`), or appended with `✅`, do NOT include it in Actions or Priority Actions. Only surface genuinely OPEN items. An email arriving about a completed action is informational — it does NOT reopen the action.
6. Separate tasks with `&nbsp;` (blank spacer line) for visual clarity — no `---` horizontal rules between tasks
7. Non-Task "Action needed" items show the email with `→`/`←` prefix, then indented `🎯 Suggested:` line, then `💡 Create task?` recommendation. Separate each "Action needed" email entry with `&nbsp;` (blank spacer line) for visual clarity.
8. Email numbers are sequential across the entire summary (not per-task)
9. **Contact attribution:** The `Contact: {name}` in `🎯`/`⏳` lines MUST be the person relevant to THAT specific action — NOT the task's generic primary contact. Match the person to the verb.
10. **Overdue vs ask age:** "overdue" refers to the task's Due date. When surfacing a specific ask, show the ask's age (e.g., "ask: 3d ago") separately from task overdue.
11. **Priority Actions (consolidated):** A single table of ALL **verified-open** actions — both 🎯 and ⏳ — from task-linked AND non-task emails. Order by urgency. Include the email number (`#X`) that triggered each action; use `—` for carryover actions not tied to a new email. Non-task actions show `(Non-Task)` instead of TID. **Never include an action that is already completed in the task file** (see rule 5 Completion-Check Gate). A new email about a completed action is NOT a new action — it is confirmation/follow-up only.
12. **Section header visibility:** Use `---` horizontal rule before `### ✅ Priority Actions` and `### ❌ Non-Task Emails`. The `###` headers with emoji prefixes MUST be visually distinct.
13. **Task creation suggestion (Non-Task):** For EACH non-task actionable email, include `💡 Create task? [Yes — {reason}]` or `[No — {reason}]`.
14. **Sync Audit:** List EVERY task file evaluated. For modified files: `+Timeline`, `+Ask`, `✅ State`, `~~Ask struck~~`. Unmodified: "no changes". Never omit.
15. **No rejected emails under tasks:** Only list emails that PASS semantic judgment under a task. Emails rejected during scope validation (wrong task, scope mismatch, irrelevant content) must NOT appear under the matched task — move them to Non-Task "Informational" or omit entirely. Never show "❌ Scope mismatch" lines under a task.
16. **Skip empty tasks:** If a task has zero valid emails after semantic judgment (all were rejected or already known with no updates), do NOT show that task in the summary at all.
17. **Ignore metadata awareness:** If the pre-match stats show `Ignored by library: X`, treat those emails as already suppressed by `assistant_brain/sync_results/ignore_candidates.json` and do not ask the user about them again unless the user says they may be task-related and wants them restored for review.
18. **Incremental ignore candidate pool:** `assistant_brain/sync_results/ignore_candidates.json` is an incremental pool for unmatched (Non-Task) emails, not a one-run snapshot. Unmatched emails written there are skipped by subsequent `email sync` runs by default and displayed under "Ignored / Filtered Emails" for user review. Pure system noise (auto-reply, OTP, etc.) is directly filtered and skipped by the script, and is NOT stored in `ignore_candidates.json` or displayed in the summary.
