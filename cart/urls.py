from django.urls import path

from cart import views

app_name = "cart"

urlpatterns = [
    path("", views.detail, name="detail"),
    path("add/", views.add, name="add"),
    path("item/<uuid:item_id>/update/", views.update, name="update"),
    path("item/<uuid:item_id>/remove/", views.remove, name="remove"),
]
