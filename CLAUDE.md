# Year-in-Search — Project Context

## What This Is
A pipeline that produces a "Year in Tech" ridge-plot visualization from Hacker News data. Discovers topics that captured outsized attention in a given year, clusters related posts, and visualizes attention curves over time.

## Architecture
Seven-phase pipeline: Ingest → Embed → Cluster → Score & Classify → Label → Curate → Visualize.

Phases 2 and 3 use toolkit modules (`toolkit.embedding`, `toolkit.clustering`) via `sys.path` import.

## Project Structure
```
src/
├── config.py       — all tunable parameters and paths
├── ingest.py       — Phase 1: HuggingFace HN dataset → filtered parquet
├── embed.py        — Phase 2: titles → 384-dim embeddings (toolkit.embedding)
├── cluster.py      — Phase 3: embeddings → HDBSCAN clusters (toolkit.clustering)
data/
├── raw/            — Phase 1 output ({year}_posts.parquet)
├── embeddings/     — Phase 2 output ({year}_embeddings.npy, {year}_ids.npy)
├── clusters/       — Phase 3 output ({year}_clusters.parquet)
├── scored/         — Phase 4 output (future)
├── curated/        — Phase 6 output (future)
output/             — Phase 7 output (ridge plot PNG/SVG)
```

## Data Source — HuggingFace HN Dataset
- Dataset: `open-index/hacker-news`
- **Schema quirks discovered during exploration:**
  - `type` is integer: `1` = story (not string `"story"`)
  - `time` is datetime string `'2006-10-09 18:21:51+00:00'` (not unix timestamp)
  - `score` and `descendants` are strings, need `pd.to_numeric()` conversion
  - Types seen: `{1, 2, 5}` — we filter to type `1` (stories)
- **Estimated size:** ~100K stories/year for recent years (after filtering to score >= 5)
- **Download:** Full dataset is 2-4 GB, one-time download

## Toolkit Dependencies
- `toolkit.embedding.embed()` — default model `all-MiniLM-L6-v2` matches config
- `toolkit.clustering.cluster()` — default params (min_cluster_size=5, min_samples=3, euclidean) match config
- Both toolkit modules are complete and tested (43 + 29 tests)

## Current Status
- **Phase A skeleton complete** (ingest, embed, cluster modules with config)
- **No data processed yet** — first run will download the full HN dataset
- Phases B-D (score, label, curate, visualize) not started
- No tests yet — this is a pipeline project, not a library

## Key Design Doc
Read `DESIGN.md` for full pipeline specification, including Phase 4 scoring formulas, Phase 5 labeling strategy, and Phase 7 ridge plot spec.

## Execution
Each phase can run standalone:
```bash
python -m src.ingest --year 2024
python -m src.embed --year 2024
python -m src.cluster --year 2024
```
Or will eventually run end-to-end via `python -m src.pipeline --year 2024`.
