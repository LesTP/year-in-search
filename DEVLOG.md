# Year-in-Search — Development Log

## Phase 1: Pipeline Skeleton (Ingest, Embed, Cluster)

### Step 1: Implement ingest, embed, cluster modules
- **Mode:** Code
- **Outcome:** complete
- **Contract changes:** none

Built three pipeline phases with shared config:
- `ingest.py` — loads full HN dataset via `datasets.load_dataset()`, filters to stories for target year, computes attention scores, saves parquet
- `embed.py` — encodes titles via `toolkit.embedding` (all-MiniLM-L6-v2), saves numpy arrays
- `cluster.py` — clusters via `toolkit.clustering` (HDBSCAN + UMAP), saves parquet
- `config.py` — all tunable parameters and paths

Both `embed.py` and `cluster.py` used `sys.path` hacks to import toolkit (later removed — see Step 4).

### Step 2: First data run
- **Mode:** Code / Debug
- **Outcome:** complete
- **Contract changes:** none

Attempted first pipeline run for year 2024.

**Ingest failure:** `datasets.load_dataset()` crashed with `IndexError: list index out of range` in `_prepare_split_single` after downloading all 235 data files (42 minutes). Root cause: `datasets` library shard builder bug on this multi-file parquet dataset.

**Fix:** Switched to `huggingface_hub.hf_hub_download()` loading per-month parquet files directly. Downloads only the target year's data (~200MB for 12 files) instead of the full 47M-row dataset. Decision recorded as D-1.

**Successful run results:**
- Ingest: 3.7M raw rows → 86,982 stories (score >= 5)
- Embed: 86,982 × 384 embedding matrix (~5 minutes on CPU)
- Cluster: 3,356 clusters, 33,026 noise items (38%)

### Step 3: Cluster exploration and quality check
- **Mode:** Code
- **Outcome:** complete
- **Contract changes:** none

Created `notebooks/explore_clusters.py` to inspect results. Key findings:
- Top clusters are coherent and recognizable: CrowdStrike outage (146 posts), xz backdoor (71 posts, very high mean attention), ChatGPT (243 posts), Apple vs EU (170 posts), Rust ecosystem (370 posts), LLMs (196 posts)
- Mid-sized clusters: mostly coherent, occasional loose groupings
- Cluster size distribution: median 10 posts, 53% small (5-10), 43% mid (11-50), 4% large (50+)
- One cluster (#95) had empty titles — data quality issue in source

### Step 4: Phase review and cleanup
- **Mode:** Review
- **Outcome:** complete
- **Contract changes:** none

Code review of all Phase 1 code. Findings applied:
- Removed dead `sys.path` hacks from `embed.py` and `cluster.py` (toolkit is pip-installed as editable package)
- Updated `requirements.txt`: replaced `datasets` with `huggingface_hub`, removed unused `tqdm`
- Fixed duplicate `# Ingest` section comment in `config.py`
- Removed unused `numpy` import from `explore_clusters.py`
- Simplified defensive column filtering to direct selection in `ingest.py`

Added structured error reporting: `IngestReport` dataclass producing JSON alongside data, separating expected skips (partial year) from unexpected errors. Decision recorded as D-2.

### Step 5: Governance framework setup
- **Mode:** Code
- **Outcome:** complete
- **Contract changes:** none

Adopted the e2e governance framework (supervised workflow, no automation):
- Created `PROJECT.md` from SPEC_project.md format
- Created `ARCHITECTURE.md` from SPEC_architecture.md format
- Copied `GOVERNANCE.md` from framework
- Rewrote `DEVPLAN.md` to match template (frontmatter, Cold Start Summary, HISTORY fence)
- Created `DEVLOG.md` with Phase 1 backfill
- Created `DECISIONS.md` with D-1 through D-3 backfill
- Slimmed `CLAUDE.md` to reference new docs instead of duplicating content

## Phase 2: Score & Classify

### Step 1: Implement score.py and run on 2024 data
- **Mode:** Code-Debug
- **Outcome:** complete
- **Contract changes:** none

Implemented `src/score.py` — Phase 4 from DESIGN.md:
- Joins `{year}_posts.parquet` + `{year}_clusters.parquet` on `id`, drops noise (cluster_id == -1)
- Groups by cluster_id, computes per-cluster:
  - 52-point weekly attention curve (ISO week bins, stored as JSON string — D-4)
  - Metrics: total_attention, peak_attention, peak_week, num_posts, duration_weeks, spike_ratio
  - Classification: spike (ratio > 4, duration ≤ 3), sustained (duration > 8), moderate (else)
- Output: `data/scored/{year}_topics.parquet` — one row per cluster
- CLI: `python -m src.score --year 2024`

**Run results (2024 data):**
- Input: 53,956 posts across 3,356 clusters (after dropping 33,026 noise items)
- Classification: 1,855 spike / 1,259 moderate / 242 sustained
- Top clusters validated against known 2024 events:
  - CrowdStrike outage → spike (peak wk 29, spike_ratio=29.95) ✓
  - xz backdoor → spike (peak wk 13, spike_ratio=31.93) ✓
  - Rust ecosystem → sustained (370 posts, 28 weeks) ✓
  - ChatGPT → sustained (243 posts, 17 weeks) ✓
  - LLMs → sustained (196 posts, 24 weeks) ✓
  - Apple vs EU → moderate (170 posts, 8 weeks, spike_ratio=10.28) ✓

**Observation:** spike_ratio median is 22.5, meaning most small clusters have high spikiness (single-week activity). The spike/moderate/sustained split is dominated by spike (55%) because many small clusters have all posts in 1-2 weeks. This is expected — the top-N filtering in later phases will surface the interesting ones.

### Step 2: Review and fixes
- **Mode:** Review
- **Outcome:** complete
- **Contract changes:** time_series changed from 52 to 53 bins (D-5)

Code review of score.py. Findings applied:
- **53-bin time series:** Extended from 52 to 53 ISO-week bins to avoid silently dropping week-53 data in years that have it (D-5). 2024 has no week 53 — verified trailing 0.0.
- **Input mutation guard:** Added `df.copy()` before adding `week` column to avoid mutating the DataFrame passed from `load()`.
- **Zero-peak guard:** Added `if peak_attention > 0` check before computing `duration_weeks` threshold to avoid counting all 52 weeks as active when attention is zero.
- **Spike ratio rounding:** Noted as optional — kept `round(spike_ratio, 2)` for now, acceptable for PoC.

Phase validation: re-ran on 2024 data, verified schema (9 columns), 53-bin time series, all categories valid, no zero-attention or zero-post clusters. Classification unchanged from Step 1.

## Phase 4: Curate

### Step 1: Implement curate.py, run, and AI curation pass
- **Mode:** Code
- **Outcome:** complete
- **Contract changes:** none

Implemented `src/curate.py` — Phase 6 from DESIGN.md:
- Loads scored topics, joins with posts+clusters for top 5 titles per cluster (pipe-joined)
- Ranks by total_attention descending, takes top 50
- Exports `data/curated/{year}_draft_topics.csv`
- CLI: `python -m src.curate --year 2024`

**Run results (2024 data):**
- 50 topics exported to draft CSV
- Category breakdown: 28 spike / 13 moderate / 9 sustained

**AI curation pass:**
- Selected 20 topics from 50, shortened labels, provided selection rationale
- Saved as `data/curated/2024_ai_curated_topics.csv` with `ai_notes` column
- User will do own pass on draft, then compare

**Post-visualization refinements:**
- Replaced "Notable Deaths" (catch-all "X has died" cluster) with top 2 individuals: Vernor Vinge (sci-fi author, singularity concept) and Daniel Kahneman (Nobel laureate, behavioral economics)
- Removed "Open Source" (perennial community discussion, not a 2024-specific event)
- Synthetic cluster entries created with per-person time series extracted from original cluster

## Phase 5: Visualize

### Step 1: Implement visualize.py and run on 2024 data
- **Mode:** Code-Debug
- **Outcome:** complete
- **Contract changes:** output files are `{year}_year_in_tech_{variant}.png/svg`

Implemented `src/visualize.py` — Phase 7 from DESIGN.md:
- Ridge plot with peak-week color gradient (cool→warm via custom colormap)
- Topics ordered chronologically by peak_week (bottom=Jan, top=Dec)
- Per-curve normalization to [0,1] for uniform row height
- White outline separates overlapping fills
- Labels positioned left of each row
- Month labels on x-axis at approximate ISO week positions
- Gaussian smoothing via `scipy.ndimage.gaussian_filter1d` at configurable sigma
- Supports curated subset filtering (--curated ai/final)
- CLI: `python -m src.visualize --year 2024`

**Smoothing comparison:**
- Tested sigma values: 0.8 (light), 1.0 (medium rare), 1.2 (medium), 1.5, 2.5 (heavy)
- User selected sigma=1.0 as best balance between spike clarity and visual smoothness
- Row spacing tuned from overlap=0.65 → 0.35 → 0.15 for clear separation

**Output files (2024, AI-curated 20 topics):**
- `output/2024_year_in_tech_raw.png/svg` — unsmoothed
- `output/2024_year_in_tech_smooth_light.png/svg` — sigma=0.8
- `output/2024_year_in_tech_smooth_medium_rare.png/svg` — sigma=1.0 (preferred)
- `output/2024_year_in_tech_smooth_medium.png/svg` — sigma=1.2

**Dependencies added:** `matplotlib`, `scipy` (not in requirements.txt yet — CPU-only, standard packages)

## Phase 3: Label

### Step 1: Implement label.py and run on 2024 data
- **Mode:** Code-Debug
- **Outcome:** complete
- **Contract changes:** added `label` column to `{year}_topics.parquet`

Implemented `src/label.py` — Phase 5 from DESIGN.md:
- Auto-label only (D-6) — picks highest-attention post title per cluster
- Cleans HN prefixes: strips "Show HN:", "Ask HN:", "Tell HN:", "Launch HN:" and leading punctuation
- Filters out empty-title posts before picking best title (data quality: 132 clusters have all-empty titles in source data)
- Merges `label` column into scored topics, saves in place
- Idempotent — drops existing `label` column before re-merging
- CLI: `python -m src.label --year 2024`

**Run results (2024 data):**
- 3,224 / 3,356 topics labeled (132 unlabeled = all-empty-title clusters from HN source data)
- Labels are full HN titles — readable but long (LLM labeling deferred per D-6)
- Top labels match known 2024 events: CrowdStrike, xz backdoor, ChatGPT, Rust, LLMs, GPT-4o, Meta Llama 3, TikTok bill

**Investigation:** 134 initially unlabeled clusters traced to empty-title posts in HN dataset. 132 had zero titled posts. 2 had titled posts but the highest-attention post was untitled — fixed by filtering empty titles before `idxmax()`.

### Step 2: Review
- **Mode:** Review
- **Outcome:** complete (nothing to fix)
- **Contract changes:** none

Code review found no issues. 82 lines, no dead code, no unused imports, no architecture drift. Clean pass.
