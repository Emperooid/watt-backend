import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import paystack
from .email import send_report_email
from .models import Appliance, Disco, PdfReportOrder, TariffBand, WaitlistSignup
from .pdf import generate_report_pdf
from .serializers import (
    ApplianceSerializer,
    CalculationRequestSerializer,
    DiscoSerializer,
    PdfReportOrderSerializer,
    ReportInitiateSerializer,
    WaitlistSignupSerializer,
)
from .services import calculate

REPORT_PRICE_KOBO = 200_000  # NGN 2,000


def _run_calculation(data: dict) -> dict:
    """Shared by /calculate/ and the report flow so a report is always
    regenerated from the same trusted logic, not whatever the client sends
    after checkout."""
    tariff = TariffBand.objects.select_related("disco").get(disco_id=data["disco_id"], band=data["band"])

    appliance_ids = [i["appliance_id"] for i in data["items"] if i.get("appliance_id")]
    appliance_lookup = {a.id: a for a in Appliance.objects.filter(id__in=appliance_ids)}

    result = calculate(
        rate_per_kwh=tariff.rate_for(data["customer_type"]),
        scenario=data["scenario"],
        raw_items=data["items"],
        appliance_lookup=appliance_lookup,
    )
    result["disco"] = tariff.disco.code
    result["band"] = tariff.band
    result["customer_type"] = data["customer_type"]
    return result, tariff.disco.name


class DiscoListView(generics.ListAPIView):
    queryset = Disco.objects.prefetch_related("tariff_bands").all()
    serializer_class = DiscoSerializer


class ApplianceListView(generics.ListAPIView):
    queryset = Appliance.objects.all()
    serializer_class = ApplianceSerializer


class CalculateView(APIView):
    def post(self, request):
        request_serializer = CalculationRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        try:
            result, _disco_name = _run_calculation(data)
        except TariffBand.DoesNotExist:
            return Response(
                {"detail": "No tariff found for that Disco/band combination."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(result)


class WaitlistView(APIView):
    def get(self, request):
        return Response({"count": WaitlistSignup.objects.count()})

    def post(self, request):
        serializer = WaitlistSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        _, created = WaitlistSignup.objects.get_or_create(email=email)
        return Response(
            {"count": WaitlistSignup.objects.count(), "already_joined": not created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


def _fulfill_order(order: PdfReportOrder) -> None:
    """Mark an order paid and email the PDF, if not already done. Safe to
    call more than once (e.g. from both the callback verify and the
    webhook) — only sends one email."""
    if order.status != PdfReportOrder.STATUS_PAID:
        order.status = PdfReportOrder.STATUS_PAID
        order.paid_at = datetime.now(dt_timezone.utc)
        order.save(update_fields=["status", "paid_at"])

    if order.report_sent:
        return

    data = order.planner_state
    result, disco_name = _run_calculation(data)
    pdf_bytes = generate_report_pdf(
        result=result,
        disco_name=disco_name,
        band=data["band"],
        customer_type=data["customer_type"],
        scenario=data["scenario"],
    )
    send_report_email(to_email=order.email, pdf_bytes=pdf_bytes)
    order.report_sent = True
    order.save(update_fields=["report_sent"])


class ReportInitiateView(APIView):
    """Start a paid PDF report order: validates the calculation inputs,
    creates a pending order, and returns a Paystack hosted checkout URL."""

    def post(self, request):
        serializer = ReportInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Fail fast on a bad Disco/band before sending anyone to checkout.
        try:
            TariffBand.objects.get(disco_id=data["disco_id"], band=data["band"])
        except TariffBand.DoesNotExist:
            return Response(
                {"detail": "No tariff found for that Disco/band combination."},
                status=status.HTTP_404_NOT_FOUND,
            )

        email = data.pop("email")
        reference = f"wau_{secrets.token_hex(12)}"
        order = PdfReportOrder.objects.create(
            email=email,
            reference=reference,
            amount_kobo=REPORT_PRICE_KOBO,
            planner_state=data,
        )

        callback_url = f"{settings.FRONTEND_URL.rstrip('/')}/planner/report-status?reference={reference}"
        try:
            paystack_data = paystack.initialize_transaction(
                email=email,
                amount_kobo=REPORT_PRICE_KOBO,
                reference=reference,
                callback_url=callback_url,
            )
        except paystack.PaystackError as err:
            order.status = PdfReportOrder.STATUS_FAILED
            order.save(update_fields=["status"])
            return Response({"detail": str(err)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(
            {"authorization_url": paystack_data["authorization_url"], "reference": reference},
            status=status.HTTP_201_CREATED,
        )


class ReportVerifyView(APIView):
    """Polled by the frontend's /planner/report-status page after the user
    is redirected back from Paystack checkout."""

    def get(self, request, reference: str):
        try:
            order = PdfReportOrder.objects.get(reference=reference)
        except PdfReportOrder.DoesNotExist:
            return Response({"detail": "Unknown reference."}, status=status.HTTP_404_NOT_FOUND)

        if order.status == PdfReportOrder.STATUS_PAID:
            return Response(PdfReportOrderSerializer(order).data)

        try:
            paystack_data = paystack.verify_transaction(reference)
        except paystack.PaystackError as err:
            return Response({"detail": str(err)}, status=status.HTTP_502_BAD_GATEWAY)

        if paystack_data.get("status") == "success" and paystack_data.get("amount") == order.amount_kobo:
            _fulfill_order(order)
        else:
            order.status = PdfReportOrder.STATUS_FAILED
            order.save(update_fields=["status"])

        return Response(PdfReportOrderSerializer(order).data)


class ReportWebhookView(APIView):
    """Paystack webhook — the reliable source of truth in case the user
    closes the tab before the callback redirect fires."""

    def post(self, request):
        signature = request.headers.get("x-paystack-signature", "")
        expected = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode(), request.body, hashlib.sha512
        ).hexdigest()
        if not settings.PAYSTACK_SECRET_KEY or not hmac.compare_digest(signature, expected):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        event = json.loads(request.body)
        if event.get("event") == "charge.success":
            reference = event["data"]["reference"]
            try:
                order = PdfReportOrder.objects.get(reference=reference)
            except PdfReportOrder.DoesNotExist:
                return Response(status=status.HTTP_200_OK)

            if event["data"].get("amount") == order.amount_kobo:
                _fulfill_order(order)

        return Response(status=status.HTTP_200_OK)
