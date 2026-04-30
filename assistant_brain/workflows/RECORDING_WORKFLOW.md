# Recording Workflow

> Event and memory recording workflow - orchestrates skills for documentation

---

## Record Event

**Trigger:** Task created/completed, meeting, decision, tracking issue

**Steps:**
1. Determine event type
2. Call `recording` (operation: event-record) with appropriate parameters
3. Confirm recording location

### Event Types & Locations

|| Event Type | Icon | Location |
||------------|------|----------|
|| Task Created | 📋 | queue.md Recent Events |
|| Task Completed | ✅ | queue.md Recent Events |
|| Task Blocked | 🔴 | queue.md Recent Events |
|| Meeting/Decision | 🤝 | queue.md Recent Events |
|| Tracking Issue | 📊 | queue.md Recent Events |
|| Task Update | - | Task file Timeline only |

### What NOT to Record in queue.md
- Email sent/received → Task file only
- Task updates → Task file only
- Minor progress → Task file only

---

## Archive Old Events

**Trigger:** Startup, events exceed window

**Steps:**
1. Check CONFIG.md "Recent Events Window" (default: 14 days)
2. Find events older than window
3. Move to `tasks/history/timeline_YYYY-MM.md`
4. Create monthly file if not exists
5. Keep last 12 months, delete older (optional)

---

## Record Memory

**Trigger:** User preference, repeated mistake, frequent contact

### Memory Types

|| File | Trigger | Skip |
||------|---------|------|
|| preferences.md | User explicitly states preference | Technical details |
|| things_to_avoid.md | Work mistake repeats 2+ times | Technical errors |
|| contacts.md | External contact mentioned 3+ times | Internal colleagues |
|| tracking.md | Item requires cross-session monitoring | Temporary states |

### Recording Steps
1. Detect candidate → Check threshold
2. Filter → Work-related only
3. Show user → Ask for approval
4. Record → If approved

---

## things_to_avoid.md Format

**Trigger:** Work mistake repeats 2+ times

**Entry Template:**
```markdown
## {Title}
- Context: {When/where}
- What went wrong: {What failed}
- Correction: {Right way}
- Count: {X}/2 [✓ VERIFIED when 2/2]
```

---

## Query Flow

### "What did I do recently?"
1. Read queue.md Recent Events
2. Show activities within window

### "What happened with T019?"
1. Read queue.md Recent Events → Find T019 creation/completion
2. Read T019.md Timeline → Get detailed history
3. Combine information

---

## Skills Used

|| Skill | Operations Used | Purpose |
||-------|-----------------|---------|
|| `recording` | event-record | Record events to queue.md or task timeline |
