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

### Display Formats

> Startup, taskboard, and pending views are handled by `scripts/dashboard.py`.
> For `status T###`, `before {person}`, and `review` formats, see [`views_config.md`](views_config.md).

## Paths
- Windows: `%USERPROFILE%/assistant_brain/`
- Unix: `~/.assistant_brain/`
- Current: `./assistant_brain/`

## Download Settings
- Default download path: `./downloads/` (project downloads folder)
- Email attachments: Save to project downloads folder
- Purpose: Downloaded files (Excel, PPT, etc.) can be directly processed by skills
