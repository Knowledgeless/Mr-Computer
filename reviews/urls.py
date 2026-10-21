from django.urls import path

from reviews import views

app_name = "reviews"

urlpatterns = [
    path("product/<slug:slug>/submit/", views.submit, name="submit"),
]
