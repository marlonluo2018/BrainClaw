# Recurring Tasks

Tasks that automatically trigger on a schedule. Added to daily log on startup.

## Active Tasks

```yaml
recurring_tasks:
  - name: "Send Philippines L&K Spend Invoice to Mickeal Martinez"
    schedule: "last week of every quarter"
    priority: High
    category: Admin
    contact: "Mickeal Martinez <Mickeal.Martinez@ibm.com>"
    note: "Submit quarterly invoice for Philippines L&K spend"
    last_completed: "Q1 2026"  # Update this field when task is completed
```

## Schedule Examples

| Frequency | Example |
|-----------|---------|
| Daily | `every day at 9am` |
| Weekly | `every Friday at 5pm` |
| Monthly | `on the 28th of every month at 6pm` |
| Quarterly | `first Monday of every quarter at 10am` |
| Custom | `every 2 weeks on Monday at 2pm` |
