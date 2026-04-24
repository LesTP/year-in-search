"""
Phase 3: Cluster — group embeddings into topic clusters via toolkit.

Usage:
    python -m src.cluster --year 2024
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import config

# Add toolkit to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "toolkit" / "src"))


def cluster_embeddings(vectors: np.ndarray) -> np.ndarray:
    """Cluster embeddings using toolkit.clustering.

    Args:
        vectors: ndarray of shape (n_posts, embedding_dim).

    Returns:
        ndarray of cluster labels, shape (n_posts,). -1 = noise.
    """
    from toolkit.clustering import ClusterConfig, cluster

    cfg = ClusterConfig(
        min_cluster_size=config.MIN_CLUSTER_SIZE,
        min_samples=config.MIN_SAMPLES,
        reduce_dims=config.REDUCE_DIMS,
    )

    print(f"Clustering {vectors.shape[0]} embeddings (reduce_dims={config.REDUCE_DIMS})...")
    result = cluster(vectors, cfg)
    print(f"  Found {result.n_clusters} clusters, {result.n_noise} noise items")
    return result.labels


def save(ids: np.ndarray, labels: np.ndarray, year: int) -> None:
    """Save cluster assignments to parquet."""
    config.CLUSTERS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({"id": ids, "cluster_id": labels})
    path = config.CLUSTERS_DIR / f"{year}_clusters.parquet"
    df.to_parquet(path, index=False)
    print(f"  Saved cluster assignments to {path}")


def run(year: int) -> np.ndarray:
    """Cluster pipeline: load embeddings, cluster, save."""
    vectors = np.load(config.EMBEDDINGS_DIR / f"{year}_embeddings.npy")
    ids = np.load(config.EMBEDDINGS_DIR / f"{year}_ids.npy")

    labels = cluster_embeddings(vectors)
    save(ids, labels, year)
    return labels


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cluster HN embeddings")
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    run(args.year)
