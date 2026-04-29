---
module: PIPELINE
phase: complete
phase_title: "All phases complete"
step: n/a
mode: n/a
blocked: null
regime: n/a
review_done: true
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

- **Phase** — All 7 phases complete (pipeline runs end-to-end)
- **Focus** — Human curation pass still pending (user will review draft vs AI curation)
- **Blocked/Broken** — Nothing

## Pending Work (Post-Pipeline)

1. **Human curation pass** — User reviews `data/curated/2024_draft_topics.csv`, creates `2024_final_topics.csv`, compares with AI curation
2. **LLM labeling** — Optional refinement (D-6). Trigger when auto-labels feel too long or ambiguous for the ridge plot. See DESIGN.md "LLM-assisted labeling" section for the full workflow: add `--llm` flag to `label.py`, use `toolkit.llm_client`, save as `llm_label` column alongside `label`. Scope: curated subset only (~20–50 LLM calls). Requires `toolkit.llm_client` to be implemented.
3. **Multi-year mode** — Run pipeline for additional years, compute cross-year baselines to filter perennial topics (Python, React, etc.), generate comparison ridge plots
4. ~~**requirements.txt update**~~ — Done (matplotlib and scipy already added)

<!-- HISTORY — Worker: stop reading here. Everything below is completed phase history. -->

## Phase 5: Visualize — Complete (see DEVLOG 2026-04-25)

## Phase 4: Curate — Complete (see DEVLOG 2026-04-25)

## Phase 3: Label — Complete (see DEVLOG 2026-04-25)

## Phase 2: Score & Classify — Complete (see DEVLOG 2026-04-25)

## Phase 1: Pipeline Skeleton (Ingest, Embed, Cluster) — Complete (see DEVLOG 2026-04-25)
