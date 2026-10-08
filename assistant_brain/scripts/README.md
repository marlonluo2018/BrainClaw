# BrainClaw Scripts

This directory contains stable, reusable BrainClaw runtime and quality tooling only. The main repository uses an explicit `.gitignore` allowlist: scripts are private by default and become version-controlled only after they are reviewed for reuse, credentials, personal paths, employee/vendor contact lists, task-specific content, and test coverage.

The root `/adhoc/` directory remains Git-ignored and is the required location for disposable, one-off, migration, report, workbook, and task-delivery scripts.

## Allowlisted runtime and quality tooling

- `dashboard.py` - dashboard and operational views
- `email_sync.py` - orchestrates task-catalog extraction, evidence preparation, strict-noise filtering, Schema validation, and diagnostic rendering
- `email_sync_catalog.py` - extracts the structured active-task catalog and archived thread markers
- `email_sync_candidates.py` - prepares explicit candidate reasons without confidence scores or ownership decisions
- `email_sync_apply.py` - executes the published Draft 2020-12 plan Schema, validates cross-record invariants, and atomically applies classifier plans
- `followup.py` - stale-task and follow-up analysis
- `shared_config.py` - shared paths, parsing, and console setup
- `run_email_sync.py` - mandatory first executable step for every explicit full sync; fetches through the Outlook skill's public JSON contract, accepts verified empty results, and blocks overlapping active fetches (a lock older than 5 minutes is treated as abandoned); failures stop without fallback
- `manage_ignore_candidates.py` - manage email-sync ignore state
- `update_task.py` - structured task-file updates
- `validate_processes.py` - process schema/index validation
- `validate_tasks.py` - Draft 2020-12 validation for active task-file structure and matching metadata
- `generate_prompts.py` - regenerate tool prompt copies
- `check_links.py` - Markdown link integrity gate
- `doctor.py` - local environment diagnostics
- `ooxml_workbook.py` - dependency-free, PII-free OOXML workbook helper

## Promotion policy

Named workbook, report, plan, roster, evidence, migration, and training-deliverable scripts belong in root `/adhoc/` and stay local by default. Do not add them to the allowlist merely because they are useful once: first remove embedded people data, private paths, customer/vendor details, and task-specific constants, then extract a reusable interface and add tests.

If a local script becomes critical, promote its generic implementation to an allowlisted module while keeping private inputs in ignored task/download files.


