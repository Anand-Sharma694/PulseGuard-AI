# PulseGuard AI — Recruiter-Ready Final-Year CSE Project

## Problem
Continuous heart-rate data is difficult to interpret when users only see raw numbers. This prototype combines rule-based thresholds, supervised machine learning, anomaly detection, risk scoring, persistence and explainable alerts in one system.

## Engineering highlights
- Full-stack web application
- REST API
- ML training pipeline
- Two-model AI ensemble
- Feature engineering
- Risk scoring
- Explainable AI output
- SQLite persistence
- Session lifecycle
- CSV export
- Automated backend tests
- Hardware integration boundary
- Responsive UI
- Responsible-AI limitation statement

## Current execution mode
Laptop-only simulator. This is intentional because no physical sensor is required to demonstrate the software architecture.

## Hardware-ready design
A future ESP32 + MAX30102 acquisition layer can send BPM windows to the backend. The AI, database and dashboard do not need to be redesigned.

## Recruiter talking points
1. I separated data acquisition from analytics.
2. I used both supervised classification and unsupervised anomaly detection.
3. I added explainability instead of exposing only a black-box label.
4. I persisted readings and implemented session management.
5. I added API tests and an export endpoint.
6. I explicitly distinguish synthetic-data performance from clinical validation.
