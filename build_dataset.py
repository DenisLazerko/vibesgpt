"""Build data/pnw_smoke_days.csv from public sources.

Sources (all free, no API key):
  - EPA AirData daily PM2.5 (parameter 88101, FRM/FEM monitors)
      https://aqs.epa.gov/aqsweb/airdata/download_files.html
  - Open-Meteo weather archive (ERA5 reanalysis): actual daily weather
  - Open-Meteo Previous Runs API: weather forecasts issued one day ahead
  - Open-Meteo Air Quality API (CAMS): the official PM2.5 forecast model

Run:  python build_dataset.py            (downloads about 90 MB of EPA zips once)
      python build_dataset.py --epa-dir PATH   (reuse already-downloaded zips)

Raw downloads are cached in data/raw/ so a second run makes no new requests.
"""

import argparse
import json
import math
import os
import time
import urllib.request

import numpy as np
import pandas as pd
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RAW = os.path.join(DATA, "raw")

YEARS = range(2013, 2026)
SEASON_START = "06-20"  # a few extra June days so 7-day features exist on Jul 1
SEASON_END = "10-31"

# EPA "CBSA Name" (metro area) -> short city name used in the project.
CITIES = {
    "Seattle-Tacoma-Bellevue, WA": "Seattle",
    "Bremerton-Silverdale, WA": "Bremerton",
    "Bellingham, WA": "Bellingham",
    "Mount Vernon-Anacortes, WA": "Mount Vernon",
    "Yakima, WA": "Yakima",
    "Ellensburg, WA": "Ellensburg",
    "Spokane-Spokane Valley, WA": "Spokane",
    "Portland-Vancouver-Hillsboro, OR-WA": "Portland",
    "Eugene, OR": "Eugene",
    "Medford, OR": "Medford",
    "Grants Pass, OR": "Grants Pass",
    "Klamath Falls, OR": "Klamath Falls",
    "Prineville, OR": "Prineville",
    "Bend-Redmond, OR": "Bend",
    "Boise City, ID": "Boise",
    "Missoula, MT": "Missoula",
    "Kalispell, MT": "Kalispell",
    "Helena, MT": "Helena",
    "Butte-Silver Bow, MT": "Butte",
    "Bozeman, MT": "Bozeman",
}

WEATHER_VARS = [
    "wind_speed_10m_max",
    "wind_direction_10m_dominant",
    "precipitation_sum",
    "temperature_2m_max",
    "relative_humidity_2m_mean",
]
FORECAST_HOURLY = [
    "wind_speed_10m_previous_day1",
    "wind_direction_10m_previous_day1",
    "precipitation_previous_day1",
    "temperature_2m_previous_day1",
    "relative_humidity_2m_previous_day1",
]


# ---------------------------------------------------------------- EPA monitors
def epa_zip(year, epa_dir):
    path = os.path.join(epa_dir, f"daily_88101_{year}.zip")
    if not os.path.exists(path):
        url = f"https://aqs.epa.gov/aqsweb/airdata/daily_88101_{year}.zip"
        print("  downloading", url)
        urllib.request.urlretrieve(url, path)
    return path


def load_epa(epa_dir):
    cols = ["State Code", "County Code", "Site Num", "Latitude", "Longitude",
            "Date Local", "Event Type", "Arithmetic Mean", "CBSA Name"]
    parts = []
    for y in YEARS:
        df = pd.read_csv(epa_zip(y, epa_dir), usecols=cols, encoding="latin-1",
                         dtype=str)
        df = df[df["CBSA Name"].isin(CITIES)]
        # Smoke-affected samples can appear twice: "Included" and "Excluded".
        # We want what people actually breathed, so drop the "Excluded" copies.
        df = df[df["Event Type"] != "Excluded"]
        df["date"] = pd.to_datetime(df["Date Local"])
        md = df["date"].dt.strftime("%m-%d")
        df = df[(md >= SEASON_START) & (md <= SEASON_END)]
        parts.append(df)
        print(f"  EPA {y}: {len(df):,} rows")
    df = pd.concat(parts, ignore_index=True)
    df["pm"] = df["Arithmetic Mean"].astype(float)
    df["lat"] = df["Latitude"].astype(float)
    df["lon"] = df["Longitude"].astype(float)
    df["city"] = df["CBSA Name"].map(CITIES)
    df["site"] = df["State Code"] + "-" + df["County Code"] + "-" + df["Site Num"]

    # One value per monitor site per day (a site can report several instruments
    # or averaging methods), then the median across the city's sites.
    site_day = df.groupby(["city", "site", "date"], as_index=False)["pm"].mean()
    city_day = (site_day.groupby(["city", "date"])["pm"]
                .agg(pm25="median", n_monitors="size").reset_index())
    city_day["pm25"] = city_day["pm25"].clip(lower=0)

    sites = df.drop_duplicates("site")
    meta = (sites.groupby("city")
            .agg(lat=("lat", "mean"), lon=("lon", "mean"), n_sites=("site", "size"))
            .reset_index())
    return city_day, meta


# ---------------------------------------------------------------- Open-Meteo
def cached_get(url, params, name):
    path = os.path.join(RAW, name + ".json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    for attempt in range(6):
        r = requests.get(url, params=params, timeout=120)
        if r.status_code == 200:
            j = r.json()
            with open(path + ".tmp", "w") as f:
                json.dump(j, f)
            os.replace(path + ".tmp", path)  # never leave a half-written cache file
            return j
        print(f"    {r.status_code} on {name}, retrying")
        time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"failed: {name} {r.text[:200]}")


def prefetch(jobs, workers=4):
    """Download many (url, params, name) requests in parallel into the cache."""
    from concurrent.futures import ThreadPoolExecutor
    todo = [j for j in jobs if not os.path.exists(os.path.join(RAW, j[2] + ".json"))]
    if todo:
        print(f"  fetching {len(todo)} files from Open-Meteo")
        with ThreadPoolExecutor(workers) as ex:
            list(ex.map(lambda j: cached_get(*j), todo))


def slug(city):
    return city.lower().replace(" ", "_")


def load_weather(meta):
    """Actual daily weather (ERA5) for each city and fire season."""
    def job(c, y):
        return ("https://archive-api.open-meteo.com/v1/archive", {
            "latitude": round(c.lat, 3), "longitude": round(c.lon, 3),
            "daily": ",".join(WEATHER_VARS), "timezone": "auto",
            "start_date": f"{y}-{SEASON_START}", "end_date": f"{y}-{SEASON_END}",
        }, f"era5_{slug(c.city)}_{y}")
    prefetch([job(c, y) for _, c in meta.iterrows() for y in YEARS])
    out = []
    for _, c in meta.iterrows():
        for y in YEARS:
            j = cached_get(*job(c, y))
            d = pd.DataFrame(j["daily"])
            d["city"] = c.city
            out.append(d)
        print(f"  weather {c.city}: done")
    w = pd.concat(out, ignore_index=True)
    w["date"] = pd.to_datetime(w.pop("time"))
    return w.rename(columns={
        "wind_speed_10m_max": "wind_max", "wind_direction_10m_dominant": "wind_dir",
        "precipitation_sum": "precip", "temperature_2m_max": "temp_max",
        "relative_humidity_2m_mean": "rh"})


def daily_from_hourly(h):
    """Turn hourly values into the same daily summaries as the ERA5 archive."""
    h = h.copy()
    h["date"] = h["time"].dt.normalize()
    rad = np.deg2rad(h["wdir"])
    h["u"] = -h["wspd"] * np.sin(rad)
    h["v"] = -h["wspd"] * np.cos(rad)
    g = h.groupby("date")
    d = pd.DataFrame({
        "wind_max": g["wspd"].max(min_count=18),
        "precip": g["precip"].sum(min_count=18),
        "temp_max": g["temp"].max(min_count=18),
        "rh": g["rh"].mean(),
        "u": g["u"].mean(), "v": g["v"].mean(),
    })
    d["wind_dir"] = (np.rad2deg(np.arctan2(-d["u"], -d["v"])) % 360).round()
    return d.drop(columns=["u", "v"]).reset_index()


def load_forecast_weather(meta):
    """Weather forecasts issued the day before (Open-Meteo Previous Runs API).

    Wind and rain forecasts in this archive start in 2024, so this only covers
    the 2024 and 2025 seasons. Used for the forecast honesty check.
    """
    def job(c, y):
        return ("https://previous-runs-api.open-meteo.com/v1/forecast", {
            "latitude": round(c.lat, 3), "longitude": round(c.lon, 3),
            "hourly": ",".join(FORECAST_HOURLY), "timezone": "auto",
            "start_date": f"{y}-{SEASON_START}", "end_date": f"{y}-{SEASON_END}",
        }, f"fcst_{slug(c.city)}_{y}")
    prefetch([job(c, y) for _, c in meta.iterrows() for y in (2024, 2025)])
    out = []
    for _, c in meta.iterrows():
        for y in (2024, 2025):
            j = cached_get(*job(c, y))
            h = pd.DataFrame(j["hourly"])
            h["time"] = pd.to_datetime(h["time"])
            h = h.rename(columns={
                "wind_speed_10m_previous_day1": "wspd",
                "wind_direction_10m_previous_day1": "wdir",
                "precipitation_previous_day1": "precip",
                "temperature_2m_previous_day1": "temp",
                "relative_humidity_2m_previous_day1": "rh"})
            d = daily_from_hourly(h)
            d["city"] = c.city
            out.append(d)
        print(f"  forecast weather {c.city}: done")
    f = pd.concat(out, ignore_index=True)
    return f.rename(columns={k: "fc_" + k for k in
                             ["wind_max", "wind_dir", "precip", "temp_max", "rh"]})


def load_cams(meta):
    """CAMS PM2.5 (the official forecast model) as a local-time daily mean.

    Open-Meteo's CAMS archive starts on 2022-08-03.
    """
    def job(c, y):
        start = "2022-08-03" if y == 2022 else f"{y}-{SEASON_START}"
        return ("https://air-quality-api.open-meteo.com/v1/air-quality", {
            "latitude": round(c.lat, 3), "longitude": round(c.lon, 3),
            "hourly": "pm2_5", "timezone": "auto",
            "start_date": start, "end_date": f"{y}-{SEASON_END}",
        }, f"cams_{slug(c.city)}_{y}")
    years = (2022, 2023, 2024, 2025)
    prefetch([job(c, y) for _, c in meta.iterrows() for y in years])
    out = []
    for _, c in meta.iterrows():
        for y in years:
            j = cached_get(*job(c, y))
            h = pd.DataFrame(j["hourly"])
            h["date"] = pd.to_datetime(h["time"]).dt.normalize()
            d = h.groupby("date")["pm2_5"].mean(numeric_only=True).rename("cams_pm25")
            # Require most hours to be present.
            n = h.groupby("date")["pm2_5"].count()
            d[n < 18] = np.nan
            d = d.reset_index()
            d["city"] = c.city
            out.append(d)
        print(f"  CAMS {c.city}: done")
    return pd.concat(out, ignore_index=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epa-dir", default=RAW, help="folder with daily_88101_YYYY.zip")
    args = ap.parse_args()
    os.makedirs(RAW, exist_ok=True)

    print("EPA monitors")
    city_day, meta = load_epa(args.epa_dir)

    # Full calendar of city-days, so gaps show up as NaN instead of vanishing.
    days = pd.concat([pd.Series(pd.date_range(f"{y}-{SEASON_START}", f"{y}-{SEASON_END}"))
                      for y in YEARS])
    grid = pd.MultiIndex.from_product([meta.city, days], names=["city", "date"]).to_frame(index=False)
    df = grid.merge(city_day, on=["city", "date"], how="left")

    print("Weather (actual)")
    df = df.merge(load_weather(meta), on=["city", "date"], how="left")
    print("Weather (forecast issued the day before)")
    df = df.merge(load_forecast_weather(meta), on=["city", "date"], how="left")
    print("CAMS")
    df = df.merge(load_cams(meta), on=["city", "date"], how="left")

    df = df.sort_values(["city", "date"]).reset_index(drop=True)
    df["n_monitors"] = df["n_monitors"].fillna(0).astype(int)
    for c in df.columns:
        if df[c].dtype == float:
            df[c] = df[c].round(2)

    meta = meta.round({"lat": 4, "lon": 4})
    meta.to_csv(os.path.join(DATA, "cities.csv"), index=False)
    df.to_csv(os.path.join(DATA, "pnw_smoke_days.csv"), index=False, date_format="%Y-%m-%d")
    print(f"Saved {len(df):,} rows for {df.city.nunique()} cities "
          f"({os.path.getsize(os.path.join(DATA, 'pnw_smoke_days.csv')) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
