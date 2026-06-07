# Web Search & Browse Workflow

> Use Tavily MCP tools for web search and content extraction.

## Tools Available

| Tool | Credit Cost | Purpose |
|------|-------------|---------|
| `tavily_search` | 1 | Search keywords, return links + snippets |
| `tavily_extract` | 1/URL | Extract content from a specific URL |
| `tavily_crawl` | 1+/page | Crawl multiple pages from a starting URL |
| `tavily_map` | 1 | Map site structure, return link list |
| `tavily_research` | ~20 | Deep research, synthesize from multiple sources |

## Cost-First Decision Flow

```
What does the user need?
├── Search for info / find links → tavily_search (1 credit)
├── View content of a known URL → tavily_extract (1 credit)
├── Discover pages on a site → tavily_map (1 credit)
├── Scrape multiple pages from a site → tavily_crawl (per page)
└── Multi-source deep analysis → tavily_research (~20 credits)
    ⚠️ Only use research when:
    - User explicitly requests deep research
    - extract returns clearly incomplete content AND user needs full details
    - Cross-verification from multiple sources is required
```

## Standard Procedure (Cost-Efficient)

**Most scenarios need only 2 steps, costing 2 credits:**

1. `tavily_search` — find relevant links and summaries
2. `tavily_extract` — extract full content from the best URL

**Progressive strategy when page content is incomplete:**

1. Try `tavily_extract` with `extract_depth: "advanced"` (1 credit)
2. If still incomplete, `tavily_search` for alternative sources, then extract those (2 credits)
3. Only then consider `tavily_research` — inform user it costs ~20 credits and get confirmation

## Usage Examples

### Search

```
tavily_search:
  query: "Red Hat DO188 course outline prerequisites"
  max_results: 5
```

### Extract (view a web page)

```
tavily_extract:
  urls: ["https://example.com/page"]
  extract_depth: "advanced"    ← recommended for JS-heavy pages
  query: "keywords"            ← optional, ranks content by relevance
```

### Crawl (scrape multiple pages)

```
tavily_crawl:
  url: "https://docs.example.com/start"
  max_depth: 2
  max_breadth: 10
  instructions: "only crawl documentation pages"
```

### Research (deep dive — use sparingly)

```
tavily_research:
  input: "detailed description of research need"
  model: "mini"    ← narrow topics; use "pro" for broad topics
```

## Rules

- **Autonomous:** search and extract (read-only operations, no approval needed)
- **Requires confirmation:** research — high cost, inform user (~20 credits) before using
- Include source links when presenting search results
- Tavily does not depend on Google/Bing — works regardless of regional restrictions
