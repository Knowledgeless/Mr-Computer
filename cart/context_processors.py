from django.db.models import Count

from cart.models import CartItem


def cart_count(request):
    if request.user.is_authenticated:
        items = CartItem.objects.filter(cart__user=request.user)
    elif request.session.session_key:
        items = CartItem.objects.filter(cart__session_key=request.session.session_key, cart__user__isnull=True)
    else:
        return {"cart_count": 0}
    return {"cart_count": items.aggregate(total=Count("pk"))["total"] or 0}
