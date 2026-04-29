# API Endpoints

Base URL: `${VITE_API_SITE}` — e.g. `http://localhost:8000/api` locally, or `https://<your-eb-app>.<region>.elasticbeanstalk.com/api` in prod.

All responses are JSON. Successful responses follow the shape:

```json
{ "items": [...], "meta": { "count": 123, "...": "..." } }
```

Errors:

```json
{ "detail": "Postcode must be 4 digits" }
```

---

## Healthcheck

### `GET /` and `GET /api/health`
Returns service status. Used by the EB load balancer.

```json
{ "status": "ok" }
```

---

## Health data

### `GET /api/health/all`
Returns merged cancer + mortality rows.

Optional query params:
- `year` — integer, e.g. `2018`
- `sex` — `males`, `females`, `persons`
- `cancer_type` — exact match, e.g. `Lung cancer`

Example: `/api/health/all?year=2018&sex=females`

Response item shape:
```json
{
  "year": 2018,
  "sex": "females",
  "cancer_type": "Lung cancer",
  "cancer_cases": 4567,
  "cancer_deaths": 3200,
  "fatality_ratio": 0.7
}
```

### `GET /api/health/filters`
Returns the distinct values available for the three filter fields.

```json
{ "items": { "years": [...], "sexes": [...], "cancer_types": [...] } }
```

---

## Emissions

### `GET /api/emissions/state`
Heavy-metal emissions aggregated by state, year, and metal.

```json
{
  "report_year": 2022,
  "state": "NSW",
  "metal": "Lead & compounds",
  "total_air_emission_kg": 1234.5,
  "total_water_emission_kg": 56.7,
  "total_land_emission_kg": 0,
  "facility_count": 14
}
```

### `GET /api/emissions/facility`
Per-facility rows with lat/lng (only rows with coordinates are returned).

---

## Disposal locations

### `GET /api/map/disposal-locations`
All verified e-waste drop-off facilities with coordinates.

```json
{
  "facility_name": "ASHFORD RURAL TRANSFER STATION",
  "address": "159 LIMESTONE ROAD",
  "suburb": "ASHFORD",
  "postcode": "2361",
  "state": "NSW",
  "latitude": -29.32,
  "longitude": 151.09,
  "coord_source": "maptiler_other",
  "verified": true
}
```

### `GET /api/map/disposal-locations/<postcode>`
Facilities for a 4-digit Australian postcode. Returns `400` if the postcode isn't 4 digits.

---

## AI device optimizer

### `POST /api/ai/device-optimizer`

Request body:
```json
{ "device_type": "phone", "issue_text": "battery drains in 2 hours" }
```

Response:
```json
{
  "device_type": "phone",
  "device_label": "Phone",
  "issue_category": "battery_drain",
  "issue_label": "Battery drain",
  "issue_explanation": "...",
  "suggestions": ["...", "...", "...", "..."],
  "model": "rule-based-v1"
}
```

`device_type` must be `phone` or `laptop`. `issue_text` cannot be empty.
