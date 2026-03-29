"""
Standardized error handling for API responses.

Defines error codes, error classes, and response models for consistent
error handling across the application.
"""

from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class ErrorCode(str, Enum):
    """Standardized error codes for API responses"""

    # General errors (1xxx)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    BAD_REQUEST = "BAD_REQUEST"

    # Domain errors (2xxx)
    DOMAIN_NOT_FOUND = "DOMAIN_NOT_FOUND"
    DOMAIN_ALREADY_EXISTS = "DOMAIN_ALREADY_EXISTS"
    INVALID_DOMAIN_NAME = "INVALID_DOMAIN_NAME"
    DOMAIN_UPDATE_FAILED = "DOMAIN_UPDATE_FAILED"
    DOMAIN_DELETE_FAILED = "DOMAIN_DELETE_FAILED"
    DOMAIN_HAS_DOCUMENTS = "DOMAIN_HAS_DOCUMENTS"

    # Document errors (3xxx)
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    DOCUMENT_UPLOAD_FAILED = "DOCUMENT_UPLOAD_FAILED"
    DOCUMENT_PROCESSING_FAILED = "DOCUMENT_PROCESSING_FAILED"
    INVALID_DOCUMENT_TYPE = "INVALID_DOCUMENT_TYPE"
    INVALID_DOCUMENT_STAGE = "INVALID_DOCUMENT_STAGE"
    DOCUMENT_TOO_LARGE = "DOCUMENT_TOO_LARGE"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"

    # Processing stage errors (4xxx)
    INVALID_STAGE = "INVALID_STAGE"
    STAGE_NOT_FOUND = "STAGE_NOT_FOUND"

    # Configuration errors (5xxx)
    CONFIG_NOT_FOUND = "CONFIG_NOT_FOUND"

    # Processing errors (6xxx)
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_FAILED = "TASK_FAILED"
    PROCESSING_TIMEOUT = "PROCESSING_TIMEOUT"
    
    # Chat errors (7xxx)
    CONVERSATION_NOT_FOUND = "CONVERSATION_NOT_FOUND"
    RAG_QUERY_FAILED = "RAG_QUERY_FAILED"


class APIError(Exception):
    """
    Base exception class for API errors.

    Provides structured error information for consistent error responses.
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize API error.

        Args:
            message: Human-readable error message
            error_code: Standardized error code
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON response"""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "timestamp": datetime.utcnow().isoformat()
        }


class ErrorResponse(BaseModel):
    """Pydantic model for error responses"""
    error_code: str = Field(..., description="Standardized error code")
    message: str = Field(..., description="Human-readable error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    timestamp: str = Field(..., description="ISO 8601 timestamp of error")


# Specific error classes for common scenarios

class DomainNotFoundError(APIError):
    """Domain not found error"""
    def __init__(self, domain_id: str):
        super().__init__(
            message=f"Domain with ID '{domain_id}' not found",
            error_code=ErrorCode.DOMAIN_NOT_FOUND,
            status_code=404,
            details={"domain_id": domain_id}
        )


class DomainAlreadyExistsError(APIError):
    """Domain already exists error"""
    def __init__(self, domain_name: str):
        super().__init__(
            message=f"Domain with name '{domain_name}' already exists",
            error_code=ErrorCode.DOMAIN_ALREADY_EXISTS,
            status_code=400,
            details={"domain_name": domain_name}
        )


class DocumentNotFoundError(APIError):
    """Document not found error"""
    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document with ID '{document_id}' not found",
            error_code=ErrorCode.DOCUMENT_NOT_FOUND,
            status_code=404,
            details={"document_id": document_id}
        )


class InvalidStageError(APIError):
    """Invalid stage error"""
    def __init__(self, stage: str, valid_stages: list):
        super().__init__(
            message=f"Invalid stage '{stage}'. Must be one of: {', '.join(valid_stages)}",
            error_code=ErrorCode.INVALID_STAGE,
            status_code=400,
            details={"stage": stage, "valid_stages": valid_stages}
        )


class ConfigNotFoundError(APIError):
    """Configuration not found error"""
    def __init__(self, config_type: str, identifier: str):
        super().__init__(
            message=f"{config_type} configuration not found: {identifier}",
            error_code=ErrorCode.CONFIG_NOT_FOUND,
            status_code=404,
            details={"config_type": config_type, "identifier": identifier}
        )


class ValidationError(APIError):
    """Validation error"""
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details=details
        )
