from django.core.paginator import Paginator
from django.test import RequestFactory, SimpleTestCase

from catalog.views import _pagination_links, _pagination_url


class ProductPaginationTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get(
            "/products/",
            {"q": "laptop", "brand": "4", "page": "6"},
        )
        self.paginator = Paginator(range(160), 16)

    def test_middle_page_links_show_neighbors_and_both_ellipses(self):
        links = _pagination_links(self.request, self.paginator, 6)

        self.assertEqual(
            [link.get("number", "...") for link in links],
            [1, "...", 5, 6, 7, "...", 10],
        )

    def test_page_url_preserves_filters_and_replaces_existing_page(self):
        url = _pagination_url(self.request, 7)

        self.assertEqual(url, "/products/?q=laptop&brand=4&page=7")

    def test_small_page_sets_show_every_page_without_ellipses(self):
        links = _pagination_links(self.request, Paginator(range(80), 16), 3)

        self.assertEqual([link["number"] for link in links], [1, 2, 3, 4, 5])
