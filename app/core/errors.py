from __future__ import annotations
from typing import Any
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.context import correlation_id_var

class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class NotConfiguredError(AppError):
    def __init__(self, provider: str):
        super().__init__(f'{provider.upper()}_NOT_CONFIGURED', f'{provider} integration is not configured', 503)

class AuthenticationRequiredError(AppError):
    def __init__(self, provider: str):
        super().__init__(f'{provider.upper()}_NOT_AUTHENTICATED', f'{provider} authentication is required', 401)

class ProviderUnavailableError(AppError):
    def __init__(self, provider: str, message: str = 'Provider unavailable'):
        super().__init__(f'{provider.upper()}_UNAVAILABLE', message, 503)

class ProviderRateLimitError(AppError):
    def __init__(self, provider: str):
        super().__init__(f'{provider.upper()}_RATE_LIMITED', f'{provider} rate limit exceeded', 429)

def error_body(code: str, message: str, details: dict[str, Any] | None = None):
    return {
        'success': False,
        'error': {
            'code': code,
            'message': message,
            'correlation_id': correlation_id_var.get() or 'unknown',
            'details': details or {},
        },
    }

async def app_error_handler(_: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content=error_body(exc.code, exc.message, exc.details))

async def validation_error_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content=error_body('VALIDATION_ERROR', 'Request validation failed', {'errors': exc.errors()}))

async def unhandled_error_handler(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content=error_body('INTERNAL_ERROR', 'Internal server error'))
