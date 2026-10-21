import uuid
from pathlib import Path

from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


PRODUCT_IMAGE_LIMIT = 150 * 1024
HERO_IMAGE_LIMIT = 300 * 1024
MAX_IMAGE_DIMENSION = 8192
ALLOWED_IMAGE_FORMATS = {"JPEG": {".jpg", ".jpeg"}, "PNG": {".png"}, "WEBP": {".webp"}}


def validate_product_image(upload):
    validate_image(upload, PRODUCT_IMAGE_LIMIT, strict_limit=True)


def validate_hero_image(upload):
    validate_image(upload, HERO_IMAGE_LIMIT, strict_limit=False)


def validate_image(upload, max_bytes, strict_limit):
    over_limit = upload.size >= max_bytes if strict_limit else upload.size > max_bytes
    if over_limit:
        limit_kb = max_bytes // 1024
        qualifier = "less than" if strict_limit else "at most"
        raise ValidationError(f"Image must be {qualifier} {limit_kb} KB.")

    suffix = Path(upload.name).suffix.lower()
    try:
        image = Image.open(upload)
        image_format = image.format
        width, height = image.size
        image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ValidationError("Upload a valid image file.") from error
    finally:
        upload.seek(0)

    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError("Only JPEG, PNG, and WebP images are supported.")
    if suffix not in ALLOWED_IMAGE_FORMATS[image_format]:
        raise ValidationError("The image extension does not match its actual format.")
    if width < 1 or height < 1 or width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        raise ValidationError(f"Image dimensions must not exceed {MAX_IMAGE_DIMENSION} × {MAX_IMAGE_DIMENSION} pixels.")
    if width * height > 40_000_000:
        raise ValidationError("Image dimensions are too large to process safely.")


def product_image_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"products/{uuid.uuid4().hex}{suffix}"


def hero_image_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"cms/banners/{uuid.uuid4().hex}{suffix}"


def brand_image_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"brands/{uuid.uuid4().hex}{suffix}"


def profile_image_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"profiles/{uuid.uuid4().hex}{suffix}"
