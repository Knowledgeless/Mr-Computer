from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from accounts.models import CustomerAddress, phone_validator

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"autocomplete": "username", "class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "class": "form-control"}))


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"autocomplete": "email", "class": "form-control"}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class CustomerAddressForm(forms.ModelForm):
    phone = forms.CharField(validators=[phone_validator], widget=forms.TelInput(attrs={"autocomplete": "tel"}))

    class Meta:
        model = CustomerAddress
        fields = (
            "label",
            "recipient_name",
            "phone",
            "address_line_1",
            "address_line_2",
            "city",
            "area",
            "postal_code",
            "is_default",
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        address = super().save(commit=False)
        if self.user is not None:
            address.user = self.user
        if commit:
            if address.is_default and address.user_id:
                CustomerAddress.objects.filter(user=address.user, is_default=True).exclude(pk=address.pk).update(is_default=False)
            address.save()
        return address
