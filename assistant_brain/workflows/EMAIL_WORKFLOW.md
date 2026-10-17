# Email Workflow

> The single home for email rules: search, drafting and sending, email sync, recording email into tasks, and follow-ups. Command syntax lives in `assistant_brain/skills/outlook_com_skill/SKILL.md` — read it before running Outlook commands.

---

## Find Emails

**Triggers:** "find emails about [topic]", "find all emails from [person]", "search for [keyword]", "find thread", "find related"

1. If the email belongs to a task, get its EntryID from the task timeline and use `get-email <EntryID>` — no search needed.
2. Otherwise start narrow: 7–14 days, the most specific keywords. If the query contains an email address, search with `--from`/`--to` on that address first rather than a display name or keywords.
3. Widen `--days` only if nothing is found; then escalate to `find-thread` (same ConversationID) or `find-related`.
4. Present results with their EntryIDs, chronologically with 📥/📤 folder markers.

Don't run a full email sync just to check one person or thread — a targeted `find` + `get-email` is far cheaper.

`assistant_brain/sync_results/` keeps the output of the last sync run; use it to look up EntryIDs instead of re-syncing. When you quote, summarize, or reply to a specific email, read it with `get-email`.

---

## Send Flow (reply / forward / redirect / compose / batch forward / send-draft)

Every outgoing email goes through the same four steps, in order. The point is that recipients, subject, and thread state come from the actual message, not from memory or a summary.

### 1. Identify the source

- If the email relates to a task, read the full task file first and take the target EntryID from its timeline.
- If the target thread isn't clear from context (several threads with the same person/topic), check Inbox and Sent Items and prefer the latest active sub-thread; if still ambiguous, ask the user which thread to use or whether to compose new.

### 2. Read it

Read the source message or full thread with `get-email` in the current turn and note its actual To, CC, subject, and body. Never state an inherited subject or recipient list you haven't just read.

### 3. Draft, iterate, and self-review (root agent end to end)

**The root agent drafts, iterates, and reviews — no subagent in the loop.** Read the task file and `contacts.md`, apply tone rules, write the body to `outbox/T###-<topic>-YYYYMMDD.html` (taskless compose: `outbox/compose-<topic>-YYYYMMDD.html`). Iteration feedback ("shorter", "add link", "drop the EPD number") is applied by editing the file directly and re-presenting — seconds, not a subagent round-trip.

**Self-review is mandatory and format-locked, not vibes.** Before every presentation, review the draft against `assistant_brain/formats/EMAIL_REVIEW_RULEBOOK.md` — that file is the **review rulebook** (screening table, the two deliberation classes, approval-route row, severity meanings), written to be applied by whoever holds it. **Reading the rulebook is part of conducting the review, every time:** if its full text is not already in context from this session, Read it first, then review — a review performed without the rulebook in context is invalid, no matter how well the reviewer remembers it. Working the rulebook removes the drafter's blind spot: the checks are explicit, ordered, and the same every time. The review is only valid if produced in the rulebook's output format — audience classification line, scanner line, 🔴 high findings with exact quotes, 🟡 low findings, checked-clean line. A review that summarizes ("looks clean") instead of working the table is not a review. Then run `py -3 assistant_brain/scripts/screen_outgoing_body.py <file> --subject "..."` as an independent pattern check — fold its findings into the review; anything it flags that your semantic pass cleared still appears as 🟡 "scanner flag, cleared for this audience".

**The review's known limit:** pattern checks and the rulebook cover known leakage shapes (identifiers, links, deliberation phrasings, approval routes, unconfirmed numbers). Reworded or novel phrasings can slip past both — the mitigations are that you (root agent) wrote the draft and read it again line by line against the table, and the user reads the body in full before approving. If a draft touches a genuinely new situation (recipient type or information category not covered by the table) and the call is uncertain, ask the user — do not guess and do not spawn a subagent.

**🔴 High findings must be highlighted, not buried.** High findings go at the **top** of the review block with the exact quoted text and the suggested fix — and the user's approval must explicitly acknowledge them ("approve and send, keep X") before sending. Presenting a high finding below the body, or sending after silent high findings, is a breach.

Command choice is the root agent's call:

| Situation | Command |
|-----------|---------|
| Same recipients, or adding people | `reply` (reply-all) |
| Sender only | `reply --only` |
| Some inherited recipients must be removed or replaced, keep the thread | `redirect` |
| New audience that needs the thread as context | `forward` (add `--no-attachments` for heavy/irrelevant attachments) |
| No thread context needed | `compose` (with `Re:` subject if continuing a topic) |

Adding one person to an ongoing discussion is a `reply`; use `redirect` only when `get-email` shows someone must be dropped. If the user names a command, check it can do what they asked; if not, explain and ask before substituting.

**Present the draft in the two-stage flow.** Stage 1 — every draft (first or iterated) is presented as: Action Type, To/CC, Subject, the complete body (every paragraph shown in full — the user reviews by reading what is presented, so anything truncated or summarized is effectively unseen), ending with exactly two options:

> **[review]** — run the rulebook review on this draft (🔍 findings with 🔴 high items highlighted)
> **[revise]** — give feedback and iterate (stays in stage 1)

Stage 2 — after the user has requested a review at least once on this draft version, the presentation offers three options:

> **[review again]** — re-run the review on the current draft (e.g. after accepting/considering findings, or to double-check before sending)
> **[revise]** — give feedback and iterate (returns the draft to stage 1: the changed version must be reviewed again before send is offered)
> **[approve and send]** — send this reviewed draft

**Command language:** the options are always displayed in English, and the user may invoke them in either English or Chinese — treat "审查"/"review" (and "再次审查"/"review again"), "继续修改"/"修改"/"revise", and "同意发送"/"发送"/"approve and send" as the same commands. When presenting, show the English labels (optionally with the Chinese hint in parentheses when the conversation is in Chinese).

**Findings persist across iterations.** Once a review has surfaced a 🔴 or 🟡 finding, it stays visible in every subsequent presentation of that draft — with its current disposition — until it is closed one of exactly two ways: (a) the draft was actually changed so the offending text no longer exists (finding marked resolved), or (b) the user explicitly gave a reason to keep it (finding marked accepted: "X 保留 — user: <reason>"). Re-wording that doesn't remove the underlying content, or a new edit that reintroduces the same pattern, reopens the finding. Findings never silently disappear between rounds — a finding absent from a later presentation must mean it was resolved or accepted, and the presentation shows which.

"approve and send" is only a valid send authorization for a draft whose current text the user has seen reviewed. Never offer "approve and send" on a version that has not been reviewed in its current form.

### 4. Send only after a reviewed draft is explicitly approved

The send gate: the user chose "approve and send" on a draft that was presented together with its 🔍 Review in the rulebook's locked format. "Do it" / "发送" before a draft exists means *start drafting*, not send. If the user asks for anything else first (e.g. "update the task file"), do that, re-present the final draft with its review, and wait for a fresh choice. Before sending, check the draft matches every requested change and nothing extra. **Every 🔴 finding still open (not resolved, not accepted with a stated reason) when the user approves must be explicitly accepted by the approval** ("approve and send, keep X") — approval that is silent over an open high finding is not a valid send authorization.

**Body transport:** the root agent wrote the HTML body to the `outbox/` file; pass it with `--body-file`. Never put body text in a shell command string: Bash/PowerShell expand `$60` into `0`. The CLI deletes the file after a successful send and keeps it on failure.

**After sending:** send commands print the Sent Items EntryID. If the email is task-related, add an `[email-out]` timeline entry with that EntryID (see Record Email in Task).

### Batch forward

Recipients come from a CSV with an `email` column and go out as BCC. The body is drafted and reviewed like any other draft (the recipient list is the CSV audience, classified as external unless known otherwise). Show the body plus the recipient source and count as the draft; after approval run `batch-forward` with `--body-file`.

---

## Email Sync

**Triggers:** "email sync", "sync emails", "check email", "check new email", "邮件同步", "同步邮件", "查看邮件", "查看新邮件"

Deterministic scripts fetch and apply; one classifier subagent makes the semantic decisions. The root agent does steps 1, 2, and 4.

1. **Fetch once.** **Codex execution requirement:** run `py -3 assistant_brain/scripts/run_email_sync.py [--days N]` exactly once with desktop/elevated execution directly, not the normal sandbox. Select that execution mode before starting the command; never launch it in the sandbox and retry after a timeout. This is the first step of every explicit sync request, before looking at any sync output. Lookback defaults to the time since the last successful fetch (max 30 days). An empty result is valid — continue. If it fails, stop and report the error; don't retry or fall back to an old snapshot, because the classifier would then apply stale mail. Don't run it for targeted searches, replies, or the dashboard; a new explicit sync request later gets a new fetch.
2. **Classify.** Spawn exactly one `email-classifier` subagent (SOP: `assistant_brain/agents/email-classifier.md`). It reads the snapshot (each email carries a ~2000-character body preview and each catalog task a `timeline_tail`, so it rarely needs per-email `get-email` or full task-file reads), decides which task each email belongs to, writes `latest-plan.json`, runs `email_sync_apply.py` once, generates the summary skeleton with `email_sync_summary.py`, fills its semantic placeholders, and returns the formatted summary. It never fetches mail and never edits task files directly.
3. The apply script validates the plan (schema, snapshot identity, every review email has an outcome, no history tasks, EntryIDs from the snapshot, one update per task+email) and writes all changes atomically, including the `<!-- email:... -->` / `<!-- conversation:... -->` markers.
4. **Relay.** Pass the classifier's summary to the user as-is. It must contain `## Email Sync Summary`, `### ✅ Priority Actions`, and `### 📋 Sync Audit — Files Modified`; if a heading is missing, send it back to the same classifier to fix.

After sync, `PROCESS_WORKFLOW.md` can suggest next steps and flag stale tasks (P1 > 3d, P2 > 7d, P3 > 14d).

---

## Record Email in Task

For task-related emails outside sync (e.g. after sending, or when the user shares one). Record only key emails — a new milestone, decision, ask, deadline, or status change; skip pure FYI and acknowledgements, and don't re-record an event the timeline already has.

1. Read the full email with `get-email` — for `[email-out]` entries especially, summarize the actual body, not the subject.
2. Add one timeline entry per event, using the email's own sent/received time (not the current time), ending with `<!-- email:ENTRY_ID -->` and `<!-- conversation:CONVERSATION_ID -->` when available:
   ```markdown
   - **Tue Mar 03, 2026** [email-out] Reply to Beng: confirmed approval <!-- email:BBB... -->
   ```
   EntryID markers go on timeline lines only, never on `## Asks` items, which stay clean for planning.
3. Extract signals into the task:

| Signal | Examples | Write to |
|--------|----------|----------|
| Decision | "approved", "agreed to proceed", "批准" | Timeline `[decision]` |
| Ask owed by me | "could you confirm by Fri", "请确认" | Asks > My Actions + Timeline `[ask]` |
| Ask owed to me | "I'll wait for your reply", "等你回复" | Asks > Waiting on Others + Timeline `[ask]` |
| Commitment by me (sent mail) | "I'll send the list", "我来处理" | Asks > My Actions + Timeline `[ask]` |
| Deadline | "due May 20", "5月20日前" | `**Due:**` + Timeline `[deadline]` |

Write these without asking first, then tell the user exactly what was written (each ask, decision, deadline, field change). If the email doesn't say who is responsible for an action, ask rather than guess an owner. Follow `TASK_WORKFLOW.md` → Update Task for the metadata review and validation.

---

## Embedded Images

When an email shows `🖼 Embedded images (N)`, it may hide key content if the subject mentions approval/confirm/quote/invoice/contract (批准/确认/报价) or charts/data, the sender is an approver, or filenames look like scans/screenshots. Then add `💡 Embedded images may contain key info — shall I check?`; on yes, `get-email` saves the images and you can read them. Ignore signatures, logos, and small `image001.png`-style banners.

---

## Geo

Group output by the task's `**Geo:**` field, never by company or brand (a PETRONAS task with Geo: China belongs under China). For matching only: `@ph.ibm.com` → Philippines, `@cn.ibm.com` → China, `@in.ibm.com` → India; "FNC China"/"CIC China" → China, "FutureNow Center Philippines"/"ASEAN" → Philippines, "CIC India" → India.

---

## Follow-Up on Stale Tasks

**Triggers:** "follow up", "催办", "chase", "nudge", "提醒一下", or with a task ID ("follow up T###").

1. Run `py -3 assistant_brain/scripts/followup.py [--task T###]` (with `--task`, the stale threshold is skipped). It returns JSON: days inactive, priority, threshold, waiting-on and owed-by-me items, process step, suggested recipient.
2. Present:
   - None: `✅ All tasks are active — nothing needs follow-up.`
   - Otherwise, sorted by priority then days inactive:
     ```
     ⚠️ {N} tasks need follow-up:
     1. [T###](path) {Title} — {days}d stale ({priority}, threshold {threshold}d)
        📥 Waiting on: • {person}: {ask} ({days_waiting}d)
        📤 I owe:      • {person}: {ask} ({days_pending}d)
        🔄 Process: {process_step}
     ```
     Show every item in `waiting_on` / `owed_by_me` (omit empty lines). "Stale" is task inactivity, "overdue" is the task Due date, "ask age" is per item — don't apply a task's overdue status to individual asks. When `action_type` is `owed_by_me`, the suggested recipient is the person I owe.
3. For each task the user picks, read the task file and the target thread (`get-email` on its timeline EntryID), then draft via the Send Flow — usually a `reply` on that thread. Recipient: `suggested_recipient`, else `contacts.md`. Tone by RACI role: decision maker — brief and outcome-focused; process contact — cite the step/PO/ticket; vendor — cite the contract/order; peer — friendly. Content: what we're waiting for, how long it's been, the specific ask.
4. After an approved send, add `[email-out] Follow-up sent to {person} re: {ask}` with the printed EntryID to the timeline.
