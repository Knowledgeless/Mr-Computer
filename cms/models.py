import uuid
from decimal import Decimal
from urllib.parse import urlparse

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from core.models import UUIDTimeStampedModel
from core.slugs import unique_slug
from core.uploads import hero_image_upload_path, profile_image_upload_path, validate_hero_image, validate_product_image


class Banner(UUIDTimeStampedModel):
    title = models.CharField(max_length=180)
    subtitle = models.CharField(max_length=320, blank=True)
    image = models.ImageField(upload_to=hero_image_upload_path, validators=[validate_hero_image])
    button_text = models.CharField(max_length=64, blank=True)
    button_url = models.CharField(max_length=500, blank=True)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "-created_at"]

    @property
    def is_currently_active(self):
        now = timezone.now()
        return self.is_active and (self.start_at is None or self.start_at <= now) and (self.end_at is None or self.end_at >= now)

    def clean(self):
        super().clean()
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            from django.core.exceptions import ValidationError

            raise ValidationError({"end_at": "Banner end time must be after its start time."})
        if self.button_url:
            parsed = urlparse(self.button_url)
            if (parsed.scheme and parsed.scheme not in {"http", "https"}) or (
                not parsed.scheme and not self.button_url.startswith("/")
            ):
                from django.core.exceptions import ValidationError

                raise ValidationError({"button_url": "Use a site-relative path or an HTTP(S) URL."})

    def __str__(self):
        return self.title


class HomeSection(UUIDTimeStampedModel):
    class SectionType(models.TextChoices):
        HERO = "HERO", "Hero"
        FEATURED_PRODUCTS = "FEATURED_PRODUCTS", "Featured products"
        CATEGORY_GRID = "CATEGORY_GRID", "Category grid"
        BRANDS = "BRANDS", "Brands"
        FLASH_SALE = "FLASH_SALE", "Flash sale"
        BEST_SELLERS = "BEST_SELLERS", "Best sellers"
        NEW_ARRIVALS = "NEW_ARRIVALS", "New arrivals"
        CUSTOM_PC = "CUSTOM_PC", "Custom PC"
        PROMOTION = "PROMOTION", "Promotion"

    section_type = models.CharField(max_length=24, choices=SectionType.choices, unique=True)
    title = models.CharField(max_length=180)
    subtitle = models.CharField(max_length=320, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.title


class Page(UUIDTimeStampedModel):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField(blank=True)
    meta_title = models.CharField(max_length=240, blank=True)
    meta_description = models.CharField(max_length=320, blank=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["title"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(type(self), self.title, self)
        if self.is_published and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class SiteSettings(UUIDTimeStampedModel):
    store_name = models.CharField(max_length=160, default="Mr. Computers")
    logo = models.ImageField(upload_to=profile_image_upload_path, blank=True, validators=[validate_product_image])
    favicon = models.ImageField(upload_to=profile_image_upload_path, blank=True, validators=[validate_product_image])
    phone = models.CharField(max_length=24, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=500, blank=True)
    facebook_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    footer_text = models.CharField(max_length=500, blank=True)
    currency = models.CharField(max_length=8, default="BDT")
    default_shipping_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
    )
    google_analytics_id = models.CharField(max_length=80, blank=True)

    class Meta:
        verbose_name_plural = "site settings"

    @classmethod
    def get_solo(cls):
        settings_id = uuid.UUID(int=1)
        instance, _ = cls.objects.get_or_create(pk=settings_id)
        return instance

    def save(self, *args, **kwargs):
        if not self.pk:
            self.pk = uuid.UUID(int=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.store_name


class ContactMessage(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        READ = "READ", "Read"
        REPLIED = "REPLIED", "Replied"
        CLOSED = "CLOSED", "Closed"

    name = models.CharField(max_length=160)
    email = models.EmailField()
    phone = models.CharField(max_length=24, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.NEW, db_index=True)

    class Meta:
        ordering = ["-created_at"]
