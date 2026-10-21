from django import forms

from accounts.models import phone_validator
from shipping.models import ShippingZone


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(max_length=160)
    customer_email = forms.EmailField(required=False)
    customer_phone = forms.CharField(max_length=24, validators=[phone_validator], widget=forms.TelInput(attrs={"autocomplete": "tel"}))
    address_line_1 = forms.CharField(max_length=240)
    address_line_2 = forms.CharField(max_length=240, required=False)
    city = forms.CharField(max_length=100)
    area = forms.CharField(max_length=120, required=False)
    postal_code = forms.CharField(max_length=20, required=False)
    shipping_zone = forms.ModelChoiceField(queryset=ShippingZone.objects.none(), required=False)
    customer_note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    coupon_code = forms.CharField(max_length=64, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["shipping_zone"].queryset = ShippingZone.objects.filter(is_active=True).order_by("name")

    def address_snapshot(self):
        return {
            "recipient_name": self.cleaned_data["customer_name"].strip(),
            "phone": self.cleaned_data["customer_phone"].strip(),
            "address_line_1": self.cleaned_data["address_line_1"].strip(),
            "address_line_2": self.cleaned_data["address_line_2"].strip(),
            "city": self.cleaned_data["city"].strip(),
            "area": self.cleaned_data["area"].strip(),
            "postal_code": self.cleaned_data["postal_code"].strip(),
        }
