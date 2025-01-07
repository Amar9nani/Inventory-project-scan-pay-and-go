from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    # Products
    path("products/add/", views.add_product, name="add_product"),
    path("products/", views.list_products, name="list_products"),
    # Suppliers
    path("suppliers/add/", views.add_supplier, name="add_supplier"),
    path("suppliers/", views.list_suppliers, name="list_suppliers"),
    # Stock Movement
    path(
        "stock-movement/add/",
        views.add_stock_movement,
        name="add_stock_movement",
    ),
    path(
        "stock-movements/",
        views.list_stock_movements,
        name="list_stock_movements",
    ),
    # Sale Orders
    path("sales/add/", views.create_sale_order, name="create_sale_order"),
    path(
        "sales/<int:order_id>/cancel/",
        views.cancel_sale_order,
        name="cancel_sale_order",
    ),
    path(
        "sales/<int:order_id>/complete/",
        views.complete_sale_order,
        name="complete_sale_order",
    ),
    path("sales/", views.list_sale_orders, name="list_sale_orders"),
    # Stock Level
    path(
        "stock-level-check/",
        views.stock_level_check,
        name="stock_level_check",
    ),
]
