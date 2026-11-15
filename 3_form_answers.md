<!-- DRAFT 3 for your approval. Answers for the Airtable submission form. -->

**Project title:** SmokeCheck

**Building as:** Team

**Team name:** vibesgpt

**Team members:** Denis Lazerko, lazerko.den@gmail.com, Lake Washington High School; [Stas fill in]

**Track:** Climate

**Starting point:** Suggested project 4.3.2, Next-day air quality forecast

**One-sentence pitch:**
SmokeCheck tells a Pacific Northwest athletic director the night before whether wildfire smoke will make tomorrow's practice unsafe, and it catches the first day of smoke about twice as often as "tomorrow = today".

**Code link:** [GitHub notebook link, after we publish]

**Write-up link:** [GitHub README link, after we publish]

**Demo video link:** [YouTube unlisted link]

**What we added:**
We built the forecast for one user and one decision: an athletic director deciding at night whether tomorrow's practice moves inside. We count a missed smoke day as three times worse than an unneeded indoor practice. Instead of one station we used 55 EPA monitors in 20 cities, and the model reads smoke in nearby and upwind cities, since smoke usually reaches them first. We then asked four questions the brief doesn't: does it catch the first day of smoke (31 of 83 vs 16 for "tomorrow = today"), does it beat the official CAMS forecast (more smoke days warned, more false alarms), does it work in four cities it never trained on (yes, about as well), and how much does it lose with real weather forecasts instead of actual weather (a little, and on 2024-2025 it no longer beats "tomorrow = today" on our cost score).

**Datasets, models and AI tools used:**
EPA AirData daily PM2.5 (https://aqs.epa.gov/aqsweb/airdata/download_files.html); Open-Meteo Historical Weather (ERA5), Previous Runs and Air Quality (CAMS) APIs (https://open-meteo.com); scikit-learn HistGradientBoostingRegressor and Ridge; pandas, NumPy, Matplotlib, Gradio; Claude (Anthropic) via Claude Code, which helped write the code and first drafts of the text.

**New to AI?** [your answer]
