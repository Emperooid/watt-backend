from django.contrib import admin

from .models import Appliance, Disco, TariffBand


class TariffBandInline(admin.TabularInline):
    model = TariffBand
    extra = 0


@admin.register(Disco)
class DiscoAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    inlines = [TariffBandInline]


@admin.register(Appliance)
class ApplianceAdmin(admin.ModelAdmin):
    list_display = ("name", "default_watts", "category", "has_inverter_alternative", "inverter_savings_pct")
    list_filter = ("category", "has_inverter_alternative")
    search_fields = ("name",)
