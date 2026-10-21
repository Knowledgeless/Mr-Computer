from django.contrib import admin

from catalog.models import (
    Attribute,
    AttributeValue,
    Brand,
    Category,
    Product,
    ProductImage,
    ProductVariant,
    ProductVariantAttribute,
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "brand", "status", "condition", "is_active", "created_at")
    list_filter = ("status", "condition", "category", "brand", "is_active")
    search_fields = ("name", "slug", "variants__sku")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "variant_name", "selling_price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("sku", "barcode", "product__name")


admin.site.register(
    [Category, Brand, Attribute, AttributeValue, ProductVariantAttribute, ProductImage]
)
