from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from catalog.models import Category, ProductVariant
from inventory.models import Inventory
from pc_builder.models import Build, BuildItem, BuildRequest


def get_build_for_request(request, build_id=None):
    if not request.session.session_key:
        request.session.create()
    build_id = build_id or request.session.get("active_pc_build")
    if build_id:
        if request.user.is_authenticated:
            build = Build.objects.filter(pk=build_id, user=request.user).first()
            if build is None:
                build = Build.objects.filter(
                    pk=build_id,
                    user__isnull=True,
                    session_key=request.session.session_key,
                ).first()
                if build is not None:
                    build.user = request.user
                    build.session_key = ""
                    build.save(update_fields=["user", "session_key", "updated_at"])
            if build is not None:
                request.session["active_pc_build"] = str(build.pk)
                return build
        else:
            build = Build.objects.filter(
                pk=build_id,
                user__isnull=True,
                session_key=request.session.session_key,
            ).first()
            if build is not None:
                return build
    if request.user.is_authenticated:
        build = Build.objects.create(user=request.user, session_key="", name="My PC Build")
    else:
        build = Build.objects.create(user=None, session_key=request.session.session_key, name="My PC Build")
    request.session["active_pc_build"] = str(build.pk)
    return build


@transaction.atomic
def add_build_item(*, build, category_id, variant_id):
    build = Build.objects.select_for_update().get(pk=build.pk)
    category = Category.objects.filter(pk=category_id, is_active=True).first()
    variant = ProductVariant.objects.select_for_update().select_related("product").filter(
        pk=variant_id,
        is_active=True,
        product__is_active=True,
    ).first()
    if category is None or variant is None:
        raise ValidationError("Choose a valid component and category.")
    if variant.product.category_id != category.pk:
        raise ValidationError("Choose a product from the selected component category.")
    inventory = Inventory.objects.select_for_update().filter(variant=variant).first()
    if inventory is None or inventory.available_quantity < 1:
        raise ValidationError("This component is currently out of stock.")
    item, _ = BuildItem.objects.update_or_create(
        build=build,
        category=category,
        defaults={"variant": variant, "quantity": 1, "unit_price": variant.selling_price},
    )
    build.total_price = sum((line.unit_price * line.quantity for line in build.items.all()), Decimal("0.00"))
    build.save(update_fields=["total_price", "updated_at"])
    return item


def create_build_request(*, form, user=None):
    build_request = form.save(commit=False)
    if user is not None and user.is_authenticated:
        build_request.user = user
    build_request.save()
    return build_request
