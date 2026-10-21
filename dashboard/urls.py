from django.urls import path

from dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("products/", views.product_list, name="products"),
    path("products/new/", views.product_form, name="product_create"),
    path("products/<uuid:product_id>/edit/", views.product_form, name="product_edit"),
    path("products/<uuid:product_id>/archive/", views.product_archive, name="product_archive"),
    path("categories/", views.categories, name="categories"),
    path("categories/<uuid:category_id>/edit/", views.categories, name="category_edit"),
    path("brands/", views.brands, name="brands"),
    path("brands/<uuid:brand_id>/edit/", views.brands, name="brand_edit"),
    path("inventory/", views.inventory, name="inventory"),
    path("inventory/history/", views.stock_history, name="stock_history"),
    path("orders/", views.orders, name="orders"),
    path("orders/<uuid:order_id>/", views.order_detail, name="order_detail"),
    path("coupons/", views.coupons, name="coupons"),
    path("coupons/<uuid:coupon_id>/edit/", views.coupons, name="coupon_edit"),
    path("media/", views.media, name="media"),
    path("media/<uuid:image_id>/protection/", views.media_protection, name="media_protection"),
    path("content/", views.content, name="content"),
    path("content/banners/new/", views.banner_form, name="banner_create"),
    path("content/banners/<uuid:banner_id>/edit/", views.banner_form, name="banner_edit"),
    path("content/pages/new/", views.page_form, name="page_create"),
    path("content/pages/<uuid:page_id>/edit/", views.page_form, name="page_edit"),
    path("content/sections/<uuid:section_id>/edit/", views.home_section_form, name="home_section_edit"),
    path("settings/", views.settings_form, name="settings"),
    path("customers/", views.customers, name="customers"),
    path("customers/<int:user_id>/role/", views.customer_role, name="customer_role"),
    path("reports/", views.reports, name="reports"),
]
