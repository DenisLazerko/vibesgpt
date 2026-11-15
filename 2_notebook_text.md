## Top of notebook

# SmokeCheck

Next-day wildfire smoke warnings for high school sports in Washington, Oregon, Idaho and Montana.

Each evening, SmokeCheck predicts tomorrow's average PM2.5 for a city. If the forecast is high enough, it says to move tomorrow's practice indoors. We compare it with two other ways of deciding: "tomorrow = today" and the official CAMS air quality forecast.

The notebook runs top to bottom in about a minute. It loads one small CSV file that `build_dataset.py` made from EPA and Open-Meteo data.

[Open in Colab button]

## 0. Setup

(no text, code only)

## 1. The data

One row per city per day, July to October, 2013-2025. `pm25` is the median of the city's EPA monitors that day. Weather is what actually happened (ERA5). Columns starting with `fc_` are weather forecasts issued the day before, which only exist for 2024-2025. `cams_pm25` is the official CAMS forecast, archived from August 2022 on.

Some Oregon monitors only took a sample every third day before 2023. Those cities show about 40 days a season in the table below. With no back-to-back days, they can't be used for training, so they become a test of cities the model has never seen.

Chart titles:
- Left: "The 20 cities"
- Right: "Smoke days per season, all 20 cities"

## 2. Features

Everything the model sees is known on the evening of day D, with one exception: tomorrow's weather. In real use that comes from a weather forecast. For training we use the weather that actually happened. Section 9 checks how much that matters.

The new idea is the regional inputs. Smoke usually reaches neighboring cities first. `reg_max` is the highest reading today within 400 km. `upwind_max` is the highest reading today among cities that lie in the direction tomorrow's wind comes from (within 600 km and ±60°).

## 3. Train / tune / test split (by time, never shuffled)

Train on 2013-2021. Choose the warning level on 2022. Score 2023-2025 once, at the end. A smoke day is a daily average above 35 µg/m³, where EPA's "unhealthy for sensitive groups" starts.

## 4. Baselines and models

- **Persistence:** tomorrow = today. The brief's baseline.
- **Climatology:** the average for that city and time of year in past seasons.
- **CAMS:** the official Copernicus forecast. It is a strong rival, but it had an advantage: part of the archived forecast was made after our evening decision time.
- **Ridge regression** and **gradient boosting**, trained on log PM2.5 so the worst days don't drown out everything else.

## 5. Pick each method's warning threshold on 2022

A missed smoke day means kids running in smoke. A false alarm means an indoor practice that wasn't needed. We count a miss as three times worse. Each method gets the threshold that gives it the lowest cost on 2022, where cost = 3 × misses + false alarms.

## 6. Freeze, then score the 2023-2025 test seasons once

The final model is whichever of ridge or boosting had the lower 2022 cost. We retrain it on 2013-2022 with the same settings, keep the 2022 thresholds, and score 2023-2025.

## 7. Onset days: the day smoke first arrives

An onset day is a smoke day that follows a clean day. "Tomorrow = today" can only catch one when today was already close to 35. Below we compare methods on the same onset days, and resample whole city-seasons 2,000 times to see how sure we can be about the differences.

## 8. Results by city

Bend, Grants Pass, Medford and Prineville had no usable training data, so the model never saw them before the test.

## 9. Honesty check: real weather forecasts instead of actual weather

The model trained on the weather that actually happened. A coach would only have the forecast. Here we swap in the forecasts that were really issued the day before (2024-2025, the only seasons available) and score again on the same days.

## 10. Where it fails

The two biggest missed warnings and the biggest false alarm, each from a different smoke event.

Chart titles (made by code): "missed warning: Medford, Aug 17 2023", "missed warning: Yakima, Aug 19 2023", "false alarm: Boise, Sep 06 2024". Legend: actual, our forecast, CAMS, persistence.

[After you approve, I'll add one short paragraph per case saying what the inputs showed. Draft:]
- Medford, Aug 17 2023: today was 19 and a nearby city was already at 69, but the forecast stayed at 24. The jump to 103 happened overnight.
- Yakima, Aug 19 2023: today was 5. Nearby cities were at 59 and upwind cities at 46. The model said 10; CAMS said 37 and would have warned. The actual value was 83.
- Boise, Sep 6 2024: today was 47 with a nearby city at 81, so the model expected more smoke (75). It cleared to 25.

## 11. A whole season

Chart titles: "Spokane, 2025", "Medford, 2023", "Bend, 2024", "Seattle, 2023". Legend: actual, our forecast, CAMS, our warning.

## 12. Why did it warn?

For each group of inputs, we replace it with a typical fire-season value and see how much the forecast changes. The three biggest changes are listed with the decision.

## 13. Try it yourself

Pick a city and an evening from the 2023-2025 fire seasons. The demo shows tomorrow's forecast, the decision, and what moved the forecast most.

Text inside the demo card:
- "MOVE PRACTICE INDOORS" / "OK TO PRACTICE OUTSIDE"
- "Our forecast for tomorrow: X µg/m³ (we warn above 25.5)"
- "Official CAMS forecast", "Persistence (tomorrow = today)"
- "What moved the forecast most:"
- "What actually happened: X µg/m³ (smoke day / not a smoke day)"
