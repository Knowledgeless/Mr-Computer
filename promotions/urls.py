from django.urls import path

from promotions import views

app_name = "promotions"

urlpatterns = [
    path("validate/", views.validate, name="validate"),
]
