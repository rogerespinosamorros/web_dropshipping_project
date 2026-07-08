from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("catalogo/", views.catalog, name="catalog"),
    path("producto/<slug:slug>/", views.product_detail, name="product_detail"),
    path("carrito/", views.cart, name="cart"),
    path("carrito/anadir/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("carrito/eliminar/<str:key>/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/",views.checkout, name="checkout",),
]


