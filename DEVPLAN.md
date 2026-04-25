---
module: PIPELINE
phase: 3
phase_title: "Label"
step: 1 of 2
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

## Current Status

- **Phase** — 3 (Label) — step 1 ready
- **Focus** — Implement auto-label in `label.py`, run on 2024 data
- **Blocked/Broken** — Nothing

## Phase 3: Label

**Inputs:**
- `data/scored/{year}_topics.parquet` — cluster metrics (3,356 rows)
- `data/raw/{year}_posts.parquet` + `data/clusters/{year}_clusters.parquet` — member post titles

**Output:**
- `data/scored/{year}_topics.parquet` — updated in place with `label` column

**Scope:** Auto-label only. LLM labeling is a planned future refinement, user-triggered (D-6).

### Step 1: Implement label.py with auto-label logic
- Join posts + clusters to get titles per cluster
- For each cluster, pick title of highest-attention post
- Clean: strip "Show HN:", "Ask HN:", "Tell HN:", "Launch HN:", leading punctuation/whitespace
- Add `label` column to scored topics, save in place
- CLI: `python -m src.label --year 2024`
- Test: run on 2024, inspect top 20 labels for readability

### Step 2: Review
- Code review of label.py

<!-- HISTORY — Worker: stop reading here. Everything below is completed phase history. -->

## Phase 2: Score & Classify — Complete (see DEVLOG 2026-04-25)

## Phase 1: Pipeline Skeleton (Ingest, Embed, Cluster) — Complete (see DEVLOG 2026-04-25)
