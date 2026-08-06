from django.urls import path

from .views import (
    ApplianceListView,
    CalculateView,
    DiscoListView,
    ReportInitiateView,
    ReportVerifyView,
    ReportWebhookView,
    WaitlistView,
)

urlpatterns = [
    path("discos/", DiscoListView.as_view(), name="disco-list"),
    path("appliances/", ApplianceListView.as_view(), name="appliance-list"),
    path("calculate/", CalculateView.as_view(), name="calculate"),
    path("waitlist/", WaitlistView.as_view(), name="waitlist"),
    path("reports/initiate/", ReportInitiateView.as_view(), name="report-initiate"),
    path("reports/verify/<str:reference>/", ReportVerifyView.as_view(), name="report-verify"),
    path("reports/webhook/", ReportWebhookView.as_view(), name="report-webhook"),
]
