from django import forms

from reviews.models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "title", "comment")
        widgets = {"comment": forms.Textarea(attrs={"rows": 4})}
