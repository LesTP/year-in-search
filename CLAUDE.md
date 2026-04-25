# Year-in-Search — Project Context

Ridge-plot visualization pipeline for Hacker News "Year in Tech" topics.

## Key Docs
- **PROJECT.md** — scope, constraints, success criteria
- **ARCHITECTURE.md** — component map, data flow, implementation sequence
- **DESIGN.md** — full pipeline spec with scoring formulas and visualization details
- **GOVERNANCE.md** — development process
- **DEVPLAN.md** — current phase and status
- **DEVLOG.md** — what happened
- **DECISIONS.md** — design decisions with rationale

## Quick Reference

### Execution
```bash
python -m src.ingest --year 2024
python -m src.embed --year 2024
python -m src.cluster --year 2024
```

### Data Schema Quirks (HuggingFace HN Dataset)
- `type` is integer: `1` = story (not string)
- `time` is datetime string (not unix timestamp)
- `score` and `descendants` are strings — need `pd.to_numeric()`
- Monthly parquet files at `data/{year}/{year}-{mm}.parquet`

### Toolkit
- `toolkit.embedding` and `toolkit.clustering` — installed as editable package, import directly
- No `sys.path` hacks needed

### Current Status
Phase 1 complete (ingest, embed, cluster). Phase 2 (score & classify) not started. See DEVPLAN.md.
