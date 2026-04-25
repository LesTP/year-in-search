"""Cluster exploration script — inspect top clusters from the pipeline run."""
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")

# Load pipeline outputs
posts = pd.read_parquet(DATA_DIR / "raw/2024_posts.parquet")
clusters = pd.read_parquet(DATA_DIR / "clusters/2024_clusters.parquet")

# Merge posts with cluster assignments
df = posts.merge(clusters, on="id", how="inner")
noise_count = (df["cluster_id"] == -1).sum()
real_count = (df["cluster_id"] >= 0).sum()
n_clusters = df[df["cluster_id"] >= 0]["cluster_id"].nunique()

print(f"Posts: {len(posts):,}")
print(f"Clustered: {len(df):,}")
print(f"Noise (cluster_id == -1): {noise_count:,}")
print(f"In real clusters: {real_count:,}")
print(f"Unique clusters: {n_clusters:,}")

# Filter out noise
clustered = df[df["cluster_id"] >= 0].copy()

# Aggregate per cluster
cluster_stats = clustered.groupby("cluster_id").agg(
    total_attention=("attention", "sum"),
    num_posts=("id", "count"),
    mean_attention=("attention", "mean"),
    max_score=("score", "max"),
).sort_values("total_attention", ascending=False)

# Add top title per cluster
top_titles = clustered.loc[clustered.groupby("cluster_id")["attention"].idxmax()][["cluster_id", "title"]]
top_titles = top_titles.set_index("cluster_id")["title"].rename("top_title")
cluster_stats = cluster_stats.join(top_titles)


def show_cluster(cluster_id, n=15):
    """Display top titles in a cluster by attention score."""
    subset = clustered[clustered["cluster_id"] == cluster_id].sort_values("attention", ascending=False)
    stats = cluster_stats.loc[cluster_id]
    print(f"=== Cluster {cluster_id} ===")
    print(f"Posts: {stats['num_posts']}  |  Total attention: {stats['total_attention']:.0f}  |  Mean: {stats['mean_attention']:.1f}")
    print()
    for _, row in subset.head(n).iterrows():
        print(f"  [{row['score']:>5}] {row['title']}")
    print()


# --- Top 30 clusters by total attention ---
print("\n" + "=" * 80)
print("TOP 30 CLUSTERS BY TOTAL ATTENTION")
print("=" * 80)
for _, row in cluster_stats.head(30).iterrows():
    print(f"  Cluster {row.name:>5} | {row['num_posts']:>4} posts | attn {row['total_attention']:>8.0f} | {row['top_title'][:80]}")

# --- Inspect top 10 clusters ---
print("\n" + "=" * 80)
print("TOP 10 CLUSTER DETAILS")
print("=" * 80)
top_ids = cluster_stats.head(10).index.tolist()
for cid in top_ids:
    show_cluster(cid)

# --- Size distribution ---
print("\n" + "=" * 80)
print("CLUSTER SIZE DISTRIBUTION")
print("=" * 80)
size_dist = cluster_stats["num_posts"].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
print(size_dist.to_string())
small = ((cluster_stats["num_posts"] >= 5) & (cluster_stats["num_posts"] <= 10)).sum()
mid = ((cluster_stats["num_posts"] >= 11) & (cluster_stats["num_posts"] <= 50)).sum()
large = (cluster_stats["num_posts"] > 50).sum()
print(f"\nClusters with 5-10 posts: {small}")
print(f"Clusters with 11-50 posts: {mid}")
print(f"Clusters with 50+ posts: {large}")

# --- Coherence spot-check: 5 random mid-sized clusters ---
print("\n" + "=" * 80)
print("COHERENCE SPOT-CHECK (5 random mid-sized clusters)")
print("=" * 80)
mid_clusters = cluster_stats[(cluster_stats["num_posts"] >= 10) & (cluster_stats["num_posts"] <= 30)]
sample_ids = mid_clusters.sample(5, random_state=42).index.tolist()
for cid in sample_ids:
    show_cluster(cid, n=10)
