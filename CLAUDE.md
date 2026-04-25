# Year-in-Search

Ridge-plot pipeline: HN data → topic discovery → attention scoring → visualization.

## Docs
- `README.md` — methodology, results, setup
- `DEVPLAN.md` — current status, gotchas, pending work (start here for cold starts)
- `ARCHITECTURE.md` — component map, data flow, contracts
- `DESIGN.md` — full spec including LLM labeling workflow
- `DECISIONS.md` — D-1 through D-6
- `DEVLOG.md` — phase history

## Notes
- Run phases from project root: `python -m src.<phase> --year 2024`
- `toolkit.embedding` and `toolkit.clustering` are editable-installed from `../toolkit`
- All config in `src/config.py`
