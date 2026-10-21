from django import forms

from accounts.models import CustomerProfile
from orders.models import Order


class OrderStatusForm(forms.Form):
    order_status = forms.ChoiceField(choices=Order.Status.choices)
    cod_collected = forms.BooleanField(required=False)
    admin_note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class CustomerRoleForm(forms.Form):
    role = forms.ChoiceField(choices=CustomerProfile.Role.choices)
