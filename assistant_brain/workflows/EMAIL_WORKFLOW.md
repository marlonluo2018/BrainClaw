# Email Workflow

> Business SOP for email operations. Global rules (Approval Policy, Draft Gate, 4-Step Email Flow, Task-First, Outlook COM Policy) live in `AGENTS.md` — apply them here, do NOT re-copy them.
>
> **ALWAYS load the email skill before executing any email operation:** read `assistant_brain/skills/outlook-com-skill/SKILL.md` for command syntax.
>
> **Sync results archive:** `assistant_brain/sync_results/` — timestamped `.md` files from each sync run. Read these for entry_ids and prior output; do NOT re-fetch from outlook.

---

## Find Emails by Content

**Triggers:** "find emails about [topic]", "find all emails from [person]", "search for [keyword]"

**Email Address Search Rule (MANDATORY):**
- If the query contains an email address (`@`), ALWAYS use `--from "<email>"` / `--to "<email>"` FIRST. Do NOT substitute keywords or display names.
- If no results in the default 7-14 day window, expand `--days` (e.g. 60/90) to search history.

**Steps:**
1. Load email skill → 2. Start narrow (7-14 days, most specific keywords) → 3. Widen `--days` only if needed → 4. Escalate to find-thread/find-related → 5. Present with entry_id.

---

## Find Thread / Find Related

**Triggers:** "find thread", "find conversation", "find replies" | "find related", "related emails", "find similar"

1. Load email skill
2. **Thread** → pull all emails sharing the same ConversationID
3. **Related** → multi-strategy: same conversation / same sender within window / shared subject terms
4. Present chronologically with folder markers (📥/📤) or sorted by relevance

---

## Reply / Forward / Redirect / Compose

> ⚠️ Apply the **Streamlined 4-Step Email Flow + Draft Gate** from `AGENTS.md` — read thread → verify recipients → draft → present for explicit approval before sending. NEVER send without a fresh, turn-specific approval.

### Command Selection (AI decides — do NOT ask user)

Analyze the original TO/CC list and intended audience, then pick autonomously:

| Situation | Command | Why |
|-----------|---------|-----|
| Same/more recipients, continuing group discussion | `reply` (reply-all) | Keeps thread + all original recipients |
| Sender only, private/narrow/simple response | `reply --only` | Narrows to From address; avoids spamming CCs |
| Complex recipient changes (prune senior leaders/stale CCs, rewrite lists) | `redirect` | Full control to overwrite recipients completely, keeps thread |
| Fewer/new recipients who need thread context | `forward` | Selectively shares context with new audience |
| Fewer recipients, no thread context needed | `compose` (with `Re:` subject) | Clean email, subject threading only |
| Route to a different handler (preserve From) | `redirect` | Appears as if from original sender |

**redirect philosophy (KEY):** `redirect` completely wipes the inherited recipient list — use it to prune decision makers once their approval is done, or hand off to a different team, while preserving the full thread below. `reply` inherits/locks recipients; `redirect` gives total `--to`/`--cc` control.

### Draft Body

- **No Redundancy Rule (from AGENTS.md):** do NOT repeat facts/numbers/dates already visible in thread history. Focus only on the new ask/question/CTA.
- **Role-Based Tone:** look up recipients in `contacts.md` → Decision Makers (formal/executive, bottom-line first) / Executors (action-first, numbered) / Colleagues (collaborative) / Unknown (neutral).
- **Stakeholder Separation (MANDATORY):** in emails to business requesters (I-level), NEVER name vendor contacts directly — use company/role references ("Red Hat", "the vendor", "the Temenos team"). Exposing vendor names leaks the supply chain and invites unwanted direct outreach.
- No signature/name in closing — Outlook auto-appends it.

### Subject Line Rules

**Purpose:** Outgoing subject identifiers let `email_sync.py` auto-match replies back to tasks.

| Priority | Identifier | Weight | Example |
|----------|-----------|--------|---------|
| 1 | EPD (plan row ID) | 3.0 | `[1032769] Red Hat Q3 TU Order` |
| 2 | Course/product code | 1.5 | `DO288 Schedule Update — FNC India W5` |
| 3 | Vendor + geo | 1.0 | `Temenos TLC — China User Setup` |
| 4 | PO / order number | 1.5 | `PO IG291921 — TU Activation` |

**Format:** `[EPD] Topic — Geo/Context` or `Code Topic — Geo`.
**When:** Compose — always. Forward — prepend identifier if missing. Reply — inherited, do NOT modify (keep `Re:` thread).

### Send Safely

> Shell-safe transport syntax (`--body-base64`, `--body-file`, `--no-attachments`) lives in `outlook-com-skill/SKILL.md` — use those command patterns there. Key rules: prefer in-memory Base64 over temp files; direct `--body` only for short single-line HTML; never pipe non-ASCII strings via stdin.

- **Forward:** add `--no-attachments` to strip heavy/irrelevant original attachments.
- Avoid emojis/decorative Unicode in business emails unless explicitly requested.

### Recipient Review (shown with every draft)

Show full To/CC list before approval. Suggest changes when: CC contains someone no longer relevant to this stage; a task RACI/contacts stakeholder is missing; reply-all hits a large DL for a narrow message (→ suggest `reply --only`); a new recipient wasn't on the original thread. Advisory only — never block on this.

---

## Email Sync (Integrated Pipeline)

**Triggers:** "email sync", "sync emails", "check email", "check new email", "邮件同步", "同步邮件", "查看邮件", "查看新邮件"

**Token optimization (MANDATORY):** do NOT run a full sync just to check one person/thread — use targeted `find --from "Name" --days N` + `get-email <id>` instead.

**Days parameter:** default 1 day (today); user can override ("email sync 3", "邮件同步 3天").

**Steps:**
1. **Pre-fetch:** `py -3 assistant_brain\scripts\run_email_sync.py --days {N} --fallback-to-existing` → outputs `assistant_brain\sync_results\latest.md`.
2. **Sub-Agent:** `task(subagent_type="email-classifier", prompt="Process latest sync results in assistant_brain/sync_results/latest.md and execute task updates")`. It semantic-matches (EPD/course codes/contacts/geo/scope), updates tasks via `update_task.py`, registers ignores via `manage_ignore_candidates.py`, and returns a summary per `assistant_brain/formats/EMAIL_SYNC_FORMAT.md`.
3. **Verify & present:** every task section must contain BOTH `Emails:` and `Actions:` — add missing `Actions:` from the task's open asks (never surface completed ones). Then present the corrected summary.

**Timeline entry rules (during sync):**
- **One event = one timeline entry.** Only add when genuinely NEW (decision/deliverable/ask/status change/milestone). Follow-ups adding nothing new are not entries.
- **EntryID MANDATORY (zero exceptions):** every timeline entry written during sync ends with `<!-- email:ENTRY_ID -->` — for all task-matched, calendar, and outbound entries. Capture the Sent Items EntryID printed by `reply`/`compose`/`forward`/`redirect`/`batch-forward`; do NOT use `--print-sent-entry-id`; report only the current send's EntryID.
- **Self-check:** count timeline entries vs `<!-- email:` markers — if they don't match, STOP and fix.

**Process intelligence:** after updates, load `PROCESS_WORKFLOW.md` → auto-suggest next step + contact, flag stale tasks (P1>3d/P2>7d/P3>14d), flag undocumented steps.

---

## Batch Forward

**Triggers:** "batch forward", "forward to multiple people", "mass forward"

1. Load email skill
2. Prepare recipient CSV (with `email` column)
3. **Draft review (from AGENTS.md):** show body + recipient source/count; NEVER send without explicit approval
4. Execute BCC-forward; use `--body-base64` for custom messages (single-line HTML → `--message`)
5. Confirm + capture EntryIDs for task timeline if task-related

---

## Record Email Reference in Task

**When:** After matching emails to tasks OR after sending a task-related email (inbound + outbound).

**Gate:** Only record key emails (new milestone/decision/ask); skip pure FYI/acknowledgement.

**Steps:**
1. Append `<!-- email:ENTRY_ID -->` to the matching Timeline entry (see example):
   ```markdown
   ## Timeline
   - **2026-03-01** [email-in] Beng PAULINO: Need your approval... <!-- email:AAA... -->
   - **2026-03-03** [email-out] Reply to Beng: confirmed approval <!-- email:BBB... -->
   ```
2. **⚠️ EntryID comments belong STRICTLY in `## Timeline`.** NEVER append them to `## Asks` items (clutters taskboard view).
3. If no Timeline entry exists yet, create one with `[email-in]`/`[email-out]` tag.
4. **Extract signal** — see below.
5. **Future lookups:** grep task file for `<!-- email:` → use `get-email` for O(1) thread lookup — bypasses searching entirely.

---

## Extract Email Content into Task

**When:** Right after recording an email reference. Pull view-relevant signal into the task so future queries don't re-read email bodies.

1. Get full body via `get-email "<entry_id>"`.
2. Scan for four signal types:

| Signal | Examples | Where to write |
|--------|----------|----------------|
| **Decision** | "approved", "agreed to proceed", "决定", "批准" | Timeline: `[decision]` |
| **Ask owed by me** (sender wants me to act) | "could you confirm by Fri", "请确认", "需要你批准" | Asks > My Actions + Timeline: `[ask]` |
| **Ask owed to me** (I asked for something) | "I'll wait for your reply", "等你回复" | Asks > Waiting on Others + Timeline: `[ask]` |
| **Deadline** | "due May 20", "5月20日前" | Task `**Due:**` + Timeline: `[deadline]` |
| **Commitment by me** (in sent emails) | "I'll send the list", "我会发", "我来处理" | Asks > My Actions + Timeline: `[ask]` |

3. Present detected signals to user for confirmation BEFORE writing (y/n/edit).
4. On confirm: append to `## Asks` + `## Timeline` (with `<!-- email:ID -->`).
5. If "n": the timeline entry already exists → no re-prompt next time (entry_id presence = processed).

**Principles:** Conservative (ask when unsure). Inbound asks → My Actions; outbound commitments → My Actions without `response_due`. One signal per timeline line. Each line carries `<!-- email:ID -->`.

---

## Embedded Image Intelligence

**When:** Any email display shows `🖼 Embedded images (N): ...`

**High-signal indicators** (advise user to check): subject contains approval/confirm/quote/invoice/contract (or 批准/确认/报价) → scanned approval/financial doc; chart/report/data (数据/图表) → metrics; sender is a decision maker/approver; email in "Owed to me" chain; filename contains screenshot/scan/approval/sign; multiple images in one email.

**Action:** append `💡 Embedded images may contain key info — shall I check?` to the summary line. If confirmed: `get-email "<id>"` → read auto-saved image paths → describe.

**Low-signal (skip):** signatures, logos, decorative banners (`image001.png` < 5 KB).

---

## Geo Detection Rules

- **For output grouping (AUTHORITATIVE):** when an email matches a task, ALWAYS use the task's `**Geo:**` field — never infer from company/brand names (e.g. PETRONAS ≠ Malaysia if task says China).
- **For email-to-task matching (search signal only):** `@ph.ibm.com` → 🇵🇭 Philippines · `@cn.ibm.com` → 🇨🇳 China · `@in.ibm.com` → 🇮🇳 India. Explicit mentions: "FNC China"/"CIC China" → China; "FutureNow Center Philippines"/"ASEAN" → Philippines; "CIC India" → India.

---

## Follow-Up on Stale Tasks

**Triggers:** "follow up", "催办", "chase", "nudge", "提醒一下" | "follow up T###", "催办 T###"

### 1. Scan stale tasks

```
py -3 assistant_brain/scripts/followup.py [--task T###]
```

Script outputs JSON: task ID, title, days inactive, priority, threshold, waiting-on info, process step, suggested recipient.

### 2. Present results

- **No stale tasks:** `✅ All tasks are active — nothing needs follow-up.`
- **Stale found** (sorted by priority then days inactive):
  ```
  ⚠️ {N} tasks need follow-up:
  1. [T###](path) {Title} — {days}d stale ({priority}, threshold {threshold}d)
     📥 Waiting on: • {person}: {ask} ({days_waiting}d)   (only if waiting_on non-empty)
     📤 I owe:      • {person}: {ask} ({days_pending}d)   (only if owed_by_me non-empty)
     🔄 Process: {process_step}                           (only if present)
  ```
- **Display rules:** `waiting_on`/`owed_by_me` are arrays — show ALL items, one bullet per ask. `suggested_recipient` is context-aware: if `action_type` = "owed_by_me", the recipient is the person I owe an action to — draft TO them.
- **Distinct signals:** "overdue" = task Due date passed (task-level) · "stale" = last Timeline entry exceeds threshold (inactivity) · "ask age" = days since a specific ask. Show stale days for the task, ask age for items. Do NOT apply task-level overdue to individual asks.

### 3. Draft follow-up emails

On user selection (all / numbers / task IDs), for each task:
0. **Read context first (MANDATORY — Task-First):** fully `Read` the task file (`assistant_brain/tasks/T###.md`) to extract Asks, Waiting-on, RACI/Contacts, and the target thread's `<!-- email:EntryID -->` from Timeline. Then `get-email <EntryID>` to read the actual thread before drafting — verify what the person owes/is owed and recipients. Never draft from JSON output alone or from memory.
1. **Recipient:** `suggested_recipient` from JSON; else look up in `contacts.md`.
2. **Tone by role** (from task RACI): Decision Maker → brief/outcome-focused · Process Contact → reference step/PO/ticket · External vendor → reference contract/order · Peer → friendly.
3. **Template:**
   ```
   Subject: Follow-up: {original subject or task title}
   Hi {first name},
   {Context — what we're waiting for, referencing specific item}
   {Time reference — "It's been {N} days since..." or "Just checking in on..."}
   {Specific ask — what action needed}
   {Closing — appropriate to tone}
   Best regards, Marlon
   ```
4. Present draft → send / edit / skip.

### 4. Send on approval + update task

- `send` → use outlook-com-skill `compose`; `edit` → modify then send; `skip` → next task.
- After sending: capture printed `EntryID`, add timeline entry `- **{today HH:mm}** [email-out]: Follow-up sent to {person} re: {ask} <!-- email:{EntryID} -->`. Follow-up emails always meet Key Email Criteria → always include EntryID.
- If applicable, note follow-up under `## Asks > Owed to me`.

### Single task mode

`follow up T###` / `催办 T###` → run `followup.py --task T###` (skip stale threshold), present info + offer to draft, then same draft → approve → send flow.
