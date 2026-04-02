# Recurring Tasks

Tasks that automatically trigger on a schedule. Added to daily log on startup.

## Format Rules

- **last_completed:** YYYY-MM format - When the task was last executed (completion date)
- **last_period:** (Optional) Period covered for reporting tasks (e.g., "2026-02" for Feb report, "2026-Q1" for Q1 report)
- Use ISO 8601 format for consistency and clarity

## Active Tasks

```yaml
recurring_tasks:
  - id: "R001"
    name: "Send Philippines L&K Spend Invoice to Mickeal Martinez"
    schedule: "last week of every quarter"
    priority: Medium
    category: Admin
    contact: "Mickeal Martinez <Mickeal.Martinez@ibm.com>"
    note: "Submit quarterly invoice for Philippines L&K spend"
    last_completed: "2026-03"  # When task was executed (March 2026)
    last_period: "2026-Q1"  # Which quarter's invoice was sent (Q1 2026)

  - id: "R002"
    name: "Send L&K Learning Report to I&D Sector Focals"
    schedule: "beginning of every month"
    priority: Medium
    category: Reporting
    contacts:
      - "Yi Tian Li <liyitian@cn.ibm.com> (Cross Sector Focal)"
      - "Cong Wang <Cong.WangDL@ibm.com> (Client Engagement Lab sector focal)"
      - "Hu Yun Li <lilhylhy@cn.ibm.com> (Distribution sector focal)"
      - "BING YAN <ybingdl@cn.ibm.com> (Industrial sector focal)"
      - "XU DONG XUAN <xuanxud@cn.ibm.com> (Finance Service sector focal)"
      - "HUI QING CHEN <huiqingc@cn.ibm.com> (Public & Communication sector focal)"
    cc: "Fei Ye <feiye@cn.ibm.com>"
    folder_link: "https://ibm.ent.box.com/folder/368947686653"
    note: "1) Upload previous month's L&K learning report to I&D sector Box folder; 2) Send email notification to contacts that folder has been updated with new data"
    last_completed: "2026-04"  # When task was executed (April 2026)
    last_period: "2026-03"  # Which month's report was sent (March 2026)
```

