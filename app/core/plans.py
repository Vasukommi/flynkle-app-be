"""Available subscription plans and limits."""

PLANS = {
    "free": {
        "price": 0,
        "daily_messages": 20,
        "daily_tokens": 5000,
        "max_conversations": 3,
        "max_file_uploads": 0,
    },
    "pro": {
        "price": 10,
        "daily_messages": 1000,
        "daily_tokens": 100000,
        "max_conversations": 100,
        "max_file_uploads": 100,
    },
}
