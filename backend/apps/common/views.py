from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            connection.ensure_connection()
            db_status = 'ok'
        except Exception as e:
            logger.error(f'Health check DB failure: {e}')
            db_status = 'error'

        status_code = 200 if db_status == 'ok' else 503
        return Response(
            {
                'status': 'ok' if db_status == 'ok' else 'degraded',
                'database': db_status,
                'version': '1.0.0',
            },
            status=status_code,
        )