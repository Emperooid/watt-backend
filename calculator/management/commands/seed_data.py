from django.core.management.base import BaseCommand
from django.db import transaction

from calculator.models import Appliance, ApplianceCategory, Disco, TariffBand

DISCOS = [
    ("EKEDC", "Eko Electricity Distribution Company"),
    ("IKEDC", "Ikeja Electric"),
    ("AEDC", "Abuja Electricity Distribution Company"),
    ("IBEDC", "Ibadan Electricity Distribution Company"),
    ("EEDC", "Enugu Electricity Distribution Company"),
    ("KEDCO", "Kano Electricity Distribution Company"),
    ("BEDC", "Benin Electricity Distribution Company"),
    ("JED", "Jos Electricity Distribution"),
    ("PHED", "Port Harcourt Electricity Distribution Company"),
    ("YEDC", "Yola Electricity Distribution Company"),
]

# Approximate, nationally-representative NERC band rates (₦/kWh) and their
# guaranteed minimum daily supply hours. Real per-Disco rates vary slightly;
# these are placeholder estimates for a "quick calculator", not billing data.
BAND_RATES = {
    "A": (225.00, 20),
    "B": (209.50, 16),
    "C": (160.00, 12),
    "D": (110.00, 8),
    "E": (75.00, 4),
}

APPLIANCES = [
    ("Standing Fan", 75, ApplianceCategory.COOLING, "fan", True, 30),
    ("Ceiling Fan", 70, ApplianceCategory.COOLING, "fan", True, 30),
    ("Refrigerator (Single Door)", 150, ApplianceCategory.KITCHEN, "fridge", True, 35),
    ("Deep Freezer", 200, ApplianceCategory.KITCHEN, "freezer", True, 35),
    ("Air Conditioner (1.5HP)", 1200, ApplianceCategory.COOLING, "ac", True, 35),
    ("Television (LED)", 100, ApplianceCategory.ELECTRONICS, "tv", False, 0),
    ("Iron", 1000, ApplianceCategory.OTHER, "iron", False, 0),
    ("Blender", 400, ApplianceCategory.KITCHEN, "blender", False, 0),
    ("Water Pump (0.5HP)", 750, ApplianceCategory.WATER, "pump", False, 0),
    ("Washing Machine", 500, ApplianceCategory.LAUNDRY, "washer", True, 25),
    ("Laptop", 65, ApplianceCategory.ELECTRONICS, "laptop", False, 0),
    ("Desktop Computer", 200, ApplianceCategory.ELECTRONICS, "desktop", False, 0),
    ("Microwave", 1000, ApplianceCategory.KITCHEN, "microwave", False, 0),
    ("Electric Kettle", 1500, ApplianceCategory.KITCHEN, "kettle", False, 0),
    ("Cooker (Electric Ignition)", 100, ApplianceCategory.KITCHEN, "cooker", False, 0),
    ("Electric Stove", 1500, ApplianceCategory.KITCHEN, "stove", False, 0),
    ("Router", 10, ApplianceCategory.ELECTRONICS, "router", False, 0),
    ("LED Bulb (20W)", 20, ApplianceCategory.LIGHTING, "bulb", False, 0),
]


class Command(BaseCommand):
    help = "Seed Discos, tariff bands, and the appliance library."

    @transaction.atomic
    def handle(self, *args, **options):
        for code, name in DISCOS:
            disco, _ = Disco.objects.update_or_create(code=code, defaults={"name": name})
            for band, (rate, min_hours) in BAND_RATES.items():
                TariffBand.objects.update_or_create(
                    disco=disco,
                    band=band,
                    defaults={"rate_per_kwh": rate, "min_hours_supply": min_hours},
                )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(DISCOS)} Discos with {len(BAND_RATES)} tariff bands each."))

        for name, watts, category, icon, has_inverter, savings_pct in APPLIANCES:
            Appliance.objects.update_or_create(
                name=name,
                defaults={
                    "default_watts": watts,
                    "category": category,
                    "icon": icon,
                    "has_inverter_alternative": has_inverter,
                    "inverter_savings_pct": savings_pct,
                },
            )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(APPLIANCES)} appliances."))
