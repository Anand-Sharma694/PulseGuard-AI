# Analytics & Reports — v7

PulseGuard v7 adds a reporting layer on top of the existing monitoring and AI pipeline.

## Analytics
The system calculates:
- total stored readings
- average/minimum/maximum BPM
- threshold-abnormal event count
- AI unusual-pattern event count
- average demonstration risk
- average classifier confidence
- a simple software stability indicator
- recent activity timeline

## PDF
The signed-in user can download a PDF summary containing:
- account name/username
- monitoring statistics
- recent events
- responsible-use limitation

The PDF is an educational software report. It must not be presented as a medical report.

## Why this matters
The project now demonstrates an end-to-end product loop:

Input → feature engineering → ML → decision → explanation → notification → persistence → analytics → report.
