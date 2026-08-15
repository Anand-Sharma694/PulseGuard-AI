# PulseGuard AI — Final Architecture

## Pipeline
Browser UI → Flask API → validation → feature extraction → Random Forest classifier + Isolation Forest → conservative AI gate → threshold/risk engine → SQLite WAL persistence → Alert Center → History/Analytics → PDF/CSV export.

## Why the alert engine is conservative
- BPM below 60 or above 100 creates a demonstration threshold alert.
- AI unusual-pattern status requires enough history, a classifier unusual prediction, an anomaly-detector vote, and a meaningful pattern signal.
- The AI layer is intentionally separate from the threshold layer.
- Duplicate alerts from rapid UI polling are suppressed within a short window.

## Important scope
Current sensor inputs are simulated in the browser. The ML models are trained on synthetic educational data. This is a final-year CSE software prototype, not a clinical device.
