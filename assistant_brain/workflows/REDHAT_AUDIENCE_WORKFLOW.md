# Red Hat Audience Targeting & Enrollment Shortlist Workflow

> **Standardized workflow for extracting promotional audiences, evaluating class waitlists, and selecting final candidate shortlists across Red Hat training courses in FNC India.**

---

## 📅 Lifecycle Timeline & Operational Phases

| Timeline Stage | Action Phase | Purpose & Execution |
|----------------|--------------|---------------------|
| **2 Weeks Ahead (Monday)** | **Phase 1: Event Promotion** | Dispatch course announcement eCards to Sector / Practice SPOCs. |
| **2 Weeks Ahead (Thu / Fri)** | **Phase 2: Target Audience Extraction** | Check class waitlist size. If < 30 registrations, run **Multi-Source Audience Extraction (5 Data Sources)** to generate Top 1,000–1,500 target candidates and dispatch large-audience batch-forward eCards. |
| **1 Week Ahead (Monday)** | **Phase 3: Final Shortlist & Roster Selection** | Run **Enrollment Evaluation Engine** on downloaded roster CSV to score waitlisted candidates, filter exclusions, select **Top 12 Confirmed (Green)** + **Backups (Yellow)**, and export styled color-coded Excel workbook for LDM. |
| **Delivery Week (Mon–Fri)** | **Phase 4: Class Delivery & Monitoring** | Track attendance, resolve access issues, collect feedback upon completion. |

---

## 🛠️ Phase 2: Multi-Source Target Audience Extraction (2 Weeks Ahead)

Used when class registrations are low (< 30) to generate a targeted promotion list.

### 1. Required Data Inputs (5 Data Sources)

| # | Data Report | Source | Purpose |
|---|-------------|--------|---------|
| **1** | **Certifications & Badges Report** | T2G / Credly export (`Credential T2G publ. Report...csv`) | Identifies active & expired prerequisite certifications (`EX200`, `EX280`, `EX294`, etc.) and excludes active target cert holders. |
| **2** | **Prerequisite Transcripts Report** | YourLearning / Transcript detail (`V3IbmReportTranscriptsDetail...csv`) | Identifies learners who completed prerequisite courses (`DO180`, `DO280`, `RH124`, `RH134`, `RH294`) via self-paced or virtual classroom. |
| **3** | **Target Course Self-Paced Transcripts** | YourLearning / Transcript detail (`V3IbmReportTranscriptsDetail...csv`) | Identifies learners who completed the self-paced version of the target Red Hat course (e.g. `DO316`, `DO374`, `DO288`). |
| **4** | **Headcount Database** | GDMIS PIR export (`extracted_columns...csv`) | Provides employee intranet ID, job role/JRSS, practice, and band for skill-equivalent scoring. |
| **5** | **Past 1-Year Class Attendance Report** | YourLearning / Transcript detail (`V3IbmReportTranscriptsDetail...csv`) | Excludes learners who already attended the target class in the last 12 months. |

---

### 2. Multi-Source Scoring & Selection Engine

#### Pass 1: Global Exclusions (Clean-up)
Before scoring, exclude candidates matching ANY of these conditions:
1. **Already Certified:** Holds an **active** target certification (e.g., `EX316` for DO316, `EX374` for DO374, `EX288` for DO288).
2. **Past 1-Year Attendees:** Appears in the past 1-year attendance report for the same course.
3. **Current Enrollees:** Already waitlisted or confirmed in the upcoming class roster (`class_<id>_enrollments.csv`).
4. **Geographic / Employment Ineligibility:** Non-India practitioners (emails not ending with `@in.ibm.com`) or non-regular employee types.

#### Pass 2: Multi-Source Inclusion Scoring
Eligible candidates in the headcount are evaluated and awarded cumulative points:

| Priority Tier | Criterion | Points | Description |
|---------------|-----------|--------|-------------|
| **Tier 1** | **Prerequisite Certification** | **+100 pts** | Holds a valid OR expired prerequisite credential from the T2G report (see Red Hat Course Mapping Table below). |
| **Tier 2** | **Prerequisite Course Completion** | **+80 pts** | Completed prerequisite course(s) via self-paced or ILT / virtual classroom. |
| **Tier 3** | **Self-Paced Target Completion** | **+60 pts** | Completed the self-paced version of the target Red Hat course. |
| **Tier 4** | **Skill / Role Match** | **+15 to +35 pts** | Skill-equivalent match in GDMIS `Job_Role_Skill_Set`: <br>• Red Hat / OpenShift / K8s / Virt: **+35 pts** <br>• Linux / Unix / SysAdmin / RHEL / DevOps: **+25 pts** <br>• Developer / Architect / Infrastructure: **+15 pts** |
| **Boost** | **Target Practices** | **+18 pts** | Practice matches DevSecOps, Platform Eng, IBM & Red Hat, Custom App, Hybrid Cloud & Data, Data Services, App Ops. |
| **Boost** | **Target Bands** | **+6 pts** | Bands `6A`, `6B`, `6G`, `7A`, `7B`, `8`/`08`, `9`/`09`. |

---

## 📋 Red Hat Course Reference Rules Table

| Course Code | Course Name | Prerequisite Credentials *(Tier 1 - 100 pts)* | Prerequisite Courses *(Tier 2 - 80 pts)* | Target Cert Exclusions *(Pass 1 Exclude)* |
|-------------|-------------|-----------------------------------------------|------------------------------------------|-------------------------------------------|
| **DO316** | OpenShift Virtualization | `EX200` (RHCSA), `EX280` (OpenShift Admin) | `DO180`, `DO280`, `RH124`, `RH134`, `DO188` | `EX316` (OpenShift Virtualization) |
| **DO374** | Ansible Automation Platform | `EX294` / `RHCE` (Ansible) | `RH294`, `AU294`, `RH124`, `RH134` | `EX374` (Ansible Advanced Automation) |
| **RH294** | Linux Automation with Ansible | `EX200` (RHCSA) | `RH124`, `RH134` | `EX294` / `RHCE` / Any active Ansible cert |
| **DO288** | OpenShift Developer II | `EX188`, `EX180`, `EX280` | `DO188`, `DO180`, `DO280` | `EX288` (OpenShift App Developer) |
| **DO280** | OpenShift Administration II | `EX200` (RHCSA) | `DO180`, `RH124`, `RH134` | `EX280` (OpenShift Administrator) |
| **DO188** | Intro to Containers with Podman | *None (Linux/Unix role priority)* | `RH124`, `RH134` | `EX188`, `EX180`, `EX280`, `EX288`, `EX380` |
| **AI267** | AI/ML on OpenShift AI | `EX280` (OpenShift Admin), `EX188` | `DO280`, `DO188`, `DO288` | `EX267` (OpenShift AI Developer) |

---

## 📊 Phase 3: Final Shortlist & Roster Selection (1 Week Ahead Monday)

Executed exactly **1 week prior** to course start date to evaluate waitlists and produce the official candidate shortlist.

### Step 1: Download Live Class Roster
Execute Playwright downloader to pull the latest registration CSV from YourLearning:
```bash
py -3 "assistant_brain/skills/enrollment-downloader/scripts/download_roster.py" <class_id>
```

### Step 2: Run Enrollment Shortlist Evaluator
Execute `check_enrollment.py` to match waitlisted learners against headcount & transcripts, apply exclusions, score candidates, and export a color-coded Excel workbook:
```bash
py -3 "assistant_brain/skills/enrollment-downloader/scripts/check_enrollment.py" <class_id> [--hc <headcount_csv>] [--history <past_attendance_csv>] [--export <output_excel_path>]
```

#### Shortlist Evaluation Logic:
- **Filter 1 (Exclusions):** Exclude non-India candidates (Country Code != `744` / email != `@in.ibm.com`), non-regular employee types (Type != `P`), and prior course completions.
- **Filter 2 (Scoring & Priority Ranking):** Score valid waitlisted candidates based on role fit (`+30`), target band (`+10`), and prerequisite credentials (`+100`). Waitlist position is used as the baseline tiebreaker.
- **Color-Coded Output Excel Workbook:**
  - 🟩 **Green (Confirmed):** Top 12 scored, qualified learners.
  - 🟨 **Yellow (Backup):** Next eligible runners-up in waitlist order.
  - 🟥 **Red (Excluded):** Ineligible or duplicate candidates.

### Step 3: Handoff to LDM
Share the final color-coded Excel workbook with LDM B Sowmya for LMS confirmation and RHID / registration notice dispatch.

---

## 4. Automation Pattern

Audience extraction can be automated using standard Python scripts:

```bash
py -3 "scripts/build_audience.py" \
  --cert-file "<path_to_t2g_report>" \
  --prereq-file "<path_to_prereq_transcript>" \
  --selfpaced-file "<path_to_selfpaced_transcript>" \
  --hc-file "<path_to_gdmis_headcount>" \
  --past-file "<path_to_past_attendance>" \
  --course-code "<COURSE_CODE>" \
  --target-count 1000
```
