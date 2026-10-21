from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Category, ProductVariant
from core.rate_limits import rate_limit
from pc_builder.forms import BuildRequestForm
from pc_builder.models import BuildItem
from pc_builder.services import add_build_item, create_build_request, get_build_for_request


def builder(request):
    build = get_build_for_request(request)
    categories = Category.objects.filter(
        is_active=True,
        products__is_active=True,
        products__variants__is_active=True,
        products__variants__inventory__quantity__gt=F("products__variants__inventory__reserved_quantity"),
    ).distinct()
    available_variants = ProductVariant.objects.filter(
        is_active=True,
        product__is_active=True,
        product__category__in=categories,
        inventory__quantity__gt=F("inventory__reserved_quantity"),
    ).select_related("product", "product__category", "inventory").order_by("product__name", "variant_name")
    items = build.items.select_related("category", "variant__product")
    return render(
        request,
        "pc_builder/builder.html",
        {
            "build": build,
            "items": items,
            "categories": categories,
            "available_variants": available_variants,
            "request_form": BuildRequestForm(),
        },
    )


@require_POST
@rate_limit(key="pc-build-item", limit=30, period=300)
def add_component(request):
    build = get_build_for_request(request)
    try:
        add_build_item(
            build=build,
            category_id=request.POST.get("category"),
            variant_id=request.POST.get("variant"),
        )
    except (ValidationError, ValueError) as error:
        message = error.messages[0] if isinstance(error, ValidationError) else "Choose a valid component and category."
        messages.error(request, message)
    else:
        messages.success(request, "Component added to your build.")
    return redirect("pc_builder:builder")


@require_POST
def remove_component(request, item_id):
    build = get_build_for_request(request)
    item = get_object_or_404(BuildItem, pk=item_id, build=build)
    item.delete()
    build.total_price = sum(line.unit_price * line.quantity for line in build.items.all())
    build.save(update_fields=["total_price", "updated_at"])
    return redirect("pc_builder:builder")


@require_POST
@rate_limit(key="pc-build-request", limit=5, period=3600)
def submit_request(request):
    form = BuildRequestForm(request.POST)
    if form.is_valid():
        create_build_request(form=form, user=request.user)
        messages.success(request, "Your custom PC request has been sent.")
        return redirect("pc_builder:builder")
    build = get_build_for_request(request)
    categories = Category.objects.filter(is_active=True)
    available_variants = ProductVariant.objects.filter(
        is_active=True,
        product__is_active=True,
        product__category__in=categories,
        inventory__quantity__gt=F("inventory__reserved_quantity"),
    ).select_related("product", "product__category", "inventory").order_by("product__name", "variant_name")
    return render(
        request,
        "pc_builder/builder.html",
        {
            "build": build,
            "items": build.items.select_related("category", "variant__product"),
            "categories": categories,
            "available_variants": available_variants,
            "request_form": form,
        },
    )
