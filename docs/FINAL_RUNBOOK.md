# Final Runbook

## Fastest Windows start
Double-click `START_PULSEGUARD.bat`.

## Manual start
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python ai\train_models.py
python backend\app.py
```
Open `http://127.0.0.1:5000`.

Demo account: `demo` / `pulse123`.

Health check: `http://127.0.0.1:5000/api/health`.

## Demo sequence
1. Register or log in.
2. Start Monitoring.
3. Use Normal, High 110 and Low 55 demo controls.
4. Open Alerts and mark events read.
5. Open Live Command Center.
6. Open History.
7. Open Insights & Reports.
8. Download CSV and PDF.
9. End session.

## If a previous server is running
Stop it with Ctrl+C before starting another copy. Only one local demo server should use the project database at a time.
