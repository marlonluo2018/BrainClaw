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

### 3. Draft

**Choose the command yourself** — the user shouldn't need to know Outlook internals. Compare the source To/CC with the intended recipients:

| Situation | Command |
|-----------|---------|
| Same recipients, or adding people | `reply` (reply-all) |
| Sender only | `reply --only` |
| Some inherited recipients must be removed or replaced, keep the thread | `redirect` |
| New audience that needs the thread as context | `forward` (add `--no-attachments` for heavy/irrelevant attachments) |
| No thread context needed | `compose` (with `Re:` subject if continuing a topic) |

Adding one person to an ongoing discussion is a `reply`; use `redirect` only when `get-email` shows someone must be dropped. If the user names a command, check it can do what they asked; if not, explain and ask before substituting.

**Body:**
- Don't repeat facts, numbers, dates, course names, budgets, or plan rows already in the thread — the recipients can see them. Say only the new question, update, or ask.
- Tone by recipient role from `contacts.md`: decision makers — formal, bottom line first; executors — action-first, numbered; colleagues — collaborative; unknown — neutral.
- In emails to business requesters (Informed stakeholders), refer to vendors by company or role ("Red Hat", "the vendor"), not by vendor contact names — naming them invites requesters to bypass L&K.
- No closing name or signature (Outlook appends it). Plain ASCII punctuation; no emojis unless asked.

**Subject (compose/forward):** `Course/Topic — Geo/Context`, e.g. `DO188 Final Shortlist & Roster Selection — FNC India`. Prefer a course/product code, then vendor + geo, then certification name. Never put EPD numbers or Class IDs in a subject — they are internal L&K admin numbers. Replies keep the inherited `Re:` subject.

**Present the draft** with:
1. Action type and one-line reason from the recipient comparison (e.g. "reply — keeps all source recipients and adds Prantar to CC")
2. Target thread: subject, last message date/sender, EntryID
3. To/CC, marking each recipient as inherited or newly added; suggest changes if a CC seems no longer relevant, a RACI stakeholder is missing, or reply-all hits a large list for a narrow message
4. Subject
5. Body as readable text (Markdown, not raw HTML)

### 4. Send only after explicit approval of this draft

Send only when the user's latest message explicitly approves the draft you just showed ("approve and send", "同意发送"). "Do it" / "发送" before a draft exists means *start drafting*, not send. If the user asks for anything else first (e.g. "update the task file"), do that, re-present the final draft, and wait for a fresh approval. Before sending, check the draft matches every requested change and nothing extra.

**Body transport:** write the HTML body with the Write tool to a new, uniquely named file in `outbox/` (e.g. `outbox/T127-reply-20260924.html`) and pass `--body-file`. Never put body text in a shell command string: Bash/PowerShell expand `$60` into `0`. The CLI deletes the file after a successful send and keeps it on failure.

**After sending:** send commands print the Sent Items EntryID. If the email is task-related, add an `[email-out]` timeline entry with that EntryID (see Record Email in Task).

### Batch forward

Recipients come from a CSV with an `email` column and go out as BCC. Show the body plus the recipient source and count as the draft; after approval run `batch-forward` with `--body-file`.

---

## Email Sync

**Triggers:** "email sync", "sync emails", "check email", "check new email", "邮件同步", "同步邮件", "查看邮件", "查看新邮件"

Deterministic scripts fetch and apply; one classifier subagent makes the semantic decisions. The root agent does steps 1, 2, and 4.

1. **Fetch once.** **Codex execution requirement:** run `py -3 assistant_brain/scripts/run_email_sync.py [--days N]` exactly once with desktop/elevated execution directly, not the normal sandbox. Select that execution mode before starting the command; never launch it in the sandbox and retry after a timeout. This is the first step of every explicit sync request, before looking at any sync output. Lookback defaults to the time since the last successful fetch (max 30 days). An empty result is valid — continue. If it fails, stop and report the error; don't retry or fall back to an old snapshot, because the classifier would then apply stale mail. Don't run it for targeted searches, replies, or the dashboard; a new explicit sync request later gets a new fetch.
2. **Classify.** Spawn exactly one `email-classifier` subagent (SOP: `assistant_brain/agents/email-classifier.md`). It reads the snapshot, decides which task each email belongs to, writes `latest-plan.json`, runs `email_sync_apply.py` once, and returns the formatted summary. It never fetches mail and never edits task files directly.
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
