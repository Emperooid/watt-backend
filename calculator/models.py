from django.db import models


class Disco(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    is_verified = models.BooleanField(
        default=False,
        help_text="True once this Disco's tariff table has been checked against an official NERC/Disco source",
    )

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class CustomerType(models.TextChoices):
    NON_MD = "non_md", "Non-MD (Residential / most homes & small businesses)"
    MD1 = "md1", "MD1 (Maximum Demand 1 — larger commercial)"
    MD2 = "md2", "MD2 (Maximum Demand 2 — industrial)"


class TariffBand(models.Model):
    BAND_CHOICES = [
        ("A", "Band A"),
        ("B", "Band B"),
        ("C", "Band C"),
        ("D", "Band D"),
        ("E", "Band E"),
    ]

    disco = models.ForeignKey(Disco, related_name="tariff_bands", on_delete=models.CASCADE)
    band = models.CharField(max_length=1, choices=BAND_CHOICES)
    non_md_rate = models.DecimalField(max_digits=8, decimal_places=2, help_text="₦/kWh for Non-MD (residential) customers")
    md1_rate = models.DecimalField(max_digits=8, decimal_places=2, help_text="₦/kWh for MD1 customers")
    md2_rate = models.DecimalField(max_digits=8, decimal_places=2, help_text="₦/kWh for MD2 customers")
    min_hours_supply = models.PositiveSmallIntegerField(
        help_text="NERC-guaranteed minimum average hours of daily supply for this band"
    )

    class Meta:
        unique_together = ("disco", "band")
        ordering = ["disco", "band"]

    def __str__(self):
        return f"{self.disco.code} - Band {self.band}"

    def rate_for(self, customer_type: str):
        return getattr(self, f"{customer_type}_rate")


class ApplianceCategory(models.TextChoices):
    COOLING = "cooling", "Cooling"
    KITCHEN = "kitchen", "Kitchen"
    LAUNDRY = "laundry", "Laundry"
    ELECTRONICS = "electronics", "Electronics"
    LIGHTING = "lighting", "Lighting"
    WATER = "water", "Water"
    OTHER = "other", "Other"


class Appliance(models.Model):
    name = models.CharField(max_length=100, unique=True)
    default_watts = models.PositiveIntegerField()
    category = models.CharField(max_length=20, choices=ApplianceCategory.choices, default=ApplianceCategory.OTHER)
    icon = models.CharField(max_length=40, blank=True, help_text="Icon slug used by the frontend")
    has_inverter_alternative = models.BooleanField(default=False)
    inverter_savings_pct = models.PositiveSmallIntegerField(
        default=0, help_text="Approx. % savings if switched to an inverter/energy-efficient model"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
