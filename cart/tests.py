from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

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


class CartUpdateAjaxTests(SimpleTestCase):
    def test_ajax_update_returns_new_line_total_and_subtotal(self):
        item = SimpleNamespace(
            pk=uuid4(),
            quantity=3,
            variant=SimpleNamespace(selling_price=Decimal("1250.50")),
        )
        cart = object()
        with (
            patch("cart.views.get_cart_for_request", return_value=cart),
            patch("cart.views.get_object_or_404", return_value=item),
            patch("cart.views.update_item_quantity", return_value=item) as update_item,
            patch("cart.views.cart_subtotal", return_value=Decimal("3751.50")),
        ):
            response = self.client.post(
                reverse("cart:update", kwargs={"item_id": item.pk}),
                {"quantity": "3"},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                HTTP_ACCEPT="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"quantity": 3, "line_total": "3751.50", "subtotal": "3751.50"},
        )
        update_item.assert_called_once_with(cart=cart, item_id=item.pk, quantity=3)

    def test_ajax_update_returns_validation_error_without_redirect(self):
        item = SimpleNamespace(pk=uuid4())
        with (
            patch("cart.views.get_cart_for_request"),
            patch("cart.views.get_object_or_404", return_value=item),
            patch("cart.views.update_item_quantity") as update_item,
        ):
            response = self.client.post(
                reverse("cart:update", kwargs={"item_id": item.pk}),
                {"quantity": "21"},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                HTTP_ACCEPT="application/json",
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Choose a quantity between 1 and 20."})
        update_item.assert_not_called()
