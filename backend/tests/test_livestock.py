"""
Tests for livestock.py — Livestock Heat Stress & Irrigation Alert Module.

Reference THI values sourced from:
  - NRC, 1971. "A Guide to Environmental Research on Animals."
  - Bohmanova et al., 2007. J. Dairy Sci. 90:1947–1956.
  - Armstrong, 1994. J. Dairy Sci. 77:2044–2050.
  - Dikmen & Hansen, 2009. J. Dairy Sci. 92:3781–3790.

THI formula:
  THI = (1.8 × T + 32) − (0.55 − 0.0055 × RH) × (1.8 × T − 26)

Hand-calculated reference values verified below.
"""

import pytest
from app.services.livestock import (
    compute_livestock_thi,
    classify_thi,
    check_irrigation_alert,
    DEFAULT_TEMP_THRESHOLD_C,
    DEFAULT_WBGT_THRESHOLD_C,
)


# ──────────────────────────────────────────────────────────────────────
# THI computation tests
# Hand-calculated references using the NRC formula:
#   THI = (1.8T + 32) − (0.55 − 0.0055 × RH) × (1.8T − 26)
# ──────────────────────────────────────────────────────────────────────

class TestComputeLivestockTHI:
    """Tests for dairy cattle Temperature-Humidity Index computation."""

    def test_reference_25c_50rh(self):
        """
        T=25°C, RH=50%
        Hand calculation:
          1.8×25+32 = 77.0
          0.55 − 0.0055×50 = 0.275
          1.8×25 − 26 = 19.0
          THI = 77.0 − 0.275 × 19.0 = 77.0 − 5.225 = 71.775
        Source: Widely cited onset-of-stress boundary condition.
        """
        thi = compute_livestock_thi(25.0, 50.0)
        assert abs(thi - 71.78) < 0.1, f"Expected ~71.78, got {thi}"

    def test_reference_30c_60rh(self):
        """
        T=30°C, RH=60%
        Hand calculation:
          1.8×30+32 = 86.0
          0.55 − 0.0055×60 = 0.22
          1.8×30 − 26 = 28.0
          THI = 86.0 − 0.22 × 28.0 = 86.0 − 6.16 = 79.84
        Source: Typical tropical daytime condition — Mild/Moderate boundary.
        """
        thi = compute_livestock_thi(30.0, 60.0)
        assert abs(thi - 79.84) < 0.1, f"Expected ~79.84, got {thi}"

    def test_reference_35c_80rh(self):
        """
        T=35°C, RH=80%
        Hand calculation:
          1.8×35+32 = 95.0
          0.55 − 0.0055×80 = 0.11
          1.8×35 − 26 = 37.0
          THI = 95.0 − 0.11 × 37.0 = 95.0 − 4.07 = 90.93
        Source: Severe heat stress — referenced in Dikmen & Hansen (2009).
        """
        thi = compute_livestock_thi(35.0, 80.0)
        assert abs(thi - 90.93) < 0.1, f"Expected ~90.93, got {thi}"

    def test_reference_40c_30rh(self):
        """
        T=40°C, RH=30%
        Hand calculation:
          1.8×40+32 = 104.0
          0.55 − 0.0055×30 = 0.385
          1.8×40 − 26 = 46.0
          THI = 104.0 − 0.385 × 46.0 = 104.0 − 17.71 = 86.29
        Source: Hot arid climate — moderate stress despite low humidity.
        """
        thi = compute_livestock_thi(40.0, 30.0)
        assert abs(thi - 86.29) < 0.1, f"Expected ~86.29, got {thi}"

    def test_reference_20c_40rh(self):
        """
        T=20°C, RH=40%
        Hand calculation:
          1.8×20+32 = 68.0
          0.55 − 0.0055×40 = 0.33
          1.8×20 − 26 = 10.0
          THI = 68.0 − 0.33 × 10.0 = 68.0 − 3.30 = 64.70
        Source: Thermoneutral zone — no stress expected.
        """
        thi = compute_livestock_thi(20.0, 40.0)
        assert abs(thi - 64.70) < 0.1, f"Expected ~64.70, got {thi}"

    def test_reference_38c_70rh(self):
        """
        T=38°C, RH=70%
        Hand calculation:
          1.8×38+32 = 100.4
          0.55 − 0.0055×70 = 0.165
          1.8×38 − 26 = 42.4
          THI = 100.4 − 0.165 × 42.4 = 100.4 − 6.996 = 93.404
        Source: Severe stress — field conditions noted by Collier et al. (2012).
        """
        thi = compute_livestock_thi(38.0, 70.0)
        assert abs(thi - 93.40) < 0.1, f"Expected ~93.40, got {thi}"

    def test_reference_42c_90rh(self):
        """
        T=42°C, RH=90%
        Hand calculation:
          1.8×42+32 = 107.6
          0.55 − 0.0055×90 = 0.055
          1.8×42 − 26 = 49.6
          THI = 107.6 − 0.055 × 49.6 = 107.6 − 2.728 = 104.872
        Source: Extreme — emergency conditions for all cattle breeds.
        """
        thi = compute_livestock_thi(42.0, 90.0)
        assert abs(thi - 104.87) < 0.1, f"Expected ~104.87, got {thi}"

    def test_output_is_float(self):
        """Return type must be float."""
        assert isinstance(compute_livestock_thi(30.0, 50.0), float)

    def test_thi_increases_with_temperature(self):
        """THI should increase monotonically with temperature at fixed RH."""
        thi_low = compute_livestock_thi(25.0, 50.0)
        thi_high = compute_livestock_thi(35.0, 50.0)
        assert thi_high > thi_low

    def test_thi_increases_with_humidity(self):
        """THI should increase when humidity increases at fixed temperature."""
        thi_dry = compute_livestock_thi(30.0, 20.0)
        thi_humid = compute_livestock_thi(30.0, 80.0)
        assert thi_humid > thi_dry


# ──────────────────────────────────────────────────────────────────────
# THI classification tests
# ──────────────────────────────────────────────────────────────────────

class TestClassifyTHI:
    """Tests for THI stress band classification."""

    def test_no_stress_well_below(self):
        assert classify_thi(60.0) == "No stress"

    def test_no_stress_just_below_boundary(self):
        assert classify_thi(71.9) == "No stress"

    def test_mild_at_boundary(self):
        """THI = 72 exactly → Mild stress begins."""
        assert classify_thi(72.0) == "Mild"

    def test_mild_mid_range(self):
        assert classify_thi(75.0) == "Mild"

    def test_mild_upper_boundary(self):
        """THI = 79.9 → still Mild."""
        assert classify_thi(79.9) == "Mild"

    def test_moderate_at_boundary(self):
        """THI = 80 → Moderate stress begins."""
        assert classify_thi(80.0) == "Moderate"

    def test_moderate_mid_range(self):
        assert classify_thi(85.0) == "Moderate"

    def test_moderate_upper_boundary(self):
        assert classify_thi(89.9) == "Moderate"

    def test_severe_at_boundary(self):
        """THI = 90 → Severe."""
        assert classify_thi(90.0) == "Severe"

    def test_severe_at_98(self):
        """THI = 98 → still Severe."""
        assert classify_thi(98.0) == "Severe"

    def test_extreme_at_99(self):
        """THI = 99 → Extreme."""
        assert classify_thi(99.0) == "Extreme"

    def test_extreme_very_high(self):
        assert classify_thi(110.0) == "Extreme"

    def test_all_bands_returned(self):
        """Each of the 5 bands should be reachable."""
        bands = {classify_thi(v) for v in [60, 75, 85, 95, 105]}
        expected = {"No stress", "Mild", "Moderate", "Severe", "Extreme"}
        assert bands == expected


# ──────────────────────────────────────────────────────────────────────
# Irrigation alert tests
# ──────────────────────────────────────────────────────────────────────

class TestCheckIrrigationAlert:
    """Tests for consecutive-day irrigation alert logic."""

    def _make_forecast(
        self,
        temps: list[float],
        wbgts: list[float | None] | None = None,
    ) -> list[dict]:
        """Helper to build a forecast_days list."""
        days = []
        for i, t in enumerate(temps):
            d: dict = {"date": f"2025-06-{i+1:02d}", "temp_c": t}
            if wbgts and i < len(wbgts) and wbgts[i] is not None:
                d["wbgt_c"] = wbgts[i]
            days.append(d)
        return days

    # --- Positive alerts ---

    def test_three_consecutive_hot_days_triggers(self):
        """3 consecutive days at ≥ 38°C should trigger."""
        days = self._make_forecast([39.0, 40.0, 38.5])
        result = check_irrigation_alert(days)
        assert result is not None
        assert "IRRIGATION ALERT" in result

    def test_four_consecutive_hot_days_triggers(self):
        """4 consecutive hot days should also trigger."""
        days = self._make_forecast([39.0, 40.0, 38.0, 41.0])
        result = check_irrigation_alert(days)
        assert result is not None

    def test_wbgt_triggers_alert(self):
        """Days with high WBGT but moderate temp should still trigger."""
        days = self._make_forecast(
            [35.0, 35.0, 35.0],  # below temp threshold
            [31.0, 32.0, 30.5],  # above WBGT threshold
        )
        result = check_irrigation_alert(days)
        assert result is not None
        assert "IRRIGATION ALERT" in result

    def test_mixed_temp_and_wbgt_triggers(self):
        """Mix of temp-triggered and WBGT-triggered days in a row."""
        days = [
            {"date": "2025-06-01", "temp_c": 39.0},                      # temp hot
            {"date": "2025-06-02", "temp_c": 36.0, "wbgt_c": 31.0},      # WBGT hot
            {"date": "2025-06-03", "temp_c": 38.5},                       # temp hot
        ]
        result = check_irrigation_alert(days)
        assert result is not None

    def test_alert_includes_start_date(self):
        """Alert message should mention the start date of the heat streak."""
        days = self._make_forecast([39.0, 40.0, 38.5])
        result = check_irrigation_alert(days)
        assert result is not None
        assert "2025-06-01" in result

    # --- Negative (no alert) ---

    def test_no_alert_below_threshold(self):
        """All days below threshold → no alert."""
        days = self._make_forecast([35.0, 36.0, 37.0, 35.5])
        result = check_irrigation_alert(days)
        assert result is None

    def test_no_alert_non_consecutive(self):
        """Hot days separated by a cool day → no consecutive streak."""
        days = self._make_forecast([39.0, 40.0, 35.0, 39.0, 40.0])
        result = check_irrigation_alert(days)
        assert result is None

    def test_no_alert_only_two_consecutive(self):
        """Only 2 consecutive hot days → below default threshold of 3."""
        days = self._make_forecast([39.0, 40.0, 35.0])
        result = check_irrigation_alert(days)
        assert result is None

    def test_empty_forecast_returns_none(self):
        """Empty forecast list → no alert."""
        result = check_irrigation_alert([])
        assert result is None

    # --- Custom thresholds ---

    def test_custom_temp_threshold(self):
        """Lower custom threshold should trigger on milder days."""
        days = self._make_forecast([33.0, 34.0, 35.0])
        result = check_irrigation_alert(days, temp_threshold_c=33.0)
        assert result is not None

    def test_custom_consecutive_days(self):
        """Custom consecutive_days=2 should trigger earlier."""
        days = self._make_forecast([39.0, 40.0])
        result = check_irrigation_alert(days, consecutive_days=2)
        assert result is not None

    def test_custom_consecutive_days_not_met(self):
        """Custom consecutive_days=4, only 3 hot days → no alert."""
        days = self._make_forecast([39.0, 40.0, 38.5])
        result = check_irrigation_alert(days, consecutive_days=4)
        assert result is None

    # --- Edge cases ---

    def test_exactly_at_temp_threshold(self):
        """Days at exactly the threshold should count as hot."""
        days = self._make_forecast([38.0, 38.0, 38.0])
        result = check_irrigation_alert(days)
        assert result is not None

    def test_invalid_consecutive_days_raises(self):
        """consecutive_days < 1 should raise ValueError."""
        with pytest.raises(ValueError, match="consecutive_days must be"):
            check_irrigation_alert([], consecutive_days=0)

    def test_streak_resets_after_cool_day(self):
        """After a cool day breaks the streak, a new streak can form."""
        #                 hot  hot  cool hot  hot  hot  → triggers at day 6
        days = self._make_forecast([39.0, 40.0, 35.0, 39.0, 40.0, 38.5])
        result = check_irrigation_alert(days)
        assert result is not None
        assert "2025-06-04" in result  # New streak starts on day 4

    def test_single_hot_day_no_alert(self):
        """A single scorching day should not trigger an alert."""
        days = self._make_forecast([45.0])
        result = check_irrigation_alert(days)
        assert result is None
