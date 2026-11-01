from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from shipping.models import ShippingRate, ShippingZone


class ShippingQuoteTests(TestCase):
    def test_quote_uses_the_rate_configured_for_the_selected_upazila(self):
        zone = ShippingZone.objects.create(
            name="Savar delivery",
            division="Dhaka",
            district="Dhaka",
            upazila="Savar",
        )
        ShippingRate.objects.create(zone=zone, rate=Decimal("125.00"))

        with (
            patch("orders.views.get_cart_for_request", return_value=object()),
            patch("orders.views.cart_subtotal", return_value=Decimal("1000.00")),
        ):
            response = self.client.get(
                reverse("orders:shipping_quote"),
                {"division": "Dhaka", "district": "Dhaka", "upazila": "Savar"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["shipping"], "125.00")
        self.assertEqual(response.json()["total"], "1125.00")

    def test_quote_rejects_a_location_not_in_the_address_dataset(self):
        response = self.client.get(
            reverse("orders:shipping_quote"),
            {"division": "Dhaka", "district": "Dhaka", "upazila": "Barisal Sadar"},
        )

        self.assertEqual(response.status_code, 400)
