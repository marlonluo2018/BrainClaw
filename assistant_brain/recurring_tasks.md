 # Recurring Tasks

Tasks that automatically trigger on a schedule.

## Task Creation Rules

On startup, calculate next due date from schedule and last_completed. Create a new task file ONLY if current date matches the schedule period.

## Format Rules

- **trigger:** `schedule` (calendar-based automatic trigger) or `email` (triggered upon receiving specific notification email)
- **last_completed:** YYYY-MM format - When the task was last executed (completion date)
- **last_period:** (Optional) Period covered for reporting tasks (e.g., "2026-02" for Feb report, "2026-Q1" for Q1 report)
- Use ISO 8601 format for consistency and clarity

## Active Tasks

```yaml
recurring_tasks:
  - id: R001
    name: "I&D BUR Review - Function Team Update"
    trigger: email
    schedule: "monthly on email notice"
    email_trigger:
      from: "Yu Jie Ai <aiyujie@cn.ibm.com>"
      subject_keywords: ["BUR", "BUR Review", "Function Team Update"]
    priority: P1
    category: Management
    geo: China
    note: "Triggered upon receiving monthly BUR review meeting invitation / update notice from Yu Jie Ai. Suggest creating task T### - I&D BUR Review - <Month YYYY>."
    last_completed: ""
    last_period: "2026-10"

  - id: R002
    name: "Send L&K Learning Report to I&D Sector Focals"
    trigger: schedule
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
    source_folder: "https://ibm.ent.box.com/folder/364440541230"
    upload_folder: "https://ibm.ent.box.com/folder/368947686653"
    note: "1) Download raw report zip and Credential Priority Certs (T2G) to Downloads; 2) Run script: py -3 assistant_brain/scripts/split_lk_report_by_focal.py '<zip_path>'; 3) Script automatically handles password decryption (HC: learningreportYYYYMM, others: learning-report), HC mapping, and generates 6 sector workbooks with 4 sheets (T2G, Industry Badge, Language, T40); 4) Upload output files to upload_folder; 5) Send Outlook notification email to focals (cc Fei Ye)"
    script: "py -3 assistant_brain/scripts/split_lk_report_by_focal.py \"<zip_or_folder>\""
    last_completed: "2026-10"
    last_period: "2026-09"
```

