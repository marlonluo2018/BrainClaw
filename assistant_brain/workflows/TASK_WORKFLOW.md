# Task Workflow

> Task operations workflow
>
> **Format Reference:** See [`../tasks/FORMATS.md`](../tasks/FORMATS.md) for task templates, status symbols, priority levels, and other format specifications (load on-demand when creating/updating tasks)

---

## Create Task

**Trigger:** User requests new task, email action item detected

**Steps:**
1. Determine next Task ID (auto-incremented from highest existing T-number in task files)
2. Extract keywords from content (see [Keyword Extraction Rules](#keyword-extraction-rules))
3. Match to process template (see [PROCESS_WORKFLOW](PROCESS_WORKFLOW.md)) → suggest RACI roles + initial Current State steps
3a. **Define Scope** → Write a one-line boundary statement (what belongs in this task and what doesn't). Check active task files for same vendor/geo/topic overlap — if overlap found, sharpen BOTH Scopes to disambiguate. Scope is mandatory; never leave it empty.
4. Present RACI matrix to user for confirmation
5. Generate filename: `T{ID}-{keyword1}-{keyword2}.md`
6. Create task file using template from [`tasks/FORMATS.md`](../tasks/FORMATS.md). **The `## Asks` section (with both `### Owed by me` and `### Owed to me` subsections) MUST be present**, even if empty. The template includes them — do not strip them out.
6a. **Email Entry ID (mandatory)** — When a timeline entry originates from an email, append the entry_id as an HTML comment: `<!-- email:{ENTRY_ID} -->`. Retrieve the ID from sync results or via `outlook_skill.py get-email`. Never omit this for email-sourced entries.
6b. **Match-Friendly Metadata** — Ensure these fields are populated for `email_sync.py` auto-matching:
   - **EPD:** Fill if a plan row ID exists (e.g., `1032769`). Pure numeric IDs score 3× in matching.
   - **Tags:** Include the most discriminating identifiers — EPD numbers, course codes (`DO288`), vendor names (`Red Hat`), geo shorthand (`FNC India`), PO numbers. See [Tag Guidelines](../tasks/FORMATS.md#tag-guidelines).
   - **Contacts:** List ALL known email correspondents (not just approvers) — every email address in Contacts/RACI enables contact-signal matching (0.8 confidence).
7. **Initialize Asks** → From the trigger content (user request or email body), detect any explicit promises:
    - "I'll send X to {person}" / "我会发给 {人}" → append to `### Owed by me` as `- [ ] {Due: Wkd Mon DD, YYYY} 🎯 {person}: {what}` (where the date shown at the start is the actual due date, or `TBD` if none specified)
    - "{person} will send X" / "等 {人} 回" → append to `### Owed to me` as `- {Due: Wkd Mon DD, YYYY} ⏳ {person}: {what}` (where the date shown at the start is the expected response/due date, or `TBD` if none specified)
    - Keep dates natural and concise (e.g. `Due: Fri Jul 17, 2026`). If no due date is specified, use `TBD`.
    - If no explicit asks: leave both subsections empty (just the headings). Do **not** keep the placeholder example lines from the template.
8. Confirm with user — show the populated Asks (if any) so the user can correct or add more before saving.

> **Note:** The dashboard derives task lists and Recent Events from file metadata (`Created:`/`Completed:` fields) — no manual index update needed.

---

## Update Task

**Trigger:** User provides new info, email relates to existing task

**Minimum scope:** When user says "update task file" without specifying fields, ALWAYS update at least: **Timeline** (new entries) + **Asks** (new/completed items, annotations). These two are mandatory; other fields (status, notes, current state) update as needed.

**Steps:**
1. Read current task file
2. **If task file lacks `## Asks` section** (legacy file): insert empty section with both `### Owed by me` and `### Owed to me` subsections before proceeding. Going forward all updates land in a properly-structured file.
3. Check if incoming information already exists (duplicate check)
4. If duplicate → Notify user and skip
5. If new → Show changes and get approval
6. **Detect Asks signals** in the user input or referenced email content:
    - **New owed-by-me** ("I'll do X" / "I'll send X" / "我会发" / "我会处理") → append `- [ ] {Due: Wkd Mon DD, YYYY} 🎯 {person}: {what}` to `### Owed by me` (using the actual due date at the start, or `TBD` if none specified)
    - **New owed-to-me** ("{person} will send X" / "等 {人} 回" / "等回复") → append `- {Due: Wkd Mon DD, YYYY} ⏳ {person}: {what}` to `### Owed to me` (using the expected response/due date at the start, or `TBD` if none specified)
   - **Owed-by-me fulfilled** (user says "done" / "已发" / "处理完了" referencing a specific item) → flip the matching `[ ]` to `[x]` (do NOT delete — kept for history)
   - **Owed-to-me received** (user says "got reply from X" / "X 回了") → remove the matching line from `### Owed to me`
   - When ambiguous which existing item is being closed, ask before flipping/removing.
6a. **Reclassify Current State items that are actually Asks.** Scan `## Current State` for items that have an external recipient (an action like "send X to {person}" / "notify {team}" / "deliver to {role}"). For each such item, propose to upgrade it to `Asks > Owed by me` and remove from Current State (or leave if it's also a meaningful internal step). This keeps cross-task views (`owed`/`waiting`) accurate. Apply the [Asks vs Current State](../tasks/FORMATS.md#asks) rules from FORMATS.md. Ask user before moving — don't auto-rewrite long-standing items silently.
7. After approval, update task file (status, fields, Asks, timeline entry)
8. **Pending-item gate (mandatory):** After every update, verify the task has at least one active (non-struck-through) item in `### Owed to me`. If all items are struck through or the section is empty, the task MUST have a new pending item added before the update is considered complete. Principle: *"if it is not closed, there should be something waiting."* If you cannot determine the next waiting item, ask the user.
9. Notify user of changes

**Update Types:**

| Field | Action |
|-------|--------|
| status | Update status field in task file |
| timeline | Append new entry. **If sourced from email, entry_id is mandatory** — append `<!-- email:{ENTRY_ID} -->` to the line. Use the email's `Received` timestamp for the date — do NOT query OS for current time. |
| notes | Append to notes section |
| stakeholders | Update RACI matrix |
| due_date | Update due field in task file |
| priority | Update priority in task file |
| asks (owed by me) | Append `- [ ] {Due: Wkd Mon DD, YYYY} 🎯 {person}: {what}` to `### Owed by me`; flip `[x]` when fulfilled |
| asks (owed to me) | Append `- {Due: Wkd Mon DD, YYYY} ⏳ {person}: {what}` to `### Owed to me`; remove line when received |
| scope | Update Scope field (e.g., after sync mismatch or discovering overlap with another task) |

---

## Complete Task

**Trigger:** User confirms task done

**Steps:**
1. Read task file → Get RACI matrix → Identify Accountable (A) and Informed (I) stakeholders
2. Update status to ✅
3. If task has "Recurring Task ID" → Update recurring_tasks.md "last_completed"
4. Add `**Completed:** {date}` to frontmatter
5. Move task file to `tasks/history/{YYYY}-Q{n}/` (quarter determined by completion date)
6. Ask user: "Draft notification email to [stakeholders]?"
7. If yes → Follow [EMAIL_WORKFLOW](EMAIL_WORKFLOW.md) to draft and send

---

## Master-Subtask Operations

### Create Master Task
1. Follow Create Task workflow
2. Add "(Master)" to title
3. Add "**Subtasks:**" field

### Create Subtask
1. Follow Create Task workflow
2. Add "**Parent Task: TXXX**" field
3. Update master's Subtasks field

### Update Relationships
- **Add subtask**: Update master's Subtasks field
- **Remove subtask**: Update master + move/archive subtask
- **Convert to master**: Add (Master) + Subtasks field

---

## Task Queries

### By Keyword
1. Search active task files for keyword (glob `tasks/T*.md`, grep content)
2. Show matching tasks with links
3. If details needed → Read specific task file

### By Stakeholder
1. Search all task files for stakeholder name in Stakeholders section
2. Group by status: ⏳ In Progress → 📋 Not Started → 🔴 Blocked
3. Display with RACI role

---

## Keyword Extraction Rules

**Priority Order (Highest First):**

| Priority | Type | Examples |
|----------|------|----------|
| 1 Highest | Ticket Number | INC0012345, SR0006789, CHG0054321, RITM123456 |
| 2 Second | Person Names | Jexer Poblete, Marlon Luo (exclude frequent approvers) |
| 3 Third | Task Type | voucher request, access request, approval task |
| 4 Fourth | Task Keywords | AZ-900, certificate, ITIL, error |
| 5 Fifth | Attachments | certificate.pdf, proof_of_training.docx |

**Output:** 3-8 keywords, sorted by priority. Skip any level without matches.

---

## Process Matching

For RACI assignment and process step mapping, see [PROCESS_WORKFLOW](PROCESS_WORKFLOW.md) and [`contacts.md` Process Roles](../contacts.md#process-roles-quick-reference).
