from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Waybill(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Создаётся"
        IN_ASSEMBLY = "in_assembly", "В сборке"
        READY = "ready", "Готова"
        ON_ROUTE = "on_route", "В пути"
        DELIVERED = "delivered", "Доставлена"

    external_id = models.CharField("ID в 1С", max_length=50, unique=True)
    date = models.DateField("Дата доставки", default=timezone.now)
    address = models.CharField("Адрес", max_length=255)
    recipient_name = models.CharField("Получатель", max_length=150, blank=True)
    phone = models.CharField("Телефон", max_length=30, blank=True)
    comment = models.TextField("Комментарий", blank=True)
    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices, default=Status.CREATED
    )
    priority_order = models.IntegerField("Порядок", default=0)
    need_sync = models.BooleanField("Нужна синхронизация", default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority_order"]
        verbose_name = "Накладная"
        verbose_name_plural = "Накладные"

    def __str__(self):
        return f"{self.external_id} — {self.address}"
    
class Driver(models.Model):   # ← добавляем в конец файла
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="driver"
    )
    phone = models.CharField("Телефон", max_length=30, blank=True)

    class Meta:
        verbose_name = "Водитель"
        verbose_name_plural = "Водители"

    def __str__(self):
        return self.user.get_full_name() or self.user.username