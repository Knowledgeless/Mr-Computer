from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cart.forms import AddCartItemForm, UpdateCartItemForm
from cart.models import CartItem
from cart.services import add_item, cart_subtotal, get_cart_for_request, update_item_quantity
from core.rate_limits import rate_limit


def detail(request):
    cart = get_cart_for_request(request)
    items = cart.items.select_related(
        "variant__product__brand",
        "variant__product__category",
        "variant__inventory",
    ).prefetch_related("variant__product__images")
    return render(
        request,
        "cart/detail.html",
        {"cart": cart, "items": items, "subtotal": cart_subtotal(cart)},
    )


@require_POST
@rate_limit(key="cart-add", limit=30, period=60)
def add(request):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    form = AddCartItemForm(request.POST)
    if not form.is_valid():
        if is_ajax:
            return JsonResponse({"error": "Select a valid product and quantity."}, status=400)
        messages.error(request, "Select a valid product and quantity.")
        return redirect("cart:detail")
    cart = get_cart_for_request(request)
    try:
        add_item(cart=cart, variant_id=form.cleaned_data["variant"].pk, quantity=form.cleaned_data["quantity"])
    except ValidationError as error:
        if is_ajax:
            return JsonResponse({"error": error.messages[0]}, status=400)
        messages.error(request, error.messages[0])
    else:
        if is_ajax:
            cart_count = cart.items.aggregate(total=Count("pk"))["total"] or 0
            return JsonResponse(
                {
                    "message": "Product added to your cart.",
                    "cart_count": cart_count,
                }
            )
        messages.success(request, "Added to your cart..!")
    return redirect("cart:detail")


@require_POST
@rate_limit(key="cart-update", limit=40, period=60)
def update(request, item_id):
    cart = get_cart_for_request(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    form = UpdateCartItemForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Choose a quantity between 1 and 20.")
        return redirect("cart:detail")
    try:
        update_item_quantity(cart=cart, item_id=item.pk, quantity=form.cleaned_data["quantity"])
    except ValidationError as error:
        messages.error(request, error.messages[0])
    return redirect("cart:detail")


@require_POST
@rate_limit(key="cart-remove", limit=40, period=60)
def remove(request, item_id):
    cart = get_cart_for_request(request)
    CartItem.objects.filter(pk=item_id, cart=cart).delete()
    messages.warning(request, "Removed from your cart..!")
    return redirect("cart:detail")
