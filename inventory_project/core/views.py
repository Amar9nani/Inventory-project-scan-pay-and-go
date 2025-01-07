from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib import messages
from django.db import models

from .models import Product, Supplier, StockMovement, SaleOrder
from .forms import ProductForm, SupplierForm, StockMovementForm


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


def create_sale_order(request):
    """
    Create a sale order by selecting a product, verifying sufficient stock, calculating total price, etc.
    """
    if request.method == "POST":
        product_id = request.POST.get("product")
        quantity = int(request.POST.get("quantity"))

        product = get_object_or_404(Product, pk=product_id)

        # Check stock
        if product.stock_quantity < quantity:
            messages.error(request, "Insufficient stock to create this sale.")
            return redirect("create_sale_order")

        # Calculate total price
        total_price = product.price * quantity

        # Create the sale in 'Pending' status
        sale_order = SaleOrder.objects.create(
            product=product,
            quantity=quantity,
            total_price=total_price,
            status="Pending",
        )

        # Immediately reduce stock (or you can do it upon "Complete", depending on your design)
        product.stock_quantity -= quantity
        product.save()

        # Record a 'StockMovement' of type 'Out'
        StockMovement.objects.create(
            product=product,
            quantity=quantity,
            movement_type="Out",
            notes=f"Sale Order #{sale_order.pk}",
        )
        messages.success(request, f"Sale Order #{sale_order.pk} created!")
        return redirect("list_sale_orders")

    products = Product.objects.all()
    return render(
        request, "core/create_sale_order.html", {"products": products}
    )


def cancel_sale_order(request, order_id):
    """
    Cancel an existing sale order, set status to 'Cancelled', and optionally restore stock if needed.
    """
    sale_order = get_object_or_404(SaleOrder, pk=order_id)

    if sale_order.status == "Pending":
        sale_order.status = "Cancelled"
        sale_order.save()

        # Optional: restore stock
        sale_order.product.stock_quantity += sale_order.quantity
        sale_order.product.save()

        # Record a StockMovement if you wish
        StockMovement.objects.create(
            product=sale_order.product,
            quantity=sale_order.quantity,
            movement_type="In",
            notes=f"Cancelled Sale Order #{sale_order.pk}",
        )

        messages.success(
            request,
            f"Sale Order #{sale_order.pk} cancelled and stock restored.",
        )
    else:
        messages.warning(request, "Only 'Pending' orders can be cancelled.")
    return redirect("list_sale_orders")


def complete_sale_order(request, order_id):
    """
    Mark an order as 'Completed' if it is valid.
    If you haven't already deducted stock, do it here.
    """
    sale_order = get_object_or_404(SaleOrder, pk=order_id)
    if sale_order.status == "Pending":
        sale_order.status = "Completed"
        sale_order.save()
        messages.success(request, f"Sale Order #{sale_order.pk} completed.")
    else:
        messages.warning(request, "Only 'Pending' orders can be completed.")
    return redirect("list_sale_orders")


def list_sale_orders(request):
    sale_orders = SaleOrder.objects.select_related("product").all()
    return render(
        request, "core/list_sale_orders.html", {"sale_orders": sale_orders}
    )


def stock_level_check(request):
    products = Product.objects.all()
    # We can just display each product’s current stock_quantity
    return render(
        request, "core/stock_level_check.html", {"products": products}
    )
