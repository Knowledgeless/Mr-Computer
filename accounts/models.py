from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from core.models import UUIDTimeStampedModel
from core.uploads import profile_image_upload_path, validate_product_image


phone_validator = RegexValidator(
    regex=r"^\+?[0-9][0-9\s()-]{7,18}$",
    message="Enter a valid phone number.",
)


class CustomerProfile(UUIDTimeStampedModel):
    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        MANAGER = "MANAGER", "Manager"
        INVENTORY_MANAGER = "INVENTORY_MANAGER", "Inventory manager"
        ORDER_MANAGER = "ORDER_MANAGER", "Order manager"
        CONTENT_MANAGER = "CONTENT_MANAGER", "Content manager"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile")
    phone = models.CharField(max_length=24, blank=True, validators=[phone_validator])
    profile_image = models.ImageField(
        upload_to=profile_image_upload_path,
        blank=True,
        validators=[validate_product_image],
    )
    marketing_opt_in = models.BooleanField(default=False)
    role = models.CharField(max_length=24, choices=Role.choices, default=Role.CUSTOMER)

    class Meta:
        indexes = [models.Index(fields=["role", "created_at"], name="profile_role_created_idx")]


class CustomerAddress(UUIDTimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_addresses")
    label = models.CharField(max_length=60, default="Home")
    recipient_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=24, validators=[phone_validator])
    address_line_1 = models.CharField(max_length=240)
    address_line_2 = models.CharField(max_length=240, blank=True)
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "-updated_at"]
        indexes = [models.Index(fields=["user", "is_default"], name="address_user_default_idx")]

    def __str__(self):
        return f"{self.label}: {self.address_line_1}, {self.city}"


class Wishlist(UUIDTimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist")

    def __str__(self):
        return f"Wishlist for {self.user}"


class WishlistItem(UUIDTimeStampedModel):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.PROTECT, related_name="wishlist_items")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["wishlist", "variant"], name="unique_wishlist_variant"),
        ]
