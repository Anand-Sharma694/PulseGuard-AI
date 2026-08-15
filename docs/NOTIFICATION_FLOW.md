# Notification Flow

PulseGuard v6 adds a local notification center.

1. Monitoring produces a BPM reading.
2. The feature engine builds the current window.
3. Random Forest + Isolation Forest produce AI signals.
4. Threshold rules and AI output produce a demonstration risk score.
5. If the result is abnormal, a notification event is stored for the signed-in user.
6. The Alerts page shows the event and supports marking it as read.
7. The browser may also request permission to show a local desktop/browser notification.

This is intentionally local and hardware-free. A future production/cloud version can replace the notification event layer with an approved push/notification provider or Blynk integration after security and validation work.
