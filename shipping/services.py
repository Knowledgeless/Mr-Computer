from shipping.models import ShippingRate


def calculate_shipping(*, zone_id, subtotal, fallback_cost):
    if zone_id:
        rates = ShippingRate.objects.filter(zone_id=zone_id, is_active=True).order_by("-minimum_order_amount")
        rate = next(
            (
                item
                for item in rates
                if subtotal >= item.minimum_order_amount
                and (item.maximum_order_amount is None or subtotal <= item.maximum_order_amount)
            ),
            None,
        )
        if rate is not None:
            return rate.rate
    return fallback_cost
