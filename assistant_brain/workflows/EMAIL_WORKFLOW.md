# Email Workflow

> **ALWAYS load the email skill before executing any email operation.**
> Load by: read `assistant_brain/skills/*/SKILL.md` → match by trigger keywords. Do NOT guess the folder name — glob for it.
>
> **Sync results archive:** `assistant_brain/sync_results/` — timestamped `.md` files from each sync run. Read these for entry_ids and prior output; do NOT re-fetch from outlook.

---

## Outlook COM Execution Policy

Outlook COM commands require access to the interactive Outlook desktop session. In Codex, do not run Outlook-backed commands through the background sandbox first, because they commonly hang or time out.

For commands invoking `assistant_brain/skills/outlook-com-skill/scripts/outlook_skill.py` or email sync Outlook fetches, request/use desktop/elevated execution directly. This applies to email search/read/thread lookup/contact lookup and all send actions (`reply`, `compose`, `forward`, `redirect`, `batch-forward`, `send-draft`), as well as calendar actions.

Local file reads/writes, `rg`, `git diff`, task markdown updates, and non-Outlook scripts should continue using the normal sandbox unless escalation is otherwise required.

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

> ⚠️ **MANDATORY DRAFT REVIEW (RIGOROUS ENFORCEMENT):** Steps 6–8 (review → recipients → approval) are NEVER skippable.
> User saying "do it" or "yes" or asking to perform another task (like "update task file") first does NOT constitute send approval.
> Send approval MUST be explicit and specific to the draft presented in the current turn (e.g., "同意发送" / "approve and send").
> If the user asks to perform another task first, the AI MUST complete that task, re-present the draft, and wait for a fresh, explicit approval before sending. Never conflate other instructions with send approval.

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
9. **Send safely** → Use the safest in-memory body transport for the specific draft.
   - Short, single-line HTML: direct `--body` is safe because Windows command-line arguments are Unicode.
   - Long, multiline, or special-character HTML: use UTF-8 `--body-base64`. Build the current draft body in a variable, encode that exact variable, and pass the ASCII Base64 string.
   - Do not use temp body files for send operations. Do not pipe normal PowerShell strings into `--body-stdin` for non-ASCII content.
   - **Command pattern:**
     ```powershell
     $body = "{html_body}"
     $body64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($body))
     py -3 "assistant_brain/skills/outlook-com-skill/scripts/outlook_skill.py" compose --to "{recipient}" --subject "{subject}" --body-base64 $body64
     ```
   - Avoid emojis and decorative Unicode in business emails unless explicitly required by the user.

---

## Reply / Forward / Redirect

> ⚠️ **MANDATORY DRAFT REVIEW (RIGOROUS ENFORCEMENT):** Steps 7–10 (draft → review → recipients → approval) are NEVER skippable.
> User saying "do it" or "yes" or asking to perform another task (like "update task file") first does NOT constitute send approval.
> Send approval MUST be explicit and specific to the draft presented in the current turn (e.g., "同意发送" / "approve and send").
> If the user asks to perform another task first, the AI MUST complete that task, re-present the draft, and wait for a fresh, explicit approval before sending. Never conflate other instructions with send approval.

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
- **Complex recipient changes on replies (Redirect Philosophy)**: When the user wants to reply to a thread but needs complex modifications to the TO and CC list (such as removing recipients or completely overwriting who is on the thread), do NOT struggle with `reply` (which inherits and locks recipients). Instead, **use `redirect`**! It is a clean forward-based action that completely wipes out all existing recipients, allowing us to specify a fresh, custom TO/CC list while preserving the entire email body thread below.

**Steps:**

### Step 1: Get email thread / Context
1. **Task context** → If the email relates to a known task, READ the task file timeline first. Identify the most recent relevant email thread (incoming or outgoing) with the target recipient. Note EntryIDs. If no prior thread exists, prepare to compose a new email.
2. **Confirm target email** → Before proceeding, show the user which email will be replied to/forwarded (Action, From, Date, Subject, To/CC, Thread context) and wait for user confirmation.

### Step 2: Read email thread
3. **Read email content** → Always use `get-email <EntryID>` to read the actual content of the identified email(s) completely. Understand what was said, what was asked, and what the current state of the conversation is. (Zero assumptions, NO guessing).

### Step 3: Draft the email
4. **Decide command** → Autonomously select the correct command (`reply`, `forward`, `compose`, or `redirect`) based on recipient and thread context.
5. **Load skill & verify recipients** → Load the email skill. For any NEW recipients added via `--to`/`--cc`, run `lookup-contact` to confirm the address. Check stakeholder type in [`contacts.md`](../contacts.md).
6. **Compose draft** → Apply appropriate tone. Do NOT include signature.
   - **⛔ No Redundancy Rule (MANDATORY):** Analyze the thread's historical text thoroughly first. **The new body MUST NOT repeat, reiterate, or re-list any facts, numbers, dates, course names, budgets, plan rows, or other parameters that are already visible in the thread history.** Focus the draft ONLY on the new ask, new question, or new follow-up.
7. **Draft review & suggest** → Self-review the draft (see [Review Checklist](#draft-review-checklist) below). If any improvements found, show 1-2 brief suggestions inline with the draft.
8. **Recipient review** → Show full To/CC list and any suggested changes (see [Recipient Review](#recipient-review) below).

### Step 4: Send safely after explicit approval
9. **Present for approval** → Display the Draft Type, Recipients (To/CC), Subject Line, and Body (as readable plain text). NEVER send without explicit, turn-specific user confirmation.
10. **Send safely** → After receiving approval, execute the send command.
    - **Recommended (Most Robust & Shell-Safe):** Write the draft HTML body to a temporary UTF-8 file (e.g. `temp_body.html`) and pass it using `--body-file`. This is completely immune to any shell escaping, quoting, or variable expansion issues.
    - **Command pattern:**
      ```powershell
      # 1. Write the body to a temp HTML file
      # 2. Run the send command
      py -3 "assistant_brain/skills/outlook-com-skill/scripts/outlook_skill.py" {compose|reply|forward|redirect} [args] --body-file "temp_body.html"
      # 3. Delete the temp HTML file
      Remove-Item "temp_body.html"
      ```
    - **Strip Original Attachments during Forward**: If forwarding an email but you do not want to carry over any original attachments (e.g. heavy spreadsheets or zip files), append the `--no-attachments` flag to the `forward` command:
      ```powershell
      py -3 "assistant_brain/skills/outlook-com-skill/scripts/outlook_skill.py" forward <email_id> --to "<recipient>" --no-attachments --body-file "temp_body.html"
      ```
    - **Alternative (In-Memory Base64):** Build the body in a PowerShell variable, base64 encode it, and pass using `--body-base64` (uses single-quoted here-string `@' ... '@` to prevent shell variable expansion).
    - **Command pattern:**
      ```powershell
      $body = @'
      {html_body}
      '@
      $body64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($body))
      py -3 "assistant_brain/skills/outlook-com-skill/scripts/outlook_skill.py" {compose|reply|forward|redirect} [args] --body-base64 $body64
      ```
    - Avoid emojis and decorative Unicode in business emails unless explicitly required by the user.

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
| **No Redundancy** | Does the draft repeat any dates, numbers, budgets, or details already mentioned in previous emails in this thread? If so, remove them. |

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
- **Draft body must be rendered as readable plain text** — never show raw HTML tags (`<p>`, `<br>`, `<strong>`, etc.) to the user. Use markdown formatting (bold, lists, line breaks) for readability. HTML is only for the send command at send time: use direct `--body` for short single-line HTML, and use UTF-8 `--body-base64` for long/multiline bodies or any body containing special characters. Do not pipe PowerShell strings into `--body-stdin` for non-ASCII content.

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
   - Update **Asks** → Strike through completed "Waiting on Others" items, check off completed "My Actions" items, add new asks if discovered
3. **Skip already-current tasks** → If the task file already reflects today's emails, skip it
4. **Process intelligence** → Load [`PROCESS_WORKFLOW.md`](PROCESS_WORKFLOW.md):
   - **Stale Detection**: Flag tasks exceeding threshold (P1 >3d, P2 >7d, P3 >14d) with follow-up contact
   - **Process Learning**: Compare new timeline entries against process files → flag undocumented steps
5. **⚠️ MANDATORY: Read format file** → `Read assistant_brain/formats/EMAIL_SYNC_FORMAT.md` — same format as Email Sync. Append `⚠️ Stale` and `📝 Process Observations` sections if applicable.
6. **Present summary** → Follow the format from the file loaded in step 5.

---

## Email Sync (Integrated)

> ⚠️ **TOKEN OPTIMIZATION RULE (MANDATORY):** Do NOT run a full `email sync` simply to check if a specific person has replied (e.g. "Darlene replied") or to find a single thread. Global sync fetches all recent emails and pre-matches them, which consumes excessive tokens and risk rate limits. Instead, use targeted search commands like `find --from "Name" --days N` to find the exact email, and then use `get-email <id>` to retrieve its full body.

**Triggers:** "email sync", "sync emails", "check email", "check new email", "check and update", "any new emails", "what's new", "show recent", "emails from [time]", "邮件同步", "同步邮件", "查看邮件", "查看新邮件"

**Days parameter:**
- Default: **1 day** (today only — designed for daily use)
- Override: user can specify days → "email sync 3", "sync emails 7 days", "邮件同步 3天"
- If user says "email sync" with no number → use 1 day

**Steps:**

1. **Fetch & Pre-Match** → Run the stable wrapper command using desktop/elevated execution, not the background sandbox:
   ```
    py -3 assistant_brain/scripts/run_email_sync.py --days {N}
    ```
    **Recommended stable command:**
    ```powershell
    py -3 assistant_brain\scripts\run_email_sync.py --days {N} --fallback-to-existing
    ```
    This utilizes the script's default robust 90-second fetch timeout and 90-second processing timeout, while enabling automatic fallback to the existing snapshot if a connection issue occurs.
   Outlook COM can hang or fail when the agent process does not share the interactive Outlook desktop session. Do not try the sandbox first for Outlook fetches. Use desktop/elevated execution directly, continue from `assistant_brain/sync_results/latest.md` when it succeeds, and ensure failed fetches do not overwrite `latest.md` or `latest-input.json`.

   **Snapshot-only fallback:** If Outlook fetch still fails but `latest-input.json` was refreshed by a successful previous run, process that existing snapshot only:
   ```powershell
   py -3 assistant_brain\scripts\run_email_sync.py --skip-fetch --input-file assistant_brain\sync_results\latest-input.json --process-timeout 30
   ```
   This wrapper handles the BOM-safe JSON snapshot, runs `email_sync.py`, outputs a compact pre-matched summary with emails already matched to tasks, noise filtered, and geo inferred, and saves the latest raw sync result to the sync archive area. The output contains `⚡NEW` (needs processing) and `✅KNOWN` (already recorded) markers.

   **Output locations:**
   - Stable latest file: `assistant_brain/sync_results/latest.md`
   - Input snapshot used for this run: `assistant_brain/sync_results/latest-input.json`
   - Incremental default-ignore pool: `assistant_brain/sync_results/ignore_candidates.json`
   - Historical timestamped snapshots remain available when `--output-file` is omitted: `assistant_brain/sync_results/{timestamp}.md`

     **Default ignore/filter behavior:**
     - **Filtered Emails:** Pure system noise, auto-replies, OTP passcodes, calendar reminders, or generic system noise. These are filtered by scripts automatically; the email sync summary should only display the total count/number of filtered emails.
     - **Ignored Emails:** Emails not filtered by script, but read and analyzed by the AI and judged as nothing important (informational with no action/task needed). The AI must automatically register these in `ignore_candidates.json` using `manage_ignore_candidates.py add <entry_id> --reason "informational"` during the sync run. In the email sync summary, ignored emails must still be displayed with full details (subject, sender, received date) so the user can verify if the AI's judgment was correct.
     - **Non-Task Emails:** Emails requiring action that are not related to active tasks. Distinguish between small actions (handle directly/one-off, no task needed) and big actions (recommend task creation). Once a Non-Task action is completed, register its ID in `ignore_candidates.json` with reason "approved by user" or "action completed" to keep subsequent syncs clean.

**User entry points / Management commands:**
- Show current ignore pool: `py -3 assistant_brain/scripts/manage_ignore_candidates.py show`
- Add one candidate to ignore pool: `py -3 assistant_brain/scripts/manage_ignore_candidates.py add <entry_id> [--reason "reason"]`
- Restore one candidate by entry ID: `py -3 assistant_brain/scripts/manage_ignore_candidates.py restore <entry_id>`
- Restore by subject keyword: `py -3 assistant_brain/scripts/manage_ignore_candidates.py restore --subject "keyword"`

*Rule:* Any email confirmed to be unrelated to any active task and requiring no action (informational) must be automatically added to the ignore candidates file during sync processing using `manage_ignore_candidates.py add <entry_id> --reason "informational"`. This keeps subsequent sync runs clean and focused only on new, actionable work.

   **⛔ RUN-ONCE RULE:** The sync script runs ONCE per user command. After the run, treat `assistant_brain/sync_results/latest.md` as the source of truth for this sync. For ALL subsequent processing in this session (semantic judgment, writing to task files, presenting summary, answering questions about the sync results), READ the saved file — do NOT re-run the pipeline. Each run produces different results (new emails arrive, timestamps shift); re-running causes confusion and duplicate processing. Only run again if the user explicitly commands another sync.

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
   - All outbound emails. `reply`/`compose`/`forward`/`redirect` print the Sent Items EntryID by default after sending, and `batch-forward` prints `EntryID (batch N): {ID}` for each sent batch. Capture the printed EntryID(s) immediately and use them in the task timeline; do not use `--print-sent-entry-id`. In the final user-facing send result, report only the EntryID(s) from the current send command; do not compare against or repeat old EntryIDs from prior sends/tests, because task timelines should reference only the current business email.

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
3. **Draft review** → Show the batch-forward message body and recipient source/recipient count to the user. NEVER send without explicit, turn-specific approval.
4. **Execute safely** → BCC-forward to all recipients. If a custom message is included, use UTF-8 `--body-base64` for the message body; `--message` is acceptable only for short, single-line HTML. Do not use temp body files and do not pipe normal PowerShell strings into stdin for non-ASCII content.
   ```powershell
   $message = "{html_message}"
   $message64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($message))
   py -3 "assistant_brain/skills/outlook-com-skill/scripts/outlook_skill.py" batch-forward "{email_id}" "{recipients_csv}" --body-base64 $message64
   ```
5. **Confirm** → Report batch completion and capture printed EntryIDs for task timeline if task-related.

---

## Create Task from Email

**Triggers:** User approves task creation after email summary

**Steps:**
1. Follow [`TASK_WORKFLOW.md`](TASK_WORKFLOW.md) → Create Task
2. Record email reference in task file (see below)

---

## Record Email Reference in Task

**When:** After matching emails to tasks OR after sending an email (compose/reply/forward/redirect/batch-forward) that relates to a task. Applies to both inbound and outbound key emails.

**Gate:** Only record if the email meets the **Key Email Criteria** (defined in Email Sync step 4 above). Skip pure FYI/acknowledgement emails.

**Steps:**

1. For each confirmed key task-email match, append `<!-- email:ENTRY_ID -->` to the corresponding Timeline entry:

   ```markdown
   ## Timeline
   - **2026-03-01** [email-in] Beng PAULINO: Need your approval... <!-- email:AAA... -->
   - **2026-03-03** [email-out] Reply to Beng: confirmed approval <!-- email:BBB... -->
   ```

1. **Format:** Timeline entry line + `<!-- email:<entry_id> -->` at end of line.
   - ⚠️ **CRITICAL:** `<!-- email:ENTRY_ID -->` comments belong STRICTLY in the `## Timeline` section. **NEVER** append them to any items in the `## Asks` section (`My Actions` / `Waiting on Others`), as they clutter the active taskboard view.
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
| **Ask owed by me** (sender wants me to do something) | "could you confirm by Fri", "please send", "need your approval" | "请确认", "麻烦发一下", "需要你批准" | Asks > My Actions + Timeline: `[ask]` |
| **Ask owed to me** (I asked for something — usually in `[email-out]`) | "I'll wait for your reply", "please advise" | "等你回复", "请告知" | Asks > Waiting on Others + Timeline: `[ask]` |
| **Deadline** | "by next Monday", "due May 20", "before Q2 close" | "5月20日前", "下周一前" | Update task `**Due:**` if more specific; add Timeline: `[deadline]` |
| **Commitment by me** (sent emails — promises I made) | "I'll send the list", "will revert by", "I'll handle this" | "我会发", "周五前给", "我来处理" | Asks > My Actions + Timeline: `[ask]` |

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
- **Inbound vs outbound matters.** Asks in inbound emails default to "My Actions"; asks in outbound emails ("I'll send X") are commitments by me — also "My Actions" but with no `response_due` unless specified.
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
### My Actions
- [ ] 2026-05-10 🎯 Beng: Confirm Rhapsody procurement path [response_due: 2026-05-13]

### Waiting on Others
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
