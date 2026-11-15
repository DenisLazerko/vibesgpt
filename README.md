# SmokeCheck

**Track:** Climate
**Team:** [name], [name]

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/grushet/smokecheck/blob/main/smokecheck.ipynb)

Code: [smokecheck.ipynb](smokecheck.ipynb) (saved with all outputs)

## The problem

Wildfire smoke now reaches Pacific Northwest towns almost every summer. Our own track practice has had to move inside because of it. [COACH LINE: one true sentence from Coach ____ about practices on smoke days, or delete this.] The call is usually made the evening before, so coaches, parents and buses can plan. [Check this with the coach.] The easy guess is "tomorrow will look like today", but that guess is always late on the first day smoke arrives. From 2023 to 2025, 83 of the 154 smoke days in our data came right after a clean day.

## What we built

SmokeCheck predicts tomorrow's average PM2.5 (fine smoke particles) for 20 cities in Washington, Oregon, Idaho and Montana. Each evening it looks at:

- today's readings in that city,
- today's readings in nearby cities and in the cities upwind of tomorrow's wind,
- the weather forecast for tomorrow (wind, rain, temperature, humidity).

If the forecast is above 25.5 µg/m³, it says "move practice indoors" and shows the three inputs that moved the forecast most. You pick a city and a date in a small web demo and get the decision back.

## What we added

We started from suggested project 4.3.2 (next-day air quality forecast) and added:

1. **A real user and decision.** An athletic director deciding tonight about tomorrow's practice. We count one missed smoke day as bad as three unneeded indoor practices, and chose the warning level on 2022 data using that rule.
2. **Our own data setup.** 55 EPA regulatory monitors in 20 cities instead of one station. Seattle alone had only 2 smoke days in 2023-2025, too few to test a warning on.
3. **Our own idea.** Smoke usually shows up in neighboring cities before it reaches you, so the model reads them, with extra weight on cities upwind of tomorrow's wind.
4. **Our own questions.** Can it warn on the first day of smoke? Does it beat the official CAMS forecast? Does it work in cities it never trained on? How much worse is it with real weather forecasts instead of the weather that actually happened?

## How it works

**Data.** EPA daily PM2.5, July to October, 2013-2025. Each city's value is the median of its monitors. Weather and the CAMS forecast come from Open-Meteo. That gives 34,840 city-days with 910 smoke days (daily average above 35 µg/m³, where EPA's "unhealthy for sensitive groups" begins).

**Split by time, never shuffled.** Train on 2013-2021, choose the warning level on 2022, test once on 2023-2025 (7,207 city-days, 154 smoke days).

**Model.** Gradient boosting (scikit-learn) on 20 inputs, predicting log PM2.5. We also tried ridge regression. Boosting did better on 2022, so we kept it.

## Results

On the 2023-2025 test seasons:

| | Tomorrow = today | CAMS (official forecast) | SmokeCheck |
|---|---|---|---|
| Smoke days warned (of 154) | 87 | 62 | **99** |
| First day of smoke warned (of 83) | 16 | 23 | **31** |
| False alarms (of 7,053 clean days) | **110** | **106** | 134 |
| Average error (µg/m³) | 3.4 | 4.1 | **2.8** |

- Against "tomorrow = today", SmokeCheck warned on 15 more first days of smoke. Resampling whole city-seasons, that gain is between +7 and +23 with 95% confidence. The cost is 24 more false alarms, about 0.4 extra indoor days per city per season.
- **Cities it never trained on.** Bend, Grants Pass, Medford and Prineville had no usable data before 2023. There it warned on 46 of 75 smoke days with 38 false alarms (tomorrow = today: 43 and 47).
- **Honesty check.** Training uses the weather that actually happened. When we swapped in the forecasts that were really issued (2024-2025 only), warnings dropped from 51 to 48 of 80 smoke days and false alarms rose from 90 to 95. On those two seasons it is no better than "tomorrow = today" on our 3-to-1 cost, though it still caught more first days (17 vs 11).
- CAMS had an advantage we could not remove: part of its archived forecast was made after our evening decision time.

**Where it fails.** Smoke that jumps in overnight. On Aug 17, 2023, Medford went from 19 to 103 µg/m³. SmokeCheck said 24, under the warning level, even though a nearby city was already at 69. On peaks, its forecast often trails the real value by a day, and it can be slow to call the end of smoke (Boise, Sep 6, 2024: forecast 75, actual 25).

This is a prototype and not official air quality guidance.

## What we'd do next

1. Add satellite fire detections (NASA FIRMS) so the model can see a fire before any monitor does. That targets the overnight misses above.
2. Use the CAMS forecast as an input instead of a rival, and run SmokeCheck live on AirNow data during the 2026 season.

## Sources

- EPA AirData daily PM2.5 (parameter 88101): https://aqs.epa.gov/aqsweb/airdata/download_files.html
- Open-Meteo Historical Weather API (ERA5): https://open-meteo.com/en/docs/historical-weather-api
- Open-Meteo Previous Runs API (weather forecasts as issued): https://open-meteo.com/en/docs/previous-runs-api
- Open-Meteo Air Quality API (CAMS forecast): https://open-meteo.com/en/docs/air-quality-api
- Libraries: pandas, NumPy, scikit-learn, Matplotlib, Gradio
- AI tools: Claude (Anthropic) through Claude Code. It helped write the data pipeline, notebook code and first drafts of the text. We checked and can explain every part.
