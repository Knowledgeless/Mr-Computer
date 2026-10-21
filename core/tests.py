from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from core.uploads import (
    HERO_IMAGE_LIMIT,
    PRODUCT_IMAGE_LIMIT,
    validate_hero_image,
    validate_product_image,
)


def png_upload_with_size(size):
    buffer = BytesIO()
    Image.new("RGB", (1, 1), "white").save(buffer, format="PNG")
    image = buffer.getvalue()
    if size < len(image):
        raise ValueError("Requested test size is too small.")
    return SimpleUploadedFile(
        "pixel.png",
        image + b"\0" * (size - len(image)),
        content_type="image/png",
    )


class ImageUploadValidationTests(SimpleTestCase):
    def test_product_image_must_be_strictly_smaller_than_150_kb(self):
        validate_product_image(png_upload_with_size(PRODUCT_IMAGE_LIMIT - 1))
        with self.assertRaisesMessage(ValidationError, "less than 150 KB"):
            validate_product_image(png_upload_with_size(PRODUCT_IMAGE_LIMIT))

    def test_hero_image_may_be_exactly_300_kb_but_not_larger(self):
        validate_hero_image(png_upload_with_size(HERO_IMAGE_LIMIT))
        with self.assertRaisesMessage(ValidationError, "at most 300 KB"):
            validate_hero_image(png_upload_with_size(HERO_IMAGE_LIMIT + 1))

    def test_image_extension_must_match_decoded_content(self):
        upload = png_upload_with_size(128)
        upload.name = "pixel.jpg"
        with self.assertRaisesMessage(ValidationError, "extension does not match"):
            validate_product_image(upload)
