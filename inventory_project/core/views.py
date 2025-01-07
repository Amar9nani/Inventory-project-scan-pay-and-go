from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib import messages
from django.db import models

from .models import Product, Supplier, StockMovement, SaleOrder
from .forms import (
    ProductForm,
    SupplierForm,
    StockMovementForm,
    SaleOrderForm,
    StockLevelFilterForm,
)


# ----- PRODUCTS -----


def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()  # Saves to DB
            messages.success(
                request, f"Product '{product.name}' was added successfully!"
            )
            return redirect(
                "list_products"
            )  # or wherever you want to go next
        else:
            # The form has errors, which will be displayed in the template
            messages.error(request, "Please correct the errors below.")
    else:
        # GET request - show the empty form
        form = ProductForm()

    return render(request, "core/add_product.html", {"form": form})


def list_products(request):
    # 1. Get optional search term from query string
    search_query = request.GET.get("search", "")

    # 2. Filter products by name if a search term is provided
    if search_query:
        # Example: partial match on product name
        products_list = Product.objects.select_related("supplier").filter(
            name__icontains=search_query
        )
    else:
        # No search term => show all products
        products_list = Product.objects.select_related("supplier").all()

    # 3. Set up pagination (e.g., 10 products per page)
    paginator = Paginator(products_list, 10)
    page_number = request.GET.get("page")  # "page" query param
    page_obj = paginator.get_page(page_number)

    context = {
        "search_query": search_query,
        "page_obj": page_obj,
    }
    return render(request, "core/list_products.html", context)


# ----- SUPPLIERS -----


def add_supplier(request):
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(
                request, f"Supplier '{supplier.name}' added successfully!"
            )
            return redirect("list_suppliers")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SupplierForm()

    return render(request, "core/add_supplier.html", {"form": form})


def list_suppliers(request):
    search_query = request.GET.get("search", "")

    # Filter suppliers by name or email (case-insensitive) if a search term is provided.
    if search_query:
        suppliers_list = Supplier.objects.filter(
            models.Q(name__icontains=search_query)
            | models.Q(email__icontains=search_query)
        )
    else:
        suppliers_list = Supplier.objects.all()

    # Paginate
    paginator = Paginator(suppliers_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "search_query": search_query,
        "page_obj": page_obj,
    }
    return render(request, "core/list_suppliers.html", context)


# ----- STOCK MOVEMENT -----


def add_stock_movement(request):
    if request.method == "POST":
        form = StockMovementForm(request.POST)
        if form.is_valid():
            stock_movement = form.save(commit=False)

            # Update the product's stock based on movement_type
            product = stock_movement.product
            import decimal

            # When setting a DecimalField value, ensure it's a Python decimal
            # value = "123.00"  # Example value as string
            # decimal_value = decimal.Decimal(value)
            # product.price = decimal_value
            # product.save()
            # print("---")
            # print(type(product.price))
            # print("---")
            if stock_movement.movement_type == "In":
                product.stock_quantity += stock_movement.quantity
            else:  # 'Out'
                product.stock_quantity -= stock_movement.quantity

            # Save updated product
            product.save()

            # Now save the StockMovement record
            stock_movement.save()

            messages.success(
                request,
                f"Stock movement '{stock_movement.movement_type}' recorded successfully for {product.name}!",
            )
            return redirect("list_stock_movements")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StockMovementForm()

    return render(request, "core/add_stock_movement.html", {"form": form})


def list_stock_movements(request):
    # Example: optional search by product name
    search_query = request.GET.get("search", "")

    if search_query:
        # Filter by product name
        movements_list = StockMovement.objects.select_related(
            "product"
        ).filter(product__name__icontains=search_query)
    else:
        movements_list = StockMovement.objects.select_related("product").all()

    # Paginate (10 per page)
    paginator = Paginator(movements_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "core/list_stock_movements.html",
        {
            "page_obj": page_obj,
            "search_query": search_query,
        },
    )


# ----- SALE ORDERS -----

# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator

from .models import Product, SaleOrder, StockMovement
from .forms import SaleOrderForm


def create_sale_order(request):
    """
    Use a Django form to create a sale order.
    We do stock checks and set total price in the view logic.
    """
    if request.method == "POST":
        form = SaleOrderForm(request.POST)
        if form.is_valid():
            # The form is valid, but we still need to do a stock check
            product = form.cleaned_data["product"]
            quantity = form.cleaned_data["quantity"]

            if product.stock_quantity < quantity:
                form.add_error(
                    "quantity", "Insufficient stock for this product."
                )
            else:
                # Enough stock => create the order
                total_price = product.price.to_decimal() * quantity

                sale_order = SaleOrder.objects.create(
                    product=product,
                    quantity=quantity,
                    total_price=total_price,
                    status="Pending",
                )

                # Deduct stock immediately (or do so only on "Complete" if that's your policy)
                product.stock_quantity -= quantity
                product.save()

                # Record a StockMovement of type 'Out'
                StockMovement.objects.create(
                    product=product,
                    quantity=quantity,
                    movement_type="Out",
                    notes=f"Sale Order #{sale_order.pk}",
                )

                messages.success(
                    request,
                    f"Sale Order #{sale_order.pk} created successfully!",
                )
                return redirect("list_sale_orders")
    else:
        # GET request => show empty form
        form = SaleOrderForm()

    return render(request, "core/create_sale_order.html", {"form": form})


def cancel_sale_order(request, order_id):
    sale_order = get_object_or_404(SaleOrder, pk=order_id)

    if sale_order.status == "Pending":
        sale_order.status = "Cancelled"
        sale_order.save()

        # Restore stock if we deducted it already
        sale_order.product.stock_quantity += sale_order.quantity
        sale_order.product.save()

        # Record stock movement
        StockMovement.objects.create(
            product=sale_order.product,
            quantity=sale_order.quantity,
            movement_type="In",
            notes=f"Cancelled Sale Order #{sale_order.pk}",
        )

        messages.success(request, f"Sale Order #{sale_order.pk} cancelled.")
    else:
        messages.warning(request, "Only 'Pending' orders can be cancelled.")

    return redirect("list_sale_orders")


def complete_sale_order(request, order_id):
    sale_order = get_object_or_404(SaleOrder, pk=order_id)
    if sale_order.status == "Pending":
        sale_order.status = "Completed"
        sale_order.save()
        messages.success(request, f"Sale Order #{sale_order.pk} completed!")
    else:
        messages.warning(request, "Only 'Pending' orders can be completed.")

    return redirect("list_sale_orders")


def list_sale_orders(request):
    # Optional filter by status
    status_filter = request.GET.get("status", "All")

    if status_filter == "All":
        orders_list = SaleOrder.objects.select_related("product").all()
    else:
        orders_list = SaleOrder.objects.select_related("product").filter(
            status=status_filter
        )

    # Paginate (10 orders per page, for example)
    paginator = Paginator(orders_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    status_choices = ["All", "Pending", "Completed", "Cancelled"]

    context = {
        "page_obj": page_obj,
        "status_filter": status_filter,
        "status_choices": status_choices,
    }
    return render(request, "core/list_sale_orders.html", context)


def stock_level_check(request):
    """
    Displays a form to filter products by name, supplier, and/or minimum stock.
    Shows a list of products that match the criteria, along with their current stock.
    """
    products = Product.objects.select_related("supplier").all()

    if request.method == "POST":
        form = StockLevelFilterForm(request.POST)

        # Start with all products

        if form.is_valid():
            # Extract cleaned data
            name = form.cleaned_data.get("name")
            supplier = form.cleaned_data.get("supplier")
            min_stock = form.cleaned_data.get("min_stock")

            # Filter by name (case-insensitive partial match)
            if name:
                products = products.filter(name__icontains=name)

            # Filter by supplier
            if supplier:
                products = products.filter(supplier=supplier)

            # Filter by stock
            if min_stock is not None:
                products = products.filter(stock_quantity__gte=min_stock)
    else:
        form = StockLevelFilterForm()

    context = {
        "form": form,
        "products": products,
    }
    return render(request, "core/stock_level_check.html", context)
