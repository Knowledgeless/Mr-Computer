from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from catalog.models import Product
from core.models import UUIDTimeStampedModel


class Review(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="product_reviews",
    )
    order_item = models.ForeignKey(
        "orders.OrderItem",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=180, blank=True)
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["product", "status"], name="review_product_status_idx")]
        constraints = [models.CheckConstraint(condition=Q(rating__gte=1) & Q(rating__lte=5), name="review_rating_range")]

    def clean(self):
        super().clean()
        if self.order_item_id and self.product_id and self.order_item.variant_id:
            if self.order_item.variant.product_id != self.product_id:
                from django.core.exceptions import ValidationError

                raise ValidationError({"order_item": "The selected order item is for a different product."})

    def __str__(self):
        return f"{self.product.name}: {self.rating}/5"
