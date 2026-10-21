from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q

from catalog.models import ProductVariant
from core.models import UUIDTimeStampedModel


class Inventory(UUIDTimeStampedModel):
    variant = models.OneToOneField(ProductVariant, on_delete=models.PROTECT, related_name="inventory")
    quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=0)
    out_of_stock_since = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gte=F("reserved_quantity")), name="inventory_reservation_within_stock"),
        ]

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity

    def __str__(self):
        return f"{self.variant.sku}: {self.available_quantity} available"


class InventoryItem(UUIDTimeStampedModel):
    class ConditionGrade(models.TextChoices):
        A_PLUS = "A+", "A+"
        A = "A", "A"
        B_PLUS = "B+", "B+"
        B = "B", "B"
        C = "C", "C"

    class Status(models.TextChoices):
        IN_STOCK = "IN_STOCK", "In stock"
        RESERVED = "RESERVED", "Reserved"
        SOLD = "SOLD", "Sold"
        DAMAGED = "DAMAGED", "Damaged"
        RETURNED = "RETURNED", "Returned"

    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name="inventory_items")
    serial_number = models.CharField(max_length=160, null=True, blank=True, unique=True)
    asset_tag = models.CharField(max_length=100, null=True, blank=True, unique=True)
    condition_grade = models.CharField(max_length=4, choices=ConditionGrade.choices, default=ConditionGrade.A)
    battery_health = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(0)])
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(0)])
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.IN_STOCK, db_index=True)
    notes = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    sold_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["variant", "status"], name="item_variant_status_idx")]

    def __str__(self):
        return self.serial_number or f"{self.variant.sku} — {self.pk}"


class InventoryTransaction(UUIDTimeStampedModel):
    class TransactionType(models.TextChoices):
        PURCHASE = "PURCHASE", "Purchase"
        SALE = "SALE", "Sale"
        RETURN = "RETURN", "Return"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"
        DAMAGE = "DAMAGE", "Damage"
        TRANSFER = "TRANSFER", "Transfer"
        RESERVATION = "RESERVATION", "Reservation"
        RELEASE = "RELEASE", "Release"

    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name="inventory_transactions")
    inventory_item = models.ForeignKey(
        InventoryItem,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions",
    )
    transaction_type = models.CharField(max_length=16, choices=TransactionType.choices)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    reference_type = models.CharField(max_length=40, blank=True)
    reference_id = models.UUIDField(null=True, blank=True)
    note = models.CharField(max_length=500)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_transactions",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["variant", "created_at"], name="stock_tx_variant_created_idx"),
            models.Index(fields=["transaction_type", "created_at"], name="stock_tx_type_created_idx"),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} — {self.variant.sku} ({self.quantity})"
