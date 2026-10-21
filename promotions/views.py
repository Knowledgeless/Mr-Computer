from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from cart.services import cart_subtotal, get_cart_for_request
from core.rate_limits import rate_limit
from promotions.forms import CouponApplyForm
from promotions.services import validate_coupon


@require_POST
@rate_limit(key="coupon-validation", limit=10, period=300)
def validate(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Sign in to use a coupon."}, status=403)
    form = CouponApplyForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"error": "Enter a valid coupon code."}, status=400)
    cart = get_cart_for_request(request)
    items = list(cart.items.select_related("variant__product__category", "variant__product__brand"))
    try:
        coupon, _, discount = validate_coupon(
            code=form.cleaned_data["code"],
            user=request.user,
            subtotal=cart_subtotal(cart),
            cart_items=items,
        )
    except ValidationError as error:
        request.session.pop("applied_coupon", None)
        return JsonResponse({"error": error.messages[0]}, status=400)
    request.session["applied_coupon"] = coupon.code
    return JsonResponse(
        {
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount": str(discount),
            "message": "Coupon is valid. It will be rechecked during checkout.",
        }
    )
