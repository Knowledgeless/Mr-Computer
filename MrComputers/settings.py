
import os
from pathlib import Path

from dotenv import load_dotenv


# =============================================================================
# BASE DIRECTORY
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================================
# ENVIRONMENT HELPERS
# =============================================================================
load_dotenv(BASE_DIR / ".env")
def env_bool(name, default=False):
    value = os.environ.get(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [
        item.strip()
        for item in os.environ.get(name, default).split(",")
        if item.strip()
    ]


# =============================================================================
# DEBUG AND SECRET KEY
# =============================================================================

# Local development defaults to DEBUG=True.
# Set DJANGO_DEBUG=False in production.
DEBUG = env_bool("DJANGO_DEBUG", True)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError(
            "DJANGO_SECRET_KEY must be configured in production."
        )

    # Development only. Never use this key in production.
    SECRET_KEY = "django-local-development-key-not-for-production"


# =============================================================================
# HOSTS AND CSRF
# =============================================================================

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1",
)

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
)


# =============================================================================
# APPLICATIONS
# =============================================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    "accounts.apps.AccountsConfig",
    "catalog.apps.CatalogConfig",
    "inventory.apps.InventoryConfig",
    "cart.apps.CartConfig",
    "orders.apps.OrdersConfig",
    "payments.apps.PaymentsConfig",
    "promotions.apps.PromotionsConfig",
    "pc_builder.apps.PcBuilderConfig",
    "reviews.apps.ReviewsConfig",
    "shipping.apps.ShippingConfig",
    "cms.apps.CmsConfig",
    "reports.apps.ReportsConfig",
    "audit.apps.AuditConfig",
    "dashboard.apps.DashboardConfig",
]


# =============================================================================
# MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =============================================================================
# URL CONFIGURATION
# =============================================================================

ROOT_URLCONF = "MrComputers.urls"

WSGI_APPLICATION = "MrComputers.wsgi.application"
ASGI_APPLICATION = "MrComputers.asgi.application"


# =============================================================================
# TEMPLATES
# =============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "builtins": ["django.contrib.humanize.templatetags.humanize"],
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "cart.context_processors.cart_count",
                "accounts.context_processors.wishlist_variant_ids",
            ],
        },
    },
]


# =============================================================================
# POSTGRESQL DATABASE
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "mrcomputers"),
        "USER": os.environ.get("POSTGRES_USER", "mrcomputers"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": (
            {"sslmode": os.environ["POSTGRES_SSLMODE"]}
            if os.environ.get("POSTGRES_SSLMODE")
            else {}
        ),
    }
}


# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"

USE_I18N = True
USE_TZ = True


# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATIC_DIR = BASE_DIR / "static"

STATICFILES_DIRS = (
    [STATIC_DIR]
    if STATIC_DIR.is_dir()
    else []
)


# =============================================================================
# MEDIA FILES
# =============================================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# =============================================================================
# UPLOAD LIMITS
# =============================================================================

DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024


# =============================================================================
# COOKIE SECURITY
# =============================================================================

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_SECURE = not DEBUG


# =============================================================================
# SECURITY HEADERS
# =============================================================================

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

X_FRAME_OPTIONS = "DENY"

SECURE_SSL_REDIRECT = env_bool(
    "DJANGO_SECURE_SSL_REDIRECT",
    not DEBUG,
)

SECURE_HSTS_SECONDS = int(
    os.environ.get(
        "DJANGO_SECURE_HSTS_SECONDS",
        "31536000" if not DEBUG else "0",
    )
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    not DEBUG
    and SECURE_HSTS_SECONDS > 0
)


# =============================================================================
# CACHE / REDIS
# =============================================================================

REDIS_URL = os.environ.get("REDIS_URL")

if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    if not DEBUG:
        raise RuntimeError(
            "Configure REDIS_URL in production when Redis-backed "
            "shared caching and rate limiting are required."
        )

    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "mr-computers-local",
        }
    }


# =============================================================================
# DEFAULT PRIMARY KEY
# =============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
