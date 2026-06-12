# Recording Workflow

> Event and memory recording workflow

---

## Record Event

**Trigger:** Task created/completed, meeting, decision, tracking issue

**Steps:**
1. Determine event type
2. Record to appropriate location using format below
3. Confirm recording location

### Event Types & Formats

| Event Type | Icon | Source | Format |
|------------|------|--------|--------|
| Task Created | 📋 | Derived from `Created:` field | `- **{Wkd Mon DD, YYYY}**: 📋 Created [{TID}](path) - {title}` |
| Task Completed | ✅ | Derived from `Completed:` field | `- **{Wkd Mon DD, YYYY}**: ✅ Completed [{TID}](path) - {title}` |
| Task Blocked | 🔴 | Task file Status field | `- **{Wkd Mon DD, YYYY}**: 🔴 Blocked [{TID}](path) - {title}` |
| Task Update | - | Task file Timeline only | `- **{Wkd Mon DD, YYYY}** [{source}]: {description}` |

> **Note:** Recent Events are derived automatically by `dashboard.py` from task file metadata (Created/Completed fields within a 14-day window). No manual recording needed.

---

5. Keep last 12 months, delete older (optional)

---

## Record Memory

**Trigger:** User preference, repeated mistake, frequent contact

### Memory Types

| File | Trigger | Skip |
|------|---------|------|
| preferences.md | User explicitly states preference | Technical details |
| things_to_avoid.md | Work mistake repeats 2+ times | Technical errors |
| contacts.md | External contact mentioned 3+ times | Internal colleagues |
| tracking.md | Item requires cross-session monitoring | Temporary states |

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

1. Run `py -3 assistant_brain/scripts/dashboard.py` → Recent Events section
2. Show activities within 14-day window

### "What happened with T019?"

1. Read T019.md Timeline → Get detailed history
2. Check `Created:`/`Completed:` fields for lifecycle dates
