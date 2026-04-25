"""
Phase 4: Score & Classify — aggregate attention per cluster, compute time series
and metrics, classify topics as spike/sustained/moderate.

Usage:
    python -m src.score --year 2024
"""

import argparse
import json

import pandas as pd

from . import config


def load(year: int) -> pd.DataFrame:
    """Join posts with cluster assignments, drop noise."""
    posts = pd.read_parquet(config.RAW_DIR / f"{year}_posts.parquet")
    clusters = pd.read_parquet(config.CLUSTERS_DIR / f"{year}_clusters.parquet")

    df = posts.merge(clusters, on="id", how="inner")
    df = df[df["cluster_id"] != -1].copy()

    print(f"  Loaded {len(posts):,} posts, {len(clusters):,} cluster assignments")
    print(f"  After dropping noise: {len(df):,} posts in {df['cluster_id'].nunique():,} clusters")

    return df


def compute_topic_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-cluster metrics and time series."""

    # ISO week number for each post (local copy to avoid mutating input)
    df = df.copy()
    df["week"] = df["timestamp"].dt.isocalendar().week.astype(int)

    results = []

    for cluster_id, group in df.groupby("cluster_id"):
        # 4a: Time series — 53-point weekly attention curve (ISO weeks 1-53)
        weekly = group.groupby("week")["attention"].sum()
        time_series = [float(weekly.get(w, 0.0)) for w in range(1, 54)]

        # 4b: Metrics
        total_attention = float(group["attention"].sum())
        peak_attention = max(time_series)
        peak_week = time_series.index(peak_attention) + 1  # 1-indexed
        num_posts = len(group)
        mean_attention = total_attention / 53  # spread across full year (ISO weeks 1-53)

        # duration: weeks with attention > 20% of peak
        if peak_attention > 0:
            threshold = 0.2 * peak_attention
            duration_weeks = sum(1 for v in time_series if v > threshold)
        else:
            duration_weeks = 0

        # spike ratio
        spike_ratio = peak_attention / mean_attention if mean_attention > 0 else 0.0

        # 4c: Classification
        if spike_ratio > config.SPIKE_RATIO_THRESHOLD and duration_weeks <= config.SPIKE_MAX_DURATION:
            category = "spike"
        elif duration_weeks > config.SUSTAINED_MIN_DURATION:
            category = "sustained"
        else:
            category = "moderate"

        results.append({
            "cluster_id": cluster_id,
            "total_attention": total_attention,
            "peak_attention": peak_attention,
            "peak_week": peak_week,
            "num_posts": num_posts,
            "duration_weeks": duration_weeks,
            "spike_ratio": round(spike_ratio, 2),
            "category": category,
            "time_series": json.dumps(time_series),
        })

    topics = pd.DataFrame(results)
    return topics


def save(topics: pd.DataFrame, year: int) -> None:
    config.SCORED_DIR.mkdir(parents=True, exist_ok=True)
    path = config.SCORED_DIR / f"{year}_topics.parquet"
    topics.to_parquet(path, index=False)
    print(f"  Saved {len(topics):,} topics to {path}")


def run(year: int) -> pd.DataFrame:
    print(f"Phase 4: Score & Classify (year={year})")
    df = load(year)
    topics = compute_topic_scores(df)
    save(topics, year)

    # Summary
    counts = topics["category"].value_counts()
    print(f"\n  Classification breakdown:")
    for cat in ["spike", "sustained", "moderate"]:
        print(f"    {cat}: {counts.get(cat, 0)}")
    print(f"  Top 5 by total attention:")
    top5 = topics.nlargest(5, "total_attention")
    for _, row in top5.iterrows():
        print(f"    cluster {row['cluster_id']:>5}: {row['total_attention']:>10,.0f} attn, "
              f"peak wk {row['peak_week']:>2}, {row['category']}")

    return topics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score & classify topic clusters")
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()
    run(args.year)
