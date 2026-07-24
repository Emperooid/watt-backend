from rest_framework import serializers

from .models import Appliance, CustomerType, Disco, TariffBand


class TariffBandSerializer(serializers.ModelSerializer):
    class Meta:
        model = TariffBand
        fields = ["band", "non_md_rate", "md1_rate", "md2_rate", "min_hours_supply"]


class DiscoSerializer(serializers.ModelSerializer):
    tariff_bands = TariffBandSerializer(many=True, read_only=True)

    class Meta:
        model = Disco
        fields = ["id", "code", "name", "is_verified", "tariff_bands"]


class ApplianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appliance
        fields = [
            "id",
            "name",
            "default_watts",
            "category",
            "icon",
            "has_inverter_alternative",
            "inverter_savings_pct",
        ]


class CalculationItemSerializer(serializers.Serializer):
    appliance_id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    watts = serializers.FloatField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)
    hours_per_day = serializers.FloatField(min_value=0, max_value=24)

    def validate(self, attrs):
        if not attrs.get("appliance_id") and not attrs.get("name"):
            raise serializers.ValidationError("Each item needs either appliance_id or a custom name.")
        return attrs


class CalculationRequestSerializer(serializers.Serializer):
    disco_id = serializers.IntegerField()
    band = serializers.ChoiceField(choices=[c[0] for c in TariffBand.BAND_CHOICES])
    customer_type = serializers.ChoiceField(choices=CustomerType.values, default=CustomerType.NON_MD)
    scenario = serializers.ChoiceField(choices=["good", "bad"], default="good")
    items = CalculationItemSerializer(many=True)
