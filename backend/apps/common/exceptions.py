import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def global_exception_handler(exc, context):
    """
    [HARD-01] Wraps DRF's default handler.
    All API errors return:
    {
        "error": {
            "code":    "validation_error",
            "message": "Human readable message",
            "detail":  <original DRF detail — dict or list>
        }
    }
    Unhandled exceptions return 500 with no internal detail exposed.
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_code = _resolve_error_code(response.status_code)
        original_detail = response.data

        # Flatten single-key {'detail': '...'} to a plain string
        if isinstance(original_detail, dict) and list(original_detail.keys()) == ['detail']:
            message = str(original_detail['detail'])
            detail = None
        elif isinstance(original_detail, dict):
            message = 'Validation failed.'
            detail = original_detail
        elif isinstance(original_detail, list):
            message = 'Validation failed.'
            detail = original_detail
        else:
            message = str(original_detail)
            detail = None

        payload = {
            'error': {
                'code':    error_code,
                'message': message,
            }
        }
        if detail is not None:
            payload['error']['detail'] = detail

        response.data = payload
        return response

    # Truly unhandled — log it, return 500 with no internal info
    logger.exception(
        f'Unhandled exception in {context.get("view").__class__.__name__}: {exc}'
    )
    return Response(
        {
            'error': {
                'code':    'internal_server_error',
                'message': 'An unexpected error occurred. Please try again later.',
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _resolve_error_code(status_code: int) -> str:
    return {
        400: 'bad_request',
        401: 'authentication_required',
        403: 'permission_denied',
        404: 'not_found',
        405: 'method_not_allowed',
        429: 'rate_limit_exceeded',
        500: 'internal_server_error',
    }.get(status_code, 'api_error')