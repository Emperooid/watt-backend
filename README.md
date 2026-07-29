# WattAmIUsing — Backend

Django + Django REST Framework API powering [WattAmIUsing](https://watt-frontend.vercel.app/), a free tool
that helps Nigerians estimate how much their appliances cost to run on their local electricity tariff.

Live API: https://watt-backend-qin8.onrender.com/api/

## Stack

- Python 3.11, Django 5.2, Django REST Framework
- PostgreSQL in production (Neon), SQLite for local dev if `DATABASE_URL` is unset
- `django-cors-headers` for CORS, `gunicorn` as the production WSGI server

## Local setup

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; use .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env          # then fill in values, see below
python manage.py migrate
python manage.py seed_data    # seeds Discos, tariff bands, and the appliance library
python manage.py runserver
```

The API is then available at `http://localhost:8000/api/`.

## Environment variables

See `.env.example` for the full list. Notable ones:

- `DATABASE_URL` — leave unset to use local SQLite; set to a Postgres URL to use Postgres (the format
  `dj-database-url` expects, e.g. `postgresql://user:pass@host/db?sslmode=require`).
- `DEBUG` — defaults to `False` if unset. Set to `True` for local development (already done in
  `.env.example`).
- `ALLOWED_HOSTS` — comma-separated. Render's own hostname is picked up automatically via its
  `RENDER_EXTERNAL_HOSTNAME` env var, so you don't need to set this for Render specifically.
- `CORS_ALLOWED_ORIGINS` — comma-separated frontend origins allowed to call the API. Defaults already
  cover `http://localhost:3000` and the deployed Vercel URL; any `*.vercel.app` preview deployment and any
  `localhost`/`127.0.0.1` port are allowed automatically in debug mode.

## Key endpoints

| Method | Path               | Description                                                                                                                     |
| ------ | ------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| GET    | `/api/discos/`      | List of Discos with their tariff bands (Non-MD/MD1/MD2 rates)                                                                    |
| GET    | `/api/appliances/`  | Appliance library with default wattage and category                                                                              |
| POST   | `/api/calculate/`   | Given a Disco/band/customer type and a list of appliances, returns cost breakdown, generator-vs-grid comparison, and insights |
| GET    | `/api/waitlist/`    | Current waitlist signup count                                                                                                    |
| POST   | `/api/waitlist/`    | Join the Version 2 waitlist with an email                                                                                        |

Example `POST /api/calculate/` body:

```json
{
  "disco_id": 1,
  "band": "B",
  "customer_type": "non_md",
  "scenario": "good",
  "items": [
    { "appliance_id": 1, "watts": 75, "quantity": 2, "hours_per_day": 8 },
    { "name": "Custom Appliance", "watts": 300, "quantity": 1, "hours_per_day": 2 }
  ]
}
```

## Data notes

- Tariff rates are seeded via `python manage.py seed_data` (see `calculator/management/commands/seed_data.py`).
  Only Ikeja Electric (`IE`) currently has NERC-verified rates (`Disco.is_verified=True`); the other 10
  Discos use placeholder estimates until real tariff tables are supplied — update `VERIFIED_BANDS` in that
  file as more come in.
- Re-running `seed_data` also removes any Disco no longer in the list, so renaming/removing a Disco code is
  safe to do there.

## Deployment (Render)

- Build command: `pip install -r requirements.txt && python manage.py migrate`
- Start command: `gunicorn config.wsgi`
- Required environment variables: `DATABASE_URL`, `SECRET_KEY`, `DEBUG=False`, `CORS_ALLOWED_ORIGINS`,
  `ALLOWED_HOSTS` (see `.env.render`, gitignored, for the exact values used for this project's deployment).

## Workflow

Work happens on `dev` and gets merged into `main` (the branch Render deploys from) once verified locally.
