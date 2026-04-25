"""
Phase 1: Ingest — load HN data from HuggingFace, filter, compute attention scores.

Usage:
    python -m src.ingest --year 2024
"""

import argparse
import json
from dataclasses import asdict, dataclass, field

import pandas as pd

from . import config


@dataclass
class IngestReport:
    """Structured report from the ingest phase for downstream review."""

    year: int
    months_loaded: list[str] = field(default_factory=list)
    months_skipped: list[str] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    total_rows_raw: int = 0
    total_rows_filtered: int = 0

    def save(self, path):
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


def load_and_filter(year: int) -> tuple[pd.DataFrame, IngestReport]:
    """Load HN dataset for a specific year, filter to stories.

    Downloads only the monthly parquet files for the target year from HuggingFace,
    avoiding the full 47M-row dataset download.

    Args:
        year: Target year (e.g. 2024).

    Returns:
        Tuple of (DataFrame, IngestReport). DataFrame has columns:
        id, title, score, num_comments, timestamp, url, attention.
    """
    from huggingface_hub import hf_hub_download
    from huggingface_hub.utils import EntryNotFoundError

    report = IngestReport(year=year)

    # Download only the monthly files for the target year
    months = [f"data/{year}/{year}-{m:02d}.parquet" for m in range(1, 13)]
    frames = []
    for month_file in months:
        print(f"  Downloading {month_file}...")
        try:
            path = hf_hub_download(
                repo_id=config.HF_DATASET,
                filename=month_file,
                repo_type="dataset",
            )
            frames.append(pd.read_parquet(path))
            report.months_loaded.append(month_file)
        except EntryNotFoundError:
            # Expected for partial years (e.g., current year)
            report.months_skipped.append(month_file)
            print(f"  Skipped {month_file} (not found — partial year?)")
        except Exception as e:
            # Unexpected error — record for review
            report.errors.append({
                "file": month_file,
                "error_type": type(e).__name__,
                "message": str(e),
            })
            print(f"  ERROR downloading {month_file}: {type(e).__name__}: {e}")

    if not frames:
        raise RuntimeError(f"No data files found for year {year}")

    df = pd.concat(frames, ignore_index=True)
    report.total_rows_raw = len(df)
    print(f"  Loaded {len(df)} rows for {year} ({len(report.months_loaded)}/12 months)")

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
    df = df[columns].copy()

    print(f"  {len(df)} stories for {year} (score >= {config.MIN_SCORE_THRESHOLD})")
    report.total_rows_filtered = len(df)
    return df, report


def save(df: pd.DataFrame, report: IngestReport, year: int) -> None:
    """Save filtered posts and ingest report."""
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RAW_DIR / f"{year}_posts.parquet"
    df.to_parquet(path, index=False)
    print(f"  Saved to {path}")

    report_path = config.RAW_DIR / f"{year}_ingest_report.json"
    report.save(report_path)
    print(f"  Report saved to {report_path}")
    if report.has_errors:
        print(f"  WARNING: {len(report.errors)} download error(s) — review {report_path}")


def run(year: int) -> pd.DataFrame:
    """Ingest pipeline: load, filter, save, return."""
    df, report = load_and_filter(year)
    save(df, report, year)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest HN data")
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    run(args.year)
