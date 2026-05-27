# Configuration

## User
```json
{
  "name": "Marlon Luo",
  "email": "luomn@cn.ibm.com",
  "email_display_name": "Meng Ning Luo",
  "title": "Learning Consultant",
  "organization": "Learning & Knowledge(L&K)",
  "language": "English",
  "tone": "Friendly",
  "timezone": "+08:00",
  "timezone_name": "Asia/Shanghai (UTC+8)"
}
```

## System
- OS: Windows 11
- Python command: `py -3 full/path/script.py` (no `cd`, no `&&`)
- Shell: PowerShell
- PowerShell syntax: `;` for sequential, `-and` for conditional (no `&&`)
- Bash syntax: `&&` for conditional chaining
- Recent Events Window: 14 days (events older than this are archived to timeline)

## Skills

> All skills live under `assistant_brain/skills/*/`. Scanned at startup by frontmatter.
> To invoke: `py -3 "assistant_brain/skills/{skill-folder}/scripts/{script}" <command> [args]`

## Tasks

> **See [`tasks/FORMATS.md`](tasks/FORMATS.md) for task formats, templates, and data structures**

### Startup Display Format

> **Focus-driven, beautified for scan-ability.** Startup uses markdown headings to create clear visual sections: a prominent `# ✅ Ready` anchor (separates startup from prior thinking), then sectioned task buckets with priority-driven hierarchy. Source data is queue.md only — no individual task file reads.

**Output skeleton (rendered as markdown):**

```markdown
## ✅ Ready | {weekday} {YYYY-MM-DD HH:mm} | User: {Name} | OS: {OS}

Skills: `{skill_name_1}` · `{skill_name_2}` · `{skill_name_3}` · ...
Processes: `{process_name_1}` · `{process_name_2}` · `{process_name_3}` · ...
Stakeholders: `{name_1}` · `{name_2}` · `{name_3}` · ... (+N more if > 10)
Tasks: {N} active · {N} overdue · {N} owed · {N} waiting

---

### {flag} {Country} ({N})

**P1 · {N}**
- {status_icon} [TID](path) {Title} — Due {date}
  - {date} {what} → {person}
  - {date} {what} ← {person}
- {status_icon} [TID](path) {Title} — was due {date} (**{N}d overdue**)

**P2 · {N}**
- {status_icon} [TID](path) {Title} — Due {date}
- {status_icon} [TID](path) {Title} (Master) — Due {date}
  - ↳ {status_icon} [TID](path) {Subtask Title} — Due {date}
    - {date} {what} (blocker note) → {person}
    - {date} {what} ← {person}
  - ↳ {status_icon} [TID](path) {Subtask Title} — P1 · was due {date} (**{N}d overdue**)

**P3 · {N}**
- {status_icon} [TID](path) {Title} — Due {date}

### {flag} {Country} ({N})

(repeat per country)

---

→ `status T###` · `pending` · `pending out` · `pending in` · `before {person}` · `review` · `taskboard`
```

**Rules:**

1. **Ready line is single-line h2** (`## ✅ Ready | {date} | User: {Name} | OS: {OS}`). Visual anchor confirming startup is complete. Use `|` separator.
2. **Four info lines** under Ready:
   - `Skills: \`name1\` · \`name2\` · ...` — list each skill name (from `skills/*/SKILL.md` frontmatter), backtick-wrapped
   - `Processes: \`name1\` · \`name2\` · ...` — list each process name (from `process/README.md` index)
   - `Contacts: \`name1\` · \`name2\` · ...` — list each contact display name (from `contacts.md`). If more than 10, show the first 10 followed by "(+N more)"
   - `Tasks: {N} active · {N} overdue` — counts from queue.md
3. **Two horizontal rules `---`**: after counts line, and before footer command bar. Three visual zones: Ready · Tasks · Commands.
4. **Primary grouping = country** (h3 with national flag emoji). Country ordering: by total task count, descending. Ties broken alphabetically.
5. **Secondary grouping inside country = priority** as bold sub-labels (`**P1 · N**`, `**P2 · N**`, `**P3 · N**`). Not headings — keeps the page compact. Order: P1 → P2 → P3. Skip priority groups that are empty within a country.
6. **Task rows.** Each task starts with one line. Format:
   `- {status_icon} [TID](path) {Title} — Due {date}`
   - `{status_icon}` is `📋` (Not Started) / `⏳` (In Progress) / `🔴` (Blocked).
   - For overdue rows: replace `Due {date}` with `was due {date} (**{N}d overdue**)`. Bold the Nd.
   - **Country and Priority are NOT repeated** on each row — they're implied by the section the row appears in.
   - If task has pending asks, they appear as indented sub-lines immediately below (see rule 14).
7. **Master tasks** appear in their own priority section with `(Master)` suffix on the title. Subtasks listed below as indented `↳` lines.
8. **Subtasks render as a nested markdown list** under the master. The line MUST start with two literal spaces, then a hyphen, a space, the `↳` arrow, and a space — followed by the task content. Without this nested-list syntax, markdown collapses the subtask into the master line. Subtask content format: `{status_icon} [TID](path) {Title} — Due {date}`.
   - Within same country and priority as master: priority/country implied, omit them on the row.
   - When subtask priority **differs** from master: explicitly include the subtask's priority. Example: P1 subtask under P2 master → content becomes `{status_icon} [TID](path) {Title} — P1 · was due {date} (**{N}d overdue**)`.
   - Subtasks always belong structurally under their master — they are NOT repeated in their own priority section, even if priority differs.
9. **Overdue is shown inline** (bold `(**Nd overdue**)` on the task row) — no separate Overdue section. The overdue count appears in the top counts line for triage at a glance.
10. **Metadata separator `·`** (middot U+00B7) within a task row; `|` only on the Ready line.
11. **Command footer**: arrow `→` prefix, commands in backticks (renders as code, indicates "type this"), middot separator. Common shortest path: `status T###` first.
12. **Pending asks shown inline** under each task that has them. This gives immediate visibility into what's blocking progress and what you're waiting on.
13. **Source: queue.md + active task file Asks sections.** Queue.md provides the task list structure; each active task file is scanned for its `## Asks` section to populate inline pending lines.
14. **Asks rendering rules:**
    - Asks appear as indented sub-lines under their task (one extra indent level beyond the task row).
    - Format: `- {date} {what} → {person}` (owed by me, unchecked `[ ]` items only) / `- {date} {what} ← {person}` (owed to me).
    - Date comes first (MM-DD or full YYYY-MM-DD if not current year), then action, then person — reads as "by {date}, {action} directed at {person}" or "since {date}, {action} waiting on {person}".
    - For subtasks: asks indent one level deeper than the `↳` line (4 spaces total from root).
    - If a task has zero pending asks (both sections empty or all owed-by-me checked off), show no sub-lines — task stays single-line.
    - Parenthetical notes (e.g., blocker conditions) from the task file are preserved: `- Assign LDM (after EPD created) → Jibu`.
    - Info line counts: `{N} owed` = total unchecked owed-by-me items across all tasks; `{N} waiting` = total owed-to-me items across all tasks.

**Country flag mapping** (extend as needed):
- 🇨🇳 China · 🇮🇳 India · 🇵🇭 Philippines · 🇸🇬 Singapore · 🌏 APAC · 🌐 Global

### `taskboard` (on-demand full task list)

When the user says `taskboard`, `show queue`, or `全部任务` — re-render the **same output as startup** (see "Startup Display Format" above), including inline pending asks. Source is queue.md + active task file Asks sections.

`taskboard` is effectively a "redisplay startup task list" shortcut for use mid-session.

### `pending` Display Format

**Triggers:** `pending`, `show pending`, `show asks`
**Variants:** `pending out` (I owe only), `pending in` (waiting on only)

**Format: Hybrid — by task (I owe) + by person (Waiting on)**

```markdown
## → I owe ({N})

**T### {Full Task Title}**
- {date} {what} → {Person}
- {date} {what} → {Person}

**T### {Full Task Title}**
- {date} {what} → {Person}

---

## ← Waiting on ({N})

### {flag} {Country}

**T### {Full Task Title}**
- {date} {what} ← {Person}
- {date} {what} ← {Person}

**T### {Full Task Title}**
- {date} {what} ← {Person}

### {flag} {Country}

**T### {Full Task Title}**
- {what} ← {Person}
```

**Rules:**
1. Section headers: `→ I owe` (my actions), `← Waiting on` (others' actions)
2. Horizontal rule `---` separates the two sections
3. **Both sections:** Primary grouping by Geo (h3 with flag emoji), secondary grouping by task (bold `T### {Full Task Title}`)
4. **I owe items:** bullets with `→ {Person}` at end
5. **Waiting on items:** bullets with `← {Person}` at end
6. Task ID includes file link: `[T###](path) {Full Task Title}` — same link format as taskboard
7. Use the full task title as it appears in queue.md — no abbreviations
7. Country ordering: by item count descending. Tasks sorted by priority (P1 first), then due date within each country
8. No tables — pure markdown list
9. `pending out` shows only the "I owe" section; `pending in` shows only "Waiting on"
10. Source: All active task file `## Asks` sections (unchecked `[ ]` owed-by-me + all owed-to-me non-struck items)

## Paths
- Windows: `%USERPROFILE%/assistant_brain/`
- Unix: `~/.assistant_brain/`
- Current: `./assistant_brain/`

## Download Settings
- Default download path: `./downloads/` (project downloads folder)
- Email attachments: Save to project downloads folder
- Purpose: Downloaded files (Excel, PPT, etc.) can be directly processed by skills
