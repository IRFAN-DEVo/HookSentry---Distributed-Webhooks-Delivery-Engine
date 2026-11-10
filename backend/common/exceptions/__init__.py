import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError, AuthenticationFailed, NotAuthenticated, PermissionDenied

logger = logging.getLogger(__name__)

class HookSentryException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'An internal system error occurred in the delivery engine.'
    default_code = 'internal_server_error'

class WorkspaceAccessDenied(PermissionDenied):
    default_detail = 'You do not have access to this workspace or resource.'
    default_code = 'workspace_access_denied'

class SSRFProtectionError(ValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Destination URL was blocked by SSRF protection filters.'
    default_code = 'ssrf_blocked'

class IdempotencyConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Idempotency key has already been used with a different request payload.'
    default_code = 'idempotency_conflict'

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        custom_data = {
            'error': {
                'code': getattr(exc, 'default_code', 'error'),
                'message': 'Request processing failed.',
                'details': response.data
            }
        }
        if isinstance(exc, ValidationError):
            custom_data['error']['code'] = 'validation_error'
            custom_data['error']['message'] = 'One or more fields failed validation.'
        elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
            custom_data['error']['code'] = 'authentication_failed'
            custom_data['error']['message'] = 'Authentication credentials were not provided or are invalid.'
        elif isinstance(exc, PermissionDenied):
            custom_data['error']['code'] = 'permission_denied'
            custom_data['error']['message'] = str(exc.detail) if hasattr(exc, 'detail') else 'Permission denied.'
        elif hasattr(exc, 'detail') and isinstance(exc.detail, str):
            custom_data['error']['message'] = exc.detail

        response.data = custom_data
        return response

    # Unhandled exceptions
    logger.exception('Unhandled exception occurred in view context: %s', context)
    return Response(
        {
            'error': {
                'code': 'internal_server_error',
                'message': 'An unexpected internal error occurred.',
                'details': str(exc) if getattr(exc, 'detail', None) else 'Contact administrator.'
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
