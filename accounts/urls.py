from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout, name="logout"),
    path("password-reset/", views.StorePasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", views.StorePasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", views.StorePasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password-reset/complete/", views.StorePasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path("account/", views.overview, name="overview"),
    path("account/orders/", views.order_list, name="orders"),
    path("account/orders/<str:order_number>/", views.order_detail, name="order_detail"),
    path("account/profile/", views.profile, name="profile"),
    path("account/addresses/", views.addresses, name="addresses"),
    path("account/addresses/<uuid:address_id>/delete/", views.address_delete, name="address_delete"),
    path("account/wishlist/", views.wishlist, name="wishlist"),
    path("account/wishlist/<uuid:variant_id>/add/", views.wishlist_add, name="wishlist_add"),
    path("account/wishlist/item/<uuid:item_id>/remove/", views.wishlist_remove, name="wishlist_remove"),
]
