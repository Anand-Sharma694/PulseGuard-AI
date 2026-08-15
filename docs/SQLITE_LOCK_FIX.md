# v10 — SQLite reliability fix

The v9 log showed repeated `sqlite3.OperationalError: database is locked`
errors while `/api/predict` inserted readings. The report itself showed the
normal path working, but rapid monitoring writes could collide.

v10 adds:
- SQLite WAL mode
- 10-second busy timeout
- retry/backoff for transient write locks
- short-lived write connections
- retry-safe notification writes
- `/api/health` database health endpoint

**Demo rule:** stop every old Flask/Python server before starting v10 and
run only one v10 server for the project demo.
