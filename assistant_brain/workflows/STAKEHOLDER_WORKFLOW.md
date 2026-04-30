# Stakeholder Workflow

> Stakeholder management workflow - orchestrates skills for stakeholder operations

---

## Match Stakeholders

**Trigger:** Creating task, drafting email, user asks about stakeholder

**Steps:**
1. Call `stakeholder` (operation: match) with contacts
2. Get matched stakeholders with RACI suggestions
3. Present to user for confirmation
4. If new contact appears 3+ times → Suggest adding to registry

---

## Suggest RACI

**Trigger:** Task creation, RACI query

**Steps:**
1. Call `stakeholder` (operation: raci-suggest) with task type and stakeholders
2. Present RACI matrix with justifications
3. Get user confirmation
4. Apply to task file

---

## Before Drafting Email

**Applies to:** All email types (new, reply, forward) - See [EMAIL_WORKFLOW: Draft Email](../workflows/EMAIL_WORKFLOW.md#draft-email-newreplyforward)

**Steps:**
1. Read `stakeholders/registry.md` → Find recipient
2. Read stakeholder's detailed file (e.g., `SH001-beng-paulino.md`)
3. Use profile (power, style, interests, concerns) for tone
4. This context is used by `email` (operation: compose) to tailor tone and content

---

## Notify Stakeholders

### When Task Blocked
1. Automatically triggered when task status → 🔴 Blocked (see [TASK_WORKFLOW: Block Task](../workflows/TASK_WORKFLOW.md#block-task))
2. Read task RACI matrix → Find Accountable (A) stakeholder
3. Call `email` (operation: compose) → Auto-draft notification with blocker details
4. Present drafted email to user for approval
5. If approved → Send via [EMAIL_WORKFLOW](../workflows/EMAIL_WORKFLOW.md#draft-email-newreplyforward)

### When Task Complete
1. Read task RACI matrix
2. Find Accountable (A) and Informed (I) stakeholders
3. Offer to draft notification emails
4. Call `email` (operation: compose) for each stakeholder

---

## Communication Styles

|| Stakeholder Type | Tone | Format |
||------------------|------|--------|
|| Decision Maker (High Power) | Formal, executive | Brief, ROI focus |
|| Influencer (Medium Power) | Professional, collaborative | Balanced detail |
|| Executor (Low Power) | Clear, supportive | Detailed instructions |
|| Information Recipient | Brief, informative | Summary with links |

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

---

## Skills Used

|| Skill | Operations Used | Purpose |
||-------|-----------------|---------|
|| `stakeholder` | match, raci-suggest | Match contacts, suggest RACI roles |
|| `email` | compose | Draft stakeholder-tailored emails |
