from rest_framework import serializers
from .models import Waybill


class WaybillSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Waybill
        fields = [
            "id",
            "external_id",
            "date",
            "address",
            "recipient_name",
            "phone",
            "comment",
            "status",
            "status_display",
            "priority_order",
        ]