# Year-in-Search — Decision Log

D-1: Monthly file download instead of full dataset
Date: 2026-04-25 | Status: Closed
Priority: Critical
Decision: Use `huggingface_hub.hf_hub_download()` to fetch per-month parquet files instead of `datasets.load_dataset()` for the full 47M-row dataset.
Rationale: The `datasets` library's shard builder crashes on this dataset (`IndexError` in `_prepare_split_single`). Monthly files download only the target year's data (~200MB vs 2-4GB). Also faster — no need to process 47M rows to extract one year.
Revisit if: The `datasets` library fixes the shard processing bug, or if the HF dataset layout changes.

D-2: Structured ingest error reporting
Date: 2026-04-25 | Status: Closed
Priority: Important
Decision: Ingest produces a JSON `IngestReport` alongside the data, separating expected skips (`EntryNotFoundError` for partial years) from unexpected errors. Report is machine-readable for model review.
Rationale: Pipeline is run manually but errors should be reviewable by a model, not just scanned visually in console output. Broad `except Exception` was silently swallowing network failures, disk errors, and corrupt parquets.
Revisit if: Pipeline becomes automated and needs a different error routing mechanism (e.g., webhook, alert).

D-3: No ARCH_[module].md files
Date: 2026-04-25 | Status: Closed
Priority: Nice-to-have
Decision: Single-module project — all phases live in one `src/` package. No per-module ARCH files.
Rationale: Seven phases but one linear pipeline. No internal module boundaries, no cross-module integration concerns. Each phase reads files from disk — no in-memory coupling.
Revisit if: Reddit multi-source extension or interactive visualization adds enough complexity to warrant separate modules.
