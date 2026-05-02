"""
Phase 7b: Visualize (ClearViz edition) — ridge plot from curated topics.

Changes from visualize.py:
  - Title states a finding; subtitle provides context
  - Serif font, off-white background
  - Inward ticks, stronger spine color
  - Top-3 topics by attention score are numbered in labels
  - Larger label font
  - Source footnote

Usage:
    python -m src.visualize_v2 --year 2025
    python -m src.visualize_v2 --year 2024 --curated ai
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

OUTPUT_V2_DIR = config.PROJECT_ROOT / "output_v2"

_LABEL_WRAP = 18  # wrap labels longer than this at the last space

# Manual break overrides: label prefix → position to insert \n
_LABEL_BREAKS = {
    "David Lynch": "David Lynch\nhas died",
    "Pebble smartwatch": "Pebble\nsmartwatch revival",
    "DOGE &": "DOGE\n& government tech",
    "Bill Atkinson": "Bill Atkinson\nhas died",
    "Apple M5": "Apple M5\n/ Mac hardware",
    "Valve /": "Valve\n/ Steam Machine",
}


def _wrap_label(text: str, width: int = _LABEL_WRAP) -> str:
    """Wrap text at the last space before *width*, with manual overrides."""
    # Check manual overrides first
    for prefix, replacement in _LABEL_BREAKS.items():
        if text.startswith(prefix) or text.lstrip("0123456789. ").startswith(prefix):
            # Preserve any leading number prefix (e.g. "1. ")
            num_prefix = ""
            rest = text
            if rest and rest[0].isdigit():
                dot_pos = rest.find(". ")
                if dot_pos != -1:
                    num_prefix = rest[:dot_pos + 2]
                    rest = rest[dot_pos + 2:]
            for pfx, repl in _LABEL_BREAKS.items():
                if rest.startswith(pfx) or rest == repl.replace("\n", " "):
                    return num_prefix + repl
    if len(text) <= width:
        return text
    idx = text.rfind(" ", 0, width)
    if idx == -1:
        idx = width
    return text[:idx] + "\n" + text[idx:].lstrip()


def load_topics(year: int, curated: str | None = None) -> pd.DataFrame:
    """Load topic data, optionally filtered to a curated subset."""
    topics = pd.read_parquet(config.SCORED_DIR / f"{year}_topics.parquet")

    if curated:
        suffix = {"ai": "ai_curated", "final": "final"}.get(curated, curated)
        curated_path = config.CURATED_DIR / f"{year}_{suffix}_topics.csv"
        curated_df = pd.read_csv(curated_path)
        topics = topics[topics["cluster_id"].isin(curated_df["cluster_id"])]
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
    """Render a ridge plot of topic attention curves (ClearViz edition)."""
    # --- Parse & prepare rows ---
    rows = []
    for _, row in topics.iterrows():
        ts = json.loads(row["time_series"]) if isinstance(row["time_series"], str) else row["time_series"]
        ts = np.array(ts, dtype=float)
        rows.append({
            "label": row["label"],
            "peak_week": int(row["peak_week"]),
            "ts": ts,
            "total": float(ts.sum()),
        })

    rows.sort(key=lambda r: r["peak_week"], reverse=True)

    n_topics = len(rows)
    weeks = np.arange(1, len(rows[0]["ts"]) + 1)

    # Identify top-3 by total attention for numbering
    by_volume = sorted(rows, key=lambda r: r["total"], reverse=True)
    top3_labels = {}
    for rank, r in enumerate(by_volume[:3], start=1):
        top3_labels[r["label"]] = rank

    # --- Layout ---
    plt.rcParams["font.family"] = "serif"
    fig_height = max(6, 1.0 + n_topics * 0.55)
    fig, ax = plt.subplots(figsize=(14, fig_height))
    fig.patch.set_facecolor("#fffff8")
    ax.set_facecolor("#fffff8")

    overlap = 0.15
    row_height = 1.0

    for i, row in enumerate(rows):
        ts = row["ts"]
        if smooth:
            ts = gaussian_filter1d(ts, sigma=sigma)

        peak = ts.max()
        ts_norm = ts / peak if peak > 0 else ts

        y_offset = i * row_height * (1 - overlap)

        # Color based on peak_week (original gradient)
        color = _PEAK_CMAP(row["peak_week"] / 53)

        # Fill
        ax.fill_between(
            weeks,
            y_offset,
            y_offset + ts_norm * row_height,
            color=color,
            alpha=0.85,
            linewidth=0,
            zorder=n_topics - i,
        )

        # Outline
        ax.plot(
            weeks,
            y_offset + ts_norm * row_height,
            color="white",
            linewidth=0.8,
            zorder=n_topics - i + 0.5,
        )

        # Label — numbered for top-3
        label_text = row["label"]
        if row["label"] in top3_labels:
            label_text = f"#{top3_labels[row['label']]}: {row['label']}"
        label_text = _wrap_label(label_text)

        ax.text(
            0, y_offset + row_height * 0.3,
            label_text,
            fontsize=13,
            fontweight="bold",
            color="#333333",
            va="center",
            ha="right",
            zorder=n_topics + 1,
        )

    # --- Axes ---
    ax.set_xlim(1, len(rows[0]["ts"]))
    ax.set_ylim(-0.1, (n_topics - 1) * row_height * (1 - overlap) + row_height + 0.1)

    ax.set_xticks([w for w, _ in _MONTH_LABELS])
    ax.set_xticklabels([m for _, m in _MONTH_LABELS], fontsize=11)
    ax.tick_params(axis="x", length=4, direction="in", color="#999999")

    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#999999")
    ax.spines["bottom"].set_linewidth(0.8)

    # Title
    ax.set_title(
        f"What Tech Cared About in {year}",
        fontsize=20,
        fontweight="normal",
        fontfamily="serif",
        pad=28,
    )

    # Subtitle
    variant = "smoothed" if smooth else "week-by-week"
    ax.text(
        0.5, 1.015,
        f"Hacker News attention by topic ({variant})",
        transform=ax.transAxes,
        fontsize=11,
        color="#888888",
        ha="center",
        va="bottom",
    )

    # Source footnote — left-aligned under labels
    ax.text(
        0, -0.04,
        "Top three topics by highest \ntotal attention are numbered",
        transform=ax.transAxes,
        fontsize=9,
        color="#999999",
        ha="right",
        va="top",
    )

    # Source — right-aligned
    ax.text(
        1.0, -0.04,
        "Source: Hacker News",
        transform=ax.transAxes,
        fontsize=9,
        color="#999999",
        ha="right",
        va="top",
    )

    fig.tight_layout()

    return fig


def run(year: int, curated: str | None = "ai") -> None:
    print(f"Phase 7b: Visualize ClearViz edition (year={year}, curated={curated})")

    topics = load_topics(year, curated=curated)
    print(f"  Loaded {len(topics)} topics")

    OUTPUT_V2_DIR.mkdir(parents=True, exist_ok=True)

    # Raw version
    fig_raw = render_ridge(topics, year, smooth=False)
    raw_png = OUTPUT_V2_DIR / f"{year}_year_in_tech_raw.png"
    raw_svg = OUTPUT_V2_DIR / f"{year}_year_in_tech_raw.svg"
    fig_raw.savefig(raw_png, dpi=200, bbox_inches="tight", facecolor="#fffff8")
    fig_raw.savefig(raw_svg, bbox_inches="tight", facecolor="#fffff8")
    plt.close(fig_raw)
    print(f"  Saved raw: {raw_png}")

    # Smoothed version
    fig = render_ridge(topics, year, smooth=True, sigma=1.0)
    smooth_png = OUTPUT_V2_DIR / f"{year}_year_in_tech_smooth.png"
    smooth_svg = OUTPUT_V2_DIR / f"{year}_year_in_tech_smooth.svg"
    fig.savefig(smooth_png, dpi=200, bbox_inches="tight", facecolor="#fffff8")
    fig.savefig(smooth_svg, bbox_inches="tight", facecolor="#fffff8")
    plt.close(fig)
    print(f"  Saved smooth: {smooth_png}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate ridge plot (ClearViz edition)")
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--curated", type=str, default="ai",
                        help="Curated list to use: 'ai', 'final', or omit for all scored topics")
    args = parser.parse_args()
    run(args.year, curated=args.curated if args.curated else None)
