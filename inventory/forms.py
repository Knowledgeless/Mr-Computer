from django import forms

from catalog.models import ProductVariant


class InventoryAdjustmentForm(forms.Form):
    variant = forms.ModelChoiceField(queryset=ProductVariant.objects.filter(is_active=True).select_related("product").order_by("product__name"))
    quantity_delta = forms.IntegerField()
    note = forms.CharField(max_length=500, widget=forms.Textarea(attrs={"rows": 3}))

    def clean_quantity_delta(self):
        delta = self.cleaned_data["quantity_delta"]
        if delta == 0:
            raise forms.ValidationError("Enter a non-zero stock adjustment.")
        return delta
