---
module: PIPELINE
phase: 4
phase_title: "Curate"
step: 1 of 4
mode: Code-Debug
blocked: null
regime: Build
review_done: false
---

# Year-in-Search — Development Plan

## Cold Start Summary

- **What this is** — Seven-phase pipeline producing a "Year in Tech" ridge plot from Hacker News data.
- **Key constraints** — Uses `toolkit.embedding` and `toolkit.clustering` (editable install from sibling project). CPU-only inference. No tests — validated by output inspection.
- **Gotchas**
  - `datasets.load_dataset()` crashes on this HF dataset — use `huggingface_hub.hf_hub_download()` with monthly parquet files instead (D-1)
  - HF dataset schema: `type` is int (1=story), `score` and `descendants` are strings needing `pd.to_numeric()`, `time` is datetime string not unix timestamp
  - toolkit is pip-installed as editable — no `sys.path` hacks needed
  - Embedding cache lives in `data/embeddings/cache/` — first run downloads the model (~80MB)
  - HDBSCAN produces ~38% noise items — this is expected, not a bug
  - Run each phase from project root: `python -m src.<phase> --year 2024`
  - ISO 8601 has week 53 in some years — time series uses 53 bins; downstream phases must handle length-53 arrays (D-5)
  - HN dataset has ~132 posts with empty titles — filter `title.str.strip() != ""` before any title-based operations

## Current Status

- **Phase** — 4 (Curate) — step 1 in progress
- **Focus** — Implement curate.py, export draft CSV, then AI curation pass
- **Blocked/Broken** — Nothing

## Phase 4: Curate

**Inputs:**
- `data/scored/{year}_topics.parquet` — labeled topics with metrics
- `data/raw/{year}_posts.parquet` + `data/clusters/{year}_clusters.parquet` — for top titles

**Outputs:**
- `data/curated/{year}_draft_topics.csv` — top 50 ranked topics for human review
- `data/curated/{year}_ai_curated_topics.csv` — AI curation pass (suggested merges, shortened labels, 15–25 selection)
- `data/curated/{year}_final_topics.csv` — human-edited final selection (manual)

### Step 1: Implement curate.py
- Load scored topics, join with posts+clusters for top 5 titles per cluster
- Rank by total_attention descending, take top 50
- Export CSV: rank, cluster_id, label, total_attention, peak_attention, peak_week, num_posts, duration_weeks, category, top_titles (pipe-joined)
- CLI: `python -m src.curate --year 2024`

### Step 2: Run on 2024 data
- Execute curate phase, inspect CSV output

### Step 3: AI curation pass
- Read draft CSV, propose: shortened labels, merge suggestions, select 15–25 topics
- Save as `{year}_ai_curated_topics.csv`
- Human does own pass on draft, then compares

### Step 4: Review
- Code review of curate.py

<!-- HISTORY — Worker: stop reading here. Everything below is completed phase history. -->

## Phase 3: Label — Complete (see DEVLOG 2026-04-25)

## Phase 2: Score & Classify — Complete (see DEVLOG 2026-04-25)

## Phase 1: Pipeline Skeleton (Ingest, Embed, Cluster) — Complete (see DEVLOG 2026-04-25)
