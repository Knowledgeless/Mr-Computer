from django.urls import path

from pc_builder import views

app_name = "pc_builder"

urlpatterns = [
    path("", views.builder, name="builder"),
    path("add/", views.add_component, name="add_component"),
    path("item/<uuid:item_id>/remove/", views.remove_component, name="remove_component"),
    path("request/", views.submit_request, name="submit_request"),
]
