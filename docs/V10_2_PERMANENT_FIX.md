# PulseGuard AI v10.2 — Stability Fix

This release fixes three concrete v10/v10.1 failures:

1. **SQLite lock storm**
   - `con()` no longer performs schema creation or commits on every request.
   - Database schema is initialized once at startup.
   - WAL mode + busy timeout are enabled once.
   - Writes use retry/backoff.

2. **Predict NameError**
   - The stored anomaly score is now explicitly assigned from the Isolation Forest decision function.
   - The response no longer references an undefined `created_alert`.

3. **Alert spam**
   - The rapid dashboard polling loop cannot create the same alert repeatedly within the short duplicate-suppression window.

The health endpoint now verifies both application and database availability.

## Clean demo procedure
Run only one Flask server for this project database. Stop old v10/v10.1 servers before launching v10.2.

The current AI model remains a demonstration model trained on synthetic data. Its metrics are not clinical validation.
