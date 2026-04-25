# Year-in-Search

## Spark
> Wanted a data-driven "Year in Tech" visualization — what topics captured outsized attention on Hacker News in a given year, rendered as a ridge plot of attention curves over time.

## What This Is
A proof-of-concept pipeline that processes Hacker News data from HuggingFace, discovers topics via embedding + clustering, scores them by attention anomaly, and produces a ridge-plot visualization. Single-source (HN), single-year default, extensible to multi-source and multi-year.

## Audience
Personal project. The output (ridge plot) is shareable; the pipeline is for the author.

## Scope

### Core
- Seven-phase pipeline: Ingest → Embed → Cluster → Score & Classify → Label → Curate → Visualize
- HN data from HuggingFace (`open-index/hacker-news`)
- Topic discovery via sentence embeddings (all-MiniLM-L6-v2) + HDBSCAN clustering
- Attention scoring with spike/sustained/moderate classification
- Ridge plot output (matplotlib)

### Flexible
- [in] LLM-assisted topic labeling (Phase 5 — can fall back to auto-label from top title)
- [in] Manual curation step (Phase 6 — CSV export for human review)
- [deferred] Multi-year anomaly scoring (cross-year baseline filtering)
- [deferred] Interactive visualization (Plotly/D3.js)

### Exclusions
- Real-time or incremental updates
- Production UI or webapp
- General news / culture / politics coverage
- Google Trends integration
- Reddit multi-source (designed for but not in PoC scope)

## Constraints
- Python 3.12, no web framework
- Uses `toolkit.embedding` and `toolkit.clustering` (editable install from sibling project)
- Runs on local machine (CPU inference for embeddings, no GPU required)
- HuggingFace dataset: monthly parquet files, ~3.7M rows/year raw, ~87K stories/year after filtering
- No tests — pipeline project validated by output inspection

## Prior Art
- Google Year in Search — commercial, proprietary, web-based. Covers all of Google search, not tech-specific.
- HN "Who is Hiring" analyses — monthly, not annual. Focus on job trends, not topics.
- This project fills a gap: tech-specific annual retrospective derived from community attention data.

## Success Criteria
- Pipeline runs end-to-end for at least one year of HN data
- ~80% of clusters contain semantically related posts (manual inspection)
- Top 20 topics for 2024 are recognizable to a tech-literate reader
- Ridge plot has clear visual separation of topics with chronological ordering
- Full pipeline runs in < 1 hour on a standard machine (excluding manual curation)

## Risks and Open Questions
- [watch] HN dataset completeness — verify coverage dates on load; supplement with HN API if needed
- [watch] Clustering granularity — too coarse merges distinct topics, too fine fragments them. Tunable via `min_cluster_size`; manual curation catches errors
- [watch] Perennial topics (Python, React) dominating — multi-year baseline filtering and spike_ratio metric address this
- [implementation] Embedding model may miss domain jargon — "LLM" and "large language model" could cluster separately. Curation step merges these.
- [watch] HN bias — tech-only, anglophone, startup-skewed. Acknowledged limitation for a tech-specific PoC.

## Extension Points
- Multi-source ingestion (Reddit tech subreddits) — designed with `source` field in post schema, early merge before clustering, z-score normalization across sources
- Multi-year comparison — cross-year anomaly scoring to filter perennials
- Embedding model swap — config-driven, can upgrade to `all-mpnet-base-v2` or API-based embeddings
- Category tagging — auto-tag topics (AI, security, languages, infra) for balanced selection

## Size Estimate
Single-module pipeline. Seven phases in one `src/` package with shared config. No internal module boundaries needed.

---

## Change History
| Date | What Changed | Why |
|------|-------------|-----|
| 2026-04-25 | Initial PROJECT.md | Restructured from DESIGN.md and CLAUDE.md per governance framework |
