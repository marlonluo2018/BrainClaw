# Email Workflow

> Detailed procedures for email operations

---

## Email Display Format

**When summarizing emails after list/search operations:**
- ALWAYS include email reference numbers (e.g., #1, #2, #3)
- Format: Use "#X" prefix in summary text
- Purpose: Enable quick reference for follow-up actions (reply, forward, get details)
- Example: "#17 Manjula (LearnQuest) - Azure APIM clarifications"

---

## Proactive Task Hints

**When:** After listing emails, checking calendar, or user mentions work items.

**Process:**
1. Extract keywords using keyword-extraction skill
2. Compare with tags in `tasks/queue.md`
3. Count only SPECIFIC identifier matches (names, emails, IDs, codes)
4. **Suggest user to review relevant emails:**
   - If 2+ matches → "Email #X may relate to task TY, would you like to review?"
   - If 0-1 match → "Email #X may need new task, would you like to review?"
5. **If meeting invites found → Remind user to check calendar:**
   - List meeting invite dates
   - Suggest: "You have X meeting invites on [dates], would you like to check your calendar for those days?"
6. Get user approval

---

## Add Tasks from Emails

**When:** Approval emails, delegation emails, direct action requests, urgent executive requests

**Criteria:** Email TO you, clear action request, requires your role/expertise, identifiable deliverable

**Skip:** FYI emails, general announcements, unclear discussion threads

---

## Draft Email Command

When user says "draft email", "draft reply", "起草邮件", or "草拟邮件":

1. **Read stakeholder context** - Check [`stakeholders/registry.md`](../stakeholders/registry.md) for recipient profile (power level, communication style, interests, concerns)
2. **Gather info** - Collect To, Subject, Body
3. **Format draft** - Prepare content with appropriate tone based on stakeholder profile, add signature
4. **Present draft** - Show email with signature, offer suggestions for improving the email content, ask for approval
5. **Iterate or send** - If changes requested → revise; If approved → send
6. **Confirm** - Report email sent