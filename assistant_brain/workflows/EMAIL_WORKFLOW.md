# Email Workflow

> Business SOP for email operations. Global rules (Approval Policy, Draft Gate, 4-Step Email Flow, Task-First, Outlook COM Policy) live in `AGENTS.md` Ã¢â‚¬â€ apply them here, do NOT re-copy them.
>
> **ALWAYS load the email skill before executing any email operation:** read `assistant_brain/skills/outlook-com-skill/SKILL.md` for command syntax.
>
> **Sync results archive:** `assistant_brain/sync_results/` Ã¢â‚¬â€ timestamped `.md` files from each sync run. Read these for entry_ids and prior output; do NOT re-fetch from outlook.

---

## Find Emails by Content

**Triggers:** "find emails about [topic]", "find all emails from [person]", "search for [keyword]"

**Email Address Search Rule (MANDATORY):**
- If the query contains an email address (`@`), ALWAYS use `--from "<email>"` / `--to "<email>"` FIRST. Do NOT substitute keywords or display names.
- If no results in the default 7-14 day window, expand `--days` (e.g. 60/90) to search history.

**Steps:**
1. Load email skill Ã¢â€ â€™ 2. Start narrow (7-14 days, most specific keywords) Ã¢â€ â€™ 3. Widen `--days` only if needed Ã¢â€ â€™ 4. Escalate to find-thread/find-related Ã¢â€ â€™ 5. Present with entry_id.

---

## Find Thread / Find Related

**Triggers:** "find thread", "find conversation", "find replies" | "find related", "related emails", "find similar"

1. Load email skill
2. **Thread** Ã¢â€ â€™ pull all emails sharing the same ConversationID
3. **Related** Ã¢â€ â€™ multi-strategy: same conversation / same sender within window / shared subject terms
4. Present chronologically with folder markers (Ã°Å¸â€œÂ¥/Ã°Å¸â€œÂ¤) or sorted by relevance

---

## Reply / Forward / Redirect / Compose

> Ã¢Å¡Â Ã¯Â¸Â Apply the **Streamlined 4-Step Email Flow + Draft Gate** from `AGENTS.md` Ã¢â‚¬â€ read thread Ã¢â€ â€™ verify recipients Ã¢â€ â€™ draft Ã¢â€ â€™ present for explicit approval before sending. NEVER send without a fresh, turn-specific approval.

### Pre-Draft Evidence Checklist (Mandatory)

Before selecting a command or displaying a draft, confirm all applicable evidence has been read in the current turn:

- [ ] `EMAIL_WORKFLOW.md` and the Outlook skill `SKILL.md`
- [ ] The complete related task file (for task-related emails) Ã¢â‚¬â€ inspect `## Timeline` for `<!-- email:ENTRY_ID -->` markers
- [ ] The exact target email or thread through `get-email`
- [ ] Target Thread Disambiguation: when multiple threads exist for the same contact/topic, inspect both Inbox & Sent Items to pick the latest active sub-thread (preferring the thread explicitly referenced or sent by user)
- [ ] `contacts.md` for recipient roles and tone
- [ ] Actual source To/CC compared against the requested final To/CC

Record this decision in the draft review as two lines:
`Command rationale: reply is used because the final list retains all source recipients and adds Prantar to CC.`
`Target Thread: [Subject Line] (Last message on [Date] by [Sender], EntryID: [ID])`
Do not invent recipient lists or an inherited subject from a task timeline, sync result, or prior conversation summary.

### Command Selection (AI decides Ã¢â‚¬â€ do NOT ask user)

Analyze the original TO/CC list and intended audience, then pick autonomously:

| Situation | Command | Why |
|-----------|---------|-----|
| Same/more recipients, continuing group discussion | `reply` (reply-all) | Keeps thread + all original recipients |
| Sender only, private/narrow/simple response | `reply --only` | Narrows to From address; avoids spamming CCs |
| Complex recipient changes (prune senior leaders/stale CCs, rewrite lists) | `redirect` | Full control to overwrite recipients completely, keeps thread |
| Fewer/new recipients who need thread context | `forward` | Selectively shares context with new audience |
| Fewer recipients, no thread context needed | `compose` (with `Re:` subject) | Clean email, subject threading only |
| Route to a different handler (preserve From) | `redirect` | Appears as if from original sender |

**redirect philosophy (KEY):** `redirect` completely wipes the inherited recipient list Ã¢â‚¬â€ use it to prune decision makers once their approval is done, or hand off to a different team, while preserving the full thread below. `reply` inherits/locks recipients; `redirect` gives total `--to`/`--cc` control.

**Recipient-change safeguard:** A request to add one person to the current discussion is presumptively a `reply` action. Do not use `redirect` merely to control recipient presentation. Use `redirect` only after `get-email` confirms that at least one inherited recipient must be removed or the original recipient set must be replaced.

### Draft Body

- **No Redundancy Rule (from AGENTS.md):** do NOT repeat facts/numbers/dates already visible in thread history. Focus only on the new ask/question/CTA.
- **Role-Based Tone:** look up recipients in `contacts.md` Ã¢â€ â€™ Decision Makers (formal/executive, bottom-line first) / Executors (action-first, numbered) / Colleagues (collaborative) / Unknown (neutral).
- **Stakeholder Separation (MANDATORY):** in emails to business requesters (I-level), NEVER name vendor contacts directly Ã¢â‚¬â€ use company/role references ("Red Hat", "the vendor", "the Temenos team"). Exposing vendor names leaks the supply chain and invites unwanted direct outreach.
- No signature/name in closing Ã¢â‚¬â€ Outlook auto-appends it.

### Subject Line Rules (MANDATORY POLICY)

**Ã¢â€ºâ€ INTERNAL NUMBER PROHIBITION:** EPD numbers (plan row IDs) and Class IDs are internal L&K administrative numbers. **NEVER put EPD numbers or Class IDs in outbound email subject lines.**

| Priority | Identifier | Weight | Example |
|----------|-----------|--------|---------|
| 1 | Course / Product code | 2.0 | `DO288 Schedule Update Ã¢â‚¬â€ FNC India` |
| 2 | Vendor + Geo | 1.5 | `Red Hat Training Calendar Ã¢â‚¬â€ FNC India Q3` |
| 3 | Certification / Exam Name | 1.0 | `AWS AI Practitioner Voucher Request` |

**Format:** `Course/Topic Ã¢â‚¬â€ Geo/Context` (e.g. `DO188 Final Shortlist & Roster Selection Ã¢â‚¬â€ FNC India`).
**When:** Compose Ã¢â‚¬â€ always use clean, external-facing subjects. Forward Ã¢â‚¬â€ prepend subject if missing. Reply Ã¢â‚¬â€ inherited, do NOT modify (keep `Re:` thread).

### Send Safely

> **⚠️ SHELL-SAFE BODY POLICY (MANDATORY):**
> NEVER embed unescaped email text inside Bash or PowerShell strings (`powershell -Command "..."` or `$body = "..."`). Any dollar sign (e.g. `$60`, `$500`, `$15,000`) is parsed by Bash/PowerShell as an empty variable, causing text corruption (e.g. `$60` turning into `0`).
>
> **Mandatory execution paths for sending/replying/forwarding:**
> 1. **Python Inline Base64 (Preferred):** Use Python to encode the string into Base64 and call `outlook_skill.py --body-base64 <b64>` directly.
> 2. **Body File:** Write the body to a file in `./downloads/` and pass `--body-file "downloads/body.html"`.
> 
> Detailed transport syntax lives in `outlook-com-skill/SKILL.md`.

- **Forward:** add `--no-attachments` to strip heavy/irrelevant original attachments.
- Avoid emojis/decorative Unicode in business emails unless explicitly requested.

### Recipient Review (shown with every draft)

Show full To/CC list before approval. Suggest changes when: CC contains someone no longer relevant to this stage; a task RACI/contacts stakeholder is missing; reply-all hits a large DL for a narrow message (Ã¢â€ â€™ suggest `reply --only`); a new recipient wasn't on the original thread. Advisory only Ã¢â‚¬â€ never block on this.

The draft must also state whether every displayed recipient is inherited from the source or newly added. If this cannot be verified from the message just read, do not present the draft.

---

## Email Sync (Integrated Pipeline)

**Triggers:** "email sync", "sync emails", "check email", "check new email", "Ã©â€šÂ®Ã¤Â»Â¶Ã¥ÂÅ’Ã¦Â­Â¥", "Ã¥ÂÅ’Ã¦Â­Â¥Ã©â€šÂ®Ã¤Â»Â¶", "Ã¦Å¸Â¥Ã§Å“â€¹Ã©â€šÂ®Ã¤Â»Â¶", "Ã¦Å¸Â¥Ã§Å“â€¹Ã¦â€“Â°Ã©â€šÂ®Ã¤Â»Â¶"

**Token optimization (MANDATORY):** do NOT run a full sync just to check one person/thread Ã¢â‚¬â€ use targeted `find --from "Name" --days N` + `get-email <id>` instead.

**Days parameter:** `run_email_sync.py` auto-calculates lookback days based on `latest.md` modification age when omitted. User can override ("email sync 3", "Ã©â€šÂ®Ã¤Â»Â¶Ã¥ÂÅ’Ã¦Â­Â¥ 3Ã¥Â¤Â©").

**Steps:**
1. **Pre-fetch:** `py -3 assistant_brain\scripts\run_email_sync.py [--days N] --fallback-to-existing` Ã¢â€ â€™ outputs `assistant_brain\sync_results\latest.md`.
2. **Sub-Agent (MANDATORY ? platform-native):** Delegate the classification, task-update, and final-summary phase to **exactly one** `email-classifier` subagent. It semantic-matches EPD/course codes/contacts/geo/scope, updates tasks via `update_task.py`, registers ignores via `manage_ignore_candidates.py`, and returns the complete user-facing summary per `assistant_brain/formats/EMAIL_SYNC_FORMAT.md`.
   - **Platform agent definitions:** keep the platform-specific classifier definitions under `assistant_brain/agents/`: OpenCode at `assistant_brain/agents/opencode/email-classifier.md`, Codex at `assistant_brain/agents/codex/email-classifier.md`, and Claude at `assistant_brain/agents/claude/email-classifier.md`. Keep their shared SOP content synchronized when it changes.
   - **OpenCode:** invoke the registered `email-classifier` subagent using the existing OpenCode mechanism. Its lightweight discovery entrypoint at `.opencode/agents/email-classifier.md` must first read and follow `assistant_brain/agents/opencode/email-classifier.md`; do not maintain the full SOP in `.opencode/`.
   - **Codex:** read `assistant_brain/agents/codex/email-classifier.md`, then use Codex's native subagent mechanism to spawn exactly one subagent and instruct it to follow that file completely. This is a real delegation; do not perform the classifier work in the root agent.
   - **Claude:** invoke the `email-classifier` subagent (`.claude/agents/email-classifier.md` or via `Agent` tool with `subagent_type: "email-classifier"`), which loads and executes the authoritative SOP from `assistant_brain/agents/claude/email-classifier.md`.
   - Do not run multiple classifier subagents for one sync, because they may otherwise write the same task files concurrently.
3. **Relay exactly (MANDATORY):** The root agent MUST use the classifier's returned summary as the user-facing response, verbatim. Do not summarize, reorganize, restyle, omit sections, add commentary, or independently regenerate the output. The classifier owns all formatting, including task `Emails:` and `Actions:` blocks, ignored-email tables, priority actions, and the sync audit.
   - **Blocking handoff check:** Before relaying, confirm the classifier output contains the required `## Email Sync Summary`, `### ✅ Priority Actions`, and `### 📋 Sync Audit — Files Modified` headings. If any are missing, return the result to the **same** classifier subagent for correction; do not fix or format it in the root agent.
   - **Permitted root-agent additions:** None, except a factual execution-error notice if the sync or classifier fails before producing a summary. Do not append process advice outside the classifier's formatted output.

**Timeline entry rules (during sync):**
- **One event = one timeline entry.** Only add when genuinely NEW (decision/deliverable/ask/status change/milestone). Follow-ups adding nothing new are not entries.
- **EntryID MANDATORY (zero exceptions):** every timeline entry written during sync ends with `<!-- email:ENTRY_ID -->` Ã¢â‚¬â€ for all task-matched, calendar, and outbound entries. Capture the Sent Items EntryID printed by `reply`/`compose`/`forward`/`redirect`/`batch-forward`; do NOT use `--print-sent-entry-id`; report only the current send's EntryID.
- **Self-check:** count timeline entries vs `<!-- email:` markers Ã¢â‚¬â€ if they don't match, STOP and fix.

**Process intelligence:** after updates, load `PROCESS_WORKFLOW.md` Ã¢â€ â€™ auto-suggest next step + contact, flag stale tasks (P1>3d/P2>7d/P3>14d), flag undocumented steps.

---

## Batch Forward

**Triggers:** "batch forward", "forward to multiple people", "mass forward"

1. Load email skill
2. Prepare recipient CSV (with `email` column)
3. **Draft review (from AGENTS.md):** show body + recipient source/count; NEVER send without explicit approval
4. Execute BCC-forward; use `--body-base64` for custom messages (single-line HTML Ã¢â€ â€™ `--message`)
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
2. **Ã¢Å¡Â Ã¯Â¸Â EntryID comments belong STRICTLY in `## Timeline` (for tracking & audit history).** NEVER append them to `## Asks` items (`My Actions` / `Waiting on Others`), which are strictly for clean action planning and commitments.
3. If no Timeline entry exists yet, create one with `[email-in]`/`[email-out]` tag.
4. **Extract signal** Ã¢â‚¬â€ see below.
5. **Future lookups:** grep task file for `<!-- email:` Ã¢â€ â€™ use `get-email` for O(1) thread lookup Ã¢â‚¬â€ bypasses searching entirely.

---

## Extract Email Content into Task

**When:** Right after recording an email reference. Pull view-relevant signal into the task so future queries don't re-read email bodies.

1. Get full body via `get-email "<entry_id>"`.
2. Scan for four signal types:

| Signal | Examples | Where to write |
|--------|----------|----------------|
| **Decision** | "approved", "agreed to proceed", "Ã¥â€ Â³Ã¥Â®Å¡", "Ã¦â€°Â¹Ã¥â€¡â€ " | Timeline: `[decision]` |
| **Ask owed by me** (sender wants me to act) | "could you confirm by Fri", "Ã¨Â¯Â·Ã§Â¡Â®Ã¨Â®Â¤", "Ã©Å“â‚¬Ã¨Â¦ÂÃ¤Â½Â Ã¦â€°Â¹Ã¥â€¡â€ " | Asks > My Actions + Timeline: `[ask]` |
| **Ask owed to me** (I asked for something) | "I'll wait for your reply", "Ã§Â­â€°Ã¤Â½Â Ã¥â€ºÅ¾Ã¥Â¤Â" | Asks > Waiting on Others + Timeline: `[ask]` |
| **Deadline** | "due May 20", "5Ã¦Å“Ë†20Ã¦â€”Â¥Ã¥â€°Â" | Task `**Due:**` + Timeline: `[deadline]` |
| **Commitment by me** (in sent emails) | "I'll send the list", "Ã¦Ë†â€˜Ã¤Â¼Å¡Ã¥Ââ€˜", "Ã¦Ë†â€˜Ã¦ÂÂ¥Ã¥Â¤â€žÃ§Ââ€ " | Asks > My Actions + Timeline: `[ask]` |

3. Present detected signals to user for confirmation BEFORE writing (y/n/edit).
4. On confirm: append to `## Asks` + `## Timeline` (with `<!-- email:ID -->`).
5. If "n": the timeline entry already exists Ã¢â€ â€™ no re-prompt next time (entry_id presence = processed).

**Principles:** Conservative (ask when unsure). Inbound asks Ã¢â€ â€™ My Actions; outbound commitments Ã¢â€ â€™ My Actions without `response_due`. One signal per timeline line. Each line carries `<!-- email:ID -->`.

---

## Embedded Image Intelligence

**When:** Any email display shows `Ã°Å¸â€“Â¼ Embedded images (N): ...`

**High-signal indicators** (advise user to check): subject contains approval/confirm/quote/invoice/contract (or Ã¦â€°Â¹Ã¥â€¡â€ /Ã§Â¡Â®Ã¨Â®Â¤/Ã¦Å Â¥Ã¤Â»Â·) Ã¢â€ â€™ scanned approval/financial doc; chart/report/data (Ã¦â€¢Â°Ã¦ÂÂ®/Ã¥â€ºÂ¾Ã¨Â¡Â¨) Ã¢â€ â€™ metrics; sender is a decision maker/approver; email in "Owed to me" chain; filename contains screenshot/scan/approval/sign; multiple images in one email.

**Action:** append `Ã°Å¸â€™Â¡ Embedded images may contain key info Ã¢â‚¬â€ shall I check?` to the summary line. If confirmed: `get-email "<id>"` Ã¢â€ â€™ read auto-saved image paths Ã¢â€ â€™ describe.

**Low-signal (skip):** signatures, logos, decorative banners (`image001.png` < 5 KB).

---

## Geo Detection Rules

- **For output grouping (AUTHORITATIVE):** when an email matches a task, ALWAYS use the task's `**Geo:**` field Ã¢â‚¬â€ never infer from company/brand names (e.g. PETRONAS Ã¢â€°Â  Malaysia if task says China).
- **For email-to-task matching (search signal only):** `@ph.ibm.com` Ã¢â€ â€™ Ã°Å¸â€¡ÂµÃ°Å¸â€¡Â­ Philippines Ã‚Â· `@cn.ibm.com` Ã¢â€ â€™ Ã°Å¸â€¡Â¨Ã°Å¸â€¡Â³ China Ã‚Â· `@in.ibm.com` Ã¢â€ â€™ Ã°Å¸â€¡Â®Ã°Å¸â€¡Â³ India. Explicit mentions: "FNC China"/"CIC China" Ã¢â€ â€™ China; "FutureNow Center Philippines"/"ASEAN" Ã¢â€ â€™ Philippines; "CIC India" Ã¢â€ â€™ India.

---

## Follow-Up on Stale Tasks

**Triggers:** "follow up", "Ã¥â€šÂ¬Ã¥Å Å¾", "chase", "nudge", "Ã¦ÂÂÃ©â€ â€™Ã¤Â¸â‚¬Ã¤Â¸â€¹" | "follow up T###", "Ã¥â€šÂ¬Ã¥Å Å¾ T###"

### 1. Scan stale tasks

```
py -3 assistant_brain/scripts/followup.py [--task T###]
```

Script outputs JSON: task ID, title, days inactive, priority, threshold, waiting-on info, process step, suggested recipient.

### 2. Present results

- **No stale tasks:** `Ã¢Å“â€¦ All tasks are active Ã¢â‚¬â€ nothing needs follow-up.`
- **Stale found** (sorted by priority then days inactive):
  ```
  Ã¢Å¡Â Ã¯Â¸Â {N} tasks need follow-up:
  1. [T###](path) {Title} Ã¢â‚¬â€ {days}d stale ({priority}, threshold {threshold}d)
     Ã°Å¸â€œÂ¥ Waiting on: Ã¢â‚¬Â¢ {person}: {ask} ({days_waiting}d)   (only if waiting_on non-empty)
     Ã°Å¸â€œÂ¤ I owe:      Ã¢â‚¬Â¢ {person}: {ask} ({days_pending}d)   (only if owed_by_me non-empty)
     Ã°Å¸â€â€ž Process: {process_step}                           (only if present)
  ```
- **Display rules:** `waiting_on`/`owed_by_me` are arrays Ã¢â‚¬â€ show ALL items, one bullet per ask. `suggested_recipient` is context-aware: if `action_type` = "owed_by_me", the recipient is the person I owe an action to Ã¢â‚¬â€ draft TO them.
- **Distinct signals:** "overdue" = task Due date passed (task-level) Ã‚Â· "stale" = last Timeline entry exceeds threshold (inactivity) Ã‚Â· "ask age" = days since a specific ask. Show stale days for the task, ask age for items. Do NOT apply task-level overdue to individual asks.

### 3. Draft follow-up emails

On user selection (all / numbers / task IDs), for each task:
0. **Read context first (MANDATORY Ã¢â‚¬â€ Task-First):** fully `Read` the task file (`assistant_brain/tasks/T###.md`) to extract Asks, Waiting-on, RACI/Contacts, and the target thread's `<!-- email:EntryID -->` from Timeline. Then `get-email <EntryID>` to read the actual thread before drafting Ã¢â‚¬â€ verify what the person owes/is owed and recipients. Never draft from JSON output alone or from memory.
1. **Recipient:** `suggested_recipient` from JSON; else look up in `contacts.md`.
2. **Tone by role** (from task RACI): Decision Maker Ã¢â€ â€™ brief/outcome-focused Ã‚Â· Process Contact Ã¢â€ â€™ reference step/PO/ticket Ã‚Â· External vendor Ã¢â€ â€™ reference contract/order Ã‚Â· Peer Ã¢â€ â€™ friendly.
3. **Template:**
   ```
   Subject: Follow-up: {original subject or task title}
   Hi {first name},
   {Context Ã¢â‚¬â€ what we're waiting for, referencing specific item}
   {Time reference Ã¢â‚¬â€ "It's been {N} days since..." or "Just checking in on..."}
   {Specific ask Ã¢â‚¬â€ what action needed}
   {Closing Ã¢â‚¬â€ appropriate to tone}
   Best regards, Marlon
   ```
4. Present draft Ã¢â€ â€™ send / edit / skip.

### 4. Send on approval + update task

- `send` Ã¢â€ â€™ use outlook-com-skill `compose`; `edit` Ã¢â€ â€™ modify then send; `skip` Ã¢â€ â€™ next task.
- After sending: capture printed `EntryID`, add timeline entry `- **{today HH:mm}** [email-out]: Follow-up sent to {person} re: {ask} <!-- email:{EntryID} -->`. Follow-up emails always meet Key Email Criteria Ã¢â€ â€™ always include EntryID.
- If applicable, note follow-up under `## Asks > Owed to me`.

### Single task mode

`follow up T###` / `Ã¥â€šÂ¬Ã¥Å Å¾ T###` Ã¢â€ â€™ run `followup.py --task T###` (skip stale threshold), present info + offer to draft, then same draft Ã¢â€ â€™ approve Ã¢â€ â€™ send flow.
