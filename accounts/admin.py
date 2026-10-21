from django.contrib import admin

from accounts.models import CustomerAddress, CustomerProfile, Wishlist, WishlistItem


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "role", "marketing_opt_in", "created_at")
    list_filter = ("role", "marketing_opt_in")
    search_fields = ("user__username", "user__email", "phone")


admin.site.register([CustomerAddress, Wishlist, WishlistItem])
