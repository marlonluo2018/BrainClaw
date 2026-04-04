# Stakeholder Module

> **Purpose:** Provide stakeholder context to AI assistant for better task execution and communication

---

## Overview

The stakeholder module helps the AI assistant understand WHO is involved in tasks, their roles, influence levels, and communication preferences. This context is essential for:

- Drafting appropriate emails (tone, level of detail, approach)
- Understanding task priorities (who is the decision maker?)
- Managing communications (who needs updates? when?)
- Navigating approvals (what is the approval chain?)

## Files

| File | Purpose |
|------|---------|
| [`registry.md`](registry.md) | Central stakeholder database with profiles |
| [`README.md`](README.md) | This file - module documentation |

## How It Works

### For AI Assistant

**When drafting emails:**
1. User says "draft email to Beng about T025"
2. AI reads [`registry.md`](registry.md) → finds Beng PAULINO profile
3. AI sees: High Power, Decision Maker, Formal communication, interests Budget/ROI
4. AI drafts email with: Executive tone, cost-benefit focus, clear decision request

**When analyzing tasks:**
1. User says "what's the status of T025?"
2. AI reads task file → sees stakeholder section with RACI
3. AI reads [`registry.md`](registry.md) for each stakeholder
4. AI provides context: "Waiting on quotation. Beng (Accountable) needs update in 2 days"

**When adding tasks:**
1. AI extracts contacts from email
2. AI checks [`registry.md`](registry.md) for each contact
3. AI auto-assigns RACI roles based on profiles
4. AI adds stakeholder section to task file

### For Users

**Adding a stakeholder:**
Simply mention them 3+ times in tasks/emails, or say "add X to stakeholder registry"

**Updating a stakeholder:**
Say "update stakeholder Beng - last interaction today" or edit [`registry.md`](registry.md) directly

**Viewing stakeholders:**
Say "show me stakeholders for T025" or "who is Beng PAULINO?"

## Stakeholder Registry Structure

**Stakeholders can be:**
- **Individuals:** Single person (e.g., Beng PAULINO)
- **Teams:** Group of people (e.g., ASEAN Procurement Operations)
- **Departments:** Organizational unit (e.g., Finance Department)
- **Organizations:** External entities (e.g., LearnQuest vendor)

Each stakeholder has:
- **ID:** Unique identifier (SH001, SH002...)
- **Identity:** Name, Email, Title, Organization, Geo
- **Influence:** Power Level, Interest Level, Role Type
- **Communication:** Preferred channel, Style, Timezone
- **Profile:** Interests, Concerns, Decision Criteria
- **Relationships:** Reports to, Manages, Collaborates with

## Task Integration

Tasks include a **Stakeholders** section with RACI matrix:

```markdown
## Stakeholders

### RACI Matrix
*List stakeholders involved in this task and their role.*

| Stakeholder | Role |
|-------------|------|
| Beng PAULINO | A |
| Marlon Luo | R |
| ASEAN Procurement Operations | C |

**Legend:** R=Responsible, A=Accountable, C=Consulted, I=Informed

### Engagement Log
```

**RACI Legend:**
- **R** = Responsible (does the work)
- **A** = Accountable (decision maker, single point of accountability)
- **C** = Consulted (provides input, two-way communication)
- **I** = Informed (kept updated, one-way communication)

## Power-Interest Framework

### High Power, High Interest → Manage Closely
- Active engagement, regular updates
- Involve in key decisions
- Weekly status updates

### High Power, Low Interest → Keep Satisfied
- Inform on major milestones
- Don't overload with details
- Monthly summaries

### Low Power, High Interest → Keep Informed
- Regular updates
- Respond to questions promptly
- Bi-weekly communications

### Low Power, Low Interest → Monitor
- Minimal communication
- Standard notifications only
- As-needed basis

---

**Last Updated:** 2026-04-04  
**Stakeholders:** See [`registry.md`](registry.md)