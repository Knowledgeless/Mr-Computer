from functools import lru_cache
import json
from pathlib import Path

from django.conf import settings

from shipping.models import ShippingRate, ShippingZone


@lru_cache(maxsize=1)
def get_delivery_locations():
    location_file = Path(settings.BASE_DIR) / "static" / "data" / "bangladesh-locations.json"
    with location_file.open(encoding="utf-8") as file:
        return json.load(file)


@lru_cache(maxsize=1)
def get_postal_locations():
    location_file = Path(settings.BASE_DIR) / "static" / "data" / "bangladesh-postal-codes.json"
    with location_file.open(encoding="utf-8") as file:
        return json.load(file)["locations"]


def is_valid_delivery_location(*, division, district, upazila):
    locations = get_delivery_locations()
    return (
        upazila in locations.get(division, {}).get(district, ())
        or upazila in get_postal_locations().get(division, {}).get(district, {})
    )


def is_valid_postal_location(*, division, district, city, postal_code):
    city_data = get_postal_locations().get(division, {}).get(district, {}).get(city)
    if city_data is None:
        return False
    expected_postal_code = city_data["postalCode"]
    return bool(expected_postal_code) and postal_code == expected_postal_code


def get_shipping_zone(*, division, district, upazila):
    return ShippingZone.objects.filter(
        division=division,
        district=district,
        upazila=upazila,
        is_active=True,
    ).first()


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
