from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomerProfile
from shipping.models import ShippingRate, ShippingZone


class ShippingDashboardTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            username="shipping-manager",
            password="test-password",
            is_staff=True,
        )
        CustomerProfile.objects.create(user=user, role=CustomerProfile.Role.MANAGER)
        self.client.force_login(user)

    def test_staff_can_create_zone_and_set_delivery_rate(self):
        response = self.client.post(
            reverse("dashboard:shipping"),
            {
                "name": "Savar Delivery",
                "division": "Dhaka",
                "district": "Dhaka",
                "upazila": "Savar",
                "description": "",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("dashboard:shipping"))
        zone = ShippingZone.objects.get(name="Savar Delivery")
        response = self.client.post(
            reverse("dashboard:shipping_rate_create", args=[zone.pk]),
            {
                "minimum_order_amount": "0.00",
                "maximum_order_amount": "",
                "rate": "125.00",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("dashboard:shipping"))
        rate = zone.rates.get()
        self.assertEqual(rate.rate, 125)
        response = self.client.post(
            reverse("dashboard:shipping_rate_edit", args=[zone.pk, rate.pk]),
            {
                "minimum_order_amount": "0.00",
                "maximum_order_amount": "5000.00",
                "rate": "90.00",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("dashboard:shipping"))
        rate.refresh_from_db()
        self.assertEqual(rate.rate, 90)
        self.assertEqual(rate.maximum_order_amount, 5000)

    def test_shipping_dashboard_lists_current_zones_and_rates(self):
        zone = ShippingZone.objects.create(
            name="Savar Delivery",
            division="Dhaka",
            district="Dhaka",
            upazila="Savar",
        )
        ShippingRate.objects.create(zone=zone, rate=125)

        response = self.client.get(reverse("dashboard:shipping"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Savar Delivery")
        self.assertContains(response, "125.00")
