from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Category, ProductVariant
from core.models import UUIDTimeStampedModel
from accounts.models import phone_validator


class Build(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        COMPLETED = "COMPLETED", "Completed"
        ARCHIVED = "ARCHIVED", "Archived"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pc_builds",
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    name = models.CharField(max_length=160, default="My PC Build")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(user__isnull=False, session_key="") | (models.Q(user__isnull=True) & ~models.Q(session_key=""))),
                name="build_has_exactly_one_owner",
            ),
        ]

    def __str__(self):
        return self.name


class BuildItem(UUIDTimeStampedModel):
    build = models.ForeignKey(Build, on_delete=models.CASCADE, related_name="items")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="build_items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name="build_items")
    quantity = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["build", "category"], name="unique_build_component_category"),
        ]

    def clean(self):
        super().clean()
        if self.category_id and self.variant_id and self.category_id != self.variant.product.category_id:
            from django.core.exceptions import ValidationError

            raise ValidationError({"category": "Selected component is not in the selected product category."})


class BuildRequest(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        CONTACTED = "CONTACTED", "Contacted"
        QUOTED = "QUOTED", "Quoted"
        APPROVED = "APPROVED", "Approved"
        BUILDING = "BUILDING", "Building"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    customer_name = models.CharField(max_length=160)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="build_requests",
    )
    phone = models.CharField(max_length=24, validators=[phone_validator])
    email = models.EmailField(blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(0)])
    purpose = models.CharField(max_length=240, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NEW, db_index=True)

    class Meta:
        ordering = ["-created_at"]
