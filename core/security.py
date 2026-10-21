import hashlib


def request_ip(request):
    return request.META.get("REMOTE_ADDR", "")[:45]


def fingerprint(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
