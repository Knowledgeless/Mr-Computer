from django.urls import path

from cms import views

app_name = "cms"

urlpatterns = [
    path("", views.contact, name="contact"),
]
