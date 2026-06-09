# Email Workflow

> **ALWAYS load the email skill before executing any email operation.**
> Load by: read `assistant_brain/skills/*/SKILL.md` → match by trigger keywords. Do NOT guess the folder name — glob for it.

---

## Check Recent Emails

**Triggers:** "check email", "any new emails", "what's new", "show recent", "emails from [time]"

**Steps:**
1. **Load skill** → Load the email skill
2. **Fetch emails** → List recent emails (Inbox + Sent Items)
3. **Extract keywords & geo** → For each email, identify:
   - Keywords (names, topics, ticket IDs)
   - Geo: `@ph.ibm.com`→Philippines, `@cn.ibm.com`→China, `@in.ibm.com`→India, or explicit mentions
4. **Match tasks** → Match emails to tasks using three signals (in priority order):
   1. **Thread match (strongest):** Grep task files for `<!-- email:` comments containing a known entry_id from the same conversation thread → instant hit, skip keyword matching
   2. **Contact match (strong):** Check if sender/recipient appears in any task's `## Contacts` section → high-confidence match
   3. **Keyword + geo (fallback):** Search [`tasks/queue.md`](../tasks/queue.md) by extracted keywords + geo — **⚠️ requires scope validation (see below)**
   - If signal 1 or 2 hits, use that match even if keyword matching would suggest something else

   **⚠️ Fallback Scope Validation (MANDATORY for signal 3):**

   Keyword + geo is the weakest signal — a brand name (Red Hat, AWS, Azure) or partner name shared across unrelated workflows will produce false positives. Before accepting a fallback match:

   1. **Compare email subject/content** against the candidate task's **Scope + Title + Category + Current State** — Scope is the primary boundary check. If the task's Scope explicitly excludes the email's topic/timeframe, reject immediately without checking other fields.
   2. **Different product/service = NO match.** Examples:
      - "Red Hat exam voucher" ≠ "Red Hat Learning Subscription Procurement"
      - "AWS certification voucher" ≠ "AWS infrastructure project"
      - "Azure credits" ≠ "Azure certification exam"
   3. **If scope doesn't match → treat as Non-Task (🔴 ACTION REQUIRED)** and suggest creating a new task or finding a better match.
   4. **Never force-fit an email into a task just because they share a vendor/brand keyword.** A task is defined by its specific deliverable, not by the vendor involved.
5. **Process-aware actions** → Load [`PROCESS_WORKFLOW.md`](PROCESS_WORKFLOW.md): for each matched task, determine current process step → generate `Action:` suggestions with specific contact + step (not generic advice)
6. **Present summary** → Use format below (REQUIRED). The `Action:` line per task comes from step 5.
7. **Persist links** → After user confirms task matches, record email references in task files (see "Record Email Reference" section)

**Summary Format (REQUIRED):**
```
📧 Email Summary: [Date Range] ([N] messages)

📌 TASK-RELATED EMAILS

🇵🇭 PHILIPPINES
Task [TID](path) - Title:
- Email #X (date time) 📥Inbox/📤Sent Sender: Subject
- Action: [suggested action]

🇨🇳 CHINA
Task [TID](path) - Title:
- Email #X (date time) 📥Inbox/📤Sent Sender: Subject

🇮🇳 INDIA
🔴 ACTION REQUIRED (No Task Match)
- Email #X (date time) 📥Inbox/📤Sent Sender: Subject

📊 GEO-BASED SUMMARY
| Geo | Task-Related | Action Required | Info |
|-----|--------------|-----------------|------|
| 🇵🇭 | X tasks, Y emails | - | - |
| 🇨🇳 | X tasks, Y emails | - | - |

🎯 PRIORITY ACTIONS
1. {geo flag} {action} ([TID](path) {Full Task Name}) — {contact}. {priority}, {overdue/due info}
2. {geo flag} {action} ([TID](path) {Full Task Name}) — {contact}. {priority}, {due info}
```

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

**Triggers:** "draft email", "compose", "write email", "new email", "send to [person]"

**Steps:**
1. **Load skill** → Load the email skill
2. **Verify recipients** → For EVERY recipient email address, run `lookup-contact` to confirm correctness. Never assume or guess an email address — even if it appears in a task file or memory.
3. **Check stakeholder** → Look up recipient in [`contacts.md`](../contacts.md)
4. **Draft** → Apply tone based on stakeholder type (see table below). No signature or name in closing — Outlook auto-appends it.
5. **Review & suggest** → Self-review the draft (see [Review Checklist](#draft-review-checklist) below). If any improvements found, show 1-2 brief suggestions inline with the draft.
6. **Present for approval** → NEVER send without user confirmation

---

## Reply / Forward

**Triggers:** "reply", "reply all", "forward"

**Steps:**
1. **Load skill** → Load the email skill
2. **Get context** → Read original email (or thread if multiple emails found)
3. **Confirm target email** → Before drafting, show the user which email will be replied to/forwarded:
   - **From:** {sender name}
   - **Date:** {received date}
   - **Subject:** {email subject}
   - **To/CC:** {key recipients}
   - **Preview:** {first line of body}

   This is critical in multi-email threads — the wrong email means wrong recipients. Wait for user confirmation before proceeding.
4. **Choose reply mode:**
   - **Default: `replyall`** — keeps all original recipients, `--to`/`--cc` append
   - **Narrow: `reply`** — sender only, `--to`/`--cc` specify exact extras
5. **Verify recipients** → For any NEW recipients added via `--to`/`--cc` (not already on the original email), run `lookup-contact` to confirm the address. Never guess email addresses.
6. **Check stakeholder** → Look up recipient in [`contacts.md`](../contacts.md)
7. **Draft** → Apply tone based on stakeholder type (see table below). No signature or name in closing — Outlook auto-appends it.
8. **Review & suggest** → Self-review the draft (see [Review Checklist](#draft-review-checklist) below). If any improvements found, show 1-2 brief suggestions inline with the draft.
9. **Present for approval** → NEVER send without user confirmation

**Tone Guidelines:**

| Stakeholder Type | Tone | Format |
|------------------|------|--------|
| Decision Maker (High Power) | Formal, executive | Brief (3-4 paragraphs), ROI focus |
| Influencer (Medium Power) | Professional, collaborative | Balanced detail |
| Executor (Low Power) | Clear, supportive | Detailed instructions |
| Unknown | Professional, neutral | Standard format |

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
[Draft displayed here]

💡 Suggestions:
1. {concise improvement} — {why}
2. {concise improvement} — {why}
```

- Show 0-2 suggestions max. If draft is already solid, skip the suggestions section entirely.
- Never block on suggestions — always present the draft for approval regardless.

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
5. **Present summary** → Use format below (REQUIRED). Append `⚠️ Stale` and `📝 Process Observations` sections if applicable.

**Progress Update Summary Format:**

> Uses the same format as "Email Sync (Integrated)" — see [Combined Summary Format](#email-sync-integrated) below. Both commands produce identical output structure. Additionally includes stale alerts and process observations at the end.

---

## Email Sync (Integrated)

**Triggers:** "email sync", "sync emails", "check and update", "邮件同步", "同步邮件"

> **⚠️ KEY DIFFERENCE FROM "Check Email":** This operation **WRITES to task files directly** without asking for confirmation. "Check Email" is read-only (only shows info). Email Sync = Check + Update + Process Intelligence in one shot.

**Days parameter:**
- Default: **1 day** (today only — designed for daily use)
- Override: user can specify days → "email sync 3", "sync emails 7 days", "邮件同步 3天"
- If user says "email sync" with no number → use 1 day

**Steps:**
1. **Load skill** → Load the email skill
2. **Fetch emails** → `find-recent --days {N}` (default 1)
3. **Extract keywords & geo + Match tasks** → Same as "Check Recent Emails" steps 3-5 (thread match → contact match → keyword+geo fallback)
4. **⚠️ WRITE to task files** → For EACH task-matched email, **immediately update the task file on disk**:
   - Timeline → Add dated entry with tag. For **key emails** (see criteria below), append `<!-- email:ENTRY_ID -->` to the timeline entry.
   - Current State → Mark completed checkboxes `[✅]`, advance `[⏳]`
   - Asks → Strike through completed items, add new asks
   - This is NOT optional. If an email indicates progress, the file MUST be updated NOW.

   **Key Email Criteria (for entry_id tracking):**

   A "key" email is one that likely needs future retrieval — reply, forward, or evidence lookup. Append `<!-- email:ENTRY_ID -->` to its timeline entry if ANY of:
   - Contains an explicit **action / ask / approval / decision** (e.g., "please confirm", "approved", "decided to go with X")
   - Delivers or requests a **deliverable** (quotation, PO, document, list)
   - Is a **milestone** in the task lifecycle (kickoff, escalation, completion notice)
   - Is **likely to be replied to or forwarded** later

   Do NOT record if ALL of:
   - Pure FYI / acknowledgement ("thanks", "noted", "got it")
   - No action required by anyone
   - No information that would need to be retrieved later

   **Outbound emails:** Same Key Email Criteria applies. The `compose`/`reply`/`replyall`/`forward` commands now output `EntryID: {ID}` after sending — capture this value and append `<!-- email:ID -->` to the timeline entry. In practice, nearly all assistant-sent emails are substantial (follow-ups, requests, templates) and will meet the criteria. Only pure acknowledgements ("noted", "thanks", "got it") are exempt.
5. **Process intelligence** → Load [`PROCESS_WORKFLOW.md`](PROCESS_WORKFLOW.md) and run:
   - **Auto-Suggest**: For each updated task, match to process template → determine next step + responsible contact
   - **Stale Detection**: Flag tasks exceeding stale threshold (P1 >3d, P2 >7d, P3 >14d)
   - **Process Learning**: Compare new timeline entries against matched process files → note undocumented steps
6. **Present combined summary** → Use format below (REQUIRED). The `→ Action:` line per task is informed by step 5's process matching. The `Updated:` section MUST show what was written to each file.

**Combined Summary Format:**

> **CRITICAL:** ALL emails MUST display email numbers (#1, #80, etc.) so user can reference them later with "check email #XX".

```
## Email Sync Summary (Date Range) — N emails

### {flag} Geo Name

**[TID](path) Task Name** | Due: YYYY-MM-DD | Last activity: YYYY-MM-DD
Updated:
- Timeline: `YYYY-MM-DD [Tag]: Description`
- Ask added: `YYYY-MM-DD ← Person: description`

Emails:
- #X — YYYY-MM-DD HH:MM — Sender: one-line summary
- #Y — YYYY-MM-DD HH:MM — Sender: one-line summary

→ Action: [suggested next step] — Contact: {name} | Due in {N}d

&nbsp;

**[TID](path) Task Name** | Due: YYYY-MM-DD | Last activity: YYYY-MM-DD
Updated: no changes — already up to date.

Emails:
- #X — YYYY-MM-DD HH:MM — Sender: one-line summary

→ Action: [suggested next step] — Contact: {name} | Due in {N}d

### {flag} Another Geo

**[TID](path) Task Name** | Due: YYYY-MM-DD | Last activity: YYYY-MM-DD
Updated:
- Timeline: `YYYY-MM-DD [Tag]: Description`

Emails:
- #X — YYYY-MM-DD HH:MM — Sender: one-line summary

→ Action: [suggested next step] — Contact: {name} | Due in {N}d

### Non-Task

Action needed:
- #X — MM-DD HH:MM — Sender: brief description
  → Action: [suggested response/action]
- #Y — MM-DD HH:MM — Sender: brief description
  → Action: [suggested response/action]

Informational: #A, #B, #C, ...

### 📝 Process Observations (only if new findings)

- T053: "vendor confirms entity" — not in offcycle-budget-approval.md (seen 2nd time)
- T044: No process file for "China vendor training" — 3 tasks followed similar path
  → Say "固化流程" to codify

### ⚠️ Stale Tasks (only if any exceed threshold)

- T0XX — Xd no activity | stuck at: "{process step}"
  → Follow up: {contact} ({role})
```

**Format rules:**
1. Email numbers are mandatory for ALL entries — handles for "check email #XX"
2. Task File Updates must show what was written to each task file
3. If a matched task required no updates, state "Updated: no changes — already up to date." — **ALWAYS still list their Emails section**
4. Each task ends with `→ Action:` line suggesting the next step
5. Separate tasks with `&nbsp;` (blank spacer line) for visual clarity — no `---` horizontal rules between tasks
6. Non-Task "Action needed" items each get their own indented `→ Action:` line
7. Email numbers are sequential across the entire summary (not per-task)
8. **Contact attribution:** The `Contact: {name}` in `→ Action:` MUST be the person relevant to THAT specific action — NOT the task's generic primary contact. If action = "reply to Rajesh", contact = Rajesh. If action = "chase Kirk for update", contact = Kirk. Match the person to the verb.
9. **Overdue vs ask age:** "overdue" refers to the task's Due date. When surfacing a specific ask, show the ask's age (e.g., "ask: 3d ago") separately from task overdue. A brand-new ask on an overdue task is NOT itself overdue.

**Sync Diff Audit Summary (MANDATORY):**

Because Email Sync writes to task files autonomously, ALWAYS end the summary with a consolidated diff block showing every file modification:

```
### 📋 Sync Audit — Files Modified

| File | Changes |
|------|---------|
| `tasks/T033-...md` | +Timeline 2026-06-08, +Ask owed by me, ✅ State checkbox #3 |
| `tasks/T044-...md` | +Timeline 2026-06-08 (with email ID) |
| `tasks/T008-...md` | no changes |

Total: 2 files modified, 1 unchanged.
```

Rules:
- List EVERY task file that was evaluated, even if no changes were made
- For each modified file, summarize changes as: `+Timeline`, `+Ask`, `✅ State`, `~~Ask struck~~`
- If a file was NOT modified, show "no changes"
- This is the user's only confirmation of what was written — never omit it

**Key difference from separate commands:** Email Sync does NOT show the full geo-grouped email summary from "Check Recent Emails". It focuses on task-relevant changes and actions needed.

**Token optimization:** When user requests full email content by number (e.g. "get email #40"), use the email ID from the last search output (`find-recent`, `find`, `find-thread`, or `find-related`). Do NOT run a new search — go directly to `get-email "<id>"` using the already-returned results.

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

**When:** After matching emails to tasks OR after sending an email (compose/reply/replyall/forward) that relates to a task. Applies to both inbound and outbound key emails.

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
   - If a deadline was extracted and the task Due date changed, update queue.md Due field (see [`TASK_WORKFLOW.md`](TASK_WORKFLOW.md) → Queue Update → Update in Queue)

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
- [ ] 2026-05-10 → Beng: Confirm Rhapsody procurement path [response_due: 2026-05-13]

### Owed to me
- 2026-05-10 ← Prantar: SOW draft (next week)

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

**Email domains:**
- `@ph.ibm.com` → 🇵🇭 Philippines
- `@cn.ibm.com` → 🇨🇳 China
- `@in.ibm.com` → 🇮🇳 India

**Explicit mentions:**
- "FNC China", "CIC China" → China
- "FutureNow Center Philippines", "ASEAN" → Philippines
- "CIC India" → India
