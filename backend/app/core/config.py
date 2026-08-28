"""
Core configuration — reads settings from environment variables.
"""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Application settings populated from environment variables."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://heatwave:heatwave@db:5432/heatwave_ews",
    )

    # Twilio (optional — dry-run mode when absent)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER: str = os.getenv("TWILIO_FROM_NUMBER", "")

    # Scheduler
    WEATHER_FETCH_INTERVAL_HOURS: int = int(
        os.getenv("WEATHER_FETCH_INTERVAL_HOURS", "3")
    )


settings = Settings()
