---
module: PIPELINE
phase: 3
phase_title: "Label"
step: 0 of 0
mode: Discuss
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

- **Phase** — 3 (Label) — not started
- **Focus** — Next up: implement Phase 5 per DESIGN.md Section 5
- **Blocked/Broken** — Nothing

## Phase 3: Label

<!-- Break into steps during the Phase Plan action. See DESIGN.md Section 5, Phase 5. -->

<!-- HISTORY — Worker: stop reading here. Everything below is completed phase history. -->

## Phase 2: Score & Classify — Complete (see DEVLOG 2026-04-25)

## Phase 1: Pipeline Skeleton (Ingest, Embed, Cluster) — Complete (see DEVLOG 2026-04-25)
