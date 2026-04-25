# Year-in-Search — Architecture

## Component Map

| Component | Responsibility | Dependencies |
|-----------|---------------|--------------|
| `config.py` | All tunable parameters and paths | none |
| `ingest.py` | Download HN data from HuggingFace, filter, compute attention scores | `config`, `huggingface_hub` |
| `embed.py` | Encode titles into 384-dim vectors | `config`, `toolkit.embedding` |
| `cluster.py` | Group embeddings into topic clusters (HDBSCAN + UMAP) | `config`, `toolkit.clustering` |
| `score.py` | Aggregate attention per cluster, compute time series, classify | `config` |
| `label.py` | Auto-label clusters from top title, optional LLM cleanup | `config`, `toolkit.llm_client` (optional) |
| `visualize.py` | Generate ridge plot from scored/labeled topics | `config`, `matplotlib` |

No cross-phase imports. Each phase reads the previous phase's output from disk.

## Data Flow

### Core Objects

- **HNPost** — `{id: int, title: str, score: int, num_comments: int, timestamp: datetime, url: str?, attention: float}`
- **Embedding** — `ndarray (n_posts, 384)` with parallel `ndarray (n_posts,)` ID mapping
- **ClusterAssignment** — `{id: int, cluster_id: int}` where -1 = noise
- **TopicScore** — `{cluster_id: int, total_attention: float, peak_attention: float, peak_week: int, num_posts: int, duration_weeks: int, spike_ratio: float, category: str, label: str, time_series: list[float]}`

### Flow

```
HuggingFace (monthly parquet)
    │
    ▼
Ingest ──→ data/raw/{year}_posts.parquet          [HNPost rows]
    │       data/raw/{year}_ingest_report.json     [structured error report]
    ▼
Embed  ──→ data/embeddings/{year}_embeddings.npy   [n × 384 float32]
    │       data/embeddings/{year}_ids.npy          [n int64]
    ▼
Cluster ─→ data/clusters/{year}_clusters.parquet   [id → cluster_id]
    │
    ▼
Score  ──→ data/scored/{year}_topics.parquet        [TopicScore rows]
    │
    ▼
Label  ──→ (updates scored data with labels)
    │
    ▼
Curate ──→ data/curated/{year}_final_topics.csv    [human-edited selection]
    │
    ▼
Visualize → output/{year}_year_in_tech.png/svg     [ridge plot]
```

Each phase is a standalone CLI: `python -m src.<phase> --year 2024`. No orchestration layer yet.

## Implementation Sequence

| Order | Phase | Rationale | Status |
|-------|-------|-----------|--------|
| 1 | Ingest | Foundation — all downstream phases depend on ingested data | Complete |
| 2 | Embed | Requires ingest output; toolkit.embedding is stable | Complete |
| 3 | Cluster | Requires embeddings; toolkit.clustering is stable | Complete |
| 4 | Score & Classify | Requires cluster assignments + original posts | Not started |
| 5 | Label | Requires scored clusters | Not started |
| 6 | Curate | Manual step — depends on labeled output | Not started |
| 7 | Visualize | Final output — depends on curated topics | Not started |

## Coupling Notes

- `toolkit.embedding` ↔ `embed.py`: tight (direct API call). Change is additive — model swap is config-only.
- `toolkit.clustering` ↔ `cluster.py`: tight (direct API call). HDBSCAN params are config-driven.
- `toolkit.llm_client` ↔ `label.py`: optional — only used if LLM labeling is enabled. Fallback is auto-label.
- Phase coupling is **serial via disk** — each phase reads files from the previous phase. No in-memory handoff. This means any phase can be re-run independently.
- `config.py` is a shared dependency of all phases but contains no logic — only constants.

## Key Decisions

D-1: Monthly file download instead of full dataset
Date: 2026-04-25 | Status: Closed
Decision: Use `huggingface_hub.hf_hub_download()` to fetch per-month parquet files instead of `datasets.load_dataset()` for the full 47M-row dataset.
Rationale: The `datasets` library's shard builder crashes on this dataset (`IndexError` in `_prepare_split_single`). Monthly files download only the target year's data (~200MB vs 2-4GB).
Revisit if: The `datasets` library fixes the shard processing bug, or if the dataset layout changes.

D-2: Structured ingest error reporting
Date: 2026-04-25 | Status: Closed
Decision: Ingest produces a JSON report (`IngestReport`) alongside the data, separating expected skips (`EntryNotFoundError` for partial years) from unexpected errors.
Rationale: Pipeline is run manually but errors should be reviewable by a model, not just scanned visually in console output.
Revisit if: Pipeline becomes automated and needs a different error routing mechanism.

D-3: No ARCH_[module].md files
Date: 2026-04-25 | Status: Closed
Decision: Single-module project — all phases live in one `src/` package. No per-module ARCH files.
Rationale: Seven phases but one linear pipeline. No internal module boundaries, no cross-module integration concerns.
Revisit if: Reddit multi-source extension adds enough complexity to warrant separate modules.

## Provisional Contracts

- **Score input format** — Score phase will join `{year}_posts.parquet` with `{year}_clusters.parquet` on `id`. Schema is stable from Phase A. No provisional concerns.
- **Label → Visualize contract** — Label produces a `label` column on the scored data. Visualize reads it. Exact format (string length, cleaning rules) will be defined when Phase 5 is built.

---

## Change History
| Date | What Changed | Why |
|------|-------------|-----|
| 2026-04-25 | Initial ARCHITECTURE.md | Created per governance framework from DESIGN.md and CLAUDE.md |
