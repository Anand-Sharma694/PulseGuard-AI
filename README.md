# ❤️ PulseGuard AI

AI-powered heart-rate monitoring and anomaly detection system.

## 🚀 Live Demo

**[Open PulseGuard AI Live Demo](https://pulseguard-ai-j3rg.onrender.com)**

> The live demo uses simulated heart-rate data. Physical heartbeat hardware is not required for the software demonstration.

## 📂 GitHub Repository

**[View Source Code](https://github.com/Anand-Sharma694/PulseGuard-AI)**

A final-year CSE educational AI health-monitoring prototype with authentication, real-time simulated heart-rate monitoring, conservative AI pattern analysis, threshold alerts, notification center, live command center, history, analytics, CSV export and PDF reporting.

**Demo data:** simulated readings and synthetic ML training data. This is not a medical diagnostic device.

## Quick start
1. Open this folder in VS Code.
2. Run `START_PULSEGUARD.bat`, or use the commands in `docs/FINAL_RUNBOOK.md`.
3. Open `http://127.0.0.1:5000`.
4. Demo account: `demo` / `pulse123`.

## Final alert behavior
- <60 BPM: LOW demonstration alert
- >100 BPM: HIGH demonstration alert
- 60–100 BPM: normal unless a persistent/strong AI pattern is detected
- duplicate same-severity alerts suppressed for 15 seconds
# PulseGuard AI — Ultimate v5

A polished, laptop-runnable AI health-monitoring software prototype.

## Start

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python ai/train_models.py
python backend/app.py
```

Open `http://127.0.0.1:5000`.

## First-time experience
The public landing page explains the project before login. A visitor can:
- read what PulseGuard does,
- understand the AI in plain language,
- see who the product is for,
- create a local account,
- or use the built-in demo account.

### Demo account
Username: `demo`
Password: `pulse123`

## Main product areas
- Personalized dashboard
- Session-based monitoring
- Random Forest + Isolation Forest
- Explainable AI
- Risk score
- AI confidence
- Trend visualization
- Personal history
- CSV export
- Notification center with unread/read state
- Personal analytics dashboard and event timeline
- Downloadable PDF monitoring report
- Optional browser notifications for abnormal demo events
- AI explanation page
- System architecture page
- SQLite persistence
- Automated API tests
- Hardware-ready acquisition boundary

## Important limitation
The current sensor input is simulated because the project is designed to run without hardware. The ML dataset is synthetic and educational. The project does not diagnose disease and is not a medical device.

## Future hardware path
ESP32 + MAX30102 -> API gateway -> same feature engine -> same AI -> same database/dashboard. A Blynk/cloud notification layer can be added after hardware integration and validation.


## v10.2 stability
Database initialization, SQLite locking, prediction score persistence, and duplicate alert generation have been hardened.

- Live Command Center with real-time trend and event stream
