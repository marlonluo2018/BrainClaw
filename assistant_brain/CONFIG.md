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

## Email Signature
```
Marlon Luo
Learning Consultant, Delivery Shared Services, L&K
Slack - @Marlon Luo
```

## System
- OS: Windows 11
- Python command: `py -3 full/path/script.py` (from project root, no `cd`, no `&&`)
- Shell: PowerShell
- PowerShell syntax: `;` for sequential, `-and` for conditional (no `&&`)
- Bash syntax: `&&` for conditional chaining
- Recent Events Window: 14 days (events older than this are archived to timeline)

## Tasks

> **See [`tasks/FORMATS.md`](tasks/FORMATS.md) for task formats, templates, and data structures**

### Startup Display Format

**Load tasks from:** [`tasks/queue.md`](tasks/queue.md)

**Format (one line per task):**
```
[TID](path) Status Title (Priority, Geo, Due: date)
```

**Display rules:**
1. **Priority ordering:** P1 first → P2 → P3
2. **P1 tasks due today/overdue:** Prefix with ⚠️
3. **ALL top-level tasks (standalone, P1, master):** Must have bullet point `-` prefix
4. **Master tasks:** Show "(Master)" suffix, then subtasks below with `↳` prefix
5. **Subtasks:** Indented with `  - ↳` format (2 spaces + bullet + arrow), no priority/geo/due details
6. **Blank line** between priority groups

**Format template:**
```
## ✅ Active Tasks ({count} total)

- ⚠️ [TID](path) Status Title (P1, Geo, Due: YYYY-MM-DD)

- [TID](path) Status Title (P2, Geo, Due: date)
- [TID](path) Status Title (P2, Geo, Due: date)

- [TID](path) Status Title (Master) (P2, Geo, Due: date)
  - ↳ [TID](path) Status Subtask title
  - ↳ [TID](path) Status Subtask title
```

**Key formatting points:**
- Top-level tasks: `- [TID](path) Status Title (Priority, Geo, Due: date)`
- P1 due today/overdue: `- ⚠️ [TID](path) Status Title (P1, Geo, Due: date)`
- Subtasks: `  - ↳ [TID](path) Status Title` (indented 2 spaces)

## Paths
- Windows: `%USERPROFILE%/assistant_brain/`
- Unix: `~/.assistant_brain/`
- Current: `./assistant_brain/`

## Download Settings
- Default download path: `./downloads/` (project downloads folder)
- Email attachments: Save to project downloads folder
- Purpose: Downloaded files (Excel, PPT, etc.) can be directly processed by skills
