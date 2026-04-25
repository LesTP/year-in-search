"""
Phase 6: Curate — export ranked topic list as CSV for human review.

Usage:
    python -m src.curate --year 2024
"""

import argparse

import pandas as pd

from . import config


def build_draft(year: int, top_n: int = 50) -> pd.DataFrame:
    """Build a ranked draft CSV of the top N topics with sample titles."""
    topics = pd.read_parquet(config.SCORED_DIR / f"{year}_topics.parquet")
    posts = pd.read_parquet(config.RAW_DIR / f"{year}_posts.parquet")
    clusters = pd.read_parquet(config.CLUSTERS_DIR / f"{year}_clusters.parquet")

    # Get top titles per cluster
    merged = posts.merge(clusters, on="id", how="inner")
    merged = merged[merged["cluster_id"] != -1]
    merged = merged[merged["title"].str.strip() != ""]

    def top_titles(group, n=5):
        top = group.nlargest(n, "attention")
        return " | ".join(top["title"].tolist())

    titles_by_cluster = merged.groupby("cluster_id").apply(top_titles).reset_index()
    titles_by_cluster.columns = ["cluster_id", "top_titles"]

    # Rank and join
    ranked = topics.nlargest(top_n, "total_attention").copy()
    ranked["rank"] = range(1, len(ranked) + 1)
    ranked = ranked.merge(titles_by_cluster, on="cluster_id", how="left")
    ranked["top_titles"] = ranked["top_titles"].fillna("")

    columns = [
        "rank", "cluster_id", "label", "total_attention", "peak_attention",
        "peak_week", "num_posts", "duration_weeks", "category", "top_titles",
    ]
    return ranked[columns]


def save(draft: pd.DataFrame, year: int) -> None:
    config.CURATED_DIR.mkdir(parents=True, exist_ok=True)
    path = config.CURATED_DIR / f"{year}_draft_topics.csv"
    draft.to_csv(path, index=False)
    print(f"  Saved {len(draft)} topics to {path}")


def run(year: int) -> pd.DataFrame:
    print(f"Phase 6: Curate (year={year})")
    draft = build_draft(year)
    save(draft, year)

    # Summary
    counts = draft["category"].value_counts()
    print(f"\n  Category breakdown (top 50):")
    for cat in ["spike", "sustained", "moderate"]:
        print(f"    {cat}: {counts.get(cat, 0)}")
    print(f"\n  Top 10:")
    for _, row in draft.head(10).iterrows():
        print(f"    {row['rank']:>2}. {row['label'][:60]:<60} {row['category']:<10} {row['total_attention']:>8,.0f}")

    return draft


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export ranked topic list for curation")
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()
    run(args.year)
