from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccountNavigationTests(TestCase):
    def get_main_navigation(self):
        url = reverse("catalog:home") if self.client.session.get("_auth_user_id") else reverse("accounts:login")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        return html.split('<nav class="navbar', 1)[1].split("</nav>", 1)[0]

    def test_signed_out_navigation_shows_login_and_sign_up(self):
        navigation = self.get_main_navigation()

        self.assertIn(">Login<", navigation)
        self.assertIn(">Sign up<", navigation)
        self.assertNotIn(">Sign out<", navigation)

    def test_signed_in_navigation_shows_sign_out_instead_of_auth_links(self):
        user = get_user_model().objects.create_user(
            username="customer",
            email="customer@example.com",
            password="test-password",
        )
        self.client.force_login(user)

        navigation = self.get_main_navigation()

        self.assertIn(">Customer<", navigation)
        self.assertIn(">Logout<", navigation)
        self.assertNotIn(">Login<", navigation)
        self.assertNotIn(">Sign up<", navigation)
        self.assertIn('method="post"', navigation)

    def test_authenticated_customer_is_redirected_away_from_login_and_signup(self):
        user = get_user_model().objects.create_user(
            username="returning-customer",
            password="test-password-123",
        )
        self.client.force_login(user)

        for url_name in ("accounts:login", "accounts:register"):
            with self.subTest(page=url_name):
                response = self.client.get(reverse(url_name))
                self.assertRedirects(response, reverse("accounts:overview"))
                self.assertIn("no-store", response.headers["Cache-Control"])
