# WattAmIUsing / PowerWise — Backend

Django + Django REST Framework API for the electricity cost calculator.

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_data     # loads Discos, tariff bands, appliance library
python manage.py runserver 8000
```

## API

- `GET /api/discos/` — list of Discos with their tariff bands (A–E, ₦/kWh)
- `GET /api/appliances/` — appliance library with default wattage
- `POST /api/calculate/` — body:
  ```json
  {
    "disco_id": 1,
    "band": "B",
    "scenario": "good",
    "items": [
      {"appliance_id": 1, "watts": 75, "quantity": 2, "hours_per_day": 8},
      {"name": "Custom Appliance", "watts": 300, "quantity": 1, "hours_per_day": 2}
    ]
  }
  ```
  Returns per-item breakdown, daily/monthly/yearly totals, a consumption ranking, and bonus insights.

Tariff rates in `calculator/management/commands/seed_data.py` are approximate,
nationally-representative placeholders — not official per-Disco billing data.

## Database

Defaults to local SQLite. Set `DATABASE_URL` in `.env` (e.g. a Postgres URL) to
switch — no code changes needed.
