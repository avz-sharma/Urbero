# ADR 0002: WAQI ground observations with explicit CAMS model fallback

The user's 2026-11-23 audit request supersedes ADR 0001's OpenAQ-only provider scope. The pure Python core and schema-driven API remain unchanged in principle.

1. WAQI geo feeds are accepted only with CPCB attribution, PM2.5, valid station coordinates, a timestamp no older than three hours, and distance within 25 km. CPCB attribution does not establish reference-grade hardware; that field remains unknown.
2. WAQI `iaqi` fields are indices. Only particulate indices are inverted using the published WAQI 2012 US-EPA scale. Reconstruction is approximate, is included in card math inputs, and cannot recover original precision or averaging. Gas indices are not passed off as concentrations or mixed with CAMS values to manufacture a valid overall AQI. With fewer than three pollutants, CPCB overall AQI stays invalid; available sub-indices remain visible.
3. Open-Meteo CAMS supplies hourly model history (`past_days=3`) and a current hourly fallback. This is archived model output, **not empirical station history**. The exact source is `Open-Meteo CAMS (Modelled)` and the current status is `modelled_live`. Model confidence is capped Low. CO is normalized from µg/m³ to mg/m³.
4. Failed WAQI -> CAMS -> actual cached stale data -> generic 503. No fabricated station baseline, no synthetic smog curve, no zero-filled missing pollutant. Original observation timestamps and model provenance survive stale fallback.
5. Thirty-minute caches and single-flight coalescing use two-decimal coordinates. Station distance is recomputed using the requesting coordinates; raw coordinates and query-token URLs are excluded from application logs. Supabase stores only grid keys and provider readings.
6. The landing page does not fetch a plan. Workspace entry requires GPS, a search result, or an explicit city-chip selection. Household presets start unselected and contain profile assumptions, not location commands.

Specifications: [WAQI API](https://aqicn.org/api/), [WAQI particulate scale](https://aqicn.org/faq/2013-09-09/revised-pm25-aqi-breakpoints/), [Open-Meteo air quality](https://open-meteo.com/en/docs/air-quality-api).

`VERIFY_BEFORE_PROD`: confirm the deployed WAQI feed's breakpoint version and its usage terms for the intended cache/deployment; validate the deployment token. Providers do not expose enough information to certify reconstructed values as official averaged CPCB AQI. Breathing, infiltration, mode and sizing assumptions require local calibration; the UI labels these estimates.
