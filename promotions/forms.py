from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from catalog.models import Brand, Category, Product
from promotions.models import Coupon


class CouponApplyForm(forms.Form):
    code = forms.CharField(max_length=64)


class CouponForm(forms.ModelForm):
    products = forms.ModelMultipleChoiceField(queryset=Product.objects.order_by("name"), required=False)
    categories = forms.ModelMultipleChoiceField(queryset=Category.objects.order_by("name"), required=False)
    brands = forms.ModelMultipleChoiceField(queryset=Brand.objects.order_by("name"), required=False)

    class Meta:
        model = Coupon
        fields = (
            "code",
            "name",
            "description",
            "discount_type",
            "discount_value",
            "minimum_order_amount",
            "maximum_discount_amount",
            "usage_limit",
            "usage_limit_per_user",
            "start_at",
            "end_at",
            "is_active",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["products"].initial = self.instance.product_rules.values_list("product_id", flat=True)
            self.fields["categories"].initial = self.instance.category_rules.values_list("category_id", flat=True)
            self.fields["brands"].initial = self.instance.brand_rules.values_list("brand_id", flat=True)

    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)
        with transaction.atomic():
            coupon = super().save(commit=True)
            coupon.product_rules.all().delete()
            coupon.category_rules.all().delete()
            coupon.brand_rules.all().delete()
            coupon.product_rules.bulk_create(
                [coupon.product_rules.model(coupon=coupon, product=item) for item in self.cleaned_data["products"]]
            )
            coupon.category_rules.bulk_create(
                [coupon.category_rules.model(coupon=coupon, category=item) for item in self.cleaned_data["categories"]]
            )
            coupon.brand_rules.bulk_create(
                [coupon.brand_rules.model(coupon=coupon, brand=item) for item in self.cleaned_data["brands"]]
            )
            return coupon
