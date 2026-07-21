from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Appliance, Disco, TariffBand
from .serializers import ApplianceSerializer, CalculationRequestSerializer, DiscoSerializer
from .services import calculate


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
            tariff = TariffBand.objects.select_related("disco").get(
                disco_id=data["disco_id"], band=data["band"]
            )
        except TariffBand.DoesNotExist:
            return Response(
                {"detail": "No tariff found for that Disco/band combination."},
                status=status.HTTP_404_NOT_FOUND,
            )

        appliance_ids = [i["appliance_id"] for i in data["items"] if i.get("appliance_id")]
        appliance_lookup = {a.id: a for a in Appliance.objects.filter(id__in=appliance_ids)}

        result = calculate(
            rate_per_kwh=tariff.rate_per_kwh,
            scenario=data["scenario"],
            raw_items=data["items"],
            appliance_lookup=appliance_lookup,
        )
        result["disco"] = tariff.disco.code
        result["band"] = tariff.band
        return Response(result)
