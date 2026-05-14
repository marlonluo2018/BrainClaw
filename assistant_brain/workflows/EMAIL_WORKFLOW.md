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

## Draft / Reply / Forward

**Triggers:** "draft email", "compose", "write email", "reply", "reply all", "forward", "send to [person]"

**Steps:**
1. **Load skill** → Load the email skill
2. **Get context** → Read original email if reply/forward
3. **Choose reply mode:**
   - **Default: `replyall`** — keeps all original recipients, `--to`/`--cc` append
   - **Narrow: `reply`** — sender only, `--to`/`--cc` specify exact extras
4. **Check stakeholder** → Look up recipient in [`stakeholders/registry.md`](../stakeholders/registry.md)
5. **Draft** → Apply tone based on stakeholder type (see table below)
6. **Add signature** → From [`CONFIG.md`](../CONFIG.md)
7. **Present for approval** → NEVER send without user confirmation

**Tone Guidelines:**

| Stakeholder Type | Tone | Format |
|------------------|------|--------|
| Decision Maker (High Power) | Formal, executive | Brief (3-4 paragraphs), ROI focus |
| Influencer (Medium Power) | Professional, collaborative | Balanced detail |
| Executor (Low Power) | Clear, supportive | Detailed instructions |
| Unknown | Professional, neutral | Standard format |

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
| entry_id | date | from | subject | folder |
|----------|------|------|---------|--------|
| AAA... | 2026-03-01 | Beng PAULINO | Need your approval... | Inbox |
| BBB... | 2026-03-03 | Marlon Luo | Re: Need your approval... | Sent Items |
```

2. **Format:** `| <entry_id> | YYYY-MM-DD | <sender_name> | <subject> | <folder_name> |`

3. **When looking up task emails later:**
   - Read the task file → get entry_ids from Email References table
   - Use email skill `get-email` for each to get current state
   - This bypasses searching entirely — O(1) email lookup

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
