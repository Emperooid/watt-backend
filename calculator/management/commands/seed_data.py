from django.core.management.base import BaseCommand
from django.db import transaction

from calculator.models import Appliance, ApplianceCategory, Disco, TariffBand

# The 11 electricity distribution companies (Discos) licensed by NERC, with
# their coverage areas.
DISCOS = [
    ("AEDC", "Abuja Electricity Distribution Company", "FCT, Niger, Kogi, Nasarawa"),
    ("BEDC", "Benin Electricity Distribution Company", "Edo, Delta, Ondo, Ekiti"),
    ("EKEDC", "Eko Electricity Distribution Company", "Southern Lagos, Agbara"),
    ("EEDC", "Enugu Electricity Distribution Company", "Enugu, Anambra, Ebonyi, Abia, Imo"),
    ("IBEDC", "Ibadan Electricity Distribution Company", "Oyo, Ogun, Osun, Kwara, parts of Niger, Ekiti, Kogi"),
    ("IE", "Ikeja Electric", "Northern Lagos"),
    ("JED", "Jos Electricity Distribution Company", "Plateau, Bauchi, Benue, Gombe"),
    ("KAEDCO", "Kaduna Electricity Distribution Company", "Kaduna, Kebbi, Sokoto, Zamfara"),
    ("KEDCO", "Kano Electricity Distribution Company", "Kano, Katsina, Jigawa"),
    ("PHED", "Port Harcourt Electricity Distribution Company", "Rivers, Bayelsa, Cross River, Akwa Ibom"),
    ("YEDC", "Yola Electricity Distribution Company", "Adamawa, Borno, Taraba, Yobe"),
]

# Real NERC MYTO band structure, "Jul 2024 - Jun 2026" column of the
# official Approved Allowed Tariffs (₦/kWh) table (nerc.gov.ng/resource-category/myto).
# Per NERC's MYTO order, these Non-MD/MD1/MD2 rates are the same nationally
# across every Disco for a given band, so a single table applies to all 11.
# band -> (min_hours_supply, non_md_rate, md1_rate, md2_rate).
NATIONAL_BANDS = {
    "A": (20, 209.50, 209.50, 209.50),
    "B": (16, 62.48, 63.17, 69.75),
    "C": (12, 45.80, 50.03, 53.41),
    "D": (8, 31.24, 45.29, 45.29),
    "E": (4, 31.24, 45.29, 45.29),
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
        for code, name, coverage in DISCOS:
            disco, _ = Disco.objects.update_or_create(
                code=code, defaults={"name": name, "coverage": coverage, "is_verified": True}
            )
            for band, (min_hours, non_md, md1, md2) in NATIONAL_BANDS.items():
                TariffBand.objects.update_or_create(
                    disco=disco,
                    band=band,
                    defaults={
                        "non_md_rate": non_md,
                        "md1_rate": md1,
                        "md2_rate": md2,
                        "min_hours_supply": min_hours,
                    },
                )
        valid_codes = {code for code, _, _ in DISCOS}
        stale, _ = Disco.objects.exclude(code__in=valid_codes).delete()
        if stale:
            self.stdout.write(self.style.WARNING(f"Removed {stale} stale Disco/tariff row(s) no longer in the list."))

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(DISCOS)} Discos with 5 tariff bands each."))

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
