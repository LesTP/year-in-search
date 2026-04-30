"""Add description column to 2025 AI-curated topics CSV."""
import pandas as pd

df = pd.read_csv("data/curated/2025_ai_curated_topics.csv")

descriptions = {
    154: "GrapheneOS, a privacy-focused Android fork, gained attention as France threatened its developers with arrest over refusing backdoors, while users debated it as the only Android OS providing full security patches.",
    191: "The US Supreme Court upheld the TikTok ban in January, the app briefly went dark, then was restored after Trump signaled a reprieve. Discussion continued throughout the year around child safety and national security.",
    192: "Google open-sourced the Pebble OS and new PebbleOS watches were announced, reviving the beloved smartwatch brand years after its original shutdown.",
    216: "\"Vibe coding\" — using LLMs to generate entire programs from natural language prompts — became a widespread meme and practice, sparking debate about whether it's the future of programming or a recipe for unmaintainable code.",
    287: "OpenAI released GPT-4.5, GPT-4.1, and GPT-5 throughout the year, each drawing intense discussion about capabilities, pricing, and the sycophancy problem in GPT-4o.",
    296: "The EU's Chat Control proposal to scan all private messages, including in encrypted apps, faced sustained opposition. Germany led the blocking minority, but the proposal kept returning in modified forms.",
    365: "Chinese lab DeepSeek released R1, an open-weight reasoning model that rivaled top Western models at a fraction of the cost. It dominated January headlines amid debates about censorship bypasses and a leaked database.",
    476: "The UK government secretly ordered Apple to create a global iCloud encryption backdoor. Apple pulled its data protection tool from the UK market rather than comply, and France publicly rejected a similar mandate.",
    1010: "Anthropic's Claude Code tool — an agentic coding assistant — entered beta and saw rapid adoption, with users reporting it could modernize legacy codebases and handle complex multi-file tasks autonomously.",
    1091: "Astral's uv, a Rust-based Python package manager, was widely praised as the best thing to happen to the Python ecosystem in a decade, with rapid adoption and enthusiastic migration guides.",
    1164: "Rust's role in systems programming was hotly debated all year. High-profile posts about migrating away from Rust sat alongside Greg Kroah-Hartman endorsing Rust in the Linux kernel, reflecting a community in active transition.",
    1743: "The EU proposed an age verification app that would effectively ban Android systems not licensed by Google. Critics saw it as both a privacy threat and an antitrust issue, with Discord implementing face-scanning age checks.",
    2033: "Google announced that Android would only allow apps from verified developers, prompting backlash from the F-Droid community and open-source advocates who saw it as a threat to sideloading.",
    2156: "LLM skepticism and debate sustained all year — from arguments that LLMs can't really build software, to studies showing they reduce public knowledge sharing, to philosophical posts about AI inevitabilism.",
    2360: "Valve announced the Steam Machine console and Steam Frame handheld, positioning itself as the architect behind bringing Windows games to ARM. Linux gaming crossed the 3% Steam market share milestone.",
    2456: "Apple launched the M5 chip and updated MacBook Pro lineup. Discussion centered on benchmarks, the x86-to-ARM performance gap, and whether Intel and AMD could catch up.",
    2501: "A journalist was accidentally added to a Signal group chat with US national security leaders planning military operations. The incident triggered scrutiny of Signal's security model and the discovery that Trump officials were using a compromised Signal clone.",
    2790: "Elon Musk's Department of Government Efficiency (DOGE) drew sustained attention as young, inexperienced engineers gained \"god mode\" access to government systems. Whistleblowers alleged sensitive data was taken from agencies like the NLRB.",
    78923: "Bill Atkinson, creator of MacPaint, HyperCard, and key member of the original Macintosh team, died in June 2025.",
    20763: "David Lynch, the visionary filmmaker behind Twin Peaks, Mulholland Drive, and Blue Velvet, died in January 2025.",
}

df["description"] = df["cluster_id"].map(descriptions)

df.to_csv("data/curated/2025_ai_curated_topics.csv", index=False)
print(f"Added descriptions to {len(df)} topics")
for _, row in df.iterrows():
    print(f"\n  {row['label']}:")
    print(f"    {row['description']}")
