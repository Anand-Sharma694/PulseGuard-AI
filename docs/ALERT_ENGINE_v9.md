# Alert Engine v9

## Changes
- Threshold alerts remain deterministic: BPM < 60 = LOW, BPM > 100 = HIGH.
- ML anomaly alerts require at least 8 readings and agreement between the classifier and anomaly detector.
- Normal readings no longer create notifications just because one ML model is noisy.
- Duplicate notifications of the same severity are suppressed for 12 seconds.
- Alert response now distinguishes `alert` (a notification was actually created) from `threshold_alert` (the reading crossed a threshold).
- UI labels a confirmed ML pattern separately from a simple threshold event.

## Demo
Use High · 110 or Low · 55 during monitoring. A notification should appear in Alerts and the unread badge should increment.

## Safety
This remains an educational software prototype using simulated readings and synthetic training data; it is not a medical diagnostic system.
