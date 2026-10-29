from django.conf import settings
from django import forms
from django.core.paginator import Paginator
from django.db.models import Avg, OuterRef, Prefetch, Q, Subquery
from django.shortcuts import get_object_or_404, render

from catalog.models import Brand, Category, Product, ProductVariant
from cms.models import Banner, HomeSection, Page
from reviews.models import Review


def _with_approved_rating(queryset):
    average_rating = (
        Review.objects.filter(product_id=OuterRef("pk"), status=Review.Status.APPROVED)
        .order_by()
        .values("product_id")
        .annotate(average=Avg("rating"))
        .values("average")
    )
    return queryset.annotate(average_rating=Subquery(average_rating))


def _pagination_url(request, page_number):
    query = request.GET.copy()
    query["page"] = page_number
    return f"{request.path}?{query.urlencode()}"


def _pagination_links(request, paginator, current_page):
    total_pages = paginator.num_pages
    if total_pages <= 7:
        page_numbers = list(range(1, total_pages + 1))
    else:
        page_numbers = {1, total_pages, current_page}
        if current_page <= 3:
            page_numbers.update(range(1, 5))
        elif current_page >= total_pages - 2:
            page_numbers.update(range(total_pages - 3, total_pages + 1))
        else:
            page_numbers.update((current_page - 1, current_page + 1))
        page_numbers = sorted(page_numbers)

    links = []
    previous_page = None
    for page_number in page_numbers:
        if previous_page is not None and page_number - previous_page > 1:
            links.append({"ellipsis": True})
        links.append(
            {
                "number": page_number,
                "url": _pagination_url(request, page_number),
            }
        )
        previous_page = page_number
    return links


class ProductFilterForm(forms.Form):
    q = forms.CharField(max_length=100, required=False)
    brand = forms.ModelChoiceField(queryset=Brand.objects.filter(is_active=True), required=False)
    condition = forms.ChoiceField(
        choices=[("", "All conditions"), *Product.Condition.choices],
        required=False,
    )
    min_price = forms.DecimalField(min_value=0, required=False)
    max_price = forms.DecimalField(min_value=0, required=False)
    sort = forms.ChoiceField(
        choices=[
            ("newest", "Newest"),
            ("price_asc", "Price: low to high"),
            ("price_desc", "Price: high to low"),
            ("name", "Name"),
        ],
        required=False,
    )


def home(request):
    sections = HomeSection.objects.filter(is_active=True).order_by("display_order")
    featured_products = _with_approved_rating(Product.objects.filter(
        is_active=True,
        status__in=[Product.Status.ACTIVE, Product.Status.OUT_OF_STOCK],
        is_featured=True,
    )).prefetch_related("images", "variants__inventory")[:8]
    new_arrivals = _with_approved_rating(Product.objects.filter(
        is_active=True,
        status__in=[Product.Status.ACTIVE, Product.Status.OUT_OF_STOCK],
        is_new_arrival=True,
    )).prefetch_related("images", "variants__inventory")[:8]
    best_sellers = _with_approved_rating(Product.objects.filter(
        is_active=True,
        status__in=[Product.Status.ACTIVE, Product.Status.OUT_OF_STOCK],
        is_best_seller=True,
    )).prefetch_related("images", "variants__inventory")[:8]
    demo_products = []
    if settings.DEBUG and not Product.objects.filter(is_active=True).exists():
        demo_products = [
            {"name": "Intel Core i5 12th Gen Processor", "brand": "Intel", "price": "14,900", "icon": "bi-cpu-fill", "tone": "blue", "tag": "Popular"},
            {"name": "ASUS TUF Gaming Laptop", "brand": "ASUS", "price": "79,900", "icon": "bi-laptop", "tone": "slate", "tag": "Gaming"},
            {"name": "Samsung 970 EVO Plus 1TB NVMe SSD", "brand": "Samsung", "price": "8,900", "icon": "bi-device-ssd-fill", "tone": "violet", "tag": "Storage"},
            {"name": "Oraimo Neckband Earphones", "brand": "Oraimo", "price": "2,400", "icon": "bi-headphones", "tone": "green", "tag": "Audio"},
            {"name": "Refurbished HP Laptop", "brand": "HP", "price": "39,900", "icon": "bi-laptop-fill", "tone": "cyan", "tag": "Refurbished"},
            {"name": "TP-Link WiFi Router AC1200", "brand": "TP-Link", "price": "4,900", "icon": "bi-router-fill", "tone": "orange", "tag": "Networking"},
        ]
    banners = [banner for banner in Banner.objects.all() if banner.is_currently_active]
    demo_banners = [
        {
            "title": "Power up your setup",
            "subtitle": "Discover the gear that makes every day more productive.",
            "image_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=1200&h=630&q=85",
            "button_text": "Shop laptops",
            "button_url": "/products/?q=laptop",
        },
        {
            "title": "Build without limits",
            "subtitle": "Find the components for your next great PC build.",
            "image_url": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=1200&h=630&q=85",
            "button_text": "Build your PC",
            "button_url": "/builder/",
        },
        {
            "title": "Your next-level workspace",
            "subtitle": "Thoughtful technology, selected for work and play.",
            "image_url": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=1200&h=630&q=85",
            "button_text": "Explore products",
            "button_url": "/products/",
        },
    ]
    context = {
        "sections": sections,
        "banners": banners,
        "demo_banners": demo_banners if not banners else [],
        "categories": Category.objects.filter(is_active=True, parent__isnull=True),
        "featured_products": featured_products,
        "new_arrivals": new_arrivals,
        "best_sellers": best_sellers,
        "demo_products": demo_products,
    }
    return render(request, "storefront/home.html", context)


def product_list(request, category_slug=None):
    products = _with_approved_rating(Product.objects.filter(
        is_active=True,
        status__in=[Product.Status.ACTIVE, Product.Status.OUT_OF_STOCK],
    )).select_related("category", "brand").prefetch_related(
        "images",
        Prefetch(
            "variants",
            queryset=ProductVariant.objects.filter(is_active=True).select_related("inventory").order_by("selling_price"),
        ),
    )
    category = None
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=category)

    form = ProductFilterForm(request.GET)
    form.is_valid()
    cleaned = form.cleaned_data if form.is_bound and not form.errors else {}
    query = cleaned.get("q", "").strip()
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(short_description__icontains=query)
            | Q(brand__name__icontains=query)
            | Q(variants__sku__icontains=query)
            | Q(variants__barcode__icontains=query)
        ).distinct()
    if cleaned.get("brand"):
        products = products.filter(brand=cleaned["brand"])
    if cleaned.get("condition"):
        products = products.filter(condition=cleaned["condition"])
    if cleaned.get("min_price") is not None:
        products = products.filter(variants__selling_price__gte=cleaned["min_price"])
    if cleaned.get("max_price") is not None:
        products = products.filter(variants__selling_price__lte=cleaned["max_price"])
    sort = cleaned.get("sort") or "newest"
    if sort == "price_asc":
        products = products.order_by("variants__selling_price", "name")
    elif sort == "price_desc":
        products = products.order_by("-variants__selling_price", "name")
    elif sort == "name":
        products = products.order_by("name")
    else:
        products = products.order_by("-created_at")
    page_obj = Paginator(products.distinct(), 16).get_page(request.GET.get("page"))
    pagination_links = _pagination_links(request, page_obj.paginator, page_obj.number)
    return render(
        request,
        "catalog/product_list.html",
        {
            "page_obj": page_obj,
            "products": page_obj.object_list,
            "category": category,
            "query": query,
            "filter_form": form,
            "pagination_links": pagination_links,
            "previous_page_url": _pagination_url(request, page_obj.previous_page_number) if page_obj.has_previous else "",
            "next_page_url": _pagination_url(request, page_obj.next_page_number) if page_obj.has_next else "",
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.filter(
            is_active=True,
            status__in=[Product.Status.ACTIVE, Product.Status.OUT_OF_STOCK],
        )
        .select_related("category", "brand")
        .prefetch_related("images", "variants__inventory", "variants__attribute_values__attribute", "variants__attribute_values__value"),
        slug=slug,
    )
    variants = product.variants.filter(is_active=True).select_related("inventory")
    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "variants": variants,
            "default_variant": variants.first(),
            "reviews": product.reviews.filter(status="APPROVED").select_related("user")[:10],
        },
    )


def content_page(request, slug):
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "cms/page_detail.html", {"page": page})
