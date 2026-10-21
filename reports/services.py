from datetime import datetime, time, timedelta

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from catalog.models import Product
from orders.models import Order, OrderItem


def dashboard_report():
    today = timezone.localdate()
    start_of_day = timezone.make_aware(datetime.combine(today, time.min))
    start_of_month = start_of_day.replace(day=1)
    paid_orders = Order.objects.filter(
        order_status=Order.Status.DELIVERED,
        payment_status=Order.PaymentStatus.PAID,
    )
    return {
        "today_sales": paid_orders.filter(created_at__gte=start_of_day).aggregate(total=Sum("total_amount"))["total"] or 0,
        "month_sales": paid_orders.filter(created_at__gte=start_of_month).aggregate(total=Sum("total_amount"))["total"] or 0,
        "new_orders": Order.objects.filter(created_at__gte=start_of_day).count(),
        "pending_orders": Order.objects.filter(
            order_status__in=[Order.Status.PENDING, Order.Status.REVIEW_REQUIRED, Order.Status.CONFIRMED],
        ).count(),
        "low_stock": Product.objects.filter(
            variants__inventory__quantity__lte=F("variants__inventory__reorder_level"),
            is_active=True,
        ).distinct().count(),
        "recent_orders": Order.objects.order_by("-created_at")[:8],
        "top_products": OrderItem.objects.filter(
            order__order_status=Order.Status.DELIVERED,
            order__payment_status=Order.PaymentStatus.PAID,
        ).values("product_name_snapshot")
        .annotate(units=Sum("quantity"), orders=Count("order_id", distinct=True))
        .order_by("-units")[:5],
        "period_days": 30,
    }


def sales_by_day(days=30):
    start = timezone.now() - timedelta(days=days)
    return (
        Order.objects.filter(
            created_at__gte=start,
            order_status=Order.Status.DELIVERED,
            payment_status=Order.PaymentStatus.PAID,
        )
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(sales=Sum("total_amount"), orders=Count("id"))
        .order_by("day")
    )
