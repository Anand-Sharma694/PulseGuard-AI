# Alert Center v8

Fixed the alert UI pipeline. The backend already persisted abnormal events into the notifications table; v8 adds the missing frontend `loadAlerts()` implementation and wires it to the Alerts navigation, bell, polling, and prediction responses.

Browser notifications are requested when supported. In-app alerts remain the reliable mechanism.

Demo: login → Dashboard → Start monitoring → High 110 / Low 55 → open Alerts.
