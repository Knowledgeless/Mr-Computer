from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from promotions.models import Coupon, CouponUsage


def validate_coupon(*, code, user, subtotal, cart_items, now=None, lock=False):
    if not getattr(user, "is_authenticated", False):
        raise ValidationError("Coupons are available to signed-in customers only.")
    normalized_code = code.strip().upper()
    if not normalized_code:
        raise ValidationError("Enter a coupon code.")
    coupons = Coupon.objects
    if lock:
        coupons = coupons.select_for_update()
    coupon = coupons.filter(code=normalized_code).first()
    if coupon is None:
        raise ValidationError("This coupon code is not valid.")
    now = now or timezone.now()
    if not coupon.is_active or now < coupon.start_at or now > coupon.end_at:
        raise ValidationError("This coupon is not currently available.")
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        raise ValidationError("This coupon has reached its usage limit.")
    if coupon.usage_limit_per_user is not None and CouponUsage.objects.filter(coupon=coupon, user=user).count() >= coupon.usage_limit_per_user:
        raise ValidationError("You have already used this coupon the maximum number of times.")
    if subtotal < coupon.minimum_order_amount:
        raise ValidationError(f"Your order must be at least {coupon.minimum_order_amount} to use this coupon.")

    product_ids = set(coupon.product_rules.values_list("product_id", flat=True))
    category_ids = set(coupon.category_rules.values_list("category_id", flat=True))
    brand_ids = set(coupon.brand_rules.values_list("brand_id", flat=True))
    has_scope = bool(product_ids or category_ids or brand_ids)
    eligible_items = [
        item
        for item in cart_items
        if not has_scope
        or item.variant.product_id in product_ids
        or item.variant.product.category_id in category_ids
        or item.variant.product.brand_id in brand_ids
    ]
    eligible_subtotal = sum((item.variant.selling_price * item.quantity for item in eligible_items), Decimal("0.00"))
    if not eligible_items or eligible_subtotal <= 0:
        raise ValidationError("This coupon does not apply to the products in your cart.")

    if coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
        discount = (eligible_subtotal * coupon.discount_value / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    elif coupon.discount_type == Coupon.DiscountType.FIXED_AMOUNT:
        discount = min(coupon.discount_value, eligible_subtotal)
    else:
        discount = Decimal("0.00")
    if coupon.maximum_discount_amount is not None:
        discount = min(discount, coupon.maximum_discount_amount)
    return coupon, eligible_items, discount


@transaction.atomic
def validate_coupon_for_checkout(*, code, user, subtotal, cart_items, now=None):
    return validate_coupon(code=code, user=user, subtotal=subtotal, cart_items=cart_items, now=now, lock=True)


def allocate_discount(discount, cart_items, eligible_items):
    allocation = {item.pk: Decimal("0.00") for item in cart_items}
    eligible_total = sum((item.variant.selling_price * item.quantity for item in eligible_items), Decimal("0.00"))
    remaining = discount
    for index, item in enumerate(eligible_items):
        line_total = item.variant.selling_price * item.quantity
        share = remaining if index == len(eligible_items) - 1 else (
            discount * line_total / eligible_total
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        share = min(share, line_total, remaining)
        allocation[item.pk] = share
        remaining -= share
    return allocation
