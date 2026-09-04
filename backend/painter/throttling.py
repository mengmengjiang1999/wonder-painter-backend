"""Small cache-backed rate limiter for the prototype API."""

import hashlib
import time
from functools import wraps

from django.core.cache import cache
from django.http import JsonResponse


def rate_limit(bucket, limit, window_seconds):
    """Limit requests per client IP in a fixed time window."""

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            address = request.META.get("REMOTE_ADDR", "unknown")
            window = int(time.time() // window_seconds)
            identity = hashlib.sha256(address.encode("utf-8")).hexdigest()
            key = f"rate-limit:{bucket}:{identity}:{window}"
            if cache.add(key, 1, timeout=window_seconds):
                count = 1
            else:
                try:
                    count = cache.incr(key)
                except ValueError:
                    cache.set(key, 1, timeout=window_seconds)
                    count = 1
            if count > limit:
                response = JsonResponse({"message": "Too many requests"}, status=429)
                response["Retry-After"] = str(window_seconds)
                return response
            return view(request, *args, **kwargs)

        return wrapped

    return decorator
