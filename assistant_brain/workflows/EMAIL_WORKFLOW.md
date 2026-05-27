# Email Workflow

> **ALWAYS load the email skill before executing any email operation.**

---

## Check Recent Emails

**Triggers:** "check email", "any new emails", "what's new", "show recent", "emails from [time]"

**Steps:**
1. **Load skill** → Load the email skill
2. **Fetch emails** → List recent emails (Inbox + Sent Items)
3. **Extract keywords & geo** → For each email, identify:
   - Keywords (names, topics, ticket IDs)
   - Geo: `@ph.ibm.com`→Philippines, `@cn.ibm.com`→China, `@in.ibm.com`→India, or explicit mentions
4. **Match tasks** → Search [`tasks/queue.md`](../tasks/queue.md) for matching tasks by keywords + geo
5. **Present summary** → Use format below (REQUIRED)
6. **Persist links** → After user confirms task matches, record email references in task files (see "Record Email Reference" section)

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
1. [Highest priority action with geo flag]
2. [Next priority action]
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
4. **Present summary** → Use format below (REQUIRED)

**Progress Update Summary Format:**

> Uses the same format as "Email Sync (Integrated)" — see [Combined Summary Format](#email-sync-integrated) below. Both commands produce identical output structure.

---

## Email Sync (Integrated)

**Triggers:** "email sync", "sync emails", "check and update", "邮件同步"

> One command to check recent emails AND update task progress. Combines "Check Recent Emails" + "Update Task Progress" into a single flow.

**Days parameter:**
- Default: **1 day** (today only — designed for daily use)
- Override: user can specify days → "email sync 3", "sync emails 7 days", "邮件同步 3天"
- If user says "email sync" with no number → use 1 day

**Steps:**
1. **Load skill** → Load the email skill
2. **Fetch emails** → `find-recent --days {N}` (default 1)
3. **Extract keywords & geo** → Match emails to tasks (same as "Check Recent Emails" steps 3-4)
4. **Present email summary** → Show abbreviated email summary (condensed — task matches only, skip non-task emails unless action required)
5. **Update task files** → For each task-matched email, update progress directly (same as "Update Task Progress" steps 2-3)
6. **Present combined summary** → Use format below (REQUIRED)

**Combined Summary Format:**

> **CRITICAL:** ALL emails MUST display email numbers (#1, #80, etc.) so user can reference them later with "check email #XX".

```
## Email Sync Summary (Date Range) — N emails

### {flag} Geo Name

**[TID](path) Task Name**
Updated:
- Timeline: `YYYY-MM-DD [Tag]: Description`
- Ask added: `YYYY-MM-DD ← Person: description`

Emails:
- #X — YYYY-MM-DD HH:MM — Sender: one-line summary
- #Y — YYYY-MM-DD HH:MM — Sender: one-line summary

→ Action: [suggested next step for this task]

&nbsp;

**[TID](path) Task Name**
Updated: no changes — already up to date.

Emails:
- #X — YYYY-MM-DD HH:MM — Sender: one-line summary

→ Action: [suggested next step for this task]

### {flag} Another Geo

**[TID](path) Task Name**
Updated:
- Timeline: `YYYY-MM-DD [Tag]: Description`

Emails:
- #X — YYYY-MM-DD HH:MM — Sender: one-line summary

→ Action: [suggested next step for this task]

### Non-Task

Action needed:
- #X — MM-DD HH:MM — Sender: brief description
  → Action: [suggested response/action]
- #Y — MM-DD HH:MM — Sender: brief description
  → Action: [suggested response/action]

Informational: #A, #B, #C, ...
```

**Format rules:**
1. Email numbers are mandatory for ALL entries — handles for "check email #XX"
2. Task File Updates must show what was written to each task file
3. If a matched task required no updates, state "Updated: no changes — already up to date." — **ALWAYS still list their Emails section**
4. Each task ends with `→ Action:` line suggesting the next step
5. Separate tasks with `&nbsp;` (blank spacer line) for visual clarity — no `---` horizontal rules between tasks
6. Non-Task "Action needed" items each get their own indented `→ Action:` line
7. Email numbers are sequential across the entire summary (not per-task)

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

**When:** After matching emails to tasks, record the link persistently.

**Steps:**
1. For each confirmed task-email match, add a row to the task file's `## Email References` table:

```markdown
## Email References
| entry_id | date | from | subject | folder | extracted |
|----------|------|------|---------|--------|-----------|
| AAA... | 2026-03-01 | Beng PAULINO | Need your approval... | Inbox | N |
| BBB... | 2026-03-03 | Marlon Luo | Re: Need your approval... | Sent Items | N |
```

2. **Format:** `| <entry_id> | YYYY-MM-DD | <sender_name> | <subject> | <folder_name> | N |`
   - `extracted` column starts as `N`. Set to `Y` after Step 3 (Extract Asks/Decisions) is complete for that email.

3. **Extract Asks / Decisions / Deadlines** (NEW — see [Extract Email Content into Task](#extract-email-content-into-task) below)

4. **When looking up task emails later:**
   - Read the task file → get entry_ids from Email References table
   - Use email skill `get-email` for each to get current state
   - This bypasses searching entirely — O(1) email lookup

---

## Extract Email Content into Task

**When:** Right after recording an email reference (Step 3 of "Record Email Reference"). Goal: pull view-relevant signal out of email bodies into the task's structured slots so future `status`/`owed`/`waiting` queries don't need to re-read email bodies.

**Trigger:** Any email reference row with `extracted: N`.

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
   - Append confirmed Timeline entries with appropriate tags
   - Update `## Email References` row: `extracted: Y`
   - If a deadline was extracted and the task Due date changed, update queue.md Due field (see [`TASK_WORKFLOW.md`](TASK_WORKFLOW.md) → Queue Update → Update in Queue)

5. **If user says "n":**
   - Still flip `extracted` to `Y` (so we don't re-prompt next time)
   - Add a one-line Timeline: `**{date}** [email-in] {subject} (no extraction needed)`

6. **If user says "edit":**
   - Show the proposed extraction as text the user can correct
   - Apply user's corrected version

**Extraction principles:**

- **Conservative.** When unsure whether a phrase is an ask vs. a soft suggestion, ask. False positives clutter Asks; false negatives drop on the floor.
- **Inbound vs outbound matters.** Asks in inbound emails default to "Owed by me"; asks in outbound emails ("I'll send X") are commitments by me — also "Owed by me" but with no `response_due` unless specified.
- **One signal per Timeline entry.** If an email has both a decision and an ask, write two Timeline lines.
- **Reference the email.** Each extracted Timeline entry should mention the entry_id snippet for traceability: `**2026-05-10** [decision] Vendor narrowed to Rhapsody + alt (email AAA...)`.

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
- **2026-05-10** [decision] Rhapsody chosen as primary vendor (email BBB123...)
- **2026-05-10** [ask] Beng asked to confirm procurement path by 2026-05-13 (email BBB123...)
- **2026-05-10** [ask] Prantar promised SOW draft early next week (email BBB123...)
```

Email Reference row updates from `extracted: N` to `extracted: Y`.

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
