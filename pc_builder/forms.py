from django import forms

from pc_builder.models import BuildRequest


class BuildRequestForm(forms.ModelForm):
    class Meta:
        model = BuildRequest
        fields = ("customer_name", "phone", "email", "budget", "purpose", "notes")
        widgets = {"notes": forms.Textarea(attrs={"rows": 4})}
