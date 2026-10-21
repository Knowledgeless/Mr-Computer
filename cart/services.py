from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from cart.models import Cart, CartItem
from catalog.models import ProductVariant
from inventory.models import Inventory


CART_TTL = timedelta(days=30)
MAX_CART_QUANTITY = 20


def _touch_cart(cart):
    cart.expires_at = timezone.now() + CART_TTL
    cart.save(update_fields=["expires_at", "updated_at"])


@transaction.atomic
def transfer_guest_cart(session_key, user):
    if not session_key or not user.is_authenticated:
        return
    guest_cart = Cart.objects.select_for_update().filter(user__isnull=True, session_key=session_key).first()
    if guest_cart is None:
        return
    user_cart = Cart.objects.select_for_update().filter(user=user).first()
    if user_cart is None:
        guest_cart.user = user
        guest_cart.session_key = ""
        _touch_cart(guest_cart)
        return guest_cart
    for guest_item in guest_cart.items.select_related("variant").order_by("variant_id"):
        existing = user_cart.items.select_for_update().filter(variant_id=guest_item.variant_id).first()
        if existing is not None:
            existing.quantity = min(MAX_CART_QUANTITY, existing.quantity + guest_item.quantity)
            existing.unit_price = guest_item.variant.selling_price
            existing.save(update_fields=["quantity", "unit_price", "updated_at"])
        else:
            guest_item.cart = user_cart
            guest_item.unit_price = guest_item.variant.selling_price
            guest_item.save(update_fields=["cart", "unit_price", "updated_at"])
    guest_cart.delete()
    _touch_cart(user_cart)
    return user_cart


def get_cart_for_request(request):
    if not request.session.session_key:
        request.session.create()
    expires_at = timezone.now() + CART_TTL
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart is None:
            cart = Cart.objects.create(user=request.user, session_key="", expires_at=expires_at)
        transfer_guest_cart(request.session.session_key, request.user)
        cart = Cart.objects.get(user=request.user)
        return cart
    cart, _ = Cart.objects.get_or_create(
        user=None,
        session_key=request.session.session_key,
        defaults={"expires_at": expires_at},
    )
    return cart


def cart_subtotal(cart):
    return sum(
        (item.variant.selling_price * item.quantity for item in cart.items.select_related("variant")),
        Decimal("0.00"),
    )


@transaction.atomic
def add_item(*, cart, variant_id, quantity):
    if quantity < 1 or quantity > MAX_CART_QUANTITY:
        raise ValidationError(f"Choose a quantity between 1 and {MAX_CART_QUANTITY}.")
    cart = Cart.objects.select_for_update().get(pk=cart.pk)
    variant = ProductVariant.objects.select_for_update().filter(
        pk=variant_id,
        is_active=True,
        product__is_active=True,
    ).select_related("product").first()
    if variant is None:
        raise ValidationError("This product is no longer available.")
    inventory = Inventory.objects.select_for_update().filter(variant=variant).first()
    if inventory is None or inventory.available_quantity < quantity:
        raise ValidationError("The requested quantity is not currently in stock.")
    item = CartItem.objects.select_for_update().filter(cart=cart, variant=variant).first()
    new_quantity = quantity + (item.quantity if item else 0)
    if new_quantity > MAX_CART_QUANTITY:
        raise ValidationError(f"You can add at most {MAX_CART_QUANTITY} of this item.")
    if inventory.available_quantity < new_quantity:
        raise ValidationError("The requested quantity is not currently in stock.")
    if item:
        item.quantity = new_quantity
        item.unit_price = variant.selling_price
        item.save(update_fields=["quantity", "unit_price", "updated_at"])
    else:
        item = CartItem.objects.create(
            cart=cart,
            variant=variant,
            quantity=quantity,
            unit_price=variant.selling_price,
        )
    _touch_cart(cart)
    return item


@transaction.atomic
def update_item_quantity(*, cart, item_id, quantity):
    if quantity < 1 or quantity > MAX_CART_QUANTITY:
        raise ValidationError(f"Choose a quantity between 1 and {MAX_CART_QUANTITY}.")
    cart = Cart.objects.select_for_update().get(pk=cart.pk)
    item = CartItem.objects.select_for_update().select_related("variant").get(pk=item_id, cart=cart)
    inventory = Inventory.objects.select_for_update().filter(variant=item.variant).first()
    if inventory is None or inventory.available_quantity < quantity:
        raise ValidationError("The requested quantity is not currently in stock.")
    item.quantity = quantity
    item.unit_price = item.variant.selling_price
    item.save(update_fields=["quantity", "unit_price", "updated_at"])
    _touch_cart(cart)
    return item
