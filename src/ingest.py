"""
Phase 1: Ingest — load HN data from HuggingFace, filter, compute attention scores.

Usage:
    python -m src.ingest --year 2024
"""

import argparse

import pandas as pd

from . import config


def load_and_filter(year: int) -> pd.DataFrame:
    """Load HN dataset, filter to stories for the given year.

    Args:
        year: Target year (e.g. 2024).

    Returns:
        DataFrame with columns: id, title, score, num_comments, timestamp, url, attention.
    """
    from datasets import load_dataset

    print(f"Loading HN dataset from {config.HF_DATASET}...")
    ds = load_dataset(config.HF_DATASET, split="train")
    df = ds.to_pandas()

    # Convert types — HF dataset stores these as strings/ints
    df["type"] = pd.to_numeric(df["type"], errors="coerce")
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0).astype(int)
    df["descendants"] = pd.to_numeric(df["descendants"], errors="coerce").fillna(0).astype(int)

    # Filter to stories (type=1)
    df = df[df["type"] == config.STORY_TYPE].copy()

    # Parse timestamp and filter to target year
    df["timestamp"] = pd.to_datetime(df["time"], utc=True)
    df = df[df["timestamp"].dt.year == year].copy()

    # Filter by minimum score
    df = df[df["score"] >= config.MIN_SCORE_THRESHOLD].copy()

    # Rename and compute attention
    df = df.rename(columns={"descendants": "num_comments"})
    df["attention"] = df["score"] + config.COMMENT_WEIGHT * df["num_comments"]

    columns = ["id", "title", "score", "num_comments", "timestamp", "url", "attention"]
    df = df[[c for c in columns if c in df.columns]].copy()

    print(f"  {len(df)} stories for {year} (score >= {config.MIN_SCORE_THRESHOLD})")
    return df


def save(df: pd.DataFrame, year: int) -> None:
    """Save filtered posts to parquet."""
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RAW_DIR / f"{year}_posts.parquet"
    df.to_parquet(path, index=False)
    print(f"  Saved to {path}")


def run(year: int) -> pd.DataFrame:
    """Ingest pipeline: load, filter, save, return."""
    df = load_and_filter(year)
    save(df, year)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest HN data")
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    run(args.year)
