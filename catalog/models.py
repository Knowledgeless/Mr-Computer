from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.text import slugify

from core.models import UUIDTimeStampedModel
from core.slugs import unique_slug
from core.uploads import brand_image_upload_path, product_image_upload_path, validate_product_image


class Category(UUIDTimeStampedModel):
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=product_image_upload_path, blank=True, validators=[validate_product_image])
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        indexes = [models.Index(fields=["is_active", "display_order"], name="category_active_order_idx")]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(type(self), self.name, self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(UUIDTimeStampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    logo = models.ImageField(upload_to=brand_image_upload_path, blank=True, validators=[validate_product_image])
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(type(self), self.name, self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(UUIDTimeStampedModel):
    class ProductType(models.TextChoices):
        COMPONENT = "COMPONENT", "Component"
        LAPTOP = "LAPTOP", "Laptop"
        PHONE = "PHONE", "Phone"
        ACCESSORY = "ACCESSORY", "Accessory"
        ROUTER = "ROUTER", "Router"
        CUSTOM_PC = "CUSTOM_PC", "Custom PC"
        OTHER = "OTHER", "Other"

    class Condition(models.TextChoices):
        NEW = "NEW", "New"
        REFURBISHED = "REFURBISHED", "Refurbished"
        USED = "USED", "Used"
        OPEN_BOX = "OPEN_BOX", "Open box"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        OUT_OF_STOCK = "OUT_OF_STOCK", "Out of stock"
        DISCONTINUED = "DISCONTINUED", "Discontinued"
        ARCHIVED = "ARCHIVED", "Archived"

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=240)
    slug = models.SlugField(max_length=260, unique=True, blank=True)
    short_description = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    product_type = models.CharField(max_length=20, choices=ProductType.choices, default=ProductType.OTHER)
    condition = models.CharField(max_length=16, choices=Condition.choices, default=Condition.NEW)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    is_featured = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    retain_media = models.BooleanField(default=False)
    meta_title = models.CharField(max_length=240, blank=True)
    meta_description = models.CharField(max_length=320, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "is_active"], name="product_category_active_idx"),
            models.Index(fields=["brand", "is_active"], name="product_brand_active_idx"),
            models.Index(fields=["status", "created_at"], name="product_status_created_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(type(self), self.name, self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductVariant(UUIDTimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="variants")
    sku = models.CharField(max_length=80, unique=True)
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    variant_name = models.CharField(max_length=160, default="Default")
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(0)])
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    compare_at_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
    )
    weight = models.DecimalField(max_digits=8, decimal_places=3, default=Decimal("0.000"), validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["product__name", "variant_name"]
        indexes = [models.Index(fields=["product", "is_active"], name="variant_product_active_idx")]

    def __str__(self):
        return f"{self.product.name} — {self.variant_name}"


class Attribute(UUIDTimeStampedModel):
    class DataType(models.TextChoices):
        TEXT = "TEXT", "Text"
        NUMBER = "NUMBER", "Number"
        BOOLEAN = "BOOLEAN", "Boolean"
        SELECT = "SELECT", "Select"

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    data_type = models.CharField(max_length=12, choices=DataType.choices, default=DataType.TEXT)
    unit = models.CharField(max_length=32, blank=True)
    is_filterable = models.BooleanField(default=False)
    is_comparable = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AttributeValue(UUIDTimeStampedModel):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=160)

    class Meta:
        ordering = ["value"]
        constraints = [
            models.UniqueConstraint(fields=["attribute", "value"], name="unique_attribute_value"),
        ]

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductVariantAttribute(UUIDTimeStampedModel):
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name="attribute_values")
    attribute = models.ForeignKey(Attribute, on_delete=models.PROTECT, related_name="variant_values")
    value = models.ForeignKey(AttributeValue, null=True, blank=True, on_delete=models.PROTECT, related_name="variant_values")
    custom_value = models.CharField(max_length=240, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["variant", "attribute"], name="unique_variant_attribute"),
            models.CheckConstraint(
                condition=(Q(value__isnull=False, custom_value="") | (Q(value__isnull=True) & ~Q(custom_value=""))),
                name="variant_attribute_has_one_value",
            ),
        ]

    def clean(self):
        super().clean()
        if self.value_id and self.attribute_id and self.value.attribute_id != self.attribute_id:
            from django.core.exceptions import ValidationError

            raise ValidationError({"value": "The selected value belongs to a different attribute."})


class ProductImage(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        CLEANUP_CANDIDATE = "CLEANUP_CANDIDATE", "Cleanup candidate"
        DELETED = "DELETED", "Deleted"

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="images")
    variant = models.ForeignKey(
        ProductVariant,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="images",
    )
    image = models.ImageField(upload_to=product_image_upload_path, validators=[validate_product_image])
    alt_text = models.CharField(max_length=240, blank=True)
    is_primary = models.BooleanField(default=False)
    retain_media = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    marked_for_deletion_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["display_order", "created_at"]
        indexes = [models.Index(fields=["product", "status"], name="image_product_status_idx")]

    def clean(self):
        super().clean()
        if self.variant_id and self.product_id and self.variant.product_id != self.product_id:
            from django.core.exceptions import ValidationError

            raise ValidationError({"variant": "The selected variant does not belong to this product."})

    def __str__(self):
        return self.alt_text or f"Image for {self.product}"
