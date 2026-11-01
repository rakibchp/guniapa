from django.core.cache import cache
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from redis.exceptions import RedisError


@require_GET
def health_check(request):
    """
    Check API, database, and configured cache availability.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        cache.set("guniapa:health-check", "ok", timeout=1)
        if cache.get("guniapa:health-check") != "ok":
            raise RedisError("Cache health check did not round-trip.")

        return JsonResponse({
            "status": "healthy",
            "service": "guniapa-api",
            "database": "connected",
            "cache": "connected",
        })

    except DatabaseError:
        return JsonResponse(
            {
                "status": "unhealthy",
                "service": "guniapa-api",
                "database": "unavailable",
                "cache": "unchecked",
            },
            status=503,
        )
    except RedisError:
        return JsonResponse(
            {
                "status": "unhealthy",
                "service": "guniapa-api",
                "database": "connected",
                "cache": "unavailable",
            },
            status=503,
        )