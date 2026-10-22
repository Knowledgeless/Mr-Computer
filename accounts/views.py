from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.forms import CustomerAddressForm, LoginForm, RegisterForm
from accounts.models import CustomerAddress, CustomerProfile, Wishlist, WishlistItem
from cart.services import transfer_guest_cart
from core.rate_limits import rate_limit
from catalog.models import ProductVariant


@rate_limit(key="login", limit=8, period=300)
def login(request):
    form = LoginForm(request=request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        session_key = request.session.session_key
        user = form.get_user()
        transfer_guest_cart(session_key, user)
        auth_login(request, user)
        messages.success(request, f"Welcome back, {request.user}!")
        destination = request.POST.get("next", "")
        if not url_has_allowed_host_and_scheme(destination, allowed_hosts={request.get_host()}):
            destination = "accounts:overview"
        return redirect(destination)
    return render(request, "accounts/login.html", {"form": form})


@rate_limit(key="register", limit=5, period=3600)
def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        session_key = request.session.session_key
        user = form.save()
        CustomerProfile.objects.create(user=user)
        transfer_guest_cart(session_key, user)
        auth_login(request, user)
        messages.success(request, f"Hello, {request.user}! Your account is ready.")
        return redirect("accounts:overview")
    return render(request, "accounts/register.html", {"form": form})


@require_POST
@login_required
def logout(request):
    messages.error(request, f"Goodbye, {request.user}!")
    auth_logout(request)
    return redirect("catalog:home")


@login_required
def overview(request):
    orders = request.user.orders.order_by("-created_at")[:5]
    return render(request, "accounts/overview.html", {"orders": orders})


@login_required
def order_list(request):
    orders = request.user.orders.order_by("-created_at")
    return render(request, "accounts/orders.html", {"orders": orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(request.user.orders, order_number=order_number)
    return render(request, "accounts/order_detail.html", {"order": order})


@login_required
def profile(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if email and request.user.__class__.objects.filter(email__iexact=email).exclude(pk=request.user.pk).exists():
            messages.error(request, "That email address is already in use.")
        else:
            request.user.email = email
            request.user.first_name = request.POST.get("first_name", "").strip()[:150]
            request.user.last_name = request.POST.get("last_name", "").strip()[:150]
            request.user.save(update_fields=["email", "first_name", "last_name"])
            messages.success(request, f"Profile updated, {request.user.first_name}!")
            return redirect("accounts:profile")
    return render(request, "accounts/profile.html")


@login_required
def addresses(request):
    form = CustomerAddressForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Address saved, {request.user}!")
        return redirect("accounts:addresses")
    return render(
        request,
        "accounts/addresses.html",
        {"form": form, "addresses": request.user.customer_addresses.all()},
    )


@require_POST
@login_required
def address_delete(request, address_id):
    address = get_object_or_404(CustomerAddress, pk=address_id, user=request.user)
    address.delete()
    messages.warning(request, f"Address removed, {request.user}!")
    return redirect("accounts:addresses")


@login_required
def wishlist(request):
    wishlist_object, _ = Wishlist.objects.get_or_create(user=request.user)
    items = wishlist_object.items.select_related("variant__product").prefetch_related("variant__product__images")
    return render(request, "accounts/wishlist.html", {"wishlist": wishlist_object, "items": items})


@require_POST
@login_required
def wishlist_add(request, variant_id):
    variant = get_object_or_404(ProductVariant, pk=variant_id, is_active=True, product__is_active=True)
    wishlist_object, _ = Wishlist.objects.get_or_create(user=request.user)
    WishlistItem.objects.get_or_create(wishlist=wishlist_object, variant=variant)
    messages.success(request, f"Added to your wishlist..!")
    return redirect("accounts:wishlist")


@require_POST
@login_required
def wishlist_remove(request, item_id):
    deleted_count, _ = WishlistItem.objects.filter(
        pk=item_id,
        wishlist__user=request.user,
    ).delete()
    if deleted_count:
        messages.warning(request, f"Removed from your wishlist..!")
    return redirect("accounts:wishlist")


class StorePasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    success_url = reverse_lazy("accounts:password_reset_done")


class StorePasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class StorePasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class StorePasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"
