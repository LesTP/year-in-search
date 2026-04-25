"""
Phase 7: Visualize — generate ridge plot from curated topics.

Produces both raw and Gaussian-smoothed versions. Topics are ordered
chronologically by peak_week, colored with a cool→warm gradient.

Usage:
    python -m src.visualize --year 2024
    python -m src.visualize --year 2024 --curated ai   # use AI-curated list
    python -m src.visualize --year 2024 --smooth-only   # skip raw version
"""

import argparse
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter1d

from . import config

# Month labels at approximate ISO week positions
_MONTH_LABELS = [
    (2, "Jan"), (6, "Feb"), (10, "Mar"), (15, "Apr"),
    (19, "May"), (23, "Jun"), (28, "Jul"), (32, "Aug"),
    (36, "Sep"), (41, "Oct"), (45, "Nov"), (49, "Dec"),
]

# Cool-to-warm gradient (blue → teal → yellow → orange → red)
_PEAK_CMAP = LinearSegmentedColormap.from_list(
    "peak_week",
    ["#4575b4", "#91bfdb", "#fee090", "#fc8d59", "#d73027"],
)


def load_topics(year: int, curated: str | None = None) -> pd.DataFrame:
    """Load topic data, optionally filtered to a curated subset."""
    topics = pd.read_parquet(config.SCORED_DIR / f"{year}_topics.parquet")

    if curated:
        suffix = {"ai": "ai_curated", "final": "final"}.get(curated, curated)
        curated_path = config.CURATED_DIR / f"{year}_{suffix}_topics.csv"
        curated_df = pd.read_csv(curated_path)
        # Keep only curated cluster_ids, in curated order
        topics = topics[topics["cluster_id"].isin(curated_df["cluster_id"])]
        # Use curated labels if available
        if "label" in curated_df.columns:
            label_map = dict(zip(curated_df["cluster_id"], curated_df["label"]))
            topics["label"] = topics["cluster_id"].map(label_map)

    return topics


def render_ridge(
    topics: pd.DataFrame,
    year: int,
    smooth: bool = False,
    sigma: float = 1.5,
) -> plt.Figure:
    """Render a ridge plot of topic attention curves.

    Args:
        topics: DataFrame with columns [label, peak_week, time_series].
        year: Year for the title.
        smooth: If True, apply Gaussian smoothing to curves.
        sigma: Gaussian kernel width (only used if smooth=True).

    Returns:
        matplotlib Figure.
    """
    # Parse time series and sort by peak_week (chronological)
    rows = []
    for _, row in topics.iterrows():
        ts = json.loads(row["time_series"]) if isinstance(row["time_series"], str) else row["time_series"]
        ts = np.array(ts, dtype=float)
        rows.append({
            "label": row["label"],
            "peak_week": int(row["peak_week"]),
            "ts": ts,
        })

    rows.sort(key=lambda r: r["peak_week"], reverse=True)

    n_topics = len(rows)
    weeks = np.arange(1, len(rows[0]["ts"]) + 1)

    # --- Layout ---
    fig_height = max(6, 1.0 + n_topics * 0.55)
    fig, ax = plt.subplots(figsize=(14, fig_height))

    overlap = 0.15  # fraction of row height that overlaps with neighbor
    row_height = 1.0

    for i, row in enumerate(rows):
        ts = row["ts"]
        if smooth:
            ts = gaussian_filter1d(ts, sigma=sigma)

        # Normalize each curve to [0, 1] so rows have uniform height
        peak = ts.max()
        if peak > 0:
            ts_norm = ts / peak
        else:
            ts_norm = ts

        # Vertical offset — bottom row first (index 0 at bottom)
        y_offset = i * row_height * (1 - overlap)

        # Color based on peak_week (1–53 → 0–1)
        color = _PEAK_CMAP(row["peak_week"] / 53)

        # Fill
        ax.fill_between(
            weeks,
            y_offset,
            y_offset + ts_norm * row_height,
            color=color,
            alpha=0.85,
            linewidth=0,
            zorder=n_topics - i,  # earlier topics in front
        )

        # Outline
        ax.plot(
            weeks,
            y_offset + ts_norm * row_height,
            color="white",
            linewidth=0.8,
            zorder=n_topics - i + 0.5,
        )

        # Label
        ax.text(
            0, y_offset + row_height * 0.3,
            row["label"],
            fontsize=8,
            fontweight="bold",
            color="#333333",
            va="center",
            ha="right",
            zorder=n_topics + 1,
        )

    # --- Axes ---
    ax.set_xlim(1, len(rows[0]["ts"]))
    ax.set_ylim(-0.1, (n_topics - 1) * row_height * (1 - overlap) + row_height + 0.1)

    # Month tick labels
    ax.set_xticks([w for w, _ in _MONTH_LABELS])
    ax.set_xticklabels([m for _, m in _MONTH_LABELS], fontsize=9)
    ax.tick_params(axis="x", length=4, color="#cccccc")

    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#cccccc")

    # Title
    variant = f"smoothed σ={sigma:.1f}" if smooth else "raw"
    ax.set_title(
        f"Year in Tech {year}  ({variant})",
        fontsize=16,
        fontweight="bold",
        pad=12,
    )

    fig.tight_layout()
    return fig


def run(year: int, curated: str | None = "ai") -> None:
    print(f"Phase 7: Visualize (year={year}, curated={curated})")

    topics = load_topics(year, curated=curated)
    print(f"  Loaded {len(topics)} topics")

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Raw version
    fig_raw = render_ridge(topics, year, smooth=False)
    raw_png = config.OUTPUT_DIR / f"{year}_year_in_tech_raw.png"
    raw_svg = config.OUTPUT_DIR / f"{year}_year_in_tech_raw.svg"
    fig_raw.savefig(raw_png, dpi=200, bbox_inches="tight")
    fig_raw.savefig(raw_svg, bbox_inches="tight")
    plt.close(fig_raw)
    print(f"  Saved raw: {raw_png}")

    # Smoothed version (sigma=1.0)
    fig = render_ridge(topics, year, smooth=True, sigma=1.0)
    smooth_png = config.OUTPUT_DIR / f"{year}_year_in_tech_smooth.png"
    smooth_svg = config.OUTPUT_DIR / f"{year}_year_in_tech_smooth.svg"
    fig.savefig(smooth_png, dpi=200, bbox_inches="tight")
    fig.savefig(smooth_svg, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved smooth: {smooth_png}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate ridge plot visualization")
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--curated", type=str, default="ai",
                        help="Curated list to use: 'ai', 'final', or omit for all scored topics")
    args = parser.parse_args()
    run(args.year, curated=args.curated if args.curated else None)
