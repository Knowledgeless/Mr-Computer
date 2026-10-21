from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from core.models import UUIDTimeStampedModel


class ShippingZone(UUIDTimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ShippingRate(UUIDTimeStampedModel):
    zone = models.ForeignKey(ShippingZone, on_delete=models.CASCADE, related_name="rates")
    minimum_order_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    maximum_order_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    rate = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["zone__name", "minimum_order_amount"]
        constraints = [
            models.CheckConstraint(
                condition=Q(maximum_order_amount__isnull=True) | Q(maximum_order_amount__gte=models.F("minimum_order_amount")),
                name="shipping_rate_amount_range",
            ),
            models.CheckConstraint(condition=Q(rate__gte=0), name="shipping_rate_nonnegative"),
        ]

    def __str__(self):
        return f"{self.zone.name}: {self.rate}"
