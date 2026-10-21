from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from catalog.models import Product
from core.rate_limits import rate_limit
from reviews.forms import ReviewForm


@require_POST
@rate_limit(key="review-submit", limit=5, period=3600)
def submit(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    form = ReviewForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please provide a valid rating.")
        return redirect("catalog:product_detail", slug=slug)
    review = form.save(commit=False)
    review.product = product
    review.user = request.user if request.user.is_authenticated else None
    review.save()
    messages.success(request, "Thank you. Your review will appear after moderation.")
    return redirect("catalog:product_detail", slug=slug)
