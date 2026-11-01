from django import forms

from accounts.models import phone_validator
from shipping.services import (
    get_postal_locations,
    is_valid_delivery_location,
    is_valid_postal_location,
)


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(
        max_length=160,
        widget=forms.TextInput(attrs={"placeholder": " "}),
    )
    customer_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"placeholder": " "}),
    )
    customer_phone = forms.CharField(
        max_length=24,
        validators=[phone_validator],
        widget=forms.TelInput(attrs={"autocomplete": "tel", "placeholder": " "}),
    )
    address_line_1 = forms.CharField(
        max_length=240,
        widget=forms.TextInput(attrs={"placeholder": " "}),
    )
    division = forms.CharField(
        label="Division",
        widget=forms.Select(
            choices=[("", "Choose a division")],
            attrs={"data-location-level": "division", "class": "form-select"},
        )
    )
    district = forms.CharField(
        label="District",
        widget=forms.Select(
            choices=[("", "Choose a district")],
            attrs={"data-location-level": "district", "class": "form-select", "disabled": True},
        )
    )
    upazila = forms.CharField(
        label="City / Upazila",
        widget=forms.Select(
            choices=[("", "Choose a city")],
            attrs={"data-location-level": "city", "class": "form-select", "disabled": True},
        )
    )
    postal_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"autocomplete": "postal-code", "readonly": True, "placeholder": " "}),
    )
    customer_note = forms.CharField(
        label="Order note",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": " "}),
    )
    coupon_code = forms.CharField(max_length=64, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
            field.widget.attrs.setdefault("placeholder", " ")
        postal_locations = get_postal_locations()
        self.fields["division"].choices = [("", "Choose a division")] + [
            (division, division) for division in sorted(postal_locations)
        ]
        for name in ("division", "district", "upazila"):
            self.fields[name].widget.attrs["data-selected"] = (
                self.data.get(name, "") if self.is_bound else self.initial.get(name, "")
            )

    def clean(self):
        cleaned_data = super().clean()
        division = cleaned_data.get("division")
        district = cleaned_data.get("district")
        upazila = cleaned_data.get("upazila")
        if division and district and upazila and not is_valid_delivery_location(
            division=division,
            district=district,
            upazila=upazila,
        ):
            self.add_error("upazila", "Choose a valid division, district, and upazila.")
        city = cleaned_data.get("upazila")
        postal_code = cleaned_data.get("postal_code")
        if division and district and city and postal_code and not is_valid_postal_location(
            division=division,
            district=district,
            city=city,
            postal_code=postal_code,
        ):
            self.add_error("postal_code", "Choose a valid upazila to set the postal code.")
        return cleaned_data

    def address_snapshot(self):
        return {
            "recipient_name": self.cleaned_data["customer_name"].strip(),
            "phone": self.cleaned_data["customer_phone"].strip(),
            "address_line_1": self.cleaned_data["address_line_1"].strip(),
            "address_line_2": "",
            "division": self.cleaned_data["division"],
            "district": self.cleaned_data["district"],
            "upazila": self.cleaned_data["upazila"],
            "city": self.cleaned_data["upazila"].strip(),
            "postal_code": self.cleaned_data["postal_code"].strip(),
        }
