from django.test import TestCase, Client
from django.urls import reverse
from .models import Product, Supplier, StockMovement, SaleOrder
from .forms import ProductForm, SupplierForm, StockMovementForm, SaleOrderForm


class ProductViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product_url = reverse("add_product")
        self.list_products_url = reverse("list_products")

        self.supplier = Supplier.objects.create(
            name="Test Supplier", email="supplier@test.com"
        )
        # self.product = Product.objects.create(
        #     name="Test Product",
        #     supplier=self.supplier,
        #     stock_quantity=100,
        #     price=10.00,
        # )

    def test_add_product_get(self):
        response = self.client.get(self.product_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/add_product.html")

    def test_add_product_post_valid(self):
        data = {
            "name": "Test Product",
            "description": "New Product Description",
            "category": "New Category",
            "price": "10.00",
            "stock_quantity": 100,
            "supplier": self.supplier.id,
        }
        response = self.client.post(self.product_url, data)
        self.assertTrue(Product.objects.filter(name="Test Product").exists())
        self.assertEqual(response.status_code, 302)  # Redirect after success

    def test_add_product_post_invalid(self):
        data = {"name": "", "price": "10.00", "stock_quantity": 100}
        response = self.client.post(self.product_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, "form", "name", "This field is required."
        )

    def test_list_products(self):
        Product.objects.create(
            name="Test Product 1",
            price="10.00",
            stock_quantity=100,
            description="Test Description 1",
            category="Test Category",
            supplier=self.supplier,
        )
        Product.objects.create(
            name="Test Product 2",
            price="20.00",
            stock_quantity=200,
            description="Test Description 2",
            category="Test Category",
            supplier=self.supplier,
        )
        response = self.client.get(self.list_products_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/list_products.html")
        self.assertContains(response, "Test Product 1")
        self.assertContains(response, "Test Product 2")

    def test_list_products_search(self):
        Product.objects.create(
            name="Test Product 1",
            price="10.00",
            stock_quantity=100,
            description="Test Description 1",
            category="Test Category",
            supplier=self.supplier,
        )
        Product.objects.create(
            name="Another Product",
            price="20.00",
            stock_quantity=200,
            description="Another Product Description",
            category="Test Category",
            supplier=self.supplier,
        )
        response = self.client.get(self.list_products_url, {"search": "Test"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product 1")
        self.assertNotContains(response, "Another Product")


class SupplierViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.supplier_url = reverse("add_supplier")
        self.list_suppliers_url = reverse("list_suppliers")

    def test_add_supplier_get(self):
        response = self.client.get(self.supplier_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/add_supplier.html")

    def test_add_supplier_post_valid(self):
        data = {
            "name": "Test Supplier",
            "email": "test@supplier.com",
            "phone": "1234567890",
            "address": "Test Address",
        }
        response = self.client.post(self.supplier_url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(
            Supplier.objects.filter(name="Test Supplier").exists()
        )

    def test_add_supplier_post_invalid(self):
        data = {
            "name": "",
            "email": "test@supplier.com",
            "phone": "1234567890",
            "address": "Test Address",
        }
        response = self.client.post(self.supplier_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, "form", "name", "This field is required."
        )

    def test_list_suppliers(self):
        Supplier.objects.create(
            name="Test Supplier 1",
            email="test1@supplier.com",
            phone="1234567890",
            address="Test Address",
        )
        Supplier.objects.create(
            name="Test Supplier 2",
            email="test2@supplier.com",
            phone="0123456789",
            address="Test Address",
        )
        response = self.client.get(self.list_suppliers_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/list_suppliers.html")
        self.assertContains(response, "Test Supplier 1")
        self.assertContains(response, "Test Supplier 2")

    def test_list_suppliers_search(self):
        Supplier.objects.create(
            name="Test Supplier 1",
            email="test1@supplier.com",
            phone="1234567890",
            address="Test Address",
        )
        Supplier.objects.create(
            name="Another Supplier",
            email="another@supplier.com",
            phone="0123456789",
            address="Test Address",
        )
        response = self.client.get(
            self.list_suppliers_url, {"search": "Test"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Supplier 1")
        self.assertNotContains(response, "Another Supplier")


class StockMovementViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.stock_movement_url = reverse("add_stock_movement")
        self.list_stock_movements_url = reverse("list_stock_movements")
        self.product = Product.objects.create(
            name="Test Product", price="10.00", stock_quantity=100
        )

    def test_add_stock_movement_get(self):
        response = self.client.get(self.stock_movement_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/add_stock_movement.html")

    def test_add_stock_movement_post_valid(self):
        data = {
            "product": self.product.id,
            "quantity": 10,
            "movement_type": "In",
        }
        response = self.client.post(self.stock_movement_url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 110)

    def test_add_stock_movement_post_invalid(self):
        data = {
            "product": self.product.id,
            "quantity": 10,
            "movement_type": "",
        }
        response = self.client.post(self.stock_movement_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, "form", "movement_type", "This field is required."
        )

    def test_list_stock_movements(self):
        StockMovement.objects.create(
            product=self.product, quantity=10, movement_type="In"
        )
        response = self.client.get(self.list_stock_movements_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/list_stock_movements.html")
        self.assertContains(response, "Test Product")

    def test_list_stock_movements_search(self):
        StockMovement.objects.create(
            product=self.product, quantity=10, movement_type="In"
        )
        response = self.client.get(
            self.list_stock_movements_url, {"search": "Test"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")


class SaleOrderViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.sale_order_url = reverse("create_sale_order")
        self.product = Product.objects.create(
            name="Test Product", price="10.00", stock_quantity=100
        )

    def test_create_sale_order_get(self):
        response = self.client.get(self.sale_order_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/create_sale_order.html")

    def test_create_sale_order_post_valid(self):
        data = {"product": self.product.id, "quantity": 10}
        response = self.client.post(self.sale_order_url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 90)
        self.assertTrue(
            SaleOrder.objects.filter(product=self.product).exists()
        )

    def test_create_sale_order_post_insufficient_stock(self):
        data = {"product": self.product.id, "quantity": 200}
        response = self.client.post(self.sale_order_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response,
            "form",
            "quantity",
            "Insufficient stock for this product.",
        )

    def test_cancel_sale_order(self):
        data = {"product": self.product.id, "quantity": 10}
        response = self.client.post(self.sale_order_url, data)

        sale_order = SaleOrder.objects.get(product=self.product)

        cancel_url = reverse("cancel_sale_order", args=[sale_order.id])
        response = self.client.post(cancel_url)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        sale_order.refresh_from_db()
        self.assertEqual(sale_order.status, "Cancelled")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 100)

    def test_complete_sale_order(self):
        sale_order = SaleOrder.objects.create(
            product=self.product,
            quantity=10,
            total_price="100.00",
            status="Pending",
        )
        complete_url = reverse("complete_sale_order", args=[sale_order.id])
        response = self.client.post(complete_url)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        sale_order.refresh_from_db()
        self.assertEqual(sale_order.status, "Completed")

    def test_list_sale_orders(self):
        SaleOrder.objects.create(
            product=self.product,
            quantity=10,
            total_price="100.00",
            status="Pending",
        )
        response = self.client.get(reverse("list_sale_orders"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/list_sale_orders.html")
        self.assertContains(response, "Test Product")

    def test_list_sale_orders_filter(self):
        SaleOrder.objects.create(
            product=self.product,
            quantity=10,
            total_price="100.00",
            status="Pending",
        )
        SaleOrder.objects.create(
            product=self.product,
            quantity=5,
            total_price="50.00",
            status="Completed",
        )
        response = self.client.get(
            reverse("list_sale_orders"), {"status": "Pending"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<td>Pending")
        self.assertNotContains(response, "<td>Completed")


class StockLevelCheckViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.stock_level_check_url = reverse("stock_level_check")
        self.supplier = Supplier.objects.create(
            name="Test Supplier", email="test@supplier.com"
        )
        self.product = Product.objects.create(
            name="Test Product",
            price="10.00",
            stock_quantity=100,
            supplier=self.supplier,
        )

    def test_stock_level_check_get(self):
        response = self.client.get(self.stock_level_check_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/stock_level_check.html")

    def test_stock_level_check_post_valid(self):
        data = {"name": "Test", "supplier": self.supplier.id, "min_stock": 50}
        response = self.client.post(self.stock_level_check_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")
