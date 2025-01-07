# core/forms.py
from django import forms
from .models import Product, Supplier, StockMovement, SaleOrder


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "category",
            "price",
            "stock_quantity",
            "supplier",
        ]
        labels = {
            "stock_quantity": "Stock Quantity",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_name(self):
        """
        Ensure no duplicates by name. This is helpful if the database hasn't saved
        or if we want to raise a nicer error before the DB constraint kicks in.
        """
        name = self.cleaned_data.get("name")
        if Product.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError(
                "A product with this name already exists."
            )
        return name

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

    def clean_stock_quantity(self):
        stock_quantity = self.cleaned_data.get("stock_quantity")
        if stock_quantity is not None and stock_quantity < 0:
            raise forms.ValidationError("Stock quantity cannot be negative.")
        return stock_quantity


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "email", "phone", "address"]
        labels = {
            "name": "Supplier Name",
        }
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_phone(self):
        """
        Ensure phone is exactly 10 digits (assuming that's the requirement).
        Also, the model already has 'unique=True' so duplicates won't be allowed.
        """
        phone = self.cleaned_data.get("phone")
        if len(phone) != 10:
            raise forms.ValidationError(
                "Phone number must be exactly 10 digits."
            )
        if not phone.isdigit():
            raise forms.ValidationError(
                "Phone number must contain only digits."
            )
        return phone

    def clean_email(self):
        """
        The model enforces uniqueness, but we can provide a friendlier message if a duplicate is found.
        """
        email = self.cleaned_data.get("email")
        if Supplier.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "A supplier with this email already exists."
            )
        return email


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ["product", "movement_type", "quantity", "notes"]
        labels = {
            "movement_type": "Movement Type",
        }
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_quantity(self):
        """Ensure quantity is positive, and if 'Out', ensure product has enough stock."""
        quantity = self.cleaned_data.get("quantity")
        movement_type = self.cleaned_data.get("movement_type")
        product = self.cleaned_data.get("product")

        if quantity is not None and quantity <= 0:
            raise forms.ValidationError(
                "Quantity must be a positive integer."
            )

        # If movement is 'Out', check product stock
        if movement_type == "Out" and product is not None:
            if product.stock_quantity < quantity:
                raise forms.ValidationError(
                    f"Insufficient stock. Currently {product.stock_quantity} in stock."
                )

        return quantity


class SaleOrderForm(forms.ModelForm):
    class Meta:
        model = SaleOrder
        # We only allow the user to pick a product and quantity
        fields = ["product", "quantity"]

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if quantity < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        return quantity

    def clean_product(self):
        """
        Optionally, you could add logic about whether a product is valid
        for ordering, etc. We'll keep it simple here.
        """
        product = self.cleaned_data["product"]
        # Potential extra validations, if needed
        return product


class StockLevelFilterForm(forms.Form):
    """
    A simple form allowing users to filter products by:
    - Partial/Full Name
    - Supplier
    - Minimum Stock
    """

    name = forms.CharField(
        required=False,
        label="Product Name",
        widget=forms.TextInput(attrs={"placeholder": "e.g. iPhone"}),
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        required=False,
        label="Supplier",
        empty_label="-- Any Supplier --",
    )
    min_stock = forms.IntegerField(
        required=False,
        label="Minimum Stock",
        min_value=0,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 10"}),
    )
