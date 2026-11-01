from django.test import TestCase

from orders.forms import CheckoutForm


class CheckoutLocationFormTests(TestCase):
    def test_division_choices_are_available_from_the_postal_location_data(self):
        form = CheckoutForm()
        divisions = {value for value, _ in form.fields["division"].choices if value}

        self.assertIn("Dhaka", divisions)
        self.assertIn("Sylhet", divisions)

    def get_valid_data(self):
        return {
            "customer_name": "Test Customer",
            "customer_email": "customer@example.com",
            "customer_phone": "01712345678",
            "address_line_1": "House 1, Road 2",
            "address_line_2": "",
            "division": "Dhaka",
            "district": "Dhaka",
            "upazila": "Savar",
            "postal_code": "1340",
            "customer_note": "",
            "coupon_code": "",
        }

    def test_accepts_a_valid_division_district_and_upazila(self):
        form = CheckoutForm(data=self.get_valid_data())

        self.assertTrue(form.is_valid(), form.errors)
        snapshot = form.address_snapshot()
        self.assertEqual(snapshot["division"], "Dhaka")
        self.assertEqual(snapshot["district"], "Dhaka")
        self.assertEqual(snapshot["upazila"], "Savar")
        self.assertEqual(snapshot["city"], "Savar")
        self.assertNotIn("area", snapshot)
        self.assertEqual(form.fields["postal_code"].widget.attrs["readonly"], True)
        self.assertNotIn("address_line_2", form.fields)

    def test_postal_code_is_validated_against_the_selected_upazila(self):
        data = self.get_valid_data()
        data["postal_code"] = "1348"
        form = CheckoutForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("postal_code", form.errors)

    def test_rejects_an_upazila_outside_the_selected_district(self):
        data = self.get_valid_data()
        data["upazila"] = "Barisal Sadar"
        form = CheckoutForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("upazila", form.errors)
