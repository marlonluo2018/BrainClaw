# Things to Avoid
*(Failure patterns repeated 2 times)*

## [Error Type]
- Context: [when it happened]
- What went wrong: [description]
- Correction: [what to do instead]
- Count: 2/2
## Tool XML Format Error
- Context: Using list_files or other tools during startup
- What went wrong: Wrapped parameters in `<args>` tags like `<args><path>...</path></args>`, causing "Missing value for required parameter" error
- Correction: Use direct format `<tool_name><param>value</param></tool_name>` without `<args>` wrapper
- Count: 1/2


---
Entries: 1 | Updated: 2026-03-23
