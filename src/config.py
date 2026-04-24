"""
Year-in-Search configuration — all tunable parameters.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
CLUSTERS_DIR = DATA_DIR / "clusters"
SCORED_DIR = DATA_DIR / "scored"
CURATED_DIR = DATA_DIR / "curated"
OUTPUT_DIR = PROJECT_ROOT / "output"

# ---------------------------------------------------------------------------
# Data source
# ---------------------------------------------------------------------------

HF_DATASET = "open-index/hacker-news"

# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------
# Ingest
MIN_SCORE_THRESHOLD = 5         # Drop posts below this score
STORY_TYPE = 1                  # HN type code: 1 = story

# ---------------------------------------------------------------------------
# Attention scoring
# ---------------------------------------------------------------------------

COMMENT_WEIGHT = 0.5            # α in: attention = score + α * num_comments

# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_BATCH_SIZE = 256
EMBEDDING_CACHE_DIR = str(EMBEDDINGS_DIR / "cache")

# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------

MIN_CLUSTER_SIZE = 5
MIN_SAMPLES = 3
REDUCE_DIMS = 50                # UMAP reduction: 384 → 50 dims

# ---------------------------------------------------------------------------
# Scoring & classification
# ---------------------------------------------------------------------------

SPIKE_RATIO_THRESHOLD = 4.0
SPIKE_MAX_DURATION = 3          # weeks
SUSTAINED_MIN_DURATION = 8      # weeks

# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------

TOP_N_TOPICS = 20               # Default number of topics to visualize
