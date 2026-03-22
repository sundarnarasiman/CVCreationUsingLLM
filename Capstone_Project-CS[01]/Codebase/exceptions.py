"""
Custom exception hierarchy for the CV Creation System.

This module defines domain-specific exceptions to replace generic Exception usage
and enable graceful, fail-fast error handling across the application.
"""


class CVSystemError(Exception):
    """Base exception for all CV System errors."""
    
    def __init__(self, message, debug_info=None):
        """
        Initialize CVSystemError.
        
        Args:
            message: User-safe error message
            debug_info: Optional dict with additional debug context (e.g., traceback, API response)
        """
        self.message = message
        self.debug_info = debug_info or {}
        super().__init__(self.message)


class ConfigurationError(CVSystemError):
    """Raised when configuration (API keys, env vars, paths) is missing or invalid."""
    pass


class FileValidationError(CVSystemError):
    """Raised when a file cannot be read, doesn't exist, has wrong format, or encoding fails."""
    pass


class DataValidationError(CVSystemError):
    """Raised when input data (JSON, resume text, job description) is malformed or incomplete."""
    pass


class APIClientError(CVSystemError):
    """Raised when OpenAI API calls fail (timeout, rate limit, authentication, network)."""
    pass


class LLMResponseError(CVSystemError):
    """Raised when LLM response cannot be parsed, validated, or is malformed."""
    pass


class ExportError(CVSystemError):
    """Raised when resume export to PDF/DOCX fails (missing schema, render error, permission denied)."""
    pass


class UserInputError(CVSystemError):
    """Raised when user input (CLI args, file paths) is invalid or unsafe."""
    pass
