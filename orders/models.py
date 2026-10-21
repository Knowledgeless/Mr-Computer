from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from catalog.models import ProductVariant
from core.models import UUIDTimeStampedModel
from promotions.models import Coupon


class Order(UUIDTimeStampedModel):
    class PaymentMethod(models.TextChoices):
        COD = "COD", "Cash on delivery"
        BKASH = "BKASH", "bKash"
        NAGAD = "NAGAD", "Nagad"
        ROCKET = "ROCKET", "Rocket"
        BANK = "BANK", "Bank transfer"
        ONLINE = "ONLINE", "Online"

    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        AUTHORIZED = "AUTHORIZED", "Authorized"
        PAID = "PAID", "Paid"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        REVIEW_REQUIRED = "REVIEW_REQUIRED", "Review required"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PROCESSING = "PROCESSING", "Processing"
        READY_TO_SHIP = "READY_TO_SHIP", "Ready to ship"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"
        RETURN_REQUESTED = "RETURN_REQUESTED", "Return requested"
        RETURNED = "RETURNED", "Returned"
        REFUNDED = "REFUNDED", "Refunded"

    class RiskLevel(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        REVIEW_REQUIRED = "REVIEW_REQUIRED", "Review required"

    order_number = models.CharField(max_length=32, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    customer_name = models.CharField(max_length=160)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=24)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    coupon_code_snapshot = models.CharField(max_length=64, blank=True)
    payment_method = models.CharField(max_length=12, choices=PaymentMethod.choices, default=PaymentMethod.COD)
    payment_status = models.CharField(max_length=12, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    order_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    shipping_address_snapshot = models.JSONField(default=dict)
    billing_address_snapshot = models.JSONField(default=dict)
    customer_note = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)
    risk_score = models.PositiveSmallIntegerField(default=0)
    risk_level = models.CharField(max_length=16, choices=RiskLevel.choices, default=RiskLevel.LOW)
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    session_fingerprint = models.CharField(max_length=64, blank=True)
    inventory_restored = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"], name="order_user_created_idx"),
            models.Index(fields=["order_status", "created_at"], name="order_status_created_idx"),
            models.Index(fields=["customer_phone", "created_at"], name="order_phone_created_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(subtotal__gte=0)
                & Q(discount_amount__gte=0)
                & Q(shipping_cost__gte=0)
                & Q(tax_amount__gte=0)
                & Q(total_amount__gte=0),
                name="order_amounts_nonnegative",
            ),
            models.CheckConstraint(condition=Q(risk_score__lte=100), name="order_risk_score_max"),
        ]

    def __str__(self):
        return self.order_number


class OrderItem(UUIDTimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        ProductVariant,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order_items",
    )
    product_name_snapshot = models.CharField(max_length=240)
    variant_name_snapshot = models.CharField(max_length=160, blank=True)
    sku_snapshot = models.CharField(max_length=80)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gte=1), name="order_item_quantity_positive"),
            models.CheckConstraint(condition=Q(discount_amount__gte=0), name="order_item_discount_nonnegative"),
        ]

    def __str__(self):
        return f"{self.quantity} × {self.product_name_snapshot}"


class OrderStatusHistory(UUIDTimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="status_history")
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, choices=Order.Status.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order_status_changes",
    )
    note = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.order.order_number}: {self.previous_status or 'NEW'} → {self.new_status}"
