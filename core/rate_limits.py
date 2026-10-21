from functools import wraps

from django.core.cache import cache
from django.http import HttpResponse, JsonResponse


def rate_limit(*, key, limit, period):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.method != "POST":
                return view_func(request, *args, **kwargs)
            user_id = request.user.pk if request.user.is_authenticated else ""
            identity = ":".join(
                (
                    str(user_id or request.session.session_key or ""),
                    request.META.get("REMOTE_ADDR", "unknown"),
                )
            )
            cache_key = f"rate-limit:{key}:{identity}"
            current_count = cache.get(cache_key, 0)
            if current_count >= limit:
                if "application/json" in request.headers.get("Accept", ""):
                    response = JsonResponse({"error": "Too many requests. Please try again later."}, status=429)
                else:
                    response = HttpResponse("Too many requests. Please try again later.", status=429)
                response["Retry-After"] = str(period)
                return response
            if not cache.add(cache_key, 1, timeout=period):
                try:
                    cache.incr(cache_key)
                except ValueError:
                    cache.add(cache_key, 1, timeout=period)
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
