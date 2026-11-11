import json
import os

from django.conf import settings
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from datetime import date

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Waybill
from .serializers import WaybillSerializer

from django.shortcuts import render

from django.contrib.auth.decorators import login_required

from rest_framework.permissions import IsAuthenticated

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


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
        if request.user.groups.filter(name="Менеджеры").exists():
            return Response({"error": "Менеджерам запрещено менять статусы"}, status=403)

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
                # Отправляем сигнал в WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "waybills_updates",  # Название комнаты (как в consumers.py)
            {
                "type": "waybill_update", # Имя метода в consumers.py
                "waybill_id": waybill.id
            }
        )

        return Response(WaybillSerializer(waybill).data)
    
class ReorderWaybills(APIView):
    """POST /api/waybills/reorder/ — обновить порядок накладных.
    
    Принимает: {"waybill_ids": [3, 1, 5, 2, ...]}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):

        if request.user.groups.filter(name="Менеджеры").exists():
            return Response({"error": "Менеджерам запрещено менять статусы"}, status=403)

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

                # Отправляем сигнал в WebSocket, что порядок изменен
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "waybills_updates",
            {
                "type": "waybills_reordered" # <--- Новый тип события
            }
        )

        return Response({"updated": updated})

@login_required
def index(request):
    """Страница водителя."""
    # Проверяем, состоит ли пользователь в группе "Менеджеры"
    is_manager = request.user.groups.filter(name="Менеджеры").exists()
    return render(request, "waybills/index.html", {"is_manager": is_manager})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sync_from_1c(request):
    """Читает mock_1c_export.json и создает/обновляет накладные."""
    file_path = os.path.join(settings.BASE_DIR, "mock_1c_export.json")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return Response({"error": "Файл выгрузки не найден"}, status=404)
    except json.JSONDecodeError:
        return Response({"error": "Ошибка формата JSON"}, status=400)

    created_count = 0
    updated_count = 0

    for item in data:
        # Ищем накладную по ID из 1С
        waybill, created = Waybill.objects.update_or_create(
            external_id=item["external_id"],
            defaults={
                "address": item["address"],
                "recipient_name": item.get("recipient_name", ""),
                "phone": item.get("phone", ""),
                "status": item.get("status", "created"),
                "comment": item.get("comment", ""),
                "date": timezone.now().date(),
            }
        )
        if created:
            created_count += 1
        else:
            updated_count += 1

    return Response({
        "success": True,
        "created": created_count,
        "updated": updated_count
    })