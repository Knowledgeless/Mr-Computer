import uuid

from django.utils.text import slugify


def unique_slug(model, value, instance=None):
    base = slugify(value) or uuid.uuid4().hex
    candidate = base
    suffix = 2
    queryset = model.objects.all()
    if instance is not None and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    while queryset.filter(slug=candidate).exists():
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate
