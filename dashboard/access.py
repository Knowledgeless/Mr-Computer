from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from accounts.models import CustomerProfile


ROLE_PERMISSIONS = {
    "overview": {
        CustomerProfile.Role.OWNER,
        CustomerProfile.Role.ADMIN,
        CustomerProfile.Role.MANAGER,
        CustomerProfile.Role.INVENTORY_MANAGER,
        CustomerProfile.Role.ORDER_MANAGER,
        CustomerProfile.Role.CONTENT_MANAGER,
    },
    "catalog": {
        CustomerProfile.Role.OWNER,
        CustomerProfile.Role.ADMIN,
        CustomerProfile.Role.MANAGER,
        CustomerProfile.Role.CONTENT_MANAGER,
    },
    "inventory": {
        CustomerProfile.Role.OWNER,
        CustomerProfile.Role.ADMIN,
        CustomerProfile.Role.MANAGER,
        CustomerProfile.Role.INVENTORY_MANAGER,
    },
    "orders": {
        CustomerProfile.Role.OWNER,
        CustomerProfile.Role.ADMIN,
        CustomerProfile.Role.MANAGER,
        CustomerProfile.Role.ORDER_MANAGER,
    },
    "content": {
        CustomerProfile.Role.OWNER,
        CustomerProfile.Role.ADMIN,
        CustomerProfile.Role.MANAGER,
        CustomerProfile.Role.CONTENT_MANAGER,
    },
    "customers": {CustomerProfile.Role.OWNER, CustomerProfile.Role.ADMIN, CustomerProfile.Role.MANAGER},
}


def dashboard_role(section):
    allowed_roles = ROLE_PERMISSIONS[section]

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if not request.user.is_staff:
                raise PermissionDenied
            role = CustomerProfile.objects.filter(user=request.user).values_list("role", flat=True).first()
            if role not in allowed_roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
