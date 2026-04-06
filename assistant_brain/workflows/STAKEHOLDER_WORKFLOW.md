# Stakeholder Workflow

> Detailed procedures for stakeholder management

---

## When to Read Stakeholder Files

- Before drafting emails to stakeholder
- When task mentions stakeholder by name
- When adding/updating tasks with stakeholders

---

## How to Read Stakeholder Files

1. Read [`stakeholders/registry.md`](../stakeholders/registry.md) → find stakeholder
2. Read stakeholder's detailed file (e.g., `SH001-beng-paulino.md`)
3. Use profile (power, style, interests, concerns) to inform actions

---

## Auto-Detect Stakeholders (When Creating Tasks)

**Process:**
1. Check email contacts (To, CC, From) against [`stakeholders/registry.md`](../stakeholders/registry.md)
2. Auto-suggest RACI roles based on:
   - **Email role:** To/From = likely R or A, CC = likely I
   - **Stakeholder power:** High Power = likely A (Accountable)
   - **Task type:** Budget task → budget approver = A, Procurement task → procurement team = C
3. Present suggested RACI matrix to user for confirmation

**RACI Suggestion Rules by Task Type:**
- **Budget tasks** → High-power stakeholder (e.g., Beng PAULINO) = Accountable
- **Procurement tasks** → Procurement team (e.g., ASEAN Procurement Operations) = Consulted
- **Training tasks** → User (Marlon Luo) = Responsible, Practice Leaders = Informed

---

## Stakeholder Notification Reminders

### When Marking Task as Blocked

**Before marking blocked:**
1. Check task RACI matrix
2. Find Accountable (A) stakeholder
3. Remind user: "Task blocked. [Stakeholder Name] (Accountable) should be notified. Draft email?"
4. Offer to draft notification email

### When Completing Task

**Before marking complete:**
1. Check task RACI matrix
2. Find Accountable (A) and Informed (I) stakeholders
3. Suggest: "Task complete. Should I draft notification email to [Stakeholder Names]?"
4. Offer to draft notification emails

### When Updating Task (Significant Changes)

**For major updates (blockers, milestones, key decisions):**
1. Check if update is significant
2. Check RACI matrix for relevant stakeholders
3. Suggest adding entry to Engagement Log
4. Offer to draft notification if needed

---

## Stakeholder-Based Queries

See [`TASK_WORKFLOW.md`](TASK_WORKFLOW.md#stakeholder-based-task-queries) for detailed query procedures.

---

## Tailoring Communication by Stakeholder Type

### Decision Makers (High Power, Accountable)
- **Tone:** Formal, executive-level
- **Content:** Executive summary, clear recommendations, ROI focus
- **Format:** Brief (3-4 paragraphs max), business impact highlighted

### Influencers (Medium Power, High Interest)
- **Tone:** Professional, collaborative
- **Content:** Detailed but organized, seek input
- **Format:** Balanced detail, technical depth as appropriate

### Executors (Low Power, Assigned Tasks)
- **Tone:** Clear, supportive
- **Content:** Step-by-step guidance, actionable items
- **Format:** Detailed instructions, resources provided

### Stakeholders (Information Recipients)
- **Tone:** Brief, informative
- **Content:** Relevant highlights, optional details
- **Format:** Summary with links to details if needed