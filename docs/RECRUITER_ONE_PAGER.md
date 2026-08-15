# PulseGuard AI — Project One-Pager

## One-line pitch
A full-stack AI system that converts continuous heart-rate patterns into understandable monitoring insights using machine learning, anomaly detection, explainable alerts and persistent user history.

## Engineering surface
Frontend: HTML/CSS/JavaScript
Backend: Python/Flask REST API
AI: scikit-learn Random Forest + Isolation Forest
Data: Pandas/NumPy + SQLite
Testing: Pytest
Export: CSV
Authentication: Local password hashing + session login
Architecture: Hardware-agnostic acquisition boundary

## Why it is interesting
The project is not only a UI. It contains a complete path from input -> features -> AI -> decision -> explanation -> persistence -> user experience.

## Current limitation
Laptop simulator + synthetic dataset. This is an educational prototype, not a clinically validated system.

## Future
ESP32/MAX30102, Blynk/cloud notifications, real datasets, security hardening, privacy controls and formal validation.
