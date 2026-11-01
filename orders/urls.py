from django.urls import path

from orders import views

app_name = "orders"

urlpatterns = [
    path("", views.checkout, name="checkout"),
    path("shipping-quote/", views.shipping_quote, name="shipping_quote"),
    path("lookup/", views.order_lookup, name="lookup"),
    path("success/<str:order_number>/", views.order_success, name="success"),
    path("<str:order_number>/", views.order_status, name="status"),
]
