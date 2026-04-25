# Year-in-Search — Project Context

Ridge-plot visualization pipeline for Hacker News "Year in Tech" topics. All 7 phases complete.

## Key Docs
- **README.md** — methodology, 2024 results, setup instructions
- **PROJECT.md** — scope, constraints, success criteria
- **ARCHITECTURE.md** — component map, data flow, implementation sequence
- **DESIGN.md** — full pipeline spec with scoring formulas, visualization details, LLM labeling workflow
- **GOVERNANCE.md** — development process (phase lifecycle, completion protocol, commit rules)
- **DEVPLAN.md** — current status and pending post-pipeline work
- **DEVLOG.md** — what happened in each phase
- **DECISIONS.md** — design decisions D-1 through D-6 with rationale

## Quick Reference

### Execution
```bash
python -m src.ingest --year 2024
python -m src.embed --year 2024
python -m src.cluster --year 2024
python -m src.score --year 2024
python -m src.label --year 2024
python -m src.curate --year 2024       # then edit data/curated/2024_draft_topics.csv
python -m src.visualize --year 2024    # outputs to output/
```

### Pipeline Modules
| Module | Phase | What it does |
|--------|-------|-------------|
| `ingest.py` | 1 | Download HN data from HuggingFace, filter, compute attention scores |
| `embed.py` | 2 | Encode titles into 384-dim vectors via `toolkit.embedding` |
| `cluster.py` | 3 | HDBSCAN + UMAP clustering via `toolkit.clustering` |
| `score.py` | 4 | Per-cluster time series (53 bins), metrics, spike/sustained/moderate classification |
| `label.py` | 5 | Auto-label clusters from highest-attention post title |
| `curate.py` | 6 | Export top-50 ranked CSV for human review |
| `visualize.py` | 7 | Ridge plot with peak-week color gradient and Gaussian smoothing (sigma=1.0) |

### Data Schema Quirks (HuggingFace HN Dataset)
- `type` is integer: `1` = story (not string)
- `time` is datetime string (not unix timestamp)
- `score` and `descendants` are strings — need `pd.to_numeric()`
- Monthly parquet files at `data/{year}/{year}-{mm}.parquet`
- ~132 posts have empty titles — filter `title.str.strip() != ""` before title-based operations

### Toolkit
- `toolkit.embedding` and `toolkit.clustering` — installed as editable package from sibling project, import directly
- No `sys.path` hacks needed

### Current Status
All 7 phases complete. Pipeline runs end-to-end for 2024 data. Pending:
- Human curation pass (compare draft vs AI-curated topics, create `2024_final_topics.csv`)
- LLM labeling refinement (optional, user-triggered — see DESIGN.md Phase 5)
- Multi-year mode (cross-year anomaly scoring)
