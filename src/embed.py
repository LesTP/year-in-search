"""
Phase 2: Embed — encode post titles into vector embeddings via toolkit.

Usage:
    python -m src.embed --year 2024
"""

import argparse

import numpy as np
import pandas as pd

from . import config


def embed_titles(df: pd.DataFrame) -> np.ndarray:
    """Embed all titles using toolkit.embedding.

    Args:
        df: DataFrame with 'title' column.

    Returns:
        ndarray of shape (n_posts, 384).
    """
    from toolkit.embedding import EmbeddingConfig, embed

    titles = df["title"].tolist()
    cfg = EmbeddingConfig(
        model=config.EMBEDDING_MODEL,
        batch_size=config.EMBEDDING_BATCH_SIZE,
        cache_dir=config.EMBEDDING_CACHE_DIR,
    )

    print(f"Embedding {len(titles)} titles...")
    result = embed(titles, cfg)
    print(f"  Shape: {result.vectors.shape}, from_cache: {result.from_cache}, computed: {result.computed}")
    return result.vectors


def save(vectors: np.ndarray, ids: np.ndarray, year: int) -> None:
    """Save embeddings and ID mapping."""
    config.EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    emb_path = config.EMBEDDINGS_DIR / f"{year}_embeddings.npy"
    ids_path = config.EMBEDDINGS_DIR / f"{year}_ids.npy"
    np.save(emb_path, vectors)
    np.save(ids_path, ids)
    print(f"  Saved embeddings to {emb_path}")
    print(f"  Saved ID mapping to {ids_path}")


def run(year: int) -> np.ndarray:
    """Embed pipeline: load posts, embed titles, save."""
    posts_path = config.RAW_DIR / f"{year}_posts.parquet"
    df = pd.read_parquet(posts_path)

    vectors = embed_titles(df)
    save(vectors, df["id"].values, year)
    return vectors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed HN titles")
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    run(args.year)
