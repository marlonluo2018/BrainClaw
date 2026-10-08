# Task Workflow

> Task operations workflow
>
> **Format Reference:** See [`../tasks/FORMATS.md`](../tasks/FORMATS.md) for task templates, status symbols, priority levels, and other format specifications (load on-demand when creating/updating tasks).
>
> Task files are the source of truth for task history and progress (see the system prompt) — read them before searching email.

---

## Create Task

**Trigger:** User requests new task, email action item detected

**Steps:**
1. Determine next Task ID (auto-incremented from highest existing T-number in task files)
2. Extract keywords from content (see [Keyword Extraction Rules](#keyword-extraction-rules))
3. Match to process template (see [PROCESS_WORKFLOW](PROCESS_WORKFLOW.md)): **READ the matched process file in `assistant_brain/process/{geo}/{process}.md`** → extract RACI roles, process steps, key rules, and email templates.
3a. **Define boundaries** → Write a positive one-line `Scope` statement describing only what belongs in the task. Add the mandatory `Exclude` field for what does not belong; use `—` only when there is genuinely no exclusion. Check active tasks for vendor/geo/topic overlap and sharpen both tasks' Scope/Exclude boundaries when needed. Never encode exclusions as `NOT ...` inside Scope.
4. Present RACI matrix to user for confirmation
5. Generate filename: `T{ID}-{keyword1}-{keyword2}.md`
6. Create the task using [`tasks/FORMATS.md`](../tasks/FORMATS.md). Required headers are `Status`, `Created`, `Priority`, `Category`, `Geo`, `Due`, `EPD`, `Scope`, and `Exclude`; use `TBD` for unknown due dates and `—` for an absent EPD/exclusion. Required sections include Contacts, Stakeholders/RACI, Tags, Asks (both subsections), Timeline, Current State, and Notes. Do not strip empty required sections.
6a. **Email source metadata** — For an email-sourced timeline entry, preserve all source facts returned by Outlook: exact received/sent timestamp, direction (`[email-in]` or `[email-out]`), `<!-- email:{ENTRY_ID} -->`, and `<!-- conversation:{CONVERSATION_ID} -->` whenever Outlook returns one. Never substitute the current time. Retrieve the exact source message when these facts are not already in the sync snapshot.
    - EntryID markers go on Timeline lines only, never on Asks items (see FORMATS.md).
6b. **Classification Evidence Metadata** — Populate these fields so `email_sync.py` can retrieve plausible candidates without deciding ownership:
   - **EPD:** Fill if a plan row ID exists (e.g., `1032769`). It is recorded as a stable identifier, not a weighted score.
   - **Tags:** Record 1–4 discriminating identifiers — EPD numbers, course codes (`DO288`), vendor/program aliases (`Red Hat Ascend`), geo shorthand (`FNC India`), or PO numbers. Avoid generic words. See [Tag Guidelines](../tasks/FORMATS.md#tag-guidelines).
   - **Contacts:** List all known correspondents, not only approvers. Every known correspondent must use an actual email address; names without a verified address may be noted temporarily but must not be treated as participant evidence. Contacts/RACI provide evidence for semantic review and never auto-assign ownership.
7. **Initialize Asks** → From the trigger content (user request or email body), detect any explicit promises:
     - "I'll send X to {person}" / "我会发给 {人}" → append to `### My Actions` as `- [ ] {Due: Wkd Mon DD, YYYY} 🎯 to {person}: {what}`. If it is an internal L&K task / self-action with no external recipient, append as `- [ ] {Due: Wkd Mon DD, YYYY} 🎯 {what}` (omit the name/colon prefix).
     - "{person} will send X" / "等 {人} 回" → append to `### Waiting on Others` as `- {Due: Wkd Mon DD, YYYY} ⏳ {person}: {what}` (where the date shown at the start is the expected response/due date, or `TBD` if none specified)
    - Keep dates natural and concise (e.g. `Due: Fri Jul 17, 2026`). If no due date is specified, use `TBD`.
    - If no explicit asks: leave both subsections empty (just the headings). Do **not** keep the placeholder example lines from the template.
8. Confirm with user — show the populated Asks (if any) so the user can correct or add more before saving.

> **Note:** The dashboard derives task lists and Recent Events from file metadata (`Created:`/`Completed:` fields) — no manual index update needed.

---

## Update Task

**Trigger:** User provides new info, email relates to existing task

**Minimum scope:** "update task file" with no fields named means at least **Timeline** (new entries) and **Asks** (new/completed items); other sections as needed.

**Steps:**
1. Read current task file
2. **If task file lacks `## Asks` section** (legacy file): insert empty section with both `### My Actions` and `### Waiting on Others` subsections before proceeding. Going forward all updates land in a properly-structured file.
3. Check if incoming information already exists (duplicate check)
3a. **Matching metadata review:** Every structured update must explicitly review `Scope`, `Exclude`, `Tags`, `Contacts/RACI`, and stable identifiers. Record the review in `matching_review` using exactly `checked-no-change`, `updated`, or `not-applicable` for each dimension. Apply changes in the same update when the source introduces:
    - a new EPD, PO, course, class-independent public identifier, or program ID → update `EPD` and/or Tags
    - a durable alias, acronym, vendor/program name, or geo shorthand → update Tags (maximum 4; keep only discriminating terms)
    - a new sender/recipient/stakeholder with a verified address → upsert Contacts and, when their responsibility is clear, RACI
    - a changed inclusion boundary → update Scope using positive-only wording
    - a discovered non-membership, adjacent task, phase, quarter, or workstream → update Exclude
    - a new email thread → preserve ConversationID on the Timeline entry
    - changed geo, category, due date, priority, or EPD → update the corresponding header field

    Record this review even when nothing changed (all `checked-no-change`); it keeps task metadata current for future email matching.
3b. **Named owners only:** Add an item to `My Actions` or `Waiting on Others` only when the source names who must act. If it's passive ("a local contact will be assigned", "EPD needs to be created"), don't guess an owner — a wrong owner makes the pending views and follow-ups chase the wrong person. Ask the user a short question ("Who should create the EPD row?") and add the item once they answer.
4. If duplicate → Notify user and skip
5. If new → for a user-requested update, show the changes and get approval. **Email-derived updates (email sync, or recording an email into a task) are written without asking first**; afterwards tell the user exactly what was written (see step 9). Rule 3b still applies — an unclear owner is a question, not a write.
6. **Detect Asks signals** in the user input or referenced email content:
    - **New owed-by-me** ("I'll do X" / "I'll send X" / "我会发" / "我会处理") → append `- [ ] {Due: Wkd Mon DD, YYYY} 🎯 to {person}: {what}` to `### My Actions`. For internal tasks / self-actions with no external recipient, append simply as `- [ ] {Due: Wkd Mon DD, YYYY} 🎯 {what}` (omit name/colon prefix).
    - **New owed-to-me** ("{person} will send X" / "等 {人} 回" / "等回复") → append `- {Due: Wkd Mon DD, YYYY} ⏳ {person}: {what}` to `### Waiting on Others` (using the expected response/due date at the start, or `TBD` if none specified)
   - **Owed-by-me fulfilled** (user says "done" / "已发" / "处理完了" referencing a specific item) → flip the matching `[ ]` to `[x]` (do NOT delete — kept for history)
   - **Owed-to-me received** (user says "got reply from X" / "X 回了") → remove the matching line from `### Waiting on Others`
   - When ambiguous which existing item is being closed, ask before flipping/removing.
6a. **Reclassify Current State items that are actually Asks.** Scan `## Current State` for items that have an external recipient (an action like "send X to {person}" / "notify {team}" / "deliver to {role}"). For each such item, propose to upgrade it to `Asks > My Actions` and remove from Current State (or leave if it's also a meaningful internal step). This keeps cross-task views (`owed`/`waiting`) accurate. Apply the [Asks vs Current State](../tasks/FORMATS.md#asks) rules from FORMATS.md. Ask user before moving — don't auto-rewrite long-standing items silently.
7. After approval, apply the complete update as one unit. During email sync, use `email_sync_apply.py`, which invokes the structured updater atomically. For direct task work, make the approved field/section changes together and immediately run `py -3 assistant_brain/scripts/validate_tasks.py --task-dir <task-file>`. Supported structured mutations include header fields, Tags, Contacts, RACI, Notes, Asks, Current State, and Timeline; never bypass the validation gate.
8. **Next-step check:** After every update, an open task should have at least one open item in `### My Actions` or `### Waiting on Others`. If both are empty, do not invent one — flag it to the user as "no next step recorded" (email sync: in the task's `Actions:` block per `EMAIL_SYNC_FORMAT.md`) and add the item once the user says what the task is waiting on.
9. Notify user of changes — list each item actually written (timeline entries, asks added/completed, field changes), not just "updated".

**Update Types:**

| Field | Action |
|-------|--------|
| status | Update status field in task file |
| timeline | Append new entry. **If sourced from email, entry_id is mandatory** — append `<!-- email:{ENTRY_ID} -->` to the line. Use the email's `Received` timestamp for the date — do NOT query OS for current time. |
| stakeholders | Update RACI matrix |
| due_date | Update due field in task file |
| priority/category/geo | Update the corresponding header field |
| EPD | Update the stable identifier header; use `—` only when none exists |
| tags | Add/remove discriminating aliases or identifiers; keep 1–4 unique tags |
| contacts | Upsert/remove correspondents by exact email address |
| RACI | Upsert/remove stakeholder roles by exact email address |
| notes | Append unique factual notes |
| matching review | Record Scope/Exclude/Tags/Contacts/Identifiers review for every structured update |
| asks (owed by me) | Append `- [ ] {Due: Wkd Mon DD, YYYY} 🎯 {person}: {what}` to `### My Actions`; flip `[x]` when fulfilled |
| asks (owed to me) | Append `- {Due: Wkd Mon DD, YYYY} ⏳ {person}: {what}` to `### Waiting on Others`; remove line when received |
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

---

## Event Recording

### Record Event

**Trigger:** Task created/completed, meeting, decision, tracking issue.

**Event formats:**

| Event Type | Icon | Source | Format |
|------------|------|--------|--------|
| Task Created | 📋 | Derived from `Created:` field | `- **{Wkd Mon DD, YYYY}**: 📋 Created [{TID}](path) - {title}` |
| Task Completed | ✅ | Derived from `Completed:` field | `- **{Wkd Mon DD, YYYY}**: ✅ Completed [{TID}](path) - {title}` |
| Task Blocked | 🔴 | Task file Status field | `- **{Wkd Mon DD, YYYY}**: 🔴 Blocked [{TID}](path) - {title}` |
| Task Update | - | Task file Timeline only | `- **{Wkd Mon DD, YYYY}** [{source}]: {description}` |

> **Note:** Recent Events are derived automatically by `dashboard.py` from task file metadata (Created/Completed fields within a 14-day window). No manual recording needed.

Keep last 12 months, delete older (optional).

### Query Flow

- **"What did I do recently?"** → `py -3 assistant_brain/scripts/dashboard.py` → Recent Events section (14-day window).
- **"What happened with T###?"** → Read task Timeline → check `Created:`/`Completed:` fields for lifecycle dates.
