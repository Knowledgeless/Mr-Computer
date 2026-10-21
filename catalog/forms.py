from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from catalog.models import Category, Product, ProductVariant
from core.uploads import validate_product_image
from inventory.models import Inventory


class ProductForm(forms.ModelForm):
    sku = forms.CharField(max_length=80)
    variant_name = forms.CharField(max_length=160, initial="Default")
    cost_price = forms.DecimalField(max_digits=12, decimal_places=2, initial=Decimal("0.00"), validators=[MinValueValidator(0)])
    selling_price = forms.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    compare_at_price = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        initial=Decimal("0.00"),
        validators=[MinValueValidator(0)],
    )
    initial_stock = forms.IntegerField(min_value=0, initial=0)
    reorder_level = forms.IntegerField(min_value=0, initial=0)
    image = forms.ImageField(required=False, validators=[validate_product_image])
    image_alt_text = forms.CharField(max_length=240, required=False)
    stock_note = forms.CharField(max_length=500, initial="Opening stock", required=False)

    class Meta:
        model = Product
        fields = (
            "name",
            "category",
            "brand",
            "short_description",
            "description",
            "product_type",
            "condition",
            "status",
            "is_featured",
            "is_new_arrival",
            "is_best_seller",
            "is_active",
            "retain_media",
            "meta_title",
            "meta_description",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "short_description": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.variant = (
            self.instance.variants.filter(is_active=True).order_by("created_at").first()
            if self.instance.pk
            else None
        )
        if self.variant is not None:
            self.fields["sku"].initial = self.variant.sku
            self.fields["variant_name"].initial = self.variant.variant_name
            self.fields["cost_price"].initial = self.variant.cost_price
            self.fields["selling_price"].initial = self.variant.selling_price
            self.fields["compare_at_price"].initial = self.variant.compare_at_price
            inventory = Inventory.objects.filter(variant=self.variant).first()
            if inventory:
                self.fields["initial_stock"].initial = inventory.quantity
                self.fields["reorder_level"].initial = inventory.reorder_level

    def clean_sku(self):
        sku = self.cleaned_data["sku"].strip()
        variants = ProductVariant.objects.filter(sku=sku)
        if self.variant:
            variants = variants.exclude(pk=self.variant.pk)
        if variants.exists():
            raise ValidationError("This SKU is already in use.")
        return sku

    def clean(self):
        cleaned = super().clean()
        selling_price = cleaned.get("selling_price")
        compare_at_price = cleaned.get("compare_at_price")
        if selling_price is not None and compare_at_price and compare_at_price < selling_price:
            self.add_error("compare_at_price", "Compare-at price must be equal to or higher than the selling price.")
        if self.variant and cleaned.get("initial_stock") is not None:
            inventory = Inventory.objects.filter(variant=self.variant).first()
            current_quantity = inventory.quantity if inventory else 0
            if cleaned["initial_stock"] != current_quantity and not cleaned.get("stock_note", "").strip():
                self.add_error("stock_note", "A reason is required when changing stock.")
        return cleaned


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("parent", "name", "slug", "description", "image", "is_active", "display_order")

    def clean_parent(self):
        parent = self.cleaned_data.get("parent")
        ancestor = parent
        while ancestor is not None:
            if self.instance.pk and ancestor.pk == self.instance.pk:
                raise ValidationError("A category cannot be nested beneath itself.")
            ancestor = ancestor.parent
        return parent


class BrandForm(forms.ModelForm):
    class Meta:
        from catalog.models import Brand

        model = Brand
        fields = ("name", "slug", "logo", "description", "website", "is_active")
