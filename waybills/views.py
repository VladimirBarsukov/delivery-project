from datetime import date

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Waybill
from .serializers import WaybillSerializer

from django.shortcuts import render

from django.contrib.auth.decorators import login_required

from rest_framework.permissions import IsAuthenticated


class TodayWaybillList(APIView):
    """GET /api/waybills/today/ — накладные на сегодня и незавершённые с прошлых дней."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()
        waybills = Waybill.objects.filter(
            date__lte=today,            # дата сегодня или раньше
        ).exclude(
            status="delivered"          # исключаем доставленные
        ).order_by("priority_order", "date")
        serializer = WaybillSerializer(waybills, many=True)
        return Response(serializer.data)
    
class UpdateStatus(APIView):
    """PATCH /api/waybills/<id>/status/ — сменить статус накладной."""
    permission_classes = [IsAuthenticated]

    # Допустимые переходы: откуда → куда можно
    ALLOWED_TRANSITIONS = {
        "ready": ["on_route"],
        "on_route": ["delivered"],
    }

    def patch(self, request, waybill_id):
        try:
            waybill = Waybill.objects.get(id=waybill_id)
        except Waybill.DoesNotExist:
            return Response(
                {"error": "Накладная не найдена"},
                status=status.HTTP_404_NOT_FOUND,
            )

        new_status = request.data.get("status")
        if not new_status:
            return Response(
                {"error": "Не передан параметр status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed = self.ALLOWED_TRANSITIONS.get(waybill.status, [])
        if new_status not in allowed:
            return Response(
                {"error": f"Из статуса '{waybill.status}' нельзя перейти в '{new_status}'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        waybill.status = new_status
        waybill.need_sync = True   # помечаем для синхронизации с 1С
        waybill.save()

        return Response(WaybillSerializer(waybill).data)
    
class ReorderWaybills(APIView):
    """POST /api/waybills/reorder/ — обновить порядок накладных.
    
    Принимает: {"waybill_ids": [3, 1, 5, 2, ...]}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        ids = request.data.get("waybill_ids")
        if not isinstance(ids, list) or not ids:
            return Response(
                {"error": "Ожидается непустой список waybill_ids"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = 0
        for index, waybill_id in enumerate(ids, start=1):
            count = Waybill.objects.filter(id=waybill_id).update(priority_order=index)
            updated += count

        return Response({"updated": updated})

@login_required
def index(request):
    """Страница водителя."""
    return render(request, "waybills/index.html")