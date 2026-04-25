"""
Phase 5: Label — auto-label each cluster from its highest-attention post title.

Usage:
    python -m src.label --year 2024
"""

import argparse
import re

import pandas as pd

from . import config

# HN title prefixes to strip
_HN_PREFIXES = re.compile(
    r"^(Show HN|Ask HN|Tell HN|Launch HN)\s*:\s*",
    re.IGNORECASE,
)


def clean_title(title: str) -> str:
    """Strip HN prefixes and leading punctuation/whitespace."""
    label = _HN_PREFIXES.sub("", title)
    label = label.lstrip("- .:;!?")
    return label.strip()


def auto_label(posts: pd.DataFrame, clusters: pd.DataFrame) -> pd.DataFrame:
    """Pick the highest-attention post title per cluster as the label.

    Returns a DataFrame with columns [cluster_id, label].
    """
    merged = posts.merge(clusters, on="id", how="inner")
    merged = merged[merged["cluster_id"] != -1]
    merged = merged[merged["title"].str.strip() != ""]

    # For each cluster, pick the title with the highest attention
    idx = merged.groupby("cluster_id")["attention"].idxmax()
    best = merged.loc[idx, ["cluster_id", "title"]].copy()
    best["label"] = best["title"].apply(clean_title)

    return best[["cluster_id", "label"]]


def run(year: int) -> pd.DataFrame:
    print(f"Phase 5: Label (year={year})")

    posts = pd.read_parquet(config.RAW_DIR / f"{year}_posts.parquet")
    clusters = pd.read_parquet(config.CLUSTERS_DIR / f"{year}_clusters.parquet")
    topics = pd.read_parquet(config.SCORED_DIR / f"{year}_topics.parquet")

    labels = auto_label(posts, clusters)

    # Merge labels into scored topics
    if "label" in topics.columns:
        topics = topics.drop(columns=["label"])
    topics = topics.merge(labels, on="cluster_id", how="left")
    topics["label"] = topics["label"].fillna("")

    # Save in place
    path = config.SCORED_DIR / f"{year}_topics.parquet"
    topics.to_parquet(path, index=False)

    labeled = (topics["label"] != "").sum()
    print(f"  Labeled {labeled:,} / {len(topics):,} topics")

    # Show top 20 by total attention
    print(f"\n  Top 20 labels by total attention:")
    top20 = topics.nlargest(20, "total_attention")
    for _, row in top20.iterrows():
        print(f"    {row['total_attention']:>10,.0f}  {row['category']:<10} {row['label']}")

    return topics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-label topic clusters")
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()
    run(args.year)
