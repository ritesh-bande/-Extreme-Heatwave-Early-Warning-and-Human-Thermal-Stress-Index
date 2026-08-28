"""
End-to-end test: fetch weather for Indian cities and compute risk.
"""
import asyncio
from app.tasks.fetch_weather import fetch_weather
from app.tasks.scheduler import compute_ward_risk, SAMPLE_WARDS


async def main():
    cities = [
        ("Nagpur", 21.1458, 79.0882),
        ("Chennai", 13.0827, 80.2707),
        ("Ahmedabad", 23.0225, 72.5714),
    ]

    for name, lat, lon in cities:
        print(f"\n{'='*60}")
        print(f"  {name} ({lat}, {lon})")
        print(f"{'='*60}")

        data = await fetch_weather(lat, lon)
        cur = data["current"]
        print(f"Current: T={cur['temp_c']}°C, RH={cur['rh_pct']}%, "
              f"Wind={cur['wind_ms']:.1f} m/s, Solar={cur['solar_wm2']} W/m²")

        print("\n5-Day Forecast:")
        for d in data["daily_forecast"]:
            print(f"  {d['date']}: {d['temp_min_c']:.1f}–{d['temp_max_c']:.1f}°C, "
                  f"RH={d['rh_mean_pct']:.0f}%, "
                  f"Wind={d['wind_max_ms']:.1f} m/s")

        # Compute risk for matching sample ward
        ward = next((w for w in SAMPLE_WARDS if abs(w["centroid_lat"] - lat) < 0.1), None)
        if ward:
            risk = compute_ward_risk(ward, data)
            print(f"\nRisk Assessment ({ward['name']}):")
            print(f"  Heat Index: {risk['heat_index']:.1f}°C")
            print(f"  WBGT:       {risk['wbgt']:.1f}°C")
            print(f"  UTCI:       {risk['utci']:.1f}°C")
            print(f"  Vulnerability Score: {risk['vulnerability_score']:.1f}")
            print(f"  MRI Score:  {risk['mri_score']:.1f}")
            print(f"  Risk Band:  {risk['risk_band']}")
            print(f"  Breakdown:  {risk['breakdown']}")


if __name__ == "__main__":
    asyncio.run(main())
