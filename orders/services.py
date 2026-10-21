import uuid
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from cart.models import Cart
from catalog.models import ProductVariant
from cms.models import SiteSettings
from core.security import fingerprint, request_ip
from inventory.models import Inventory, InventoryTransaction
from inventory.services import _sync_product_status
from orders.models import Order, OrderItem, OrderStatusHistory
from payments.models import Payment
from promotions.models import CouponUsage
from promotions.services import allocate_discount, validate_coupon
from shipping.models import ShippingZone
from shipping.services import calculate_shipping


def _order_risk(*, phone, email, ip, session_hash, now):
    cutoff = now - timedelta(hours=24)
    score = 0
    phone_orders = Order.objects.filter(customer_phone=phone, created_at__gte=cutoff).count()
    if phone_orders >= 2:
        score += min(30, phone_orders * 10)
    cancelled_orders = Order.objects.filter(
        customer_phone=phone,
        order_status__in=[Order.Status.CANCELLED, Order.Status.RETURNED],
        created_at__gte=now - timedelta(days=90),
    ).count()
    if cancelled_orders >= 2:
        score += min(35, cancelled_orders * 10)
    if ip:
        ip_orders = Order.objects.filter(source_ip=ip, created_at__gte=cutoff).count()
        if ip_orders >= 5:
            score += min(20, (ip_orders - 4) * 5)
    if session_hash and Order.objects.filter(session_fingerprint=session_hash, created_at__gte=cutoff).exists():
        score += 30
    score = min(score, 100)
    if score >= 80:
        level = Order.RiskLevel.REVIEW_REQUIRED
    elif score >= 60:
        level = Order.RiskLevel.HIGH
    elif score >= 30:
        level = Order.RiskLevel.MEDIUM
    else:
        level = Order.RiskLevel.LOW
    return score, level


@transaction.atomic
def create_order_from_cart(
    *,
    cart_id,
    user,
    customer_name,
    customer_email="",
    customer_phone,
    shipping_address,
    billing_address=None,
    customer_note="",
    coupon_code="",
    shipping_zone_id=None,
    request=None,
):
    cart = Cart.objects.select_for_update().get(pk=cart_id)
    if cart.user_id != (user.pk if getattr(user, "is_authenticated", False) else None):
        raise ValidationError("This cart does not belong to the current customer.")

    cart_items = list(
        cart.items.select_related("variant__product__category", "variant__product__brand")
        .order_by("variant_id")
    )
    if not cart_items:
        raise ValidationError("Your cart is empty.")

    variant_ids = [item.variant_id for item in cart_items]
    variants = list(
        ProductVariant.objects.select_for_update()
        .filter(pk__in=variant_ids, is_active=True, product__is_active=True)
        .select_related("product", "product__category", "product__brand")
        .order_by("pk")
    )
    variants_by_id = {variant.pk: variant for variant in variants}
    if len(variants_by_id) != len(set(variant_ids)):
        raise ValidationError("One or more products in your cart are no longer available.")
    inventories = {
        inventory.variant_id: inventory
        for inventory in Inventory.objects.select_for_update()
        .filter(variant_id__in=variant_ids)
        .order_by("variant_id")
    }
    if len(inventories) != len(set(variant_ids)):
        raise ValidationError("Inventory is not configured for one or more cart products.")

    subtotal = Decimal("0.00")
    for item in cart_items:
        variant = variants_by_id[item.variant_id]
        inventory = inventories[item.variant_id]
        if inventory.available_quantity < item.quantity:
            raise ValidationError(f"Not enough stock is available for {variant.product.name}.")
        item.variant = variant
        subtotal += variant.selling_price * item.quantity

    if shipping_zone_id:
        zone = ShippingZone.objects.filter(pk=shipping_zone_id, is_active=True).first()
        if zone is None:
            raise ValidationError("Select a valid delivery area.")
    else:
        zone = None
    configured_shipping = calculate_shipping(
        zone_id=zone.pk if zone else None,
        subtotal=subtotal,
        fallback_cost=SiteSettings.get_solo().default_shipping_cost,
    )

    coupon = None
    eligible_items = []
    item_discount = Decimal("0.00")
    if coupon_code.strip():
        if not getattr(user, "is_authenticated", False):
            raise ValidationError("Sign in to apply a coupon.")
        coupon, eligible_items, item_discount = validate_coupon(
            code=coupon_code,
            user=user,
            subtotal=subtotal,
            cart_items=cart_items,
            lock=True,
        )
    discount_by_item = allocate_discount(item_discount, cart_items, eligible_items)
    free_shipping = coupon is not None and coupon.discount_type == coupon.DiscountType.FREE_SHIPPING
    shipping_cost = Decimal("0.00") if free_shipping else configured_shipping
    tax_amount = Decimal("0.00")
    total_amount = subtotal - item_discount + shipping_cost + tax_amount
    if total_amount < 0:
        raise ValidationError("Order total cannot be negative.")

    now = timezone.now()
    ip = request_ip(request) if request else ""
    session_key = request.session.session_key if request and request.session.session_key else ""
    session_hash = fingerprint(session_key) if session_key else ""
    risk_score, risk_level = _order_risk(
        phone=customer_phone,
        email=customer_email,
        ip=ip,
        session_hash=session_hash,
        now=now,
    )
    order_status = (
        Order.Status.REVIEW_REQUIRED
        if risk_level == Order.RiskLevel.REVIEW_REQUIRED
        else Order.Status.PENDING
    )
    order = Order.objects.create(
        order_number=f"MC-{now:%Y%m%d}-{uuid.uuid4().hex[:8].upper()}",
        user=user if getattr(user, "is_authenticated", False) else None,
        customer_name=customer_name.strip(),
        customer_email=customer_email.strip(),
        customer_phone=customer_phone.strip(),
        subtotal=subtotal,
        discount_amount=item_discount,
        shipping_cost=shipping_cost,
        tax_amount=tax_amount,
        total_amount=total_amount,
        coupon=coupon,
        coupon_code_snapshot=coupon.code if coupon else "",
        payment_method=Order.PaymentMethod.COD,
        payment_status=Order.PaymentStatus.PENDING,
        order_status=order_status,
        shipping_address_snapshot={**shipping_address, "zone": zone.name if zone else ""},
        billing_address_snapshot=billing_address or shipping_address,
        customer_note=customer_note.strip(),
        risk_score=risk_score,
        risk_level=risk_level,
        source_ip=ip or None,
        session_fingerprint=session_hash,
    )
    OrderStatusHistory.objects.create(order=order, new_status=order.order_status, note="Order placed.")

    for item in cart_items:
        variant = variants_by_id[item.variant_id]
        inventory = inventories[item.variant_id]
        if inventory.available_quantity < item.quantity:
            raise ValidationError(f"Not enough stock is available for {variant.product.name}.")
        line_discount = discount_by_item[item.pk]
        line_subtotal = variant.selling_price * item.quantity
        OrderItem.objects.create(
            order=order,
            variant=variant,
            product_name_snapshot=variant.product.name,
            variant_name_snapshot=variant.variant_name,
            sku_snapshot=variant.sku,
            unit_price=variant.selling_price,
            quantity=item.quantity,
            discount_amount=line_discount,
            total_amount=line_subtotal - line_discount,
        )
        inventory.quantity -= item.quantity
        if inventory.available_quantity == 0 and inventory.out_of_stock_since is None:
            inventory.out_of_stock_since = now
        inventory.save(update_fields=["quantity", "out_of_stock_since", "updated_at"])
        InventoryTransaction.objects.create(
            variant=variant,
            transaction_type=InventoryTransaction.TransactionType.SALE,
            quantity=item.quantity,
            reference_type="ORDER",
            reference_id=order.pk,
            note=f"Stock deducted for {order.order_number}.",
        )
        _sync_product_status(variant.product_id)

    Payment.objects.create(
        order=order,
        payment_method=Order.PaymentMethod.COD,
        amount=total_amount,
        status=Order.PaymentStatus.PENDING,
    )
    if coupon:
        CouponUsage.objects.create(
            coupon=coupon,
            user=user,
            order=order,
            discount_amount=item_discount + (configured_shipping if free_shipping else Decimal("0.00")),
        )
        coupon.used_count += 1
        coupon.save(update_fields=["used_count", "updated_at"])
    cart.items.all().delete()
    return order


ORDER_TRANSITIONS = {
    Order.Status.PENDING: {Order.Status.CONFIRMED, Order.Status.CANCELLED, Order.Status.REVIEW_REQUIRED},
    Order.Status.REVIEW_REQUIRED: {Order.Status.PENDING, Order.Status.CONFIRMED, Order.Status.CANCELLED},
    Order.Status.CONFIRMED: {Order.Status.PROCESSING, Order.Status.CANCELLED},
    Order.Status.PROCESSING: {Order.Status.READY_TO_SHIP, Order.Status.CANCELLED},
    Order.Status.READY_TO_SHIP: {Order.Status.SHIPPED, Order.Status.CANCELLED},
    Order.Status.SHIPPED: {Order.Status.DELIVERED, Order.Status.RETURN_REQUESTED},
    Order.Status.DELIVERED: {Order.Status.RETURN_REQUESTED},
    Order.Status.RETURN_REQUESTED: {Order.Status.RETURNED, Order.Status.DELIVERED},
    Order.Status.RETURNED: {Order.Status.REFUNDED},
    Order.Status.CANCELLED: set(),
    Order.Status.REFUNDED: set(),
}


@transaction.atomic
def update_order_status(*, order_id, new_status, changed_by=None, cod_collected=False):
    order = Order.objects.select_for_update().get(pk=order_id)
    previous_status = order.order_status
    if new_status not in ORDER_TRANSITIONS.get(order.order_status, set()):
        raise ValidationError(f"Cannot move an order from {order.get_order_status_display()} to {new_status}.")

    if new_status == Order.Status.CANCELLED and not order.inventory_restored:
        items = list(order.items.select_related("variant").order_by("variant_id"))
        variant_ids = [item.variant_id for item in items if item.variant_id]
        inventories = {
            inventory.variant_id: inventory
            for inventory in Inventory.objects.select_for_update()
            .filter(variant_id__in=variant_ids)
            .order_by("variant_id")
        }
        for item in items:
            if item.variant_id is None or item.variant_id not in inventories:
                raise ValidationError("Cannot cancel because stock history is incomplete for this order.")
            inventory = inventories[item.variant_id]
            inventory.quantity += item.quantity
            inventory.out_of_stock_since = None
            inventory.save(update_fields=["quantity", "out_of_stock_since", "updated_at"])
            InventoryTransaction.objects.create(
                variant=item.variant,
                transaction_type=InventoryTransaction.TransactionType.RETURN,
                quantity=item.quantity,
                reference_type="ORDER",
                reference_id=order.pk,
                note=f"Stock restored after cancellation of {order.order_number}.",
                created_by=changed_by,
            )
            _sync_product_status(item.variant.product_id)
        order.inventory_restored = True

    order.order_status = new_status
    OrderStatusHistory.objects.create(
        order=order,
        previous_status=previous_status,
        new_status=new_status,
        changed_by=changed_by,
    )
    update_fields = ["order_status", "inventory_restored", "updated_at"]
    if new_status == Order.Status.DELIVERED and cod_collected and order.payment_method == Order.PaymentMethod.COD:
        order.payment_status = Order.PaymentStatus.PAID
        order.save(update_fields=update_fields + ["payment_status"])
        order.payments.filter(status=Order.PaymentStatus.PENDING).update(
            status=Order.PaymentStatus.PAID,
            paid_at=timezone.now(),
        )
    elif new_status == Order.Status.REFUNDED:
        order.payment_status = Order.PaymentStatus.REFUNDED
        order.save(update_fields=update_fields + ["payment_status"])
        order.payments.exclude(status=Order.PaymentStatus.REFUNDED).update(status=Order.PaymentStatus.REFUNDED)
    else:
        order.save(update_fields=update_fields)
    return order
