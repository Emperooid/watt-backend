from django.contrib import admin

from .models import Appliance, Disco, PdfReportOrder, TariffBand, WaitlistSignup


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


@admin.register(WaitlistSignup)
class WaitlistSignupAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at")
    search_fields = ("email",)
    ordering = ("-created_at",)


@admin.register(PdfReportOrder)
class PdfReportOrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "email", "status", "report_sent", "created_at", "paid_at")
    list_filter = ("status", "report_sent")
    search_fields = ("email", "reference")
    ordering = ("-created_at",)
    readonly_fields = ("reference", "amount_kobo", "planner_state", "created_at", "paid_at")
