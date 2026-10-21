from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator

from catalog.models import ProductVariant


class AddCartItemForm(forms.Form):
    variant = forms.ModelChoiceField(
        queryset=ProductVariant.objects.filter(is_active=True, product__is_active=True),
        widget=forms.HiddenInput(),
    )
    quantity = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
    )


class UpdateCartItemForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=20)
