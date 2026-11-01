from django.test import TestCase


class HealthCheckTests(TestCase):
    def test_health_check_reports_database_and_cache(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "healthy",
                "service": "guniapa-api",
                "database": "connected",
                "cache": "connected",
            },
        )
