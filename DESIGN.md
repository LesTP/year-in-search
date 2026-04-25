# HN Year-in-Tech: Design Doc & Project Plan

## 1. Overview

**Goal:** Build a proof-of-concept pipeline that produces a "Year in Tech" ridge-plot visualization, derived entirely from Hacker News data. The system discovers what topics captured outsized attention in a given year, clusters related posts into coherent topics, and visualizes their attention curves over time.

**Scope:** Proof of concept. Single source (HN), extensible to multi-source and multi-year later.

**Non-goals (for now):**
- General news / culture / politics coverage
- Real-time or incremental updates
- Production-grade UI
- Google Trends integration (may be added later as a cross-reference signal)

---

## 2. Conceptual Model

We are detecting **year-specific anomalies in tech attention** as measured by Hacker News engagement.

A post's score and comment count on HN represent collective editorial judgment — the community already upvotes what it finds noteworthy. Our job is to:

1. Aggregate that signal across related posts into **topics**
2. Identify which topics had **abnormal attention** in a given year
3. Classify attention patterns (spike vs. sustained)
4. Visualize the result

---

## 3. Data Source

### HuggingFace HN Dataset
- **URL:** https://huggingface.co/datasets/open-index/hacker-news
- **Contents:** HN posts with title, score, comment count, timestamp, URL, author
- **Coverage:** Historical HN data (verify exact date range on load)

### Key Fields

| Field        | Use                                      |
|-------------|------------------------------------------|
| `title`     | Text for embedding and clustering         |
| `score`     | Primary attention signal                  |
| `descendants` (comments) | Secondary attention signal     |
| `time`      | Temporal binning (weekly)                 |
| `type`      | Filter to `story` only                   |

### Attention Score

For each post, define a combined attention score:

```
attention = score + α * num_comments
```

Where `α` weights comment importance relative to upvotes. Start with `α = 0.5`. This is tunable.

---

## 4. Pipeline Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        HN YEAR-IN-TECH PIPELINE                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: INGEST                                                 │
│  ┌─────────────┐                                                 │
│  │ HF Dataset  │──→ Load, filter to year(s), filter to stories   │
│  └─────────────┘                                                 │
│         │                                                        │
│         ▼                                                        │
│  Phase 2: EMBED                                                  │
│  ┌─────────────────────┐                                         │
│  │ all-MiniLM-L6-v2    │──→ 384-dim embeddings for all titles    │
│  └─────────────────────┘                                         │
│         │                                                        │
│         ▼                                                        │
│  Phase 3: CLUSTER                                                │
│  ┌─────────────┐                                                 │
│  │  HDBSCAN    │──→ Topic clusters + noise labels                │
│  └─────────────┘                                                 │
│         │                                                        │
│         ▼                                                        │
│  Phase 4: SCORE & CLASSIFY                                       │
│  ┌──────────────────────────┐                                    │
│  │ Aggregate attention      │──→ Per-topic time series            │
│  │ Anomaly scoring          │──→ Spike vs. sustained vs. noise    │
│  └──────────────────────────┘                                    │
│         │                                                        │
│         ▼                                                        │
│  Phase 5: LABEL                                                  │
│  ┌──────────────────────────┐                                    │
│  │ Auto-label (top title)   │                                    │
│  │ Optional: LLM cleanup    │                                    │
│  └──────────────────────────┘                                    │
│         │                                                        │
│         ▼                                                        │
│  Phase 6: CURATE (manual)                                        │
│  ┌──────────────────────────┐                                    │
│  │ Export ranked topics      │──→ CSV for human review            │
│  │ Human selects/edits       │                                    │
│  └──────────────────────────┘                                    │
│         │                                                        │
│         ▼                                                        │
│  Phase 7: VISUALIZE                                              │
│  ┌──────────────────────────┐                                    │
│  │ Ridge plot (matplotlib)  │──→ Final output                     │
│  └──────────────────────────┘                                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Phase Details

### Phase 1 — Ingest

**Input:** HuggingFace dataset identifier
**Output:** `data/raw/{year}_posts.parquet`

Steps:
1. Load dataset from HuggingFace (`datasets` library)
2. Filter to `type == "story"`
3. Filter to target year(s) by timestamp
4. Drop posts with `score < 5` (noise floor — removes dead submissions)
5. Save to parquet per year

**Schema:**

```python
@dataclass
class HNPost:
    id: int
    title: str
    score: int
    num_comments: int
    timestamp: datetime
    url: str | None
    attention: float  # computed: score + α * num_comments
```

---

### Phase 2 — Embed

**Input:** Filtered posts
**Output:** `data/embeddings/{year}_embeddings.npy` + index mapping

Steps:
1. Load `all-MiniLM-L6-v2` via `sentence-transformers`
2. Encode all titles → 384-dim vectors
3. Save embeddings as numpy array
4. Save ID-to-index mapping

**Performance:** ~10K titles/sec on CPU. A full year of HN (~100K stories after filtering) takes ~10 seconds.

**Caching:** Embeddings are deterministic for a given model + title. Cache aggressively — never re-embed the same data.

---

### Phase 3 — Cluster

**Input:** Embeddings
**Output:** `data/clusters/{year}_clusters.parquet` (post ID → cluster ID)

Steps:
1. (Optional) Reduce dimensionality with UMAP (384 → 50 dims) for faster clustering
2. Run HDBSCAN with `min_cluster_size=5`, `min_samples=3`
3. Posts labeled `-1` are noise — drop them
4. Save cluster assignments

**Tuning parameters:**

| Parameter          | Start value | Effect                                    |
|-------------------|-------------|-------------------------------------------|
| `min_cluster_size`| 5           | Smaller = more clusters, more noise       |
| `min_samples`     | 3           | Controls density requirement              |
| `metric`          | `euclidean` | Standard for normalized sentence embeddings|

**Expected output:** 200–500 clusters per year (many will be tiny/irrelevant — that's fine, scoring handles this).

---

### Phase 4 — Score & Classify

**Input:** Posts with cluster assignments
**Output:** `data/scored/{year}_topics.parquet`

For each cluster, compute:

#### 4a. Time Series
- Bin posts by **week** (ISO week number)
- Per week: sum of `attention` scores for all posts in the cluster
- Result: 53-point attention curve per cluster (ISO weeks 1–53; years without week 53 get a trailing 0)

#### 4b. Metrics

| Metric               | Formula                                            | Purpose                     |
|----------------------|----------------------------------------------------|-----------------------------|
| `total_attention`     | Sum of all post attention scores in cluster         | Overall magnitude           |
| `peak_attention`      | Max weekly attention                               | Spike height                |
| `peak_week`           | Week number of peak                                | When it happened            |
| `num_posts`           | Count of posts in cluster                          | Activity volume             |
| `duration_weeks`      | Weeks with attention > 20% of peak                 | How long it lasted          |
| `spike_ratio`         | `peak_attention / mean_attention`                  | Spikiness                   |

#### 4c. Classification

```python
if spike_ratio > 4 and duration_weeks <= 3:
    category = "spike"
elif duration_weeks > 8:
    category = "sustained"
else:
    category = "moderate"
```

Thresholds are tunable. Start with these, adjust after inspecting results.

#### 4d. Multi-Year Anomaly (optional, for multi-year mode)

If processing multiple years, compute a baseline:

```
baseline_mean = mean(attention across non-target years)
year_spike_score = mean(target_year_attention) / baseline_mean
```

Topics with high `year_spike_score` are year-specific. Topics with similar attention across years are perennials (e.g., "Python", "React") and should be deprioritized.

---

### Phase 5 — Label

**Input:** Scored clusters with member posts
**Output:** Labeled topics added to scored data

#### Auto-labeling (default)
- For each cluster, select the title of the **highest-scored post** as the label
- Clean it: strip "Show HN:", "Ask HN:", leading punctuation, etc.

#### LLM-assisted labeling (optional)
- For each cluster, send the top 10 titles to an LLM:
  ```
  These are Hacker News titles about the same topic:
  1. {title_1}
  2. {title_2}
  ...
  Generate a short, clean topic label (2-5 words).
  ```
- Use any available LLM (local or API)

---

### Phase 6 — Curate

**Input:** Ranked, labeled topic list
**Output:** `data/curated/{year}_final_topics.csv`

Export a CSV with columns:
```
rank, cluster_id, label, total_attention, peak_attention, peak_week,
num_posts, duration_weeks, category, top_titles (top 5)
```

Human review:
1. Scan the list (~top 50)
2. Merge topics that should be combined (mark with same group ID)
3. Edit labels for clarity
4. Select final 15–25 topics for visualization
5. Save curated CSV

This step is intentionally manual for the PoC. Automation can come later.

---

### Phase 7 — Visualize

**Input:** Curated topics + their weekly attention time series
**Output:** Ridge plot image (PNG/SVG)

#### Ridge Plot Spec
- X-axis: weeks of the year (1–52), labeled with month names
- Y-axis: stacked topics, ordered by peak week (chronological)
- Each row: filled area chart of weekly attention
- Color: gradient by peak week (Jan=cool, Dec=warm) or by category
- Labels: topic name on the left of each row

#### Implementation
- `matplotlib` + manual offset stacking, or `joypy` library
- Separate visual treatment for sustained topics (optional):
  - Thicker, lower-opacity bands vs. sharp spikes
  - Or a separate panel below the main ridge plot

#### Output Files
- `output/{year}_year_in_tech.png` (high-res)
- `output/{year}_year_in_tech.svg` (vector)

---

## 6. Project Structure

```
year-in-search/
├── DESIGN.md                    # This document
├── CLAUDE.md                    # Project-specific AI context
├── requirements.txt             # Python dependencies
│
├── src/
│   ├── __init__.py
│   ├── ingest.py                # Phase 1: data loading and filtering
│   ├── embed.py                 # Phase 2: sentence embeddings
│   ├── cluster.py               # Phase 3: HDBSCAN clustering
│   ├── score.py                 # Phase 4: anomaly scoring
│   ├── label.py                 # Phase 5: topic labeling
│   ├── visualize.py             # Phase 7: ridge plot generation
│   ├── config.py                # Shared constants and parameters
│   └── pipeline.py              # End-to-end orchestrator
│
├── data/
│   ├── raw/                     # Phase 1 output
│   ├── embeddings/              # Phase 2 output
│   ├── clusters/                # Phase 3 output
│   ├── scored/                  # Phase 4 output
│   └── curated/                 # Phase 6 output (human-edited CSVs)
│
├── output/                      # Phase 7 output (images)
│
└── notebooks/
    └── explore.ipynb            # Exploratory analysis / debugging
```

---

## 7. Dependencies

```
# Core
datasets          # HuggingFace dataset loading
pandas            # Data manipulation
pyarrow           # Parquet I/O
numpy             # Numerical operations

# Embedding
sentence-transformers  # all-MiniLM-L6-v2

# Clustering
hdbscan           # Density-based clustering
umap-learn        # Optional: dimensionality reduction before clustering

# Visualization
matplotlib        # Ridge plots
joypy             # Optional: simplified ridge plot API

# Utilities
tqdm              # Progress bars
```

---

## 8. Configuration

All tunable parameters live in `src/config.py`:

```python
# Ingest
MIN_SCORE_THRESHOLD = 5         # Drop posts below this score
STORY_TYPES = ["story"]         # HN post types to include

# Attention
COMMENT_WEIGHT = 0.5            # α in: attention = score + α * comments

# Embedding
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Clustering
MIN_CLUSTER_SIZE = 5
MIN_SAMPLES = 3
USE_UMAP = True
UMAP_DIMS = 50

# Scoring
SPIKE_RATIO_THRESHOLD = 4.0
SPIKE_MAX_DURATION = 3          # weeks
SUSTAINED_MIN_DURATION = 8      # weeks

# Visualization
TOP_N_TOPICS = 20               # Default number of topics to visualize
```

---

## 9. Execution Modes

### Single-year mode (default)
```bash
python -m src.pipeline --year 2024
```

### Multi-year mode
```bash
python -m src.pipeline --years 2020 2021 2022 2023 2024
```

Multi-year mode enables:
- Cross-year anomaly scoring (filter out perennial topics)
- Comparison ridge plots (one per year)

### Step-by-step mode (for debugging / manual intervention)
```bash
python -m src.ingest --year 2024
python -m src.embed --year 2024
python -m src.cluster --year 2024
python -m src.score --year 2024
python -m src.label --year 2024
# ... manual curation of CSV ...
python -m src.visualize --year 2024
```

---

## 10. Known Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| HN dataset incomplete or stale | Missing recent data | Check coverage dates on load; supplement with HN API if needed |
| Clustering too coarse/fine | Topics merged or fragmented | Tunable `min_cluster_size`; manual curation catches errors |
| HN bias (tech-only, US-centric) | Misses non-anglophone tech events | Acknowledged — this is a tech-specific PoC, not general news |
| Embedding model misses domain jargon | "LLM" and "large language model" in different clusters | Related queries merge in curation step; can fine-tune later |
| Perennial topics dominate (Python, React) | Crowds out year-specific events | Multi-year baseline filtering; spike_ratio metric penalizes flat curves |

---

## 11. Future Extensions (Post-PoC)

- **Interactive visualization:** Plotly/D3.js version with hover details, drill-down
- **Automated curation:** LLM-based cluster merging and label generation
- **Webapp:** Simple Flask/Streamlit app to browse year-in-review by year
- **Embedding upgrade:** Swap to `all-mpnet-base-v2` or OpenAI embeddings if cluster quality is insufficient
- **Category tagging:** Auto-tag topics (AI, security, languages, infra, etc.) for balanced selection

### 11a. Multi-Source: Reddit Tech Subreddits

**Goal:** Add tech subreddit data as a second attention signal alongside HN. Topics that spike on *both* sources have strong cross-validation. Source-specific spikes reveal community-specific interests (HN = startups/products, Reddit = broader dev community).

**Target subreddits:** `r/programming`, `r/technology`, `r/machinelearning`, `r/webdev`, `r/devops`, `r/rust`, `r/golang`, `r/python`, `r/javascript`

**Data source options:**
- HuggingFace: Reddit submission dumps (various community datasets)
- Pushshift/Arctic Shift archives
- Reddit API (rate-limited, requires auth)

**Schema mapping:**

| HN field      | Reddit equivalent       | Notes                              |
|---------------|------------------------|------------------------------------|
| `title`       | `title`                | Direct match                       |
| `score`       | `score`                | Reddit scores are 10-100x higher   |
| `descendants` | `num_comments`         | Direct match                       |
| `time`        | `created_utc`          | Unix timestamp in Reddit           |
| `type=story`  | subreddit filter        | Filter by target subreddit list    |
| —             | `subreddit`            | New field: source context          |

**Key design decisions:**

1. **Merge strategy: early (before clustering).** Concatenate HN + Reddit titles into one embedding matrix, cluster together. Add a `source` column so results can be broken down by origin. This is simpler than matching clusters cross-source and lets topics naturally form across both communities.

2. **Attention normalization.** Reddit scores are much higher than HN (a front-page Reddit post might get 5000+ points vs. 500 on HN). Normalize per-source before combining:
   ```python
   # Per-source z-score normalization
   attention_normalized = (attention - source_mean) / source_std
   ```

3. **Schema extension.** Add `source` field to the post schema:
   ```python
   @dataclass
   class Post:
       id: int
       title: str
       score: int
       num_comments: int
       timestamp: datetime
       url: str | None
       attention: float
       source: str           # "hn" or "reddit"
       source_detail: str    # "hn" or subreddit name (e.g. "r/programming")
   ```

4. **Implementation.** New module `src/ingest_reddit.py` with the same `run(year) -> DataFrame` interface. The rest of the pipeline (embed, cluster, score, visualize) works unchanged — it just sees more rows.

5. **Visualization enhancement.** Ridge plot could color-code by source agreement:
   - Topics with both HN + Reddit signal → high confidence (bold)
   - HN-only or Reddit-only → lower confidence (lighter)

**Prerequisites:** Complete the HN pipeline end-to-end first (Phases A-D). Reddit integration is additive — it only touches ingest and config.

---

## 12. Success Criteria

The PoC is successful if:

1. **Pipeline runs end-to-end** for at least one year of HN data
2. **Clusters are coherent** — manual inspection shows that ~80% of clusters contain semantically related posts
3. **Top topics are recognizable** — a tech-literate human looks at the top 20 topics for 2024 and says "yes, those were the big things"
4. **Ridge plot is readable** — clear visual separation of topics, chronological ordering makes narrative sense
5. **The whole process takes < 1 hour** (excluding manual curation) on a standard machine
