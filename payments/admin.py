from django.contrib import admin

from payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "payment_method", "amount", "status", "paid_at", "created_at")
    list_filter = ("payment_method", "status", "created_at")
    search_fields = ("order__order_number", "transaction_id")
    readonly_fields = ("created_at", "updated_at")
