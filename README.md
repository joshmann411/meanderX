# MeanderX — Phase 1

Project foundation for ingesting Con Edison ArcGIS feeder/queue data.

See docs for data-source findings and decisions.

Run locally:

1. Copy `.env.example` to `.env` and edit values.
2. Start PostGIS and app with `docker-compose up --build`.
3. Start app directly via `uvicorn app.main:app --reload`.

Run tests:

```
pytest -q
```
# meanderX