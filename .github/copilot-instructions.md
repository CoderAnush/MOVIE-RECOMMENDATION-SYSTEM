## Purpose

These instructions give an AI coding agent the minimum, high-value context needed to be productive in this repository.
Be specific: where the system starts, important side-effects, data expectations, and fast ways to run and test features.

## Big-picture architecture (one-paragraph)

This is a hybrid movie recommendation system combining a Fuzzy Logic engine and an ANN-based predictor. Core runtime pieces are the FastAPI backend (`api.py`), ML engines in `models/` (e.g. `fuzzy_model.py`, `enhanced_ann_model.py`, `ann_model.py`, `hybrid_system.py`), a fast loader for the MovieLens 10M preprocessed data (`fast_complete_loader.py`), and a simple frontend under `frontend/` served with Python's http.server. `final_hybrid_demo.py` / `enhanced_recommendation_engine.py` implement higher-level combination strategies; `performance_optimizer.py` wraps caching/optimization used by the API.

## Quick start (developer-run)

- Install deps: `pip install -r requirements.txt` (use virtualenv/.venv).
- Run locally (recommended): `python run_local.py` — this starts the backend (api.py → uvicorn on 127.0.0.1:8080) and a frontend server on 3000 and opens the browser.
- Alternative backend run: `python -m uvicorn api:app --host 127.0.0.1 --port 8080 --reload` (api.py expects to run as a script or via uvicorn; default port inside api.py is 8080).
- Frontend manual: `cd frontend && python -m http.server 3000 --bind 127.0.0.1`.
- API docs: http://127.0.0.1:8080/docs

## Important files and what they do (quick map)

- `api.py` — FastAPI endpoints, startup initialization. Note: importing/running this will attempt to load the full database via `fast_complete_loader` (heavy). Avoid importing `api.py` in unit tests.
- `fast_complete_loader.py` — Loads the preprocessed MovieLens data (parquet preferred). Look here for poster mapping and generation fallbacks.
- `models/fuzzy_model.py` — Fuzzy rules and membership functions (47 rules). Primary business logic for fuzzy recommendations.
- `models/enhanced_ann_model.py`, `models/ann_model.py` — ANN model code (training and prediction hooks).
- `models/hybrid_system.py`, `final_hybrid_demo.py`, `enhanced_recommendation_engine.py` — Hybrid combination strategies and explanation utilities.
- `performance_optimizer.py` — Wraps hybrid system with caching, batch helpers, and performance stats used by `api.py`.
- `run_local.py` — Local developer convenience for starting backend + frontend; uses ports 8080 (backend) and 3000 (frontend).
- `processed/` — Expected place for `movies_enriched.parquet` and `dataset_summary.json`. `fast_complete_loader` uses these; missing files trigger fallback datasets.

## Project-specific conventions & gotchas

- Ports: backend defaults to 8080 (note README sometimes shows 8000/8000; trust `api.py` and `run_local.py` which use 8080). Frontend uses 3000.
- Heavy import side-effects: many modules (especially `api.py`) try to load `get_fast_complete_database()` at import time. To iterate quickly, import lower-level modules (e.g., `models.fuzzy_model`) rather than `api`.
- Genre / preference keys: user preference keys use snake_case fields (e.g., `sci_fi`) and 0–10 scale. Movie genres in datasets are mixed-case strings; code often lowercases/normalizes genres (see `fast_complete_loader.get_recommendation_explanation`).
- Recommendation score scales: fuzzy/ann outputs are normalized to 0–10. Hybrid combination strategies live in `hybrid_system.py` / `final_hybrid_demo.py`.
- Caching: `RecommendationCache` in `api.py` and `performance_optimizer.initialize_optimized_system(...)` configure cache size/ttl — change here for perf tuning.
- Data fallbacks: if `processed/movies_enriched.parquet` is missing, loader falls back to CSV or demo DBs (`real_movies_enhanced_demo`, `real_movies_db_omdb`). Expect different dataset sizes when fallbacks are used.

## Common developer workflows & commands

- Run tests (project has many test_*.py files): `python run_tests.py` (wrapper) or run a single test: `python test_enhanced_system.py`.
- Start only the API (without frontend): `python api.py` or `python -m uvicorn api:app --host 127.0.0.1 --port 8080 --reload`.
- Query example (PowerShell):

  $body = @{ user_preferences = @{ action = 9; comedy = 3; romance = 2; thriller = 8; sci_fi = 7; drama = 6; horror = 1 }; movie = @{ title = 'Mad Max: Fury Road'; year = 2015; genres = @('Action','Adventure'); popularity = 85 } } | ConvertTo-Json -Depth 3; Invoke-RestMethod -Uri "http://127.0.0.1:8080/recommend" -Method POST -Body $body -ContentType "application/json"

## Where to make targeted edits

- Add/modify fuzzy rules: `models/fuzzy_model.py` (rule definitions live here).
- Change ANN architecture or training: `models/ann_model.py` and `models/enhanced_ann_model.py`.
- Change loader expectations or poster mapping: `fast_complete_loader.py` (search `_get_poster_mapping`).
- Adjust API behavior (caching, TTL, endpoints): `api.py` (`RecommendationCache`, startup_event, endpoint models).

## Testing & debugging tips

- If the API is slow to start, check `fast_complete_loader` — it may be loading large preprocessed files. Use the demo DB modules under the repository root (`real_movies_enhanced_demo.py`) for lightweight testing.
- Avoid importing `api.py` inside tests; instead import `models.*` or `fast_complete_loader` helpers.
- Logs: `api.py` uses Python logging; set environment or modify logging.basicConfig level for more verbosity.

## Integration & external dependencies

- OMDB integration and poster fetching logic is present in `real_movies_db_omdb.py` and `complete_omdb_processor.py` — these expect API keys and cache files. Do not commit secrets.
- The system relies on preprocessed MovieLens outputs in `processed/` for best performance (`movies_enriched.parquet`, `dataset_summary.json`).

If anything above is unclear or you want me to expand examples (sample request bodies, tests to add, or precise quickfixes for a failing test), tell me which area to expand.
