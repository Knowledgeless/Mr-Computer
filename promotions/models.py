from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from catalog.models import Brand, Category, Product
from core.models import UUIDTimeStampedModel


class Coupon(UUIDTimeStampedModel):
    class DiscountType(models.TextChoices):
        PERCENTAGE = "PERCENTAGE", "Percentage"
        FIXED_AMOUNT = "FIXED_AMOUNT", "Fixed amount"
        FREE_SHIPPING = "FREE_SHIPPING", "Free shipping"

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=16, choices=DiscountType.choices)
    discount_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    minimum_order_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    maximum_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    usage_limit_per_user = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    is_active = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "start_at", "end_at"], name="coupon_active_period_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(discount_value__gte=0), name="coupon_discount_nonnegative"),
            models.CheckConstraint(condition=Q(minimum_order_amount__gte=0), name="coupon_min_order_nonnegative"),
            models.CheckConstraint(condition=Q(used_count__gte=0), name="coupon_used_count_nonnegative"),
            models.CheckConstraint(
                condition=Q(maximum_discount_amount__isnull=True) | Q(maximum_discount_amount__gte=0),
                name="coupon_max_discount_nonnegative",
            ),
        ]

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            from django.core.exceptions import ValidationError

            raise ValidationError({"end_at": "Coupon end time must be after its start time."})
        if self.discount_type == self.DiscountType.PERCENTAGE and self.discount_value > 100:
            from django.core.exceptions import ValidationError

            raise ValidationError({"discount_value": "Percentage discounts cannot exceed 100%."})
        if self.discount_type == self.DiscountType.FREE_SHIPPING and self.discount_value != 0:
            from django.core.exceptions import ValidationError

            raise ValidationError({"discount_value": "Free-shipping coupons do not use a discount value."})

    def __str__(self):
        return self.code


class CouponProduct(UUIDTimeStampedModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="product_rules")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="coupon_rules")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["coupon", "product"], name="unique_coupon_product")]


class CouponCategory(UUIDTimeStampedModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="category_rules")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="coupon_rules")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["coupon", "category"], name="unique_coupon_category")]


class CouponBrand(UUIDTimeStampedModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="brand_rules")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="coupon_rules")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["coupon", "brand"], name="unique_coupon_brand")]


class CouponUsage(UUIDTimeStampedModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.PROTECT, related_name="usages")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="coupon_usages")
    order = models.OneToOneField("orders.Order", on_delete=models.PROTECT, related_name="coupon_usage")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["coupon", "user"], name="coupon_usage_user_idx")]
        constraints = [
            models.CheckConstraint(condition=Q(discount_amount__gte=0), name="coupon_usage_discount_nonnegative"),
        ]
