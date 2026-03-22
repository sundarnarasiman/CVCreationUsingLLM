"""
User-friendly error messages with emoji indicators.

This module provides a centralized message system for communicating errors,
warnings, and status updates to users in the terminal with clear, actionable
guidance and emoji icons for visual clarity.
"""

from logging_config import get_logger

logger = get_logger(__name__)

# Message templates with emoji indicators
MESSAGE_TEMPLATES = {
    # Configuration errors
    "api_key_missing": "❌ OpenAI API key not found. Set OPENAI_API_KEY environment variable.",
    "config_invalid": "❌ Configuration error: {detail}",
    
    # File errors
    "file_not_found": "❌ File not found: {path}",
    "file_not_readable": "❌ Cannot read file: {path} ({reason})",
    "file_encoding_error": "❌ File encoding error: {path} (expected {encoding})",
    "file_permission_denied": "❌ Permission denied reading: {path}",
    
    # Input validation
    "input_empty": "❌ {field} is empty. Please provide valid input.",
    "input_invalid": "❌ Invalid input for {field}: {detail}",
    "input_path_unsafe": "❌ Invalid file path: {path}",
    
    # JSON/Data parsing
    "json_parse_error": "❌ Invalid JSON format in {context}. Please check the file format.",
    "data_missing_keys": "❌ Missing required fields in {context}: {fields}",
    "data_type_error": "❌ Data type error in {context}: expected {expected}, got {actual}",
    
    # LLM/API errors
    "api_timeout": "⏱️ Request timed out. Please check your connection and try again.",
    "api_rate_limit": "⏱️ Rate limited. Please wait a moment and try again.",
    "api_auth_failed": "❌ Authentication failed. Check OPENAI_API_KEY validity.",
    "api_error": "❌ API error: {detail}",
    "llm_response_invalid": "❌ Invalid response from LLM. Please try again.",
    "llm_parse_failed": "❌ Could not parse LLM response. Please try again.",
    
    # Export/formatting errors
    "export_failed": "❌ Export failed: {detail}",
    "pdf_generation_failed": "❌ PDF generation failed: {detail}",
    "docx_generation_failed": "❌ Word document generation failed: {detail}",
    "export_permission_denied": "❌ Cannot write to output directory: {path}",
    
    # Workflow errors
    "workflow_max_iterations": "❌ Revision iteration limit reached. Finalizing with last version.",
    "workflow_failed": "❌ Workflow failed: {detail}",
    "matching_failed": "❌ Profile-to-job matching failed: {detail}",
    
    # Success/Info
    "success": "✅ {message}",
    "info": "ℹ️ {message}",
    "warning": "⚠️ {message}",
    "in_progress": "⏳ {message}",
}


def get_message(error_type, **kwargs):
    """
    Get a formatted user-friendly message.
    
    Args:
        error_type: Message template key (e.g., "file_not_found", "api_timeout")
        **kwargs: Format string arguments (e.g., path="resume.pdf")
    
    Returns:
        str: Formatted message with emoji indicator
    """
    template = MESSAGE_TEMPLATES.get(error_type, "❌ An unexpected error occurred.")
    
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.debug(f"Missing format argument {e} for message type {error_type}")
        return template


def print_error(error_type, **kwargs):
    """
    Print an error message to terminal and log it.
    
    Args:
        error_type: Message template key
        **kwargs: Format arguments
    """
    message = get_message(error_type, **kwargs)
    print(message, file=__import__('sys').stderr)
    logger.error(message)


def print_warning(warning_type, **kwargs):
    """
    Print a warning message to terminal and log it.
    
    Args:
        warning_type: Message template key
        **kwargs: Format arguments
    """
    message = get_message(warning_type, **kwargs)
    print(message)
    logger.warning(message)


def print_status(status_type, message):
    """
    Print a status message (info/warning/success).
    
    Args:
        status_type: Type of status ("success", "info", "warning", "in_progress")
        message: Status message content
    """
    formatted = get_message(status_type, message=message)
    print(formatted)
    logger.info(formatted)


def error_file_operation(file_path, operation="read", error_obj=None):
    """
    Generate contextual error message for file operations.
    
    Args:
        file_path: Path to file that failed
        operation: Operation type ("read", "write", "parse")
        error_obj: Optional exception object for debugging
    
    Returns:
        str: Contextual error message
    """
    if error_obj:
        error_name = type(error_obj).__name__
        if error_name == "FileNotFoundError":
            return get_message("file_not_found", path=file_path)
        elif error_name == "PermissionError":
            return get_message("file_permission_denied", path=file_path)
        elif error_name == "UnicodeDecodeError":
            return get_message("file_encoding_error", path=file_path, encoding="utf-8")
        elif error_name == "JSONDecodeError":
            return get_message("json_parse_error", context=file_path)
        else:
            return get_message("file_not_readable", path=file_path, reason=str(error_obj))
    
    if operation == "read":
        return get_message("file_not_readable", path=file_path, reason="access denied")
    else:
        return get_message("file_not_readable", path=file_path, reason=f"{operation} failed")


def error_api_operation(api_name="OpenAI", operation="request", error_obj=None):
    """
    Generate contextual error message for API operations.
    
    Args:
        api_name: Name of API (e.g., "OpenAI", "Embedding")
        operation: Operation type ("request", "parse", "timeout")
        error_obj: Optional exception object
    
    Returns:
        str: Contextual error message
    """
    if error_obj:
        error_name = type(error_obj).__name__
        if "Timeout" in error_name or "timeout" in str(error_obj).lower():
            return get_message("api_timeout")
        elif "rate" in str(error_obj).lower():
            return get_message("api_rate_limit")
        elif "auth" in str(error_obj).lower() or "401" in str(error_obj):
            return get_message("api_auth_failed")
        else:
            return get_message("api_error", detail=f"{api_name}: {str(error_obj)[:80]}")
    
    if operation == "timeout":
        return get_message("api_timeout")
    elif operation == "parse":
        return get_message("llm_parse_failed")
    else:
        return get_message("api_error", detail=f"{api_name} {operation} failed")
