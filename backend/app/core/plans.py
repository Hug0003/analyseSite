
PLANS = {
    "starter": {
        "daily_scans": 5,
        "features": ["basic_scan"],
        "label": "Starter (Gratuit)",
        "history_days": 7,
        "monitor_limit": 1
    },
    "pro": {
        "daily_scans": 50,
        "features": ["basic_scan", "deep_scan", "pdf_export", "history", "ai_assistant"],
        "label": "Pro",
        "history_days": 30,
        "monitor_limit": 10
    },
    "agency": {
        "daily_scans": 9999,
        "features": ["basic_scan", "deep_scan", "pdf_export", "history", "ai_assistant", "whitelabel", "api_access", "lead_widget"],
        "label": "Agency",
        "history_days": 3650,
        "monitor_limit": 9999
    }
}
