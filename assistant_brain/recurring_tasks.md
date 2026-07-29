 # Recurring Tasks

Tasks that automatically trigger on a schedule.

## Task Creation Rules

On startup, calculate next due date from schedule and last_completed. Create a new task file ONLY if current date matches the schedule period.

## Format Rules

- **last_completed:** YYYY-MM format - When the task was last executed (completion date)
- **last_period:** (Optional) Period covered for reporting tasks (e.g., "2026-02" for Feb report, "2026-Q1" for Q1 report)
- Use ISO 8601 format for consistency and clarity

## Active Tasks

```yaml
recurring_tasks: []
```

