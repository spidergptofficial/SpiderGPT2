"""SpiderGPT Custom Exceptions and Error Standards.

Ensures consistent API error structures matching the SpiderGPT format:
{
  "error": {
    "code": "...",
    "message": "...",
    "details": {}
  }
}
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class SpiderGPTException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(
            status_code=status_code,
            detail={"code": self.code, "message": self.message, "details": self.details},
        )


class AuthenticationRequiredException(SpiderGPTException):
    def __init__(self, message: str = "Authentication credentials were not provided or have expired."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTH_REQUIRED",
            message=message,
        )


class InvalidTokenException(SpiderGPTException):
    def __init__(self, message: str = "The provided authentication token is invalid or expired."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INVALID_TOKEN",
            message=message,
        )


class ForbiddenException(SpiderGPTException):
    def __init__(self, message: str = "You do not have permission to access this resource."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=message,
        )


class NotFoundException(SpiderGPTException):
    def __init__(self, resource: str = "Resource", message: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=message or f"{resource} not found.",
        )


class UsageLimitReachedException(SpiderGPTException):
    def __init__(
        self,
        usage_type: str,
        limit: int,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        msg = message or f"You have reached your limit for {usage_type} ({limit}). Upgrade your plan for higher limits."
        d = details or {}
        d.update({"usage_type": usage_type, "limit": limit})
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="USAGE_LIMIT_REACHED",
            message=msg,
            details=d,
        )


class FeatureNotAvailableException(SpiderGPTException):
    def __init__(self, feature: str, required_plan: str = "PRO"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FEATURE_NOT_AVAILABLE",
            message=f"Feature '{feature}' is not available on your current plan. Upgrade to {required_plan} to unlock.",
            details={"feature": feature, "required_plan": required_plan},
        )


class PaymentRequiredException(SpiderGPTException):
    def __init__(self, message: str = "Payment or active subscription required to access this resource."):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            code="PAYMENT_REQUIRED",
            message=message,
        )


class PaymentFailedException(SpiderGPTException):
    def __init__(self, message: str = "Payment processing failed.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="PAYMENT_FAILED",
            message=message,
            details=details,
        )


class ProviderUnavailableException(SpiderGPTException):
    def __init__(self, provider_type: str, provider_name: str, message: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="PROVIDER_UNAVAILABLE",
            message=message or f"{provider_type.title()} provider '{provider_name}' is currently unavailable or unconfigured.",
            details={"provider_type": provider_type, "provider_name": provider_name},
        )


class AIProviderException(SpiderGPTException):
    def __init__(self, message: str, provider: str, details: Optional[Dict[str, Any]] = None):
        d = details or {}
        d["provider"] = provider
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="AI_PROVIDER_ERROR",
            message=message,
            details=d,
        )


class ImageProviderException(SpiderGPTException):
    def __init__(self, message: str, provider: str, details: Optional[Dict[str, Any]] = None):
        d = details or {}
        d["provider"] = provider
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="IMAGE_PROVIDER_ERROR",
            message=message,
            details=d,
        )


class SearchProviderException(SpiderGPTException):
    def __init__(self, message: str, provider: str, details: Optional[Dict[str, Any]] = None):
        d = details or {}
        d["provider"] = provider
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="SEARCH_PROVIDER_ERROR",
            message=message,
            details=d,
        )


class ValidationErrorException(SpiderGPTException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=message,
            details=details,
        )


class SpiderAlreadyExistsException(SpiderGPTException):
    def __init__(self, message: str = "A Spider has already been created for this user. Only one Spider is allowed."):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="SPIDER_ALREADY_EXISTS",
            message=message,
        )


class RateLimitExceededException(SpiderGPTException):
    def __init__(self, message: str = "Too many requests. Please slow down."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMIT_EXCEEDED",
            message=message,
        )
