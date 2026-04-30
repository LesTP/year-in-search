"""Add short representative topic labels to the draft CSV based on top 5 titles per cluster."""
import pandas as pd

df = pd.read_csv("data/curated/2025_draft_topics.csv")

# Map of cluster_id -> short topic label, derived from reading all 5 top titles
topic_labels = {
    2156: "LLMs (debate & skepticism)",
    1164: "Rust (adoption & migration)",
    365: "DeepSeek R1",
    2790: "DOGE & government tech",
    287: "GPT-4.5 / GPT-5",
    191: "TikTok US ban",
    2603: "Programming culture & craft",
    1309: "Docker alternatives & containers",
    296: "EU Chat Control (encryption)",
    1010: "Claude Code",
    2360: "Valve / Steam Machine",
    1662: "Israel-Gaza conflict",
    1533: "LLM interpretability & research",
    1409: "Nuclear energy",
    285: "Gemini (models & CLI)",
    1003: "Claude (Anthropic)",
    2501: "Signal & government leaks",
    1583: "PostgreSQL ecosystem",
    563: "Robotics",
    2095: "Wealth & life choices",
    2168: "Open source movement",
    2456: "Apple M5 / Mac hardware",
    3524: "Ask HN: What are you working on?",
    1058: "Fonts & typography",
    797: "Git",
    2228: "Apple design & direction",
    2953: "Blogging",
    1631: "OpenAI & Microsoft",
    476: "Apple vs UK encryption backdoor",
    1581: "ChatGPT (usage & culture)",
    1546: "SQLite",
    3346: "Notable deaths",
    216: "Vibe coding",
    1442: "Google AI (Search & ethics)",
    2033: "Android developer verification",
    1743: "EU age verification",
    1091: "uv (Python packaging)",
    1865: "Music software & tools",
    2940: "Software development opinions",
    1762: "TLS / HTTPS certificates",
    1922: "College & education trends",
    192: "Pebble smartwatch revival",
    1590: "Databases",
    802: "GitHub & Microsoft",
    2476: "Trains & urban transit",
    2012: "Code quality & philosophy",
    674: "Hacker News (meta)",
    154: "GrapheneOS",
    1659: "Google (culture & criticism)",
    2368: "Go language",
}

df["topic_label"] = df["cluster_id"].map(topic_labels)

df.to_csv("data/curated/2025_draft_topics.csv", index=False)
print("Added topic_label column to 2025_draft_topics.csv")
print(f"\nLabels:")
for _, row in df.iterrows():
    print(f"  {row['rank']:>2}. {row['topic_label']}")
