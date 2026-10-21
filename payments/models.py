from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from core.models import UUIDTimeStampedModel
from orders.models import Order


class Payment(UUIDTimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    payment_method = models.CharField(max_length=12, choices=Order.PaymentMethod.choices, default=Order.PaymentMethod.COD)
    transaction_id = models.CharField(max_length=160, blank=True, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=12, choices=Order.PaymentStatus.choices, default=Order.PaymentStatus.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gte=0), name="payment_amount_nonnegative"),
        ]

    def clean(self):
        super().clean()
        if self.order_id and self.amount > self.order.total_amount:
            from django.core.exceptions import ValidationError

            raise ValidationError({"amount": "Payment cannot exceed the validated order total."})

    def __str__(self):
        return f"{self.order.order_number} — {self.get_status_display()}"
