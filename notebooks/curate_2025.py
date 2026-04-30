"""Create 2025 AI-curated topics CSV with selected topics + breakout deaths."""
import json
import pandas as pd
import numpy as np

# Load scored topics and posts+clusters for breakout extraction
topics = pd.read_parquet("data/scored/2025_topics.parquet")
posts = pd.read_parquet("data/raw/2025_posts.parquet")
clusters = pd.read_parquet("data/clusters/2025_clusters.parquet")

# Selected cluster IDs and their curated labels
selected = {
    2456: "Apple M5 / Mac hardware",
    476: "Apple vs UK encryption backdoor",
    1010: "Claude Code",
    365: "DeepSeek R1",
    1743: "EU age verification",
    296: "EU Chat Control (encryption)",
    2033: "Android developer verification",
    287: "GPT-4.5 / GPT-5",
    154: "GrapheneOS",
    216: "Vibe coding",
    2156: "LLMs (debate & skepticism)",
    1164: "Rust (adoption & migration)",
    2360: "Valve / Steam Machine",
    2790: "DOGE & government tech",
    191: "TikTok US ban",
    2501: "Signal & government leaks",
    1091: "uv (Python packaging)",
    192: "Pebble smartwatch revival",
}

# Filter scored topics to selected clusters
curated = topics[topics["cluster_id"].isin(selected.keys())].copy()
curated["label"] = curated["cluster_id"].map(selected)

# --- Extract breakout deaths from cluster 3346 ---
df = posts.merge(clusters, on="id", how="inner")
deaths_cluster = df[df["cluster_id"] == 3346].copy()
deaths_cluster["week"] = deaths_cluster["timestamp"].dt.isocalendar().week.astype(int)

breakout_names = {
    "Bill Atkinson": ["bill atkinson"],
    "David Lynch": ["david lynch"],
}

for person, keywords in breakout_names.items():
    # Find posts mentioning this person
    mask = deaths_cluster["title"].str.lower().apply(
        lambda t: any(kw in str(t) for kw in keywords)
    )
    person_posts = deaths_cluster[mask]

    if len(person_posts) == 0:
        print(f"  WARNING: No posts found for {person}")
        continue

    # Build time series
    weekly = person_posts.groupby("week")["attention"].sum()
    time_series = [float(weekly.get(w, 0.0)) for w in range(1, 54)]

    total_attention = float(person_posts["attention"].sum())
    peak_attention = max(time_series)
    peak_week = time_series.index(peak_attention) + 1
    num_posts = len(person_posts)
    threshold = 0.2 * peak_attention if peak_attention > 0 else 0
    duration_weeks = sum(1 for v in time_series if v > threshold)
    mean_attention = total_attention / 53
    spike_ratio = round(peak_attention / mean_attention, 2) if mean_attention > 0 else 0

    if spike_ratio > 4 and duration_weeks <= 3:
        category = "spike"
    elif duration_weeks > 8:
        category = "sustained"
    else:
        category = "moderate"

    # Use synthetic cluster IDs (negative to avoid collision)
    synthetic_id = -hash(person) % 100000

    new_row = pd.DataFrame([{
        "cluster_id": synthetic_id,
        "total_attention": total_attention,
        "peak_attention": peak_attention,
        "peak_week": peak_week,
        "num_posts": num_posts,
        "duration_weeks": duration_weeks,
        "spike_ratio": spike_ratio,
        "category": category,
        "time_series": json.dumps(time_series),
        "label": f"{person} has died",
    }])

    curated = pd.concat([curated, new_row], ignore_index=True)
    print(f"  {person}: {num_posts} posts, peak wk {peak_week}, {total_attention:.0f} attn, {category}")

# Save
curated.to_csv("data/curated/2025_ai_curated_topics.csv", index=False)
print(f"\nSaved {len(curated)} curated topics to data/curated/2025_ai_curated_topics.csv")
