# Email Workflow

> **ALWAYS load the email skill before executing any email operation.**
> Load by: read `assistant_brain/skills/*/SKILL.md` → match by trigger keywords. Do NOT guess the folder name — glob for it.
>
> **Sync results archive:** `assistant_brain/sync_results/` — timestamped `.md` files from each sync run. Read these for entry_ids and prior output; do NOT re-fetch from outlook.

---

---

## Find Emails by Content

**Triggers:** "find emails about [topic]", "find all emails from [person]", "search for [keyword]"

**Steps:**
1. **Load skill** → Load the email skill
2. **Start narrow** → Search with a small recent window first (usually 7-14 days) using the most specific available keywords, names, IDs, geo, or exact subject fragments
3. **Widen only if needed** → If the first search does not find the email, expand the date range gradually and make the query more specific before broadening further
4. **Escalate search method** → If direct search is still noisy or incomplete, use find-thread or find-related from a confirmed result
5. **Present** → Show results with entry_id for further operations

---

## Find Thread / Conversation

**Triggers:** "find thread", "find conversation", "show whole conversation", "find replies"

**Steps:**
1. **Load skill** → Load the email skill
2. **Find thread** → Pull all emails sharing the same ConversationID
3. **Present** → Show thread chronologically, with folder markers (📥/📤)

---

## Find Related Emails

**Triggers:** "find related", "related emails", "what else is related to this", "find similar"

**Steps:**
1. **Load skill** → Load the email skill
2. **Find related** → Multi-strategy search:
   - Thread (same conversation)
   - Sender (same person within time window)
   - Keyword (shared subject terms)
3. **Present** → Show results sorted by relevance

---

## Compose New Email

> ⚠️ **MANDATORY DRAFT REVIEW:** Steps 6–8 (review → recipients → approval) are NEVER skippable.
> User saying "do it" or "yes" for the action item does NOT constitute send approval.
> Send approval = user explicitly confirms AFTER seeing the rendered draft.

**Triggers:** "draft email", "compose", "write email", "new email", "send to [person]"

**Steps:**
1. **Load skill** → Load the email skill
2. **Verify recipients** → For EVERY recipient email address, run `lookup-contact` to confirm correctness. Never assume or guess an email address — even if it appears in a task file or memory.
3. **Check stakeholder** → Look up recipient in [`contacts.md`](../contacts.md)
4. **Draft** → Apply tone based on stakeholder type (see table below). No signature or name in closing — Outlook auto-appends it.
5. **Subject line** → Apply [Subject Line Rules](#subject-line-rules) — include at least one high-weight identifier from the related task.
6. **Review & suggest** → Self-review the draft (see [Review Checklist](#draft-review-checklist) below). If any improvements found, show 1-2 brief suggestions inline with the draft.
7. **Recipient review** → Show To/CC list and suggest changes (see [Recipient Review](#recipient-review) below).
8. **Present for approval** → NEVER send without user confirmation
9. **Send via --body-stdin** → Pipe HTML body via stdin: `echo "body" | py -3 ... --body-stdin`. NEVER pass body content as inline argument (shell expansion corrupts `$` signs). Non-ASCII characters (em dashes, curly quotes, etc.) are safe — the script handles UTF-8 stdin.

---

## Reply / Forward / Redirect

> ⚠️ **MANDATORY DRAFT REVIEW:** Steps 7–10 (draft → review → recipients → approval) are NEVER skippable.
> User saying "do it" or "yes" for the action item does NOT constitute send approval.
> Send approval = user explicitly confirms AFTER seeing the rendered draft.

**Triggers:** "reply", "reply all", "forward", "redirect"

### Command Selection (AI decides — do NOT ask user)

> **⚠️ The AI MUST pick the correct send command autonomously based on the decision tree below. Never present options or ask "reply or forward?" — just use the right one.**

**Decision tree:**

1. Are the desired recipients the SAME as (or a superset of) the original thread?
   - **YES** → `reply` (reply-all). Use `--to`/`--cc` to append extras.
   - **NO** → go to step 2.

2. Does the recipient need to see the thread history / prior context?
   - **YES** → `forward` (full recipient control + thread context preserved below).
   - **NO** → `compose` with `Re: {subject}` to maintain subject continuity.

3. Is this going to ONLY the original sender?
   - **YES** → `reply --only`

**Summary table:**

| Situation | Command | Why |
|-----------|---------|-----|
| Same/more recipients, continuing conversation | `reply` (reply-all) | Keeps thread + all original recipients |
| Fewer recipients, but they need thread context | `forward` | Full control over To/CC, thread visible below |
| Fewer recipients, no thread context needed | `compose` (with `Re:` subject) | Clean email, subject threading only |
| Sender only | `reply --only` | Narrows to From address |
| Entirely new people, need original context | `forward` | They see what was discussed |
| Route to different handler (preserve From) | `redirect` | Appears as if from original sender |

**Common patterns:**
- User says "email George about this" (George is on CC but not the primary) → `forward` (narrow recipients, keep context)
- User says "reply to confirm" → `reply` (same recipients)
- User says "let [new person] know" → `forward` (new person needs context)
- User says "send a fresh email to X about Y" → `compose`

**Steps:**
1. **Task context** → If the email relates to a known task, READ the task file timeline first. Identify the most recent relevant email thread (incoming or outgoing) with the target recipient. Note EntryIDs.
2. **Read email content** → Use `get-email <EntryID>` to read the actual content of the identified email(s). Understand what was said, what was asked, and what the current state of the conversation is.
3. **Decide command** → Based on the thread context:
   - Existing thread with same/more recipients → `reply` (reply-all)
   - Existing thread but narrowing recipients → `forward` or `compose`
   - No prior thread with this recipient → `compose`
4. **Confirm target email** → Before drafting, show the user which email will be replied to/forwarded:
   - **Action:** Reply All / Forward / Compose
   - **From:** {sender name}
   - **Date:** {received date}
   - **Subject:** {email subject}
   - **To/CC:** {key recipients}
   - **Thread context:** {1-line summary of what this email said/asked}

   This is critical in multi-email threads — the wrong email means wrong recipients. Wait for user confirmation before proceeding.
5. **Load skill** → Load the email skill
6. **Verify recipients** → For any NEW recipients added via `--to`/`--cc` (not already on the original email), run `lookup-contact` to confirm the address. Never guess email addresses.
7. **Check stakeholder** → Look up recipient in [`contacts.md`](../contacts.md)
8. **Draft** → Apply tone based on stakeholder type (see table below). No signature or name in closing — Outlook auto-appends it.
9. **Review & suggest** → Self-review the draft (see [Review Checklist](#draft-review-checklist) below). If any improvements found, show 1-2 brief suggestions inline with the draft.
10. **Recipient review** → Show To/CC list and suggest changes (see [Recipient Review](#recipient-review) below).
11. **Present for approval** → NEVER send without user confirmation
12. **Send via --body-stdin** → Pipe HTML body via stdin: `echo "body" | py -3 ... --body-stdin`. NEVER pass body content as inline argument (shell expansion corrupts `$` signs). Non-ASCII characters (em dashes, curly quotes, etc.) are safe — the script handles UTF-8 stdin.

**Tone Guidelines:**

| Stakeholder Type | Tone | Format |
|------------------|------|--------|
| Decision Maker (High Power) | Formal, executive | Brief (3-4 paragraphs), ROI focus |
| Influencer (Medium Power) | Professional, collaborative | Balanced detail |
| Executor (Low Power) | Clear, supportive | Detailed instructions |
| Unknown | Professional, neutral | Standard format |

---

## Subject Line Rules

**Purpose:** Outgoing subject lines carry identifiers that `email_sync.py` uses to auto-match replies back to tasks. A good subject = every future reply matches automatically.

**Rules (priority order — include the highest available):**

| Priority | Identifier | Weight in matching | Example |
| -------- | ---------- | ------------------ | ------- |
| 1 | EPD (plan row ID) | 3.0 | `[1032769] Red Hat Q3 TU Order` |
| 2 | Course code / product code | 1.5 | `DO288 Schedule Update — FNC India W5` |
| 3 | Vendor + geo | 1.0 each | `Temenos TLC — China User Setup` |
| 4 | PO / order number | 1.5 | `PO IG291921 — TU Activation` |

**Format:** `[EPD] Topic — Geo/Context` or `Code Topic — Geo` (natural reading, not machine-looking)

**When to apply:**

- **Compose:** Always — you control the subject.
- **Forward:** Prepend identifier if missing from original subject (e.g., `[1032769] Fwd: ...`).
- **Reply:** Subject is inherited — do NOT modify (replies must keep `Re:` thread intact).

---

## Draft Review Checklist

> After drafting, run through this checklist internally. If 1-2 items can be improved, show brief suggestions alongside the draft. Don't rewrite — just flag what could be better and why.

| Check | What to look for |
| ----- | ---------------- |
| **Clarity** | Is the ask / next step obvious within the first 2 sentences? |
| **Brevity** | Any sentence that can be cut without losing meaning? |
| **Tone match** | Does it match the stakeholder type from the table above? |
| **Action clarity** | Is there a clear call-to-action or next step? Who does what by when? |
| **Recipient awareness** | Are we addressing the right person for this ask? |

**Output format (shown with draft):**

```text
📧 {Operation Type} | {Thread Context}

[Draft displayed here]

💡 Suggestions:
1. {concise improvement} — {why}
2. {concise improvement} — {why}
```

**Operation Type & Thread Context (mandatory header):**

| Operation | Header format |
| --------- | ------------- |
| New email | `📧 New Email` |
| Reply | `📧 Reply-all to: {sender name}` or `📧 Reply (sender only) to: {sender name}` |
| Forward | `📧 Forward: {original subject}` |
| Redirect | `📧 Redirect: {original subject}` |

Thread context line (shown below the header for reply/forward/redirect):

```text
Thread: "{subject}" — last from {sender}, {date}
```

- Show 0-2 suggestions max. If draft is already solid, skip the suggestions section entirely.
- Never block on suggestions — always present the draft for approval regardless.
- **Draft body must be rendered as readable plain text** — never show raw HTML tags (`<p>`, `<br>`, `<strong>`, etc.) to the user. Use markdown formatting (bold, lists, line breaks) for readability. HTML is only for the `--body-stdin` pipe at send time.

---

## Recipient Review

> Shown as part of every draft presentation — BEFORE user approves sending.

**Purpose:** Catch wrong recipients before sending. On reply-all threads CC lists grow stale; on compose the right stakeholders may be missing.

**Output format (shown with every draft):**

```text
👥 Recipients:
  To: {Name} <email>, ...
  CC: {Name} <email>, ...

  💡 Suggestions: {one-line per suggestion, or "— None" if list looks correct}
```

**When to suggest changes:**

| Situation                                                                     | Suggestion                                                      |
| ----------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Someone on CC is no longer relevant to this stage                             | "Consider removing {Name} — not involved in activation step"    |
| A stakeholder from the task RACI or contacts.md is missing                    | "Consider adding {Name} to CC — {role} on this task"            |
| Reply-all includes a large DL but the message is only relevant to one person  | "Consider reply --only to {Name}"                               |
| A new recipient was added by user but not on the original thread              | "Adding {Name} — not on original thread (FYI)"                  |
| To/CC looks correct for the context                                           | "— None"                                                        |

**Rules:**

- Always show the full To/CC list — even when no changes suggested
- For reply-all: inherited recipients come from the original email; show them all
- For compose: recipients come from user instruction + contacts.md lookup
- Suggestions are advisory — user decides; never block on this

---

## Stakeholder Separation

> When drafting emails to business requesters (I-level stakeholders), do NOT name vendor contacts directly. Use role/company references instead.

| ❌ Don't | ✅ Do |
|----------|-------|
| "Kirk confirmed activations are in progress" | "Red Hat confirmed activations are in progress" |
| "Sunni sent the trainer list" | "The Red Hat team sent the trainer list" |

**Why:** Vendor contact names are internal coordination details. Exposing them to business requesters leaks the supply chain and can create unwanted direct outreach.

**Rule:** In emails to I-level stakeholders, refer to vendors by **company name** or **role** ("the vendor", "Red Hat", "the Temenos team") — never by individual name.

---

## Update Task Progress from Emails

**Triggers:** "update tasks", "update progress", "sync tasks", "update task files"

> Run this AFTER checking recent emails. Analyzes email content and updates task files with actual progress (timeline, current state, asks) — NOT email references.

**Steps:**
1. **Identify task-matched emails** → From the email summary, identify emails that indicate progress on active tasks
2. **For each task with progress:**
   - Determine what changed: PO released? Approval received? LDM assigned? Quotation received? Cancellation? New blocker?
   - Update **Timeline** → Add dated entry with tag (e.g., `[PO Released]`, `[Approval]`, `[LDM Assigned]`)
   - Update **Current State** → Mark completed checkboxes `[✅]`, advance `[⏳]` markers
   - Update **Asks** → Strike through completed "Owed to me" items, check off completed "Owed by me" items, add new asks if discovered
3. **Skip already-current tasks** → If the task file already reflects today's emails, skip it
4. **Process intelligence** → Load [`PROCESS_WORKFLOW.md`](PROCESS_WORKFLOW.md):
   - **Stale Detection**: Flag tasks exceeding threshold (P1 >3d, P2 >7d, P3 >14d) with follow-up contact
   - **Process Learning**: Compare new timeline entries against process files → flag undocumented steps
5. **⚠️ MANDATORY: Read format file** → `Read assistant_brain/formats/EMAIL_SYNC_FORMAT.md` — same format as Email Sync. Append `⚠️ Stale` and `📝 Process Observations` sections if applicable.
6. **Present summary** → Follow the format from the file loaded in step 5.

---

## Email Sync (Integrated)

**Triggers:** "email sync", "sync emails", "check email", "check new email", "check and update", "any new emails", "what's new", "show recent", "emails from [time]", "邮件同步", "同步邮件", "查看邮件", "查看新邮件"

**Days parameter:**
- Default: **1 day** (today only — designed for daily use)
- Override: user can specify days → "email sync 3", "sync emails 7 days", "邮件同步 3天"
- If user says "email sync" with no number → use 1 day

**Steps:**

1. **Fetch & Pre-Match** → Run the pipeline (single command):
   ```
   py -3 assistant_brain/skills/outlook-com-skill/scripts/outlook_skill.py find-recent --days {N} --json | py -3 assistant_brain/scripts/email_sync.py
   ```
   This outputs a compact pre-matched summary with emails already matched to tasks, noise filtered, and geo inferred. The output contains `⚡NEW` (needs processing) and `✅KNOWN` (already recorded) markers.

   **⛔ RUN-ONCE RULE:** The sync script runs ONCE per user command. The output is saved to `assistant_brain/sync_results/{timestamp}.md`. For ALL subsequent processing in this session (semantic judgment, writing to task files, presenting summary, answering questions about the sync results), READ the saved file — do NOT re-run the pipeline. Each run produces different results (new emails arrive, timestamps shift); re-running causes confusion and duplicate processing. Only run again if the user explicitly commands another sync.

2. **⚠️ MANDATORY: Read format file** → `Read assistant_brain/formats/EMAIL_SYNC_FORMAT.md` — do this NOW, before processing.

3. **Semantic Judgment** → Two-pass analysis:

   **Pass A — Validate task-matched emails:** For each `⚡NEW` task-matched email:
   - **Scope validation:** The pre-match output shows each task's Scope. Verify the email matches it. If not → move to Non-Task.
   - **Operation-type check:** Master/procurement tasks (budget, POs, vendor payments) must NOT capture individual-level operational emails (learner voucher requests, exam registrations, assignment approvals). If a "master" task captures an email about a specific person's request/approval → reassign to the person-specific task or move to Unmatched for new task creation.
   - **⚠️SCOPE? handling:** Emails flagged `⚠️SCOPE?` by the script have a detected temporal conflict. Do NOT record these to the matched task. Re-evaluate: assign to correct task, or move to Non-Task.
   - **⚠️EXCLUDED? handling:** Emails flagged `⚠️EXCLUDED?` have hit exclusion keywords from the matched task's Exclude field. This signals a likely false match — verify carefully before accepting. Default action: move to Unmatched or reassign.
   - **⚠️GENERIC handling:** Emails flagged `⚠️GENERIC` are from system/automated senders whose templates contain no identifying information. You MUST `get-email #N` to read the full body. After reading, the body must contain at least ONE explicit identifier (person name, exam code, PO number) linking to the matched task. If no explicit link → move to Non-Task or Unmatched. NEVER infer identity/details from task context.
   - **Extract signals:** Asks, decisions, deadlines from subject context.
   - For **Ambiguous** emails (confidence < 0.8): you MUST read the full email body (`get-email #N`). After reading, the body must contain at least ONE explicit identifier (person name, ID/code, PO number) linking to the matched task. If the body is generic with no identifying information → Non-Task or hold for user verification. NEVER accept an ambiguous match based on "the task is expecting this" reasoning alone.

   **Pass B — Scan Calendar & Unmatched for missed task links (MANDATORY):**
   - **Task context:** The sync output includes a "📋 Active Tasks Not Matched" section listing all active tasks (with scope, contacts, geo) that the script did NOT match to any email. Use this as your reference for cross-matching. Combined with the matched-task section above it, you have the FULL active task list.
   - Review EVERY item in the 📅 Calendar section AND the Non-Task/Unmatched section.
   - For each item: read the subject line, sender name, and any visible content. Cross-reference against ALL active task scopes, keywords, contacts, and project names from both sections.
   - If wording/content relates to an active task (e.g., subject mentions a training name, project code, person from a task's contacts, or date matching a task milestone) → reassign to that task as `⚡NEW`.
   - Do NOT passively accept the script's reject decision. The script uses keyword/contact matching only — it cannot understand semantic relationships, abbreviations, or indirect references. The AI MUST apply judgment here.
   - When in doubt, read the full email body (`get-email #N`) to confirm or rule out the match.

4. **⚠️ WRITE to task files** → For EACH confirmed task-matched `⚡NEW` email:
   - Timeline → Add dated entry with tag. **ALWAYS append `<!-- email:ENTRY_ID -->`** — no exceptions.
   - Current State → Mark completed checkboxes `[✅]`, advance `[⏳]`
   - Asks → Strike through completed items, add new asks
   - This is NOT optional. If an email indicates progress, the file MUST be updated NOW.
   - **Entry IDs:** Use the `ID:` lines from the sync output (step 1) or the saved file (shown at end of output as `📁 Saved: ...`). Do NOT re-run outlook skill to fetch IDs — they are already in the output.

   **⛔ Body-Read Rule for Timeline Summaries:**

   Before writing a timeline summary for any `[email-out]` entry, you MUST read the full email body via `get-email "<ID>"`. Outgoing email previews (150 chars) typically show only the greeting — they do NOT convey what was communicated. Never infer or guess outgoing email content from subject/preview alone.

   For `[email-in]` entries: if the subject + preview clearly convey the key action/decision/ask, you may write the summary without reading the full body. If ambiguous, read first.

   **⛔ Content-Only Rule:**

   Timeline summaries MUST describe ONLY what is explicitly stated in the email. Never fill in details (person names, exam codes, amounts) from task context when the email doesn't contain them. If an email says "please approve my request" without naming the person → write "LRT: Approval request #LIC39572 — identity unconfirmed." Do NOT mark asks as completed or update Current State unless the email explicitly names the deliverable.

   **⛔ Deduplication Rule (before writing ANY timeline entry):**

   READ the task file's existing timeline FIRST. Do NOT add an entry if:
   - An existing entry already describes the **same action/event** (same sender doing the same thing)
   - The new email is a follow-up/detail/reply in the same thread that adds no new milestone, decision, or ask
   - The semantic meaning is already captured (e.g., "delegated invite to Xiang Yi" already recorded → a second email with invite details is NOT a new event)

   **One event = one timeline entry.** Multiple emails about the same action collapse into the single entry that first captured it. Only add a new entry when the email represents a genuinely NEW event: a new decision, new deliverable, new ask, status change, or new milestone.

   **⛔ EntryID Rule (ZERO EXCEPTIONS):**

   Every timeline entry written during email sync MUST end with `<!-- email:ENTRY_ID -->`. This applies to:
   - All task-matched emails (key or not)
   - All calendar items recorded to tasks
   - All outbound emails (compose/reply/forward output `EntryID: {ID}` after sending)

   **Self-check before finishing step 4:** Count timeline entries you wrote. Count `<!-- email:` markers you wrote. If counts don't match → STOP and fix before proceeding.

   There is NO "non-key email" exemption. The entryID enables O(1) lookup for future replies and thread tracking. Missing it means broken thread continuity.

5. **Process intelligence** → Load [`PROCESS_WORKFLOW.md`](PROCESS_WORKFLOW.md) and run:
   - **Auto-Suggest**: For each updated task, match to process template → determine next step + responsible contact
   - **Stale Detection**: Flag tasks exceeding stale threshold (P1 >3d, P2 >7d, P3 >14d)
   - **Process Learning**: Compare new timeline entries against matched process files → note undocumented steps

6. **Present combined summary** → Follow the format from the file loaded in step 2. The action/wait line per task is informed by step 5's process matching.
   - **⛔ Before generating Actions/Priority Actions:** For each task, verify proposed 🎯/⏳ items against the task file's Asks and Current State. If the action is already marked completed (`[x]`, `[✅]`, `~~`, `✅` suffix), do NOT surface it as an action. New emails about already-completed work are informational, not actionable.

**Token optimization:** When user requests full email content by number (e.g. "get email #40"), use the email ID from the pre-match output. Do NOT run a new search — go directly to `get-email "<id>"`.

---

## Batch Forward

**Triggers:** "batch forward", "forward to multiple people", "mass forward"

**Steps:**
1. **Load skill** → Load the email skill
2. **Prepare CSV** → Create recipient list with "email" column
3. **Execute** → BCC-forward to all recipients
4. **Confirm** → Report batch completion

---

## Create Task from Email

**Triggers:** User approves task creation after email summary

**Steps:**
1. Follow [`TASK_WORKFLOW.md`](TASK_WORKFLOW.md) → Create Task
2. Record email reference in task file (see below)

---

## Record Email Reference in Task

**When:** After matching emails to tasks OR after sending an email (compose/reply/forward) that relates to a task. Applies to both inbound and outbound key emails.

**Gate:** Only record if the email meets the **Key Email Criteria** (defined in Email Sync step 4 above). Skip pure FYI/acknowledgement emails.

**Steps:**

1. For each confirmed key task-email match, append `<!-- email:ENTRY_ID -->` to the corresponding Timeline entry:

   ```markdown
   ## Timeline
   - **2026-03-01** [email-in] Beng PAULINO: Need your approval... <!-- email:AAA... -->
   - **2026-03-03** [email-out] Reply to Beng: confirmed approval <!-- email:BBB... -->
   ```

1. **Format:** Timeline entry line + `<!-- email:<entry_id> -->` at end of line
   - If the Timeline entry was already written (e.g., during sync), append the comment to the existing line
   - If no Timeline entry exists yet, create one with the appropriate `[email-in]`/`[email-out]` tag

1. **Extract Asks / Decisions / Deadlines** — see [Extract Email Content into Task](#extract-email-content-into-task) below

1. **When looking up task emails later:**
   - Grep the task file for `<!-- email:` to get all tracked entry_ids
   - Use email skill `get-email` for each to get current state
   - This bypasses searching entirely — O(1) email lookup

---

## Extract Email Content into Task

**When:** Right after recording an email reference (Step 3 of "Record Email Reference"). Goal: pull view-relevant signal out of email bodies into the task's structured slots so future `status`/`owed`/`waiting` queries don't need to re-read email bodies.

**Trigger:** During email sync, after writing a timeline entry with `<!-- email:ID -->` — extract asks/decisions from the email body in the same pass.

**Steps:**

1. **Get full email body** via `get-email "<entry_id>"`.

2. **Scan body for four signal types:**

| Signal | Examples (English) | Examples (Chinese) | Where to write |
|--------|--------------------|--------------------|----------------|
| **Decision** | "we'll go with vendor X", "approved", "agreed to proceed" | "决定", "批准", "确认采用" | Timeline: `[decision]` |
| **Ask owed by me** (sender wants me to do something) | "could you confirm by Fri", "please send", "need your approval" | "请确认", "麻烦发一下", "需要你批准" | Asks > Owed by me + Timeline: `[ask]` |
| **Ask owed to me** (I asked for something — usually in `[email-out]`) | "I'll wait for your reply", "please advise" | "等你回复", "请告知" | Asks > Owed to me + Timeline: `[ask]` |
| **Deadline** | "by next Monday", "due May 20", "before Q2 close" | "5月20日前", "下周一前" | Update task `**Due:**` if more specific; add Timeline: `[deadline]` |
| **Commitment by me** (sent emails — promises I made) | "I'll send the list", "will revert by", "I'll handle this" | "我会发", "周五前给", "我来处理" | Asks > Owed by me + Timeline: `[ask]` |

3. **For each extracted signal, present to user for confirmation BEFORE writing:**

   ```
   📩 Email AAA... (2026-05-10, from Prantar):
   I detected:
   • Ask owed by me: "Confirm vendor selection" [response_due: 2026-05-13]
   • Decision: "Vendor narrowed to Rhapsody + alt"

   Add these to T033? [y/n/edit]
   ```

4. **On confirmation:**
   - Append confirmed Asks to `## Asks` section in the task file (preserve `response_due` if found in email)
   - Append confirmed Timeline entries with appropriate tags (with `<!-- email:ID -->` if not already present)
   - If a deadline was extracted and the task Due date changed, update the Due field directly in the task file

5. **If user says "n":**
   - The timeline entry with `<!-- email:ID -->` already exists — no further action needed
   - The presence of the entry_id in Timeline means "already processed" (no re-prompt next time)

6. **If user says "edit":**
   - Show the proposed extraction as text the user can correct
   - Apply user's corrected version

**Extraction principles:**

- **Conservative.** When unsure whether a phrase is an ask vs. a soft suggestion, ask. False positives clutter Asks; false negatives drop on the floor.
- **Inbound vs outbound matters.** Asks in inbound emails default to "Owed by me"; asks in outbound emails ("I'll send X") are commitments by me — also "Owed by me" but with no `response_due` unless specified.
- **One signal per Timeline entry.** If an email has both a decision and an ask, write two Timeline lines.
- **Reference the email.** Each extracted Timeline entry carries the `<!-- email:ID -->` comment for traceability. Additional signal entries (e.g., a separate `[decision]` line) can reference the same ID.

**Example — full extraction:**

Email body (entry_id = `BBB123...`):
> Hi Marlon,
>
> Per our call, we'll go with Rhapsody as primary vendor. Could you confirm the procurement path with Beng by Friday May 13? Once confirmed, I'll send the SOW draft early next week.
>
> Thanks, Prantar

Extraction:

```markdown
## Asks
### Owed by me
- [ ] 2026-05-10 🎯 Beng: Confirm Rhapsody procurement path [response_due: 2026-05-13]

### Owed to me
- 2026-05-10 → Prantar: SOW draft (next week)

## Timeline
- **2026-05-10** [decision] Rhapsody chosen as primary vendor <!-- email:BBB123... -->
- **2026-05-10** [ask] Beng asked to confirm procurement path by 2026-05-13 <!-- email:BBB123... -->
- **2026-05-10** [ask] Prantar promised SOW draft early next week <!-- email:BBB123... -->
```

---

## Embedded Image Intelligence

**When:** Any email display shows `🖼 Embedded images (N): ...`

**Purpose:** Embedded images often carry key information that isn't in the email body text (approval screenshots, charts, eCards, process diagrams, signature scans). The AI should proactively flag when images likely contain actionable content.

**High-signal indicators** (advise user to check):

| Indicator | Why |
|-----------|-----|
| Subject contains: approval, 批准, confirm, 确认, quotation, 报价, invoice, contract | Image may be a scanned approval or financial document |
| Subject contains: chart, report, dashboard, data, 数据, 图表 | Image likely contains data/metrics |
| Sender is a decision maker or approver (from task RACI) | Approval screenshot or signed doc |
| Email is in "Owed to me" ask chain | Image may be the deliverable being awaited |
| Image filename contains: screenshot, scan, approval, sign, chart, report | Self-explanatory |
| Multiple embedded images in a single email | Higher chance of structured visual content |

**Action:** When any high-signal indicator matches, append to the email summary line:

```text
  💡 Embedded images may contain key info — shall I check?
```

**If user confirms:** Run `get-email "<id>"` → Read auto-saved image paths → describe content.

**Low-signal (skip advisory):** Email signatures, company logos, decorative banners (filenames like `image001.png` with size < 5 KB, or known logo patterns).

---

## Geo Detection Rules

### For output grouping (AUTHORITATIVE)

**⚠️ When an email is matched to a task, ALWAYS use the task file's `**Geo:**` field for display grouping. Never infer geo from company/brand names (e.g., PETRONAS ≠ Malaysia if task says China).**

### For email-to-task matching (search signal only)

Email-domain geo helps narrow candidate tasks during matching — it is NOT used for output grouping.

**Email domains:**
- `@ph.ibm.com` → 🇵🇭 Philippines
- `@cn.ibm.com` → 🇨🇳 China
- `@in.ibm.com` → 🇮🇳 India

**Explicit mentions:**
- "FNC China", "CIC China" → China
- "FutureNow Center Philippines", "ASEAN" → Philippines
- "CIC India" → India
