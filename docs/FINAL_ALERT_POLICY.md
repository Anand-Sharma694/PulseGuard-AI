# Final Alert Policy

PulseGuard AI uses a two-layer decision system:

1. Demonstration threshold: LOW below 60 BPM, HIGH above 100 BPM.
2. AI pattern analysis is advisory for in-range readings and requires:
   - at least 10 readings in the current history window,
   - Random Forest unusual classification,
   - Isolation Forest anomaly agreement, and
   - a strong current-window signal (standard deviation >= 15 BPM or absolute latest change >= 25 BPM, or extreme <50/>115 BPM).

A single normal-range reading such as 70, 75, 78 or 83 BPM does not create an alert.

Repeated alerts of the same severity are suppressed for 15 seconds to prevent dashboard polling from flooding the Alert Center.

This is an educational prototype using simulated/synthetic data and is not a medical diagnostic device.
