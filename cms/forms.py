from django import forms

from cms.models import Banner, ContactMessage, HomeSection, Page, SiteSettings


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ("title", "subtitle", "image", "button_text", "button_url", "start_at", "end_at", "is_active", "display_order")
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ("title", "slug", "content", "meta_title", "meta_description", "is_published")
        widgets = {"content": forms.Textarea(attrs={"rows": 12})}


class HomeSectionForm(forms.ModelForm):
    class Meta:
        model = HomeSection
        fields = ("title", "subtitle", "display_order", "is_active")


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = (
            "store_name",
            "logo",
            "favicon",
            "phone",
            "email",
            "address",
            "facebook_url",
            "youtube_url",
            "instagram_url",
            "footer_text",
            "currency",
            "default_shipping_cost",
            "google_analytics_id",
        )


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "phone", "subject", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}
