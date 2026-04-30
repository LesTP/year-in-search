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


def _download_year(year: int) -> tuple[pd.DataFrame, IngestReport]:
    """Download monthly parquet files from HuggingFace for the target year.

    Returns the raw concatenated DataFrame (no filtering) and an IngestReport.
    """
    from huggingface_hub import hf_hub_download
    from huggingface_hub.utils import EntryNotFoundError

    report = IngestReport(year=year)

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
            report.months_skipped.append(month_file)
            print(f"  Skipped {month_file} (not found — partial year?)")
        except Exception as e:
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
    return df, report


def _filter_and_score(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Filter raw data to stories and compute attention scores."""
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
    return df


# Path for the intermediate cached download (before filtering/scoring)
def _cache_path(year: int):
    return config.RAW_DIR / f"{year}_raw_download.parquet"


def load_and_filter(year: int, redownload: bool = False) -> tuple[pd.DataFrame, IngestReport]:
    """Load HN dataset for a specific year, filter to stories.

    Uses a cached raw download if available. Pass redownload=True to force
    a fresh download from HuggingFace.

    Args:
        year: Target year (e.g. 2024).
        redownload: If True, download fresh even if cached data exists.

    Returns:
        Tuple of (DataFrame, IngestReport). DataFrame has columns:
        id, title, score, num_comments, timestamp, url, attention.
    """
    cache = _cache_path(year)

    if cache.exists() and not redownload:
        print(f"  Using cached download: {cache}")
        raw_df = pd.read_parquet(cache)
        report = IngestReport(year=year, total_rows_raw=len(raw_df))
        print(f"  {len(raw_df)} cached rows for {year}")
    else:
        raw_df, report = _download_year(year)
        # Cache the raw download for future runs
        config.RAW_DIR.mkdir(parents=True, exist_ok=True)
        raw_df.to_parquet(cache, index=False)
        print(f"  Cached raw download to {cache}")

    df = _filter_and_score(raw_df, year)
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


def run(year: int, redownload: bool = False) -> pd.DataFrame:
    """Ingest pipeline: load, filter, save, return."""
    df, report = load_and_filter(year, redownload=redownload)
    save(df, report, year)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest HN data")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--redownload", action="store_true",
                        help="Force fresh download from HuggingFace (ignores cache)")
    args = parser.parse_args()
    run(args.year, redownload=args.redownload)
