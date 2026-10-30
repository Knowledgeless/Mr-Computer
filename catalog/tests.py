from django.core.paginator import Paginator
from django.test import RequestFactory, SimpleTestCase

from catalog.views import ProductFilterForm, _pagination_links, _pagination_url


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


class ProductFilterFormTests(SimpleTestCase):
    def test_filter_selects_have_float_label_hooks_and_price_fields_use_ranges(self):
        form = ProductFilterForm()

        for field_name in ("brand", "condition", "sort"):
            field = form.fields[field_name]
            self.assertEqual(field.widget.attrs["class"], "form-select")
            self.assertIn("data-filter-control", field.widget.attrs)

        for field_name in ("min_price", "max_price"):
            field = form.fields[field_name]
            self.assertEqual(field.widget.input_type, "range")
            self.assertEqual(field.widget.attrs["step"], "100")

    def test_price_range_values_validate_as_filter_parameters(self):
        form = ProductFilterForm(
            {"min_price": "100", "max_price": "2000"},
            price_slider_max=2000,
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["min_price"], 100)
        self.assertEqual(form.cleaned_data["max_price"], 2000)
        self.assertIn('type="range"', form["min_price"].as_widget())

        self.assertEqual(form.fields["brand"].empty_label, "")
        self.assertEqual(form.fields["condition"].choices[0], ("", ""))
        self.assertEqual(form.fields["sort"].choices[0], ("", ""))
