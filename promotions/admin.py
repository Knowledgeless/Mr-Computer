from django.contrib import admin

from promotions.models import Coupon, CouponBrand, CouponCategory, CouponProduct, CouponUsage


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "discount_value", "used_count", "is_active", "start_at", "end_at")
    list_filter = ("discount_type", "is_active", "start_at", "end_at")
    search_fields = ("code", "name")


admin.site.register([CouponBrand, CouponCategory, CouponProduct, CouponUsage])
