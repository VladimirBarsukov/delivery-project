from django.contrib import admin
from .models import Waybill, Driver


@admin.register(Waybill)
class WaybillAdmin(admin.ModelAdmin):
    list_display = ("external_id", "address", "status", "date", "priority_order")
    list_filter = ("status", "date")
    search_fields = ("address", "recipient_name", "external_id")
    ordering = ("priority_order",)

@admin.register(Driver)   # ← новый класс
class DriverAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")