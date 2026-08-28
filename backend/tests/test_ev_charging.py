"""
Tests for EV Thermal Runaway Prevention API.

Includes:
  1. Unit tests for the derating helper ``_get_charge_rate_multiplier``
  2. Unit tests for ``_extract_temperatures``
  3. Integration tests for ``GET /api/ev-safety/{ward_id}`` via TestClient
  4. A mock "charging station" polling demo

Run with:
    pytest tests/test_ev_charging.py -v
"""

import time
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.ev_safety import (
    _get_charge_rate_multiplier,
    _extract_temperatures,
    CHARGING_DERATING_POLICY,
    DEFAULT_MULTIPLIER,
    DEFAULT_REASON,
    router,
)
from app.main import app

client = TestClient(app)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Helper: build a fake risk-store entry
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _make_ward_data(
    ambient_temp: float,
    forecast_temps: list[float] | None = None,
) -> dict:
    """Build a minimal risk-store entry for testing."""
    forecast = []
    if forecast_temps:
        for i, t in enumerate(forecast_temps):
            forecast.append({"date": f"2026-05-{15 + i:02d}", "temp_c": t})

    return {
        "current": {
            "ward_id": 1,
            "ward_name": "Test Ward",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temp_c": ambient_temp,
            "rh_pct": 50.0,
            "wind_ms": 2.0,
            "solar_wm2": 500.0,
            "heat_index": 40.0,
            "wbgt": 30.0,
            "utci": 35.0,
            "vulnerability_score": 0.5,
            "mri_score": 0.6,
            "risk_band": "Orange",
            "breakdown": {},
        },
        "forecast": forecast,
        "ward": {
            "id": 1,
            "name": "Test Ward",
            "centroid_lat": 21.0,
            "centroid_lon": 79.0,
        },
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  1. Unit tests — _get_charge_rate_multiplier
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestGetChargeRateMultiplier:
    """Verify every tier of the derating policy."""

    def test_normal_below_35(self):
        """< 35 °C → full rate (1.0)."""
        mult, reason = _get_charge_rate_multiplier(30.0)
        assert mult == 1.0
        assert reason == DEFAULT_REASON

    def test_normal_at_boundary_34_9(self):
        """34.9 °C → still normal."""
        mult, _ = _get_charge_rate_multiplier(34.9)
        assert mult == 1.0

    def test_mild_caution_35(self):
        """35 °C → mild caution (0.85)."""
        mult, reason = _get_charge_rate_multiplier(35.0)
        assert mult == 0.85
        assert "Mild" in reason

    def test_mild_caution_39(self):
        """39 °C → still mild caution."""
        mult, _ = _get_charge_rate_multiplier(39.0)
        assert mult == 0.85

    def test_moderate_40(self):
        """40 °C → moderate (0.70)."""
        mult, reason = _get_charge_rate_multiplier(40.0)
        assert mult == 0.70
        assert "Moderate" in reason

    def test_moderate_41_9(self):
        """41.9 °C → still moderate."""
        mult, _ = _get_charge_rate_multiplier(41.9)
        assert mult == 0.70

    def test_severe_42(self):
        """42 °C → severe (0.50)."""
        mult, reason = _get_charge_rate_multiplier(42.0)
        assert mult == 0.50
        assert "Severe" in reason

    def test_severe_44_9(self):
        """44.9 °C → still severe."""
        mult, _ = _get_charge_rate_multiplier(44.9)
        assert mult == 0.50

    def test_extreme_45(self):
        """45 °C → extreme (0.30)."""
        mult, reason = _get_charge_rate_multiplier(45.0)
        assert mult == 0.30
        assert "Extreme" in reason

    def test_extreme_50(self):
        """50 °C → extreme."""
        mult, _ = _get_charge_rate_multiplier(50.0)
        assert mult == 0.30

    def test_freezing_temperature(self):
        """Negative temps → normal (1.0)."""
        mult, _ = _get_charge_rate_multiplier(-5.0)
        assert mult == 1.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  2. Unit tests — _extract_temperatures
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestExtractTemperatures:
    """Validate temperature extraction from risk-store data."""

    def test_with_forecast(self):
        """Forecast peak should be the max of forecast temps."""
        data = _make_ward_data(38.0, [39.0, 44.0, 41.0])
        ambient, peak = _extract_temperatures(data)
        assert ambient == 38.0
        assert peak == 44.0

    def test_without_forecast(self):
        """When no forecast exists, peak should fall back to ambient."""
        data = _make_ward_data(36.0, [])
        ambient, peak = _extract_temperatures(data)
        assert ambient == 36.0
        assert peak == 36.0

    def test_forecast_none(self):
        """Missing forecast key handled gracefully."""
        data = _make_ward_data(40.0)
        # Remove forecast entirely
        del data["forecast"]
        ambient, peak = _extract_temperatures(data)
        assert ambient == 40.0
        assert peak == 40.0

    def test_ambient_higher_than_forecast(self):
        """If ambient is higher than all forecast temps."""
        data = _make_ward_data(46.0, [42.0, 41.0])
        ambient, peak = _extract_temperatures(data)
        assert ambient == 46.0
        assert peak == 42.0  # peak is just max of forecast


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  3. Integration tests — GET /api/ev-safety/{ward_id}
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestEvSafetyEndpoint:
    """Test the FastAPI endpoint via TestClient."""

    def _patch_store(self, store_data: dict):
        """Return a context-manager that patches get_risk_store."""
        return patch(
            "app.api.ev_safety.get_risk_store",
            return_value=store_data,
        )

    def test_normal_conditions(self):
        """Ambient 30 °C, forecast peak 33 °C → multiplier 1.0."""
        data = _make_ward_data(30.0, [31.0, 33.0, 32.0])
        with self._patch_store({1: data}):
            resp = client.get("/api/ev-safety/1")

        assert resp.status_code == 200
        body = resp.json()
        assert body["ward_id"] == 1
        assert body["recommended_charge_rate_multiplier"] == 1.0
        assert body["ambient_temp_c"] == 30.0
        assert body["forecast_peak_temp_c"] == 33.0
        assert "timestamp" in body
        assert "reason" in body

    def test_severe_heat(self):
        """Ambient 38 °C but forecast peaks at 43 °C → 0.50 (severe)."""
        data = _make_ward_data(38.0, [40.0, 43.0, 41.0])
        with self._patch_store({1: data}):
            resp = client.get("/api/ev-safety/1")

        assert resp.status_code == 200
        body = resp.json()
        assert body["recommended_charge_rate_multiplier"] == 0.50

    def test_extreme_heat(self):
        """Ambient 46 °C → extreme (0.30)."""
        data = _make_ward_data(46.0, [44.0, 43.0])
        with self._patch_store({1: data}):
            resp = client.get("/api/ev-safety/1")

        assert resp.status_code == 200
        body = resp.json()
        assert body["recommended_charge_rate_multiplier"] == 0.30

    def test_mild_caution(self):
        """Ambient 37 °C, forecast peak 38 °C → 0.85."""
        data = _make_ward_data(37.0, [36.0, 38.0])
        with self._patch_store({1: data}):
            resp = client.get("/api/ev-safety/1")

        assert resp.status_code == 200
        body = resp.json()
        assert body["recommended_charge_rate_multiplier"] == 0.85

    def test_moderate_heat(self):
        """Forecast peaks at 41 °C → 0.70."""
        data = _make_ward_data(34.0, [39.0, 41.0])
        with self._patch_store({1: data}):
            resp = client.get("/api/ev-safety/1")

        assert resp.status_code == 200
        body = resp.json()
        assert body["recommended_charge_rate_multiplier"] == 0.70

    def test_ward_not_found(self):
        """Non-existent ward_id → 404."""
        resp = client.get("/api/ev-safety/9999")
        assert resp.status_code == 404

    def test_no_weather_data(self):
        """Ward exists but no ingestion yet → 503."""
        with self._patch_store({}):
            resp = client.get("/api/ev-safety/1")

        assert resp.status_code == 503

    def test_response_schema_keys(self):
        """Verify all expected keys are present in the response payload."""
        data = _make_ward_data(35.5, [36.0])
        with self._patch_store({1: data}):
            resp = client.get("/api/ev-safety/1")

        expected_keys = {
            "ward_id",
            "timestamp",
            "ambient_temp_c",
            "forecast_peak_temp_c",
            "recommended_charge_rate_multiplier",
            "reason",
        }
        assert set(resp.json().keys()) == expected_keys


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  4. Mock "charging station" polling demo
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Maximum supported charge rate for the simulated station (kW)
STATION_MAX_CHARGE_KW = 150.0


def _simulate_charging_decision(advisory: dict) -> dict:
    """
    Simulate what a real charging station controller would do
    upon receiving an advisory payload.

    Parameters
    ----------
    advisory : dict
        The JSON body returned by GET /api/ev-safety/{ward_id}.

    Returns
    -------
    dict
        Simulated station action.
    """
    multiplier = advisory["recommended_charge_rate_multiplier"]
    effective_kw = round(STATION_MAX_CHARGE_KW * multiplier, 1)
    return {
        "station_id": "CS-DEMO-001",
        "ward_id": advisory["ward_id"],
        "max_charge_kw": STATION_MAX_CHARGE_KW,
        "effective_charge_kw": effective_kw,
        "multiplier_applied": multiplier,
        "reason": advisory["reason"],
    }


class TestMockChargingStation:
    """
    Simulates a charging station that polls the EV-safety endpoint and
    adjusts its charging rate.  This is a *demo* — in production the
    station firmware would call the API over HTTPS.
    """

    POLL_SCENARIOS: list[tuple[float, list[float], float]] = [
        # (ambient, forecast_temps, expected_multiplier)
        (30.0, [32.0, 33.0], 1.0),
        (37.0, [38.0, 39.0], 0.85),
        (39.0, [41.0, 40.0], 0.70),
        (40.0, [43.0, 42.0], 0.50),
        (44.0, [47.0, 46.0], 0.30),
    ]

    @pytest.mark.parametrize(
        "ambient,forecast,expected_mult",
        POLL_SCENARIOS,
        ids=["normal", "mild", "moderate", "severe", "extreme"],
    )
    def test_polling_cycle(self, ambient, forecast, expected_mult):
        """Simulate one poll -> decide -> print cycle."""
        data = _make_ward_data(ambient, forecast)
        with patch("app.api.ev_safety.get_risk_store", return_value={1: data}):
            resp = client.get("/api/ev-safety/1")

        assert resp.status_code == 200
        advisory = resp.json()
        assert advisory["recommended_charge_rate_multiplier"] == expected_mult

        # Simulate what the station would do
        action = _simulate_charging_decision(advisory)
        expected_kw = round(STATION_MAX_CHARGE_KW * expected_mult, 1)
        assert action["effective_charge_kw"] == expected_kw

        # Print demo output (visible with pytest -s)
        print(
            f"\n[Charging Station CS-DEMO-001] "
            f"Ambient={advisory['ambient_temp_c']}C  "
            f"ForecastPeak={advisory['forecast_peak_temp_c']}C  "
            f"-> Multiplier={advisory['recommended_charge_rate_multiplier']}  "
            f"-> Charging at {action['effective_charge_kw']} kW "
            f"(max {STATION_MAX_CHARGE_KW} kW)  "
            f"| {advisory['reason']}"
        )

    def test_full_polling_loop(self):
        """
        Simulate a station polling every N seconds across changing
        conditions (here we just iterate scenarios sequentially).
        """
        print("\n" + "=" * 72)
        print("  MOCK CHARGING STATION - POLLING DEMO")
        print("=" * 72)

        for label, (ambient, forecast, expected_mult) in zip(
            ["06:00 AM", "10:00 AM", "01:00 PM", "03:00 PM", "04:30 PM"],
            self.POLL_SCENARIOS,
        ):
            data = _make_ward_data(ambient, forecast)
            with patch(
                "app.api.ev_safety.get_risk_store",
                return_value={1: data},
            ):
                resp = client.get("/api/ev-safety/1")

            advisory = resp.json()
            action = _simulate_charging_decision(advisory)

            print(
                f"  [{label}]  "
                f"T={advisory['ambient_temp_c']:5.1f}C  "
                f"Peak={advisory['forecast_peak_temp_c']:5.1f}C  "
                f"-> {action['effective_charge_kw']:6.1f} kW  "
                f"({advisory['reason']})"
            )

        print("=" * 72)
