from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import CustomerProfile
from audit.models import AuditLog
from audit.services import log_event
from catalog.forms import BrandForm, CategoryForm, ProductForm
from catalog.models import Brand, Category, Product, ProductImage, ProductVariant
from cms.forms import BannerForm, HomeSectionForm, PageForm, SiteSettingsForm
from cms.models import Banner, HomeSection, Page, SiteSettings
from core.slugs import unique_slug
from dashboard.access import dashboard_role
from dashboard.forms import CustomerRoleForm, OrderStatusForm
from inventory.forms import InventoryAdjustmentForm
from inventory.models import Inventory, InventoryTransaction
from inventory.services import adjust_stock
from orders.models import Order
from orders.services import update_order_status
from promotions.forms import CouponForm
from promotions.models import Coupon
from reports.services import dashboard_report, sales_by_day


def _product_snapshot(product):
    variant = product.variants.filter(is_active=True).order_by("created_at").first()
    return {
        "name": product.name,
        "status": product.status,
        "selling_price": str(variant.selling_price) if variant else "",
        "sku": variant.sku if variant else "",
    }


@dashboard_role("overview")
def overview(request):
    report = dashboard_report()
    sales = {row["day"]: float(row["sales"] or 0) for row in sales_by_day().values("day", "sales")}
    today = timezone.localdate()
    chart_days = []
    for offset in range(29, -1, -1):
        day = today - timedelta(days=offset)
        chart_days.append({"label": day.strftime("%b %-d"), "sales": sales.get(day, 0)})
    maximum_sales = max((day["sales"] for day in chart_days), default=0) or 1
    for day in chart_days:
        day["height"] = max(3, round(day["sales"] / maximum_sales * 100)) if day["sales"] else 3
    status_counts = {
        row["order_status"]: row["count"]
        for row in Order.objects.values("order_status").annotate(count=Count("id"))
    }
    status_total = sum(status_counts.values())
    status_colors = {
        Order.Status.DELIVERED: "green",
        Order.Status.SHIPPED: "blue",
        Order.Status.CANCELLED: "red",
        Order.Status.REFUNDED: "violet",
        Order.Status.PENDING: "orange",
        Order.Status.REVIEW_REQUIRED: "orange",
    }
    running_percent = 0
    status_chart_stops = []
    status_summaries = []
    for status, count in status_counts.items():
        percentage = round(count / status_total * 100) if status_total else 0
        color = status_colors.get(status, "gray")
        status_summaries.append(
            {
                "key": status.lower(),
                "label": Order.Status(status).label,
                "count": count,
                "percent": percentage,
            }
        )
        if percentage:
            status_chart_stops.append(f"var(--status-{color}) {running_percent}% {running_percent + percentage}%")
            running_percent += percentage
    if running_percent < 100:
        status_chart_stops.append(f"var(--status-gray) {running_percent}% 100%")
    low_stock_rows = Inventory.objects.select_related("variant__product").filter(
        quantity__lte=F("reorder_level")
    ).order_by("quantity", "variant__product__name")[:6]
    activity = [
        {
            "action": event.action.replace("_", " ").title(),
            "model_name": event.model_name,
            "username": event.user.username if event.user_id else "System",
            "created_at": event.created_at,
        }
        for event in AuditLog.objects.select_related("user").order_by("-created_at")[:5]
    ]
    report.update(
        {
            "products_count": Product.objects.filter(is_active=True).count(),
            "in_stock_products": Product.objects.filter(
                is_active=True,
                variants__inventory__quantity__gt=F("variants__inventory__reserved_quantity"),
            ).distinct().count(),
            "customers_count": CustomerProfile.objects.filter(role=CustomerProfile.Role.CUSTOMER).count(),
            "out_of_stock_count": Inventory.objects.filter(quantity__lte=F("reserved_quantity")).count(),
            "chart_days": chart_days,
            "status_counts": status_summaries,
            "status_total": status_total,
            "status_chart": ", ".join(status_chart_stops) if status_chart_stops else "var(--status-gray) 0 100%",
            "chart_max": max((day["sales"] for day in chart_days), default=0),
            "low_stock_rows": low_stock_rows,
            "recent_activity": activity,
            "database_host": f"{settings.DATABASES['default']['HOST']}:{settings.DATABASES['default']['PORT']}",
        }
    )
    if settings.DEBUG and not report["top_products"] and report["products_count"] == 0:
        report["demo_products"] = [
            {"name": "ASUS TUF Gaming Laptop", "units": "Demo", "icon": "bi-laptop"},
            {"name": "Intel Core i5 Processor", "units": "Demo", "icon": "bi-cpu"},
            {"name": "Oraimo Neckband Earphones", "units": "Demo", "icon": "bi-headphones"},
            {"name": "TP-Link WiFi Router", "units": "Demo", "icon": "bi-router"},
        ]
    return render(request, "dashboard/overview.html", {"report": report})


@dashboard_role("catalog")
def product_list(request):
    products = Product.objects.select_related("category", "brand").prefetch_related("variants__inventory", "images")
    query = request.GET.get("q", "").strip()[:100]
    if query:
        products = products.filter(Q(name__icontains=query) | Q(variants__sku__icontains=query))
    return render(request, "dashboard/products.html", {"products": products.distinct(), "query": query})


@dashboard_role("catalog")
def product_form(request, product_id=None):
    product = get_object_or_404(Product, pk=product_id) if product_id else Product()
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            old_data = _product_snapshot(product) if product.pk else {}
            product = form.save(commit=False)
            if not product.slug:
                product.slug = unique_slug(Product, product.name, product)
            product.save()
            variant = form.variant or ProductVariant(product=product)
            variant.product = product
            variant.sku = form.cleaned_data["sku"]
            variant.variant_name = form.cleaned_data["variant_name"]
            variant.cost_price = form.cleaned_data["cost_price"]
            variant.selling_price = form.cleaned_data["selling_price"]
            variant.compare_at_price = form.cleaned_data["compare_at_price"]
            variant.save()

            inventory = Inventory.objects.select_for_update().filter(variant=variant).first()
            quantity = form.cleaned_data["initial_stock"]
            if inventory is None:
                inventory = Inventory.objects.create(
                    variant=variant,
                    quantity=quantity,
                    reorder_level=form.cleaned_data["reorder_level"],
                    out_of_stock_since=timezone.now() if quantity == 0 else None,
                )
                if quantity:
                    InventoryTransaction.objects.create(
                        variant=variant,
                        transaction_type=InventoryTransaction.TransactionType.PURCHASE,
                        quantity=quantity,
                        note=form.cleaned_data["stock_note"] or "Opening stock",
                        created_by=request.user,
                    )
            else:
                delta = quantity - inventory.quantity
                if delta:
                    adjust_stock(
                        variant_id=variant.pk,
                        quantity_delta=delta,
                        note=form.cleaned_data["stock_note"],
                        created_by=request.user,
                    )
                    inventory.refresh_from_db()
                inventory.reorder_level = form.cleaned_data["reorder_level"]
                inventory.save(update_fields=["reorder_level", "updated_at"])
            if quantity == 0 and product.status == Product.Status.ACTIVE:
                product.status = Product.Status.OUT_OF_STOCK
                product.save(update_fields=["status", "updated_at"])
            uploaded_image = form.cleaned_data.get("image")
            if uploaded_image:
                ProductImage.objects.create(
                    product=product,
                    image=uploaded_image,
                    alt_text=form.cleaned_data.get("image_alt_text", ""),
                    is_primary=not product.images.exists(),
                )
            log_event(
                action="PRODUCT_SAVED",
                instance=product,
                user=request.user,
                request=request,
                old_data=old_data,
                new_data=_product_snapshot(product),
            )
        messages.success(request, "Product saved.")
        return redirect("dashboard:products")
    return render(
        request,
        "dashboard/product_form.html",
        {"form": form, "product": product, "title": "Edit product" if product.pk else "Add product"},
    )


@require_POST
@dashboard_role("catalog")
def product_archive(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    old_data = _product_snapshot(product)
    product.status = Product.Status.ARCHIVED
    product.is_active = False
    product.save(update_fields=["status", "is_active", "updated_at"])
    log_event(action="PRODUCT_ARCHIVED", instance=product, user=request.user, request=request, old_data=old_data)
    messages.success(request, "Product archived. Historical orders are unchanged.")
    return redirect("dashboard:products")


@dashboard_role("catalog")
def categories(request, category_id=None):
    category = get_object_or_404(Category, pk=category_id) if category_id else Category()
    form = CategoryForm(request.POST or None, request.FILES or None, instance=category)
    if request.method == "POST" and form.is_valid():
        category = form.save(commit=False)
        if not category.slug:
            category.slug = unique_slug(Category, category.name, category)
        category.save()
        log_event(action="CATEGORY_SAVED", instance=category, user=request.user, request=request)
        messages.success(request, "Category saved.")
        return redirect("dashboard:categories")
    return render(
        request,
        "dashboard/categories.html",
        {
            "categories": Category.objects.select_related("parent"),
            "form": form,
            "editing": bool(category_id),
        },
    )


@dashboard_role("catalog")
def brands(request, brand_id=None):
    brand = get_object_or_404(Brand, pk=brand_id) if brand_id else Brand()
    form = BrandForm(request.POST or None, request.FILES or None, instance=brand)
    if request.method == "POST" and form.is_valid():
        brand = form.save(commit=False)
        if not brand.slug:
            brand.slug = unique_slug(Brand, brand.name, brand)
        brand.save()
        log_event(action="BRAND_SAVED", instance=brand, user=request.user, request=request)
        messages.success(request, "Brand saved.")
        return redirect("dashboard:brands")
    return render(
        request,
        "dashboard/brands.html",
        {"brands": Brand.objects.all(), "form": form, "editing": bool(brand_id)},
    )


@dashboard_role("inventory")
def inventory(request):
    form = InventoryAdjustmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        variant = form.cleaned_data["variant"]
        old_quantity = Inventory.objects.get(variant=variant).quantity
        try:
            updated = adjust_stock(
                variant_id=variant.pk,
                quantity_delta=form.cleaned_data["quantity_delta"],
                note=form.cleaned_data["note"],
                created_by=request.user,
            )
        except ValidationError as error:
            form.add_error(None, error.messages[0])
        else:
            log_event(
                action="STOCK_ADJUSTED",
                instance=updated,
                user=request.user,
                request=request,
                old_data={"quantity": old_quantity},
                new_data={"quantity": updated.quantity},
            )
            messages.success(request, "Inventory adjusted and transaction recorded.")
            return redirect("dashboard:inventory")
    rows = Inventory.objects.select_related("variant__product").order_by("variant__product__name")
    return render(request, "dashboard/inventory.html", {"rows": rows, "form": form})


@dashboard_role("orders")
def orders(request):
    queryset = Order.objects.prefetch_related("items").order_by("-created_at")
    status = request.GET.get("status", "")
    if status in Order.Status.values:
        queryset = queryset.filter(order_status=status)
    return render(
        request,
        "dashboard/orders.html",
        {"orders": queryset, "statuses": Order.Status.choices, "selected_status": status},
    )


@dashboard_role("orders")
@transaction.atomic
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items", "payments", "status_history"), pk=order_id)
    form = OrderStatusForm(
        request.POST or None,
        initial={"order_status": order.order_status, "admin_note": order.admin_note},
    )
    if request.method == "POST" and form.is_valid():
        old_status = order.order_status
        old_admin_note = order.admin_note
        if form.cleaned_data["order_status"] != order.order_status:
            try:
                order = update_order_status(
                    order_id=order.pk,
                    new_status=form.cleaned_data["order_status"],
                    changed_by=request.user,
                    cod_collected=form.cleaned_data["cod_collected"],
                )
            except ValidationError as error:
                form.add_error("order_status", error.messages[0])
                return render(request, "dashboard/order_detail.html", {"order": order, "form": form})
        if form.cleaned_data["admin_note"] != order.admin_note:
            order.admin_note = form.cleaned_data["admin_note"]
            order.save(update_fields=["admin_note", "updated_at"])
        if old_status != order.order_status or old_admin_note != order.admin_note:
            log_event(
                action="ORDER_STATUS_CHANGED" if old_status != order.order_status else "ORDER_NOTE_UPDATED",
                instance=order,
                user=request.user,
                request=request,
                old_data={"status": old_status, "admin_note": old_admin_note},
                new_data={"status": order.order_status, "admin_note": order.admin_note},
            )
        messages.success(request, "Order updated.")
        return redirect("dashboard:order_detail", order_id=order.pk)
    return render(request, "dashboard/order_detail.html", {"order": order, "form": form})


@dashboard_role("catalog")
def coupons(request, coupon_id=None):
    coupon = get_object_or_404(Coupon, pk=coupon_id) if coupon_id else Coupon()
    form = CouponForm(request.POST or None, instance=coupon)
    if request.method == "POST" and form.is_valid():
        coupon = form.save()
        log_event(action="COUPON_SAVED", instance=coupon, user=request.user, request=request)
        messages.success(request, "Coupon saved.")
        return redirect("dashboard:coupons")
    return render(
        request,
        "dashboard/coupons.html",
        {"coupons": Coupon.objects.all(), "form": form, "editing": bool(coupon_id)},
    )


@dashboard_role("inventory")
def stock_history(request):
    transactions = InventoryTransaction.objects.select_related("variant__product", "created_by")[:200]
    return render(request, "dashboard/stock_history.html", {"transactions": transactions})


@require_POST
@dashboard_role("content")
def media_protection(request, image_id):
    image = get_object_or_404(ProductImage, pk=image_id)
    image.retain_media = request.POST.get("retain_media") == "on"
    image.save(update_fields=["retain_media", "updated_at"])
    log_event(action="MEDIA_RETENTION_CHANGED", instance=image, user=request.user, request=request)
    return redirect("dashboard:media")


@dashboard_role("content")
def media(request):
    images = ProductImage.objects.select_related("product", "variant").order_by("-created_at")
    return render(request, "dashboard/media.html", {"images": images})


@dashboard_role("content")
def content(request):
    return render(
        request,
        "dashboard/content.html",
        {
            "banners": Banner.objects.all(),
            "pages": Page.objects.all(),
            "sections": HomeSection.objects.all(),
        },
    )


@dashboard_role("content")
def banner_form(request, banner_id=None):
    banner = get_object_or_404(Banner, pk=banner_id) if banner_id else Banner()
    form = BannerForm(request.POST or None, request.FILES or None, instance=banner)
    if request.method == "POST" and form.is_valid():
        banner = form.save()
        log_event(action="BANNER_SAVED", instance=banner, user=request.user, request=request)
        messages.success(request, "Hero banner saved.")
        return redirect("dashboard:content")
    return render(request, "dashboard/form_page.html", {"form": form, "title": "Edit banner" if banner.pk else "Add hero banner"})


@dashboard_role("content")
def page_form(request, page_id=None):
    page = get_object_or_404(Page, pk=page_id) if page_id else Page()
    form = PageForm(request.POST or None, instance=page)
    if request.method == "POST" and form.is_valid():
        page = form.save()
        log_event(action="PAGE_SAVED", instance=page, user=request.user, request=request)
        messages.success(request, "Page saved.")
        return redirect("dashboard:content")
    return render(request, "dashboard/form_page.html", {"form": form, "title": "Edit page" if page.pk else "Add page"})


@dashboard_role("content")
def home_section_form(request, section_id):
    section = get_object_or_404(HomeSection, pk=section_id)
    form = HomeSectionForm(request.POST or None, instance=section)
    if request.method == "POST" and form.is_valid():
        section = form.save()
        log_event(action="HOME_SECTION_SAVED", instance=section, user=request.user, request=request)
        messages.success(request, "Homepage section saved.")
        return redirect("dashboard:content")
    return render(
        request,
        "dashboard/form_page.html",
        {"form": form, "title": f"Edit {section.get_section_type_display()} section"},
    )


@dashboard_role("content")
def settings_form(request):
    site_settings = SiteSettings.get_solo()
    form = SiteSettingsForm(request.POST or None, request.FILES or None, instance=site_settings)
    if request.method == "POST" and form.is_valid():
        site_settings = form.save()
        log_event(action="SITE_SETTINGS_SAVED", instance=site_settings, user=request.user, request=request)
        messages.success(request, "Store settings saved.")
        return redirect("dashboard:settings")
    return render(request, "dashboard/form_page.html", {"form": form, "title": "Store settings"})


@dashboard_role("customers")
def customers(request):
    query = request.GET.get("q", "").strip()[:100]
    users = CustomerProfile.objects.select_related("user").order_by("-created_at")
    if query:
        users = users.filter(Q(user__username__icontains=query) | Q(user__email__icontains=query))
    return render(
        request,
        "dashboard/customers.html",
        {"profiles": users.distinct(), "query": query, "roles": CustomerProfile.Role.choices},
    )


@require_POST
@dashboard_role("customers")
def customer_role(request, user_id):
    if not request.user.is_superuser:
        profile_role = CustomerProfile.objects.filter(user=request.user).values_list("role", flat=True).first()
        if profile_role not in {CustomerProfile.Role.OWNER, CustomerProfile.Role.ADMIN}:
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied
    profile = get_object_or_404(CustomerProfile.objects.select_related("user"), user_id=user_id)
    form = CustomerRoleForm(request.POST)
    if form.is_valid():
        old_role = profile.role
        profile.role = form.cleaned_data["role"]
        profile.user.is_staff = profile.role != CustomerProfile.Role.CUSTOMER
        profile.user.save(update_fields=["is_staff"])
        profile.save(update_fields=["role", "updated_at"])
        log_event(
            action="USER_PERMISSION_CHANGED",
            instance=profile,
            user=request.user,
            request=request,
            old_data={"role": old_role},
            new_data={"role": profile.role},
        )
        messages.success(request, "Staff role updated.")
    else:
        messages.error(request, "Choose a valid role.")
    return redirect("dashboard:customers")


@dashboard_role("overview")
def reports(request):
    return render(request, "dashboard/reports.html", {"sales_by_day": sales_by_day()})
