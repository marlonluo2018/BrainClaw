# Email Workflow

> **ALWAYS follow this workflow when user requests email operations**

---

## List/Check Emails

**Triggers:** "list emails", "check emails", "show emails", "emails from [time]"

**MANDATORY Steps:**
1. **Load workflow** → Read [`workflows/EMAIL_WORKFLOW.md`](EMAIL_WORKFLOW.md)
2. **Get emails** → Use [`outlook-skill`](../skills/outlook-skill/SKILL.md) skill to list emails
3. **Extract keywords & geo** → For each email, identify:
   - Keywords (names, topics, ticket IDs)
   - Geo: `@ph.ibm.com`→Philippines, `@cn.ibm.com`→China, `@in.ibm.com`→India, or explicit mentions
4. **Match tasks** → Search [`tasks/queue.md`](../tasks/queue.md) for matching tasks by keywords + geo
5. **Present summary** → Use format below (REQUIRED)

**Summary Format (REQUIRED):**
```
📧 Email Summary: [Date Range] ([N] messages)

📌 TASK-RELATED EMAILS

🇵🇭 PHILIPPINES
Task [TID](path) - Title:
- Email #X (date time) Sender: Subject
- Action: [suggested action]

🇨🇳 CHINA
Task [TID](path) - Title:
- Email #X (date time) Sender: Subject

🇮🇳 INDIA
🔴 ACTION REQUIRED (No Task Match)
- Email #X (date time) Sender: Subject [LRT approval/urgent item]

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

## Draft Email

**Triggers:** "draft email", "compose email", "reply", "forward"

**Steps:**
1. **Get context** → Read original email if reply/forward
2. **Check stakeholder** → Look up recipient in [`stakeholders/registry.md`](../stakeholders/registry.md)
3. **Draft** → Use appropriate tone (formal for decision makers, professional for others)
4. **Add signature** → From [`CONFIG.md`](../CONFIG.md)
5. **Present for approval** → NEVER send without approval

---

## Create Task from Email

**Triggers:** User approves task creation after email summary

**Steps:**
1. Follow [`TASK_WORKFLOW.md`](TASK_WORKFLOW.md) → Create Task
2. Link email reference in task timeline

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
