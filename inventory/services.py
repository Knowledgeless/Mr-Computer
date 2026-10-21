from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, F
from django.utils import timezone

from catalog.models import Product, ProductVariant
from inventory.models import Inventory, InventoryTransaction


def _stock_timestamp(inventory):
    if inventory.available_quantity == 0 and inventory.out_of_stock_since is None:
        inventory.out_of_stock_since = timezone.now()
    elif inventory.available_quantity > 0:
        inventory.out_of_stock_since = None


def _sync_product_status(product_id):
    product = Product.objects.select_for_update().get(pk=product_id)
    active_variants = ProductVariant.objects.filter(product_id=product_id, is_active=True)
    if active_variants.exists() and not Inventory.objects.filter(
        variant__in=active_variants,
        quantity__gt=F("reserved_quantity"),
    ).exists():
        if product.status not in {Product.Status.DRAFT, Product.Status.DISCONTINUED, Product.Status.ARCHIVED}:
            product.status = Product.Status.OUT_OF_STOCK
            product.save(update_fields=["status", "updated_at"])
    elif product.status == Product.Status.OUT_OF_STOCK:
        product.status = Product.Status.ACTIVE
        product.save(update_fields=["status", "updated_at"])


@transaction.atomic
def receive_stock(*, variant_id, quantity, note, created_by=None, transaction_type=InventoryTransaction.TransactionType.PURCHASE):
    if quantity < 1:
        raise ValidationError("Received quantity must be positive.")
    variant = ProductVariant.objects.select_for_update().get(pk=variant_id)
    inventory = Inventory.objects.select_for_update().get(variant=variant)
    inventory.quantity += quantity
    _stock_timestamp(inventory)
    inventory.save(update_fields=["quantity", "out_of_stock_since", "updated_at"])
    InventoryTransaction.objects.create(
        variant=variant,
        transaction_type=transaction_type,
        quantity=quantity,
        note=note,
        created_by=created_by,
    )
    _sync_product_status(variant.product_id)
    return inventory


@transaction.atomic
def decrease_stock(*, variant_id, quantity, note, created_by=None, reference_type="", reference_id=None,
                   transaction_type=InventoryTransaction.TransactionType.SALE):
    if quantity < 1:
        raise ValidationError("Quantity must be positive.")
    variant = ProductVariant.objects.select_for_update().get(pk=variant_id)
    inventory = Inventory.objects.select_for_update().get(variant=variant)
    if inventory.available_quantity < quantity:
        raise ValidationError(f"Insufficient stock for {variant.sku}.")
    inventory.quantity -= quantity
    _stock_timestamp(inventory)
    inventory.save(update_fields=["quantity", "out_of_stock_since", "updated_at"])
    InventoryTransaction.objects.create(
        variant=variant,
        transaction_type=transaction_type,
        quantity=quantity,
        reference_type=reference_type,
        reference_id=reference_id,
        note=note,
        created_by=created_by,
    )
    _sync_product_status(variant.product_id)
    return inventory


@transaction.atomic
def reserve_stock(*, variant_id, quantity, note, created_by=None, reference_type="", reference_id=None):
    if quantity < 1:
        raise ValidationError("Quantity must be positive.")
    variant = ProductVariant.objects.select_for_update().get(pk=variant_id)
    inventory = Inventory.objects.select_for_update().get(variant=variant)
    if inventory.available_quantity < quantity:
        raise ValidationError(f"Insufficient stock for {variant.sku}.")
    inventory.reserved_quantity += quantity
    _stock_timestamp(inventory)
    inventory.save(update_fields=["reserved_quantity", "out_of_stock_since", "updated_at"])
    InventoryTransaction.objects.create(
        variant=variant,
        transaction_type=InventoryTransaction.TransactionType.RESERVATION,
        quantity=quantity,
        reference_type=reference_type,
        reference_id=reference_id,
        note=note,
        created_by=created_by,
    )
    return inventory


@transaction.atomic
def release_stock(*, variant_id, quantity, note, created_by=None, reference_type="", reference_id=None):
    if quantity < 1:
        raise ValidationError("Quantity must be positive.")
    variant = ProductVariant.objects.select_for_update().get(pk=variant_id)
    inventory = Inventory.objects.select_for_update().get(variant=variant)
    if inventory.reserved_quantity < quantity:
        raise ValidationError("Cannot release more stock than is reserved.")
    inventory.reserved_quantity -= quantity
    _stock_timestamp(inventory)
    inventory.save(update_fields=["reserved_quantity", "out_of_stock_since", "updated_at"])
    InventoryTransaction.objects.create(
        variant=variant,
        transaction_type=InventoryTransaction.TransactionType.RELEASE,
        quantity=quantity,
        reference_type=reference_type,
        reference_id=reference_id,
        note=note,
        created_by=created_by,
    )
    return inventory


@transaction.atomic
def adjust_stock(*, variant_id, quantity_delta, note, created_by=None):
    if quantity_delta == 0:
        raise ValidationError("Inventory adjustment must change stock.")
    variant = ProductVariant.objects.select_for_update().get(pk=variant_id)
    inventory = Inventory.objects.select_for_update().get(variant=variant)
    updated_quantity = inventory.quantity + quantity_delta
    if updated_quantity < inventory.reserved_quantity:
        raise ValidationError("Adjustment cannot reduce physical stock below reserved stock.")
    inventory.quantity = updated_quantity
    _stock_timestamp(inventory)
    inventory.save(update_fields=["quantity", "out_of_stock_since", "updated_at"])
    InventoryTransaction.objects.create(
        variant=variant,
        transaction_type=InventoryTransaction.TransactionType.ADJUSTMENT,
        quantity=abs(quantity_delta),
        note=note,
        created_by=created_by,
    )
    _sync_product_status(variant.product_id)
    return inventory


def mark_media_cleanup_candidates(*, grace_period=timedelta(days=7), eligibility_period=timedelta(days=2), now=None):
    from catalog.models import ProductImage

    now = now or timezone.now()
    cutoff = now - eligibility_period
    candidates = ProductImage.objects.filter(
        status=ProductImage.Status.ACTIVE,
        product__retain_media=False,
        retain_media=False,
        is_primary=False,
        product__variants__inventory__quantity=0,
        product__variants__inventory__reserved_quantity=0,
        product__variants__inventory__out_of_stock_since__lte=cutoff,
    ).exclude(product__is_featured=True).exclude(
        product__status__in=[Product.Status.DRAFT, Product.Status.ACTIVE]
    ).annotate(product_image_count=Count("product__images")).filter(product_image_count__gt=1).distinct()
    return candidates


@transaction.atomic
def mark_cleanup_candidates(*, now=None):
    from catalog.models import ProductImage

    now = now or timezone.now()
    candidates = mark_media_cleanup_candidates(now=now)
    updated = []
    for image in candidates.select_for_update():
        image.status = ProductImage.Status.CLEANUP_CANDIDATE
        image.marked_for_deletion_at = now
        image.save(update_fields=["status", "marked_for_deletion_at", "updated_at"])
        updated.append(image.pk)
    return updated


@transaction.atomic
def delete_expired_media_candidates(*, grace_period=timedelta(days=7), now=None):
    from catalog.models import ProductImage

    now = now or timezone.now()
    cutoff = now - grace_period
    eligibility_cutoff = now - timedelta(days=2)
    deleted_ids = []
    candidates = ProductImage.objects.filter(
        status=ProductImage.Status.CLEANUP_CANDIDATE,
        marked_for_deletion_at__lte=cutoff,
    ).select_related("product").order_by("pk")
    for image in candidates.select_for_update():
        product_inventory = list(
            Inventory.objects.filter(variant__product=image.product).only(
                "quantity",
                "reserved_quantity",
                "out_of_stock_since",
            )
        )
        stock_is_still_eligible = bool(product_inventory) and all(
            inventory.available_quantity == 0
            and inventory.out_of_stock_since is not None
            and inventory.out_of_stock_since <= eligibility_cutoff
            for inventory in product_inventory
        )
        image_count = ProductImage.objects.filter(product=image.product, status=ProductImage.Status.ACTIVE).count()
        product_protected = (
            image.product.retain_media
            or image.retain_media
            or image.product.is_featured
            or image.product.status in {Product.Status.DRAFT, Product.Status.ACTIVE}
            or image_count < 1
        )
        if not stock_is_still_eligible or product_protected:
            image.status = ProductImage.Status.ACTIVE
            image.marked_for_deletion_at = None
            image.save(update_fields=["status", "marked_for_deletion_at", "updated_at"])
            continue
        if image.image and image.image.storage.exists(image.image.name):
            image.image.storage.delete(image.image.name)
        image.status = ProductImage.Status.DELETED
        image.deleted_at = now
        image.save(update_fields=["status", "deleted_at", "updated_at"])
        deleted_ids.append(image.pk)
    return deleted_ids
