from django.urls import path
from .views import TodayWaybillList, UpdateStatus, ReorderWaybills, index, sync_from_1c

urlpatterns = [
    path("", index, name="index"),   # ← новый маршрут
    path("today/", TodayWaybillList.as_view(), name="today-waybills"),
    path("<int:waybill_id>/status/", UpdateStatus.as_view(), name="update-status"),
    path("reorder/", ReorderWaybills.as_view(), name="reorder-waybills"),
    path("sync/", sync_from_1c, name="sync-1c"),
]