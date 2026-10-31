from accounts.models import WishlistItem


def wishlist_variant_ids(request):
    if not request.user.is_authenticated:
        return {"wishlist_variant_ids": set()}

    return {
        "wishlist_variant_ids": set(
            WishlistItem.objects.filter(wishlist__user=request.user).values_list("variant_id", flat=True)
        )
    }
