"""Append synthetic breakout entries to scored parquet so visualize can find them."""
import pandas as pd

scored = pd.read_parquet("data/scored/2025_topics.parquet")
curated = pd.read_csv("data/curated/2025_ai_curated_topics.csv")

# Find synthetic entries (not in scored)
scored_ids = set(scored["cluster_id"])
synthetic = curated[~curated["cluster_id"].isin(scored_ids)].copy()

if len(synthetic) > 0:
    # Drop the label column (scored parquet may not have it yet; label phase adds it)
    cols = [c for c in scored.columns if c in synthetic.columns]
    synthetic = synthetic[cols]
    scored = pd.concat([scored, synthetic], ignore_index=True)
    scored.to_parquet("data/scored/2025_topics.parquet", index=False)
    print(f"Appended {len(synthetic)} synthetic entries to scored parquet")
else:
    print("No synthetic entries to add")
