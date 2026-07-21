"""Pure calculation logic for the electricity cost calculator.

Kept free of Django ORM/request concerns so it stays easy to unit test.
"""

from dataclasses import dataclass, field
from decimal import Decimal

DAYS_PER_MONTH = 30
MONTHS_PER_YEAR = 12

# Grid supply is rarely 100% reliable. "Bad day" scenario approximates a
# household getting a fraction of its usual hours due to outages. This is a
# rough placeholder multiplier, not a measured statistic.
BAD_DAY_HOURS_FACTOR = 0.3

# Rough benchmark used only for the "% of average household bill" insight.
# Placeholder until real survey data is available.
AVERAGE_HOUSEHOLD_MONTHLY_BILL = 25000


@dataclass
class LineItem:
    name: str
    watts: float
    quantity: int
    hours_per_day: float
    has_inverter_alternative: bool = False
    inverter_savings_pct: int = 0

    effective_hours: float = field(init=False, default=0.0)
    kwh_per_day: float = field(init=False, default=0.0)
    cost_per_day: float = field(init=False, default=0.0)


def calculate(*, rate_per_kwh: Decimal, scenario: str, raw_items: list[dict], appliance_lookup: dict) -> dict:
    factor = 1.0 if scenario == "good" else BAD_DAY_HOURS_FACTOR
    rate = float(rate_per_kwh)

    items: list[LineItem] = []
    for raw in raw_items:
        appliance = appliance_lookup.get(raw.get("appliance_id"))
        name = appliance.name if appliance else (raw.get("name") or "Custom Appliance")
        line = LineItem(
            name=name,
            watts=float(raw["watts"]),
            quantity=int(raw["quantity"]),
            hours_per_day=float(raw["hours_per_day"]),
            has_inverter_alternative=bool(appliance.has_inverter_alternative) if appliance else False,
            inverter_savings_pct=int(appliance.inverter_savings_pct) if appliance else 0,
        )
        line.effective_hours = line.hours_per_day * factor
        line.kwh_per_day = (line.watts * line.quantity * line.effective_hours) / 1000
        line.cost_per_day = line.kwh_per_day * rate
        items.append(line)

    daily_kwh = sum(i.kwh_per_day for i in items)
    daily_cost = sum(i.cost_per_day for i in items)
    monthly_kwh = daily_kwh * DAYS_PER_MONTH
    monthly_cost = daily_cost * DAYS_PER_MONTH
    yearly_cost = monthly_cost * MONTHS_PER_YEAR

    ranking = []
    if daily_kwh > 0:
        for i in sorted(items, key=lambda x: x.kwh_per_day, reverse=True):
            ranking.append({
                "name": i.name,
                "kwh_per_day": round(i.kwh_per_day, 3),
                "share_pct": round((i.kwh_per_day / daily_kwh) * 100, 1),
            })

    insights = _build_insights(items, rate)

    return {
        "scenario": scenario,
        "rate_per_kwh": rate,
        "items": [
            {
                "name": i.name,
                "watts": i.watts,
                "quantity": i.quantity,
                "hours_per_day": i.hours_per_day,
                "effective_hours": round(i.effective_hours, 2),
                "kwh_per_day": round(i.kwh_per_day, 3),
                "cost_per_day": round(i.cost_per_day, 2),
            }
            for i in items
        ],
        "totals": {
            "daily_kwh": round(daily_kwh, 3),
            "daily_cost": round(daily_cost, 2),
            "monthly_kwh": round(monthly_kwh, 2),
            "monthly_cost": round(monthly_cost, 2),
            "yearly_cost": round(yearly_cost, 2),
        },
        "ranking": ranking,
        "insights": insights,
    }


def _build_insights(items: list[LineItem], rate: float) -> list[str]:
    if not items:
        return []

    top = max(items, key=lambda x: x.kwh_per_day)
    insights = []

    eight_hour_monthly_cost = (top.watts * top.quantity * 8 / 1000) * rate * DAYS_PER_MONTH
    insights.append(
        f"Running {top.name.lower()} for 8 hours every day could cost approximately "
        f"₦{eight_hour_monthly_cost:,.0f} every month."
    )

    monthly_cost = top.cost_per_day * DAYS_PER_MONTH
    if monthly_cost > 0:
        share_of_average = min((monthly_cost / AVERAGE_HOUSEHOLD_MONTHLY_BILL) * 100, 100)
        insights.append(
            f"{top.name} accounts for approximately {share_of_average:.0f}% of the average "
            "household electricity bill."
        )

    if top.has_inverter_alternative and top.inverter_savings_pct:
        insights.append(
            f"Replacing this with an inverter model could save up to {top.inverter_savings_pct}%."
        )

    return insights
