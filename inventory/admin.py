from django.contrib import admin

from inventory.models import Inventory, InventoryItem, InventoryTransaction


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("variant", "quantity", "reserved_quantity", "available_quantity", "reorder_level", "out_of_stock_since")
    list_filter = ("out_of_stock_since",)
    search_fields = ("variant__sku", "variant__product__name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ("variant", "transaction_type", "quantity", "reference_type", "created_by", "created_at")
    list_filter = ("transaction_type", "created_at")
    search_fields = ("variant__sku", "reference_id", "note")
    readonly_fields = ("created_at", "updated_at")


admin.site.register(InventoryItem)
