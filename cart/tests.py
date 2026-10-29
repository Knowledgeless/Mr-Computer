from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.db.models import Count
from django.test import SimpleTestCase
from django.urls import reverse

from cart.context_processors import cart_count


class CartAddRequestTests(SimpleTestCase):
    def test_ajax_add_returns_json_error_for_invalid_product(self):
        response = self.client.post(
            reverse("cart:add"),
            {},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"error": "Select a valid product and quantity."},
        )

    def test_regular_add_keeps_redirect_fallback(self):
        response = self.client.post(reverse("cart:add"), {})

        self.assertRedirects(response, reverse("cart:detail"), fetch_redirect_response=False)


class CartCountTests(SimpleTestCase):
    def test_badge_counts_cart_lines_instead_of_item_quantities(self):
        item_query = Mock()
        item_query.aggregate.return_value = {"total": 2}
        request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True))

        with patch("cart.context_processors.CartItem.objects.filter", return_value=item_query):
            self.assertEqual(cart_count(request), {"cart_count": 2})

        aggregate_argument = item_query.aggregate.call_args.kwargs["total"]
        self.assertIsInstance(aggregate_argument, Count)
        self.assertEqual(aggregate_argument.source_expressions[0].name, "pk")
