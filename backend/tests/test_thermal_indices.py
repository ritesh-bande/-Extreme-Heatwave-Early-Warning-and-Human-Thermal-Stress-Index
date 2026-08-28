"""
Tests for thermal_indices.py

Reference values sourced from:
  - Heat Index: NWS Heat Index Calculator & Rothfusz lookup tables
  - WBGT: ISO 7243 reference conditions & Liljegren test cases
  - UTCI: UTCI assessment scale reference table (Bröde et al., 2012)

Each test case includes a source comment for traceability.
"""

import pytest
from app.services.thermal_indices import (
    compute_heat_index,
    compute_wbgt,
    compute_utci,
    classify_risk,
)


# ──────────────────────────────────────────────────────────────────────
# Heat Index tests
# Source: NWS Heat Index Chart
# https://www.weather.gov/ama/heatindex
# ──────────────────────────────────────────────────────────────────────

class TestComputeHeatIndex:
    """Tests for NOAA/Rothfusz Heat Index computation."""

    def test_low_temperature_simple_formula(self):
        """Below 80°F (~26.7°C) threshold → simple Steadman formula applies."""
        # At 25°C, 50% RH → HI should be close to ambient
        hi = compute_heat_index(25.0, 50.0)
        assert 23.0 <= hi <= 27.0, f"Expected ~25°C, got {hi}"

    def test_moderate_heat_moderate_humidity(self):
        """33°C (91.4°F), 40% RH → NWS chart: ~33°C (91°F HI)."""
        hi = compute_heat_index(33.0, 40.0)
        assert 30.0 <= hi <= 36.0, f"Expected ~33°C, got {hi}"

    def test_high_heat_high_humidity(self):
        """35°C (95°F), 80% RH → NWS chart: ~52°C (126°F HI)."""
        hi = compute_heat_index(35.0, 80.0)
        assert 45.0 <= hi <= 58.0, f"Expected ~52°C, got {hi}"

    def test_extreme_heat_low_humidity(self):
        """40°C (104°F), 20% RH → NWS chart: ~37°C (98°F HI)."""
        hi = compute_heat_index(40.0, 20.0)
        assert 34.0 <= hi <= 42.0, f"Expected ~37°C, got {hi}"

    def test_very_high_heat_very_high_humidity(self):
        """38°C (100.4°F), 70% RH → should produce dangerous HI > 50°C."""
        hi = compute_heat_index(38.0, 70.0)
        assert hi > 45.0, f"Expected > 45°C for extreme conditions, got {hi}"

    def test_moderate_conditions_low_rh(self):
        """30°C, 30% RH → mild heat stress, HI near ambient."""
        hi = compute_heat_index(30.0, 30.0)
        assert 28.0 <= hi <= 33.0, f"Expected ~30°C, got {hi}"

    def test_output_is_float(self):
        """Return type should be float."""
        assert isinstance(compute_heat_index(30.0, 50.0), float)


# ──────────────────────────────────────────────────────────────────────
# WBGT tests
# Source: ISO 7243:2017 reference conditions
# These are approximate since we're using estimated Tw and Tg
# ──────────────────────────────────────────────────────────────────────

class TestComputeWBGT:
    """Tests for simplified outdoor WBGT estimation."""

    def test_mild_conditions(self):
        """25°C, 50% RH, 2 m/s wind, 300 W/m² solar → WBGT ~20-24°C."""
        wbgt = compute_wbgt(25.0, 50.0, 2.0, 300.0)
        assert 18.0 <= wbgt <= 26.0, f"Expected ~20-24°C, got {wbgt}"

    def test_hot_humid_sunny(self):
        """35°C, 80% RH, 1 m/s wind, 800 W/m² solar → WBGT ~32-36°C."""
        wbgt = compute_wbgt(35.0, 80.0, 1.0, 800.0)
        assert 28.0 <= wbgt <= 38.0, f"Expected ~32-36°C, got {wbgt}"

    def test_hot_dry_windy(self):
        """40°C, 20% RH, 5 m/s wind, 500 W/m² → WBGT moderate."""
        wbgt = compute_wbgt(40.0, 20.0, 5.0, 500.0)
        assert 22.0 <= wbgt <= 34.0, f"Got {wbgt}"

    def test_no_solar_radiation(self):
        """30°C, 60% RH, 2 m/s wind, 0 W/m² (night) → lower WBGT."""
        wbgt = compute_wbgt(30.0, 60.0, 2.0, 0.0)
        assert 20.0 <= wbgt <= 28.0, f"Got {wbgt}"

    def test_zero_wind(self):
        """35°C, 60% RH, 0 m/s wind, 600 W/m² → higher stress."""
        wbgt = compute_wbgt(35.0, 60.0, 0.0, 600.0)
        assert 26.0 <= wbgt <= 36.0, f"Got {wbgt}"

    def test_increases_with_humidity(self):
        """WBGT should increase when humidity increases, all else equal."""
        wbgt_low = compute_wbgt(35.0, 30.0, 2.0, 500.0)
        wbgt_high = compute_wbgt(35.0, 90.0, 2.0, 500.0)
        assert wbgt_high > wbgt_low, (
            f"Higher humidity should give higher WBGT: {wbgt_low} vs {wbgt_high}"
        )

    def test_output_is_float(self):
        """Return type should be float."""
        assert isinstance(compute_wbgt(30.0, 50.0, 2.0, 400.0), float)


# ──────────────────────────────────────────────────────────────────────
# UTCI tests
# Source: UTCI assessment scale (Bröde et al., 2012)
#   No thermal stress:  9–26°C
#   Moderate heat stress: 26–32°C
#   Strong heat stress: 32–38°C
#   Very strong heat stress: 38–46°C
#   Extreme heat stress: >46°C
# ──────────────────────────────────────────────────────────────────────

class TestComputeUTCI:
    """Tests for UTCI computation (pythermalcomfort or fallback)."""

    def test_comfortable_conditions(self):
        """20°C, 50% RH, 1 m/s wind, MRT=20°C → no thermal stress (9-26)."""
        utci = compute_utci(20.0, 50.0, 1.0, 20.0)
        assert 9.0 <= utci <= 30.0, f"Expected comfortable range, got {utci}"

    def test_moderate_heat_stress(self):
        """30°C, 50% RH, 1 m/s, MRT=40°C → moderate heat stress (~28-34)."""
        utci = compute_utci(30.0, 50.0, 1.0, 40.0)
        assert 25.0 <= utci <= 40.0, f"Expected moderate heat stress, got {utci}"

    def test_strong_heat_stress(self):
        """35°C, 60% RH, 1 m/s, MRT=55°C → strong heat stress."""
        utci = compute_utci(35.0, 60.0, 1.0, 55.0)
        assert 30.0 <= utci <= 48.0, f"Expected strong heat stress, got {utci}"

    def test_extreme_conditions(self):
        """42°C, 40% RH, 0.5 m/s, MRT=65°C → very strong / extreme."""
        utci = compute_utci(42.0, 40.0, 0.5, 65.0)
        assert utci > 35.0, f"Expected high UTCI, got {utci}"

    def test_wind_reduces_utci(self):
        """Higher wind should reduce UTCI (more convective cooling)."""
        utci_calm = compute_utci(35.0, 50.0, 0.5, 45.0)
        utci_windy = compute_utci(35.0, 50.0, 5.0, 45.0)
        assert utci_windy < utci_calm, (
            f"Wind should reduce UTCI: calm={utci_calm}, windy={utci_windy}"
        )

    def test_output_is_float(self):
        """Return type should be float."""
        assert isinstance(compute_utci(25.0, 50.0, 1.0, 30.0), float)


# ──────────────────────────────────────────────────────────────────────
# Risk classification tests
# ──────────────────────────────────────────────────────────────────────

class TestClassifyRisk:
    """Tests for thermal index risk band classification."""

    # Heat Index bands
    def test_hi_green(self):
        assert classify_risk(25.0, "heat_index") == "Green"

    def test_hi_yellow(self):
        assert classify_risk(29.0, "heat_index") == "Yellow"

    def test_hi_orange(self):
        assert classify_risk(35.0, "heat_index") == "Orange"

    def test_hi_red(self):
        assert classify_risk(45.0, "heat_index") == "Red"

    def test_hi_purple(self):
        assert classify_risk(55.0, "heat_index") == "Purple"

    # WBGT bands
    def test_wbgt_green(self):
        assert classify_risk(24.0, "wbgt") == "Green"

    def test_wbgt_yellow(self):
        assert classify_risk(27.0, "wbgt") == "Yellow"

    def test_wbgt_orange(self):
        assert classify_risk(29.0, "wbgt") == "Orange"

    def test_wbgt_red(self):
        assert classify_risk(31.0, "wbgt") == "Red"

    def test_wbgt_purple(self):
        assert classify_risk(34.0, "wbgt") == "Purple"

    # UTCI bands
    def test_utci_green(self):
        assert classify_risk(20.0, "utci") == "Green"

    def test_utci_orange(self):
        assert classify_risk(35.0, "utci") == "Orange"

    def test_utci_purple(self):
        assert classify_risk(47.0, "utci") == "Purple"

    # Edge cases
    def test_exact_threshold_is_higher_band(self):
        """At exact threshold value, should go to the higher band."""
        # At 27.0 exactly, >= threshold means next band
        assert classify_risk(27.0, "heat_index") == "Yellow"

    def test_invalid_index_type_raises(self):
        with pytest.raises(ValueError, match="Unknown index_type"):
            classify_risk(30.0, "invalid_index")

    def test_case_insensitive(self):
        """Index type lookup should be case-insensitive."""
        assert classify_risk(25.0, "Heat_Index") == "Green"
        assert classify_risk(25.0, "WBGT") == "Green"
