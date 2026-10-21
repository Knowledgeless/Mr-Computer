from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from cart.services import cart_subtotal, get_cart_for_request
from core.rate_limits import rate_limit
from core.security import fingerprint
from orders.forms import CheckoutForm
from orders.models import Order
from orders.services import create_order_from_cart


@require_http_methods(["GET", "POST"])
@rate_limit(key="checkout", limit=5, period=300)
def checkout(request):
    cart = get_cart_for_request(request)
    if not cart.items.exists():
        messages.info(request, "Your cart is empty.")
        return redirect("cart:detail")
    initial = {}
    if request.user.is_authenticated:
        initial.update(
            customer_name=request.user.get_full_name() or request.user.username,
            customer_email=request.user.email,
        )
        address = request.user.customer_addresses.filter(is_default=True).first()
        if address:
            initial.update(
                customer_phone=address.phone,
                address_line_1=address.address_line_1,
                address_line_2=address.address_line_2,
                city=address.city,
                area=address.area,
                postal_code=address.postal_code,
            )
    if request.method == "GET":
        initial["coupon_code"] = request.session.get("applied_coupon", "")
    form = CheckoutForm(request.POST or None, initial=initial if request.method == "GET" else None)
    if request.method == "POST" and form.is_valid():
        try:
            order = create_order_from_cart(
                cart_id=cart.pk,
                user=request.user,
                customer_name=form.cleaned_data["customer_name"],
                customer_email=form.cleaned_data["customer_email"],
                customer_phone=form.cleaned_data["customer_phone"],
                shipping_address=form.address_snapshot(),
                customer_note=form.cleaned_data["customer_note"],
                coupon_code=form.cleaned_data["coupon_code"] or request.session.get("applied_coupon", ""),
                shipping_zone_id=form.cleaned_data["shipping_zone"].pk if form.cleaned_data["shipping_zone"] else None,
                request=request,
            )
        except ValidationError as error:
            for message in error.messages:
                form.add_error(None, message)
        else:
            request.session.pop("applied_coupon", None)
            messages.success(request, "Your order has been placed.")
            return redirect("orders:success", order_number=order.order_number)
    return render(
        request,
        "checkout/checkout.html",
        {
            "form": form,
            "cart": cart,
            "items": cart.items.select_related("variant__product"),
            "subtotal": cart_subtotal(cart),
        },
    )


def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if order.user_id:
        if not request.user.is_authenticated or order.user_id != request.user.pk:
            raise Http404
    elif not order.session_fingerprint or not request.session.session_key:
        raise Http404
    elif order.session_fingerprint != fingerprint(request.session.session_key):
        raise Http404
    return render(request, "checkout/success.html", {"order": order})


@require_http_methods(["GET", "POST"])
@rate_limit(key="order-lookup", limit=8, period=300)
def order_lookup(request):
    order = None
    error = ""
    if request.method == "POST":
        order_number = request.POST.get("order_number", "").strip().upper()
        phone = request.POST.get("phone", "").strip()
        order = Order.objects.filter(order_number=order_number, customer_phone=phone, user__isnull=True).first()
        if order is None:
            error = "No guest order matched those details."
    return render(request, "checkout/order_lookup.html", {"order": order, "error": error})


def order_status(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not request.user.is_authenticated or order.user_id != request.user.pk:
        raise Http404
    return render(request, "accounts/order_detail.html", {"order": order})
