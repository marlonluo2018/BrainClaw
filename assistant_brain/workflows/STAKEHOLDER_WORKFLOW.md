# Stakeholder Workflow

> Stakeholder management workflow

---

## Match Stakeholders

**Trigger:** Creating task, drafting email, user asks about stakeholder

**Steps:**
1. Extract contacts from email (To/CC/From) or user request
2. Read [`stakeholders/registry.md`](../stakeholders/registry.md)
3. Match each contact by name or email against registry
4. For each match, suggest RACI role based on:
   - **Email role**: To/From → R or A, CC → I
   - **Stakeholder power**: High Power → A
   - **Task type rules** (see [RACI Rules](#raci-rules-by-task-type))
5. Flag unmatched contacts separately
6. Present matches + RACI suggestions to user for confirmation
7. If new contact appears 3+ times → Suggest adding to registry

**Contact Format (from email):**
```
Name: "Beng PAULINO", Email: "beng@example.com", Role: "from"
Name: "Marlon Luo", Email: "luomn@cn.ibm.com", Role: "to"
```

---

## Suggest RACI

**Trigger:** Task creation, RACI query

**Steps:**
1. Identify task type (Budget, Procurement, Training, Approval, Technical, General)
2. For each stakeholder, apply RACI rules (task type + power level)
3. Present RACI matrix with justifications
4. Get user confirmation
5. Apply to task file

---

## RACI Rules by Task Type

| Task Type | R (Responsible) | A (Accountable) | C (Consulted) | I (Informed) |
|-----------|-----------------|-----------------|---------------|--------------|
| Budget | Task owner | High-power approver | Finance team | Other managers |
| Procurement | Requester | Budget owner | Procurement team | End users |
| Training | Trainee | Manager | Training provider | HR |
| Approval | Executor | Approver | Subject experts | Stakeholders |
| Technical | Developer | Tech lead | Architect | Product owner |
| General | To/From → R | High Power → A | - | CC → I |

**Power-Based Rules:**

| Power Level | Typical RACI Role |
|-------------|-------------------|
| High | A (Accountable) or I (Informed) |
| Medium | C (Consulted) or R (Responsible) |
| Low | R (Responsible) or I (Informed) |

---

## Before Drafting Email

**Applies to:** All email types (new, reply, forward) - See [EMAIL_WORKFLOW](EMAIL_WORKFLOW.md)

**Steps:**
1. Read [`stakeholders/registry.md`](../stakeholders/registry.md) → Find recipient
2. Read stakeholder's detailed file (e.g., `SH001-beng-paulino.md`)
3. Use profile (power, style, interests, concerns) to select tone from Communication Styles below
4. Pass context to email drafting (see [EMAIL_WORKFLOW](EMAIL_WORKFLOW.md))

---

## Notify Stakeholders

### When Task Blocked
1. Automatically triggered when task status → 🔴 Blocked (see [TASK_WORKFLOW](TASK_WORKFLOW.md))
2. Read task RACI matrix → Find Accountable (A) stakeholder
3. Draft notification email with blocker details using Communication Styles below
4. Present drafted email to user for approval
5. If approved → Send via [EMAIL_WORKFLOW](EMAIL_WORKFLOW.md)

### When Task Complete
1. Read task RACI matrix
2. Find Accountable (A) and Informed (I) stakeholders
3. Offer to draft notification emails
4. Draft using Communication Styles based on each stakeholder's type

---

## Communication Styles

| Stakeholder Type | Tone | Format |
|------------------|------|--------|
| Decision Maker (High Power) | Formal, executive | Brief, ROI focus |
| Influencer (Medium Power) | Professional, collaborative | Balanced detail |
| Executor (Low Power) | Clear, supportive | Detailed instructions |
| Information Recipient | Brief, informative | Summary with links |

---

## Stakeholder Queries

**"Show tasks for [stakeholder]":**
1. Search all task files for stakeholder in RACI section
2. Extract: Task ID, Title, Status, RACI Role
3. Group by status
4. Display in format:
   ```
   Tasks for [Stakeholder Name]:
   
   In Progress (⏳):
   - [T025](../tasks/T025-xxx.md): Task Title - Role: A
   
   Not Started (📋):
   - [T019](../tasks/T019-xxx.md): Task Title - Role: C
   ```
