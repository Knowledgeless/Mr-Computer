from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from cms.forms import ContactMessageForm
from core.rate_limits import rate_limit


@require_http_methods(["GET", "POST"])
@rate_limit(key="contact-message", limit=5, period=3600)
def contact(request):
    form = ContactMessageForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thanks for contacting us. Our team will follow up.")
        return redirect("cms:contact")
    return render(request, "storefront/contact.html", {"form": form})
