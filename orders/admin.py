from django.contrib import admin

from orders.models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = (
        "variant",
        "product_name_snapshot",
        "variant_name_snapshot",
        "sku_snapshot",
        "unit_price",
        "quantity",
        "discount_amount",
        "total_amount",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer_name", "customer_phone", "total_amount", "payment_status", "order_status", "created_at")
    list_filter = ("order_status", "payment_status", "payment_method", "risk_level", "created_at")
    search_fields = ("order_number", "customer_name", "customer_phone", "customer_email")
    readonly_fields = ("order_number", "risk_score", "risk_level", "created_at", "updated_at")
    inlines = [OrderItemInline]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("order", "previous_status", "new_status", "changed_by", "created_at")
    readonly_fields = ("order", "previous_status", "new_status", "changed_by", "note", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return False
