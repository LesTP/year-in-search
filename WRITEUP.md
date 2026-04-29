# Year in Tech: Discovering What Mattered from Community Attention Data

*A data pipeline that turns a year of Hacker News activity into a ridge-plot visualization of the topics that captured outsized attention in tech.*

---

## 1. Introduction

The starting point for this project was a ridge plot chart — the kind produced by Google's "Year in Search" — saved on a phone since 2022. Those charts are compelling: each row is a topic, each curve shows when and how intensely the public paid attention, and together they tell the story of a year. The idea was simple: recreate this for the tech world, using data rather than editorial curation to decide what topics earned a slot.

Google's original charts are editorially curated — someone picks the keywords, pulls Trends data, and plots the curves. The visualization half is straightforward. The hard half is *topic discovery*: figuring out what to plot in the first place. This project tackles both, building a seven-stage pipeline that starts from raw community data and ends with a finished ridge plot — with minimal manual intervention.

The result for 2024 captures 20 topics spanning the year: the Boeing 737 MAX crisis in January, the xz supply chain backdoor in March, the CrowdStrike outage in July, and sustained year-round discussion of LLMs, Rust, and PostgreSQL, among others.

---

## 2. Data Sourcing Challenges

### The Google Trends dead end

The natural first instinct was to use Google Trends as the data source — it's the closest analog to the original "Year in Search" charts. Early research revealed three problems:

1. **No corpus access.** Google Trends does not expose the full universe of search queries. You can only fetch time series for queries you already know. This makes automated topic discovery impossible through Trends alone — you need a candidate list first.

2. **Normalization fragility.** Trends returns relative indices (0–100) normalized per request. Comparing across queries requires anchor-keyword workarounds or overlapping batch stitching. For a prototype, this adds complexity without adding signal.

3. **Limited API access.** The official Google Trends API is still in alpha with restricted access. The main alternative, `pytrends`, is an unofficial scraper that breaks when Google changes internal endpoints and is subject to rate limiting and bot detection.

The fundamental issue: Google Trends is a *measurement* tool, not a *discovery* tool. It answers "how much attention did X get?" but not "what should X be?"

### The Hacker News dataset

The breakthrough was finding the `open-index/hacker-news` dataset on HuggingFace — a comprehensive archive of HN posts with titles, scores, comment counts, and timestamps. HN turned out to be an ideal source for tech topic discovery:

- **Community-driven editorial signal.** HN's upvoting and commenting already surfaces what the tech community finds noteworthy. The collective judgment is baked into the data — no external curation needed.
- **Topic coherence.** Tech-focused community means less noise from entertainment, sports, and politics. The signal-to-noise ratio for tech topics is high.
- **Temporal coverage.** Full historical data allows both single-year analysis and cross-year baseline comparisons.
- **Scale.** Roughly 87,000 filtered stories per year — enough for statistical clustering, small enough to process on a laptop CPU.

This reframed the problem from "find the right search terms" to "discover topics from community attention data" — a clustering problem rather than a keyword-selection problem.

---

## 3. The Processing Pipeline

The pipeline has seven stages, each a standalone CLI module that reads the previous stage's output from disk. No orchestration layer — each phase is run manually in sequence.

### Stage 1: Ingest

Downloads monthly parquet files from HuggingFace for the target year, filters to stories with score >= 5, and computes an attention score:

```
attention = score + 0.5 × num_comments
```

The comment weight (0.5) balances upvotes (broad approval) with discussion (depth of engagement). A post with 200 upvotes and 100 comments scores 250.

**Data quality note:** The initial attempt used `datasets.load_dataset()`, which crashed with an `IndexError` after downloading all 235 data files (42 minutes wasted). Root cause: a shard-builder bug in the `datasets` library on this multi-file parquet dataset. The fix was switching to `huggingface_hub.hf_hub_download()` to fetch per-month files directly — downloading only the target year's ~200MB instead of the full 2–4GB dataset.

For 2024: 3.7M raw rows → 86,982 stories after filtering.

### Stage 2: Embed

Encodes post titles into 384-dimensional vectors using `all-MiniLM-L6-v2`, a sentence transformer that runs on CPU. The model captures semantic similarity — "CrowdStrike outage causes global IT disruption" and "Millions of Windows machines crash after faulty update" end up near each other in embedding space even though they share few words.

~5 minutes on CPU for ~87K titles.

### Stage 3: Cluster

UMAP reduces the 384-dimensional embeddings to 50 dimensions, then HDBSCAN groups semantically similar titles into topic clusters. This is fully unsupervised — no predefined categories, no keyword lists, no training data. The algorithm discovers topics from the structure of the embedding space.

For 2024: 3,356 clusters from 86,982 posts, with 38% classified as noise (not belonging to any cluster). The noise rate is expected for HDBSCAN and actually desirable — many HN posts are one-off stories that shouldn't form topics.

Cluster quality was validated manually: top clusters are immediately recognizable (CrowdStrike outage, xz backdoor, ChatGPT, Apple vs EU, Rust ecosystem, LLMs). Mid-sized clusters are mostly coherent with occasional loose groupings.

### Stage 4: Score & Classify

For each cluster, computes a 53-point weekly attention curve (ISO weeks 1–53) and derives five metrics:

| Metric | What it measures |
|--------|-----------------|
| `total_attention` | Overall magnitude across the year |
| `peak_attention` | Height of the tallest week |
| `peak_week` | When the peak occurred |
| `duration_weeks` | Weeks with attention > 20% of peak |
| `spike_ratio` | Peak ÷ mean attention (spikiness) |

Topics are then classified:
- **Spike** — sharp, short-lived events (spike_ratio > 4, duration ≤ 3 weeks). E.g., CrowdStrike outage (spike_ratio = 29.95), xz backdoor (31.93).
- **Sustained** — persistent year-round discussion (duration > 8 weeks). E.g., Rust ecosystem (28 weeks), LLMs (24 weeks).
- **Moderate** — everything in between.

The classification is key because spike and sustained topics are fundamentally different phenomena — a spike is a news event, sustained attention is an ongoing community concern. They require different visual treatment and different selection criteria.

### Stage 5: Label

Auto-labels each cluster with the title of its highest-attention post, cleaned of HN-specific prefixes ("Show HN:", "Ask HN:", etc.). LLM-assisted labeling was designed but deferred — auto-labels from the top title are good enough for the prototype, and the curation step handles manual relabeling.

### Stage 6: Curate

Exports the top 50 topics by total attention as a CSV for human review. The curator scans the list, merges overlapping topics, shortens labels, and selects 15–25 for the final visualization.

An AI curation pass was also performed as a comparison: the model selected 20 topics, shortened labels, and provided selection rationale. The human reviewer then adjusts — for example, replacing a generic "Notable Deaths" catch-all cluster with the two specific individuals (Vernor Vinge, Daniel Kahneman) by extracting per-person time series from the original cluster.

### Stage 7: Visualize

Renders a ridge plot where each row is a topic's weekly attention curve, ordered chronologically by peak week (January at top, December at bottom). Topics are colored with a cool-to-warm gradient — blue for January peaks, red for December. Gaussian smoothing (σ=1.0) removes weekly jitter while preserving spike character.

Multiple smoothing levels were tested (σ = 0.8, 1.0, 1.2, 1.5, 2.5). σ=1.0 was selected as the best balance between spike clarity and visual smoothness. Row spacing was tuned from 0.65 overlap down to 0.15 for clear separation.

---

## 4. Development Workflow: Structuring AI-Assisted Work

### The problem with long sessions

AI-assisted development has a session continuity problem. A coding agent accumulates context over a conversation — what's been tried, what failed, why a particular approach was chosen — but that context lives only in the chat history. If the session ends (context window fills up, the tool crashes, the human steps away), all of that accumulated understanding is lost. The next session starts from zero, and the human spends the first 15 minutes re-explaining what the project is, what's been done, and what to do next.

This gets worse as projects grow. A simple script needs no continuity. A multi-phase pipeline with design decisions, data quirks, and iterative tuning needs a lot. The question is: where should that continuity live?

### Documents as the persistent brain

The approach used here treats **documents as the project's persistent memory**, not the AI's context window. A small set of structured files captures everything the agent needs to orient itself on a cold start:

- **A project definition** — what this is, what it isn't, who it's for, what "done" looks like. Written once during project scoping. Prevents the agent from drifting into scope that was explicitly excluded.

- **An architecture map** — components, data flow, dependencies, implementation sequence. The agent reads this to understand how the pieces fit together and what to work on next.

- **A development plan** — current status, active phase, known gotchas. This is the key document for cold starts: the agent reads it and knows exactly where work left off, what's blocked, and what traps to avoid. It's updated after every step, so it's always current.

- **A development log** — what was done, what happened, what broke, what was learned. Not for the agent to read routinely, but invaluable when debugging ("why did we switch from `datasets.load_dataset()` to monthly file downloads?") or when reviewing what a phase actually produced.

- **A decision log** — design forks and their rationale. When the project chose auto-labeling over LLM labeling, or 53 ISO week bins over 52, the reasoning was recorded with alternatives considered. This prevents re-litigating settled decisions in future sessions.

The principle: **the intelligence lives in the documents, not in the agent.** The agent is stateless — it reconstructs everything it needs from files every time. This makes sessions interruptible at any point without losing progress, and makes it trivial to resume after a break of hours or days.

### Phase-based progression

Work is organized into phases with explicit lifecycle stages: plan the phase, execute steps within it, review the output, then close and clean up. Each phase has a clear scope and a defined "done" state.

This structure serves two purposes. First, it creates natural checkpoints. At the end of a phase, the development plan gets updated, completed work gets summarized to a single line, and the next phase's scope gets defined. The plan never grows unboundedly — it stays compact because finished work is compressed.

Second, it forces a plan-before-code discipline. Even when the next step seems obvious, explicitly stating what will be done before doing it produces better outcomes. The agent makes fewer mistakes when it's thought about the step before starting to code — and the human can course-correct before work begins rather than after.

### Work regime classification

Not all work is the same, and recognizing this upfront prevents wasted effort. Work falls into three regimes:

- **Build** — correctness is verifiable by objective criteria (tests pass, output matches spec, code compiles). The agent can evaluate its own work.
- **Refine** — correctness requires human judgment (visual design, naming, UX feel). The agent can't tell if it's right without showing someone.
- **Explore** — the goal is to make a decision, not produce code (technology selection, architecture alternatives). Work should stop for a human decision.

The classification is simple but surprisingly useful. Most wasted AI-assisted development time comes from the agent grinding on Refine or Explore work in Build mode — endlessly tweaking a visualization that only a human can evaluate, or making an architectural choice that should have been a discussion. Identifying the regime upfront and handling each differently avoids this.

### Why this matters even for small projects

This project — a single-module pipeline built in a day — is small enough that the overhead of structured documents might seem unnecessary. In practice, the governance framework was adopted mid-project and backfilled with existing history. Even at this scale, three things were immediately useful:

1. **Cold-start resilience.** The development plan with its gotchas section (the HuggingFace `datasets` library crash, the 132 empty-title posts, the ISO week 53 edge case) meant that no session had to rediscover these problems.

2. **Decision archaeology.** Six decisions were logged during the project. Weeks later, when considering changes or extensions, the rationale is right there — not buried in a chat transcript that may no longer exist.

3. **Transferability.** Anyone (human or AI) picking up this project can read four files and have complete context. No onboarding conversation needed.

The framework scales down gracefully. A small project needs a 16-line instruction file and a compact plan. A large project needs the same structure with more detail. The overhead is proportional to the project's complexity, not fixed.

---

## 5. Outcomes and Learnings

### What worked

**Unsupervised topic discovery is viable.** The embedding + clustering approach produces recognizable, coherent topics without any predefined categories or keyword lists. The top 20 topics for 2024 are immediately identifiable to anyone who follows tech news — no human had to tell the pipeline what to look for.

**Community attention is a strong editorial signal.** HN's collective upvoting and commenting approximates editorial judgment surprisingly well. The spike/sustained classification automatically separates news events from ongoing themes. The pipeline correctly identifies both the CrowdStrike outage (sharp spike, week 29) and the Rust ecosystem (broad sustained attention, 28 weeks) as significant — for entirely different reasons.

**Serial-via-disk architecture is robust.** Each phase reads files from the previous phase and writes files to disk. No in-memory coupling, no shared state. Any phase can be re-run independently. If clustering parameters change, you re-run stages 3–7 without touching ingestion or embedding. This made iterative tuning straightforward.

**The governance framework added value even for a small project.** The project adopted a structured governance approach (DEVPLAN, DEVLOG, DECISIONS.md) mid-stream. Even for a single-day pipeline project, having a DEVPLAN with cold-start context and a decision log with rationale for choices like "53-bin time series" and "auto-label first, defer LLM labeling" made session resumption and retrospective review much faster.

### Limitations

**HN bias is real.** Hacker News skews toward startups, open source, systems programming, and Silicon Valley. Topics like enterprise software, mobile development, or non-English tech communities are underrepresented. This is acknowledged — it's a tech-community-specific view, not a universal one.

**38% noise rate means lost signal.** Over a third of posts don't cluster. Some of these are genuinely one-off stories, but others might be smaller topics that fall below HDBSCAN's `min_cluster_size` threshold. Lowering the threshold produces more clusters but at the cost of coherence.

**No cross-year baseline filtering.** Perennial topics (Python, JavaScript, React) appear every year. Without a multi-year baseline, there's no automated way to distinguish "Python was big in 2024" from "Python is always big." The spike_ratio metric partially addresses this for spiky events, but sustained perennials still surface.

**Curation is still partially manual.** The pipeline automates discovery and scoring, but the final topic selection requires human judgment — merging overlapping clusters, choosing which sustained topics are interesting vs. perennial, adjusting labels for the chart. This is by design (the "hybrid" approach), but it means the pipeline isn't fully push-button.

---

## 6. Future Directions

### 2025 on Hacker News

The immediate next step: run the same pipeline on 2025 data. This is straightforward — the pipeline is parameterized by year. The 2025 results are more interesting to a general audience because they're more recent.

### Reddit as a second source

Running the pipeline independently on Reddit tech subreddits (`r/programming`, `r/technology`) and comparing with HN results would answer a genuinely interesting question: how much do these communities agree on what matters? Where do their attention curves diverge? Reddit has a different demographic and moderation culture — the delta between HN and Reddit topic rankings would itself be informative.

The pipeline is designed for this: the post schema includes a `source` field, attention scoring uses source-specific z-score normalization, and each phase reads from disk with no source-specific logic hardcoded.

### Multi-year anomaly scoring

With two or more years of data, cross-year baseline filtering becomes possible. A topic's "year-specific-ness" would be:

```
z = (mean_attention_year_Y − baseline_mean) / baseline_std
```

This would automatically demote perennials (Python, React, JavaScript) and surface topics that are genuinely new in the target year. The scoring infrastructure already supports this — it just needs the baseline data.

### Job postings ("Year in Hiring")

A more ambitious extension: apply the same pipeline to job posting data. The attention signal becomes posting volume rather than upvotes, and the topics are technologies, roles, and industries rather than news events. This would produce directly useful intelligence — "what skills saw hiring spikes in 2024?" — but the data source question is harder. Public job board APIs are more fragmented than HN's clean HuggingFace dataset, and the signal-to-noise ratio is lower (many duplicate postings, recruiter spam, geographic variation).

---

## 7. Conclusion

The project started as "I want to recreate that ridge plot chart" and evolved into a signal-extraction problem. The key insight was that topic discovery — not visualization — is the hard part, and that community attention data from Hacker News provides a surprisingly clean signal for automated topic discovery via embedding and clustering.

The result is a seven-stage pipeline that takes raw HN data and produces a finished "Year in Tech" ridge plot with minimal manual intervention. The 2024 output captures 20 topics that align well with what a tech-literate reader would remember from the year — from the xz backdoor to the CrowdStrike outage to the ongoing rise of LLMs.

The framework is extensible: same pipeline, different data source, different year, different questions. The next step is 2025 data and a Reddit comparison — testing whether the approach generalizes beyond a single community's attention signal.
