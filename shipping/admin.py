from django.contrib import admin

from shipping.models import ShippingRate, ShippingZone


class ShippingRateInline(admin.TabularInline):
    model = ShippingRate
    extra = 1


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "division", "district", "upazila", "is_active")
    list_filter = ("is_active", "division", "district")
    search_fields = ("name", "division", "district", "upazila")
    inlines = [ShippingRateInline]


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ("zone", "minimum_order_amount", "maximum_order_amount", "rate", "is_active")
    list_filter = ("is_active", "zone__division", "zone__district")
    search_fields = ("zone__name", "zone__division", "zone__district", "zone__upazila")
