from django.shortcuts import render

# Create your views here.
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    """
    Check the API and database availability.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        return JsonResponse({
            "status": "healthy",
            "service": "guniapa-api",
            "database": "connected",
        })

    except DatabaseError:
        return JsonResponse(
            {
                "status": "unhealthy",
                "service": "guniapa-api",
                "database": "unavailable",
            },
            status=503,
        )