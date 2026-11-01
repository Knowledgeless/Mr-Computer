from django import forms

from accounts.models import CustomerProfile
from orders.models import Order
from shipping.models import ShippingRate, ShippingZone


class OrderStatusForm(forms.Form):
    order_status = forms.ChoiceField(choices=Order.Status.choices)
    cod_collected = forms.BooleanField(required=False)
    admin_note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class CustomerRoleForm(forms.Form):
    role = forms.ChoiceField(choices=CustomerProfile.Role.choices)


class ShippingZoneForm(forms.ModelForm):
    class Meta:
        model = ShippingZone
        fields = ("name", "division", "district", "upazila", "description", "is_active")


class ShippingRateForm(forms.ModelForm):
    class Meta:
        model = ShippingRate
        fields = ("minimum_order_amount", "maximum_order_amount", "rate", "is_active")
