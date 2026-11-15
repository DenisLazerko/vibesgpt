**Project title:** SmokeCheck

**Building as:** Team

**Team name:** vibesgpt

**Team members:** Denis Lazerko, lazerko.den@gmail.com, Lake Washington High School; Stas Grushetsky, s.grushetsky@gmail.com, Mercer Island High School.

**Track:** Climate

**Starting point:** Suggested project 4.3.2, Next-day air quality forecast

**One-sentence pitch:**
SmokeCheck tells a Pacific Northwest athletic director the night before whether wildfire smoke will make tomorrow's practice unsafe, and it catches the first day of smoke about twice as often as "tomorrow = today".

**Code link:** https://github.com/DenisLazerko/vibesgpt/edit/main

**Write-up link:** [GITHUB README LINK, after publishing]

**What we added:**
We built the forecast for one user and one decision: an athletic director deciding at night whether tomorrow's practice moves inside. We count a missed smoke day as three times worse than an unneeded indoor practice. Instead of one station we used 55 EPA monitors in 20 cities, and the model reads smoke in nearby and upwind cities, since smoke usually reaches them first. We then asked four questions the brief doesn't:
- Does it catch the first day of smoke? Yes, 31 of 83, versus 16 for "tomorrow = today".
- Does it beat the official CAMS forecast? It warns on more smoke days (99 vs 62) but has more false alarms.
- Does it work in four cities it never trained on? Yes, about as well as elsewhere.
- How much does it lose with real weather forecasts instead of actual weather? A little, and on 2024-2025 it no longer beats "tomorrow = today" on our cost score.

**Datasets, models and AI tools used:**
EPA AirData daily PM2.5 (https://aqs.epa.gov/aqsweb/airdata/download_files.html); Open-Meteo Historical Weather (ERA5), Previous Runs and Air Quality (CAMS) APIs (https://open-meteo.com); scikit-learn HistGradientBoostingRegressor and Ridge; pandas, NumPy, Matplotlib, Gradio; Claude (Anthropic) via Claude Code, which helped write the code and first drafts of the text.

**New to AI?** No.
