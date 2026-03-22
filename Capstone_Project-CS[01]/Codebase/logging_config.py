"""
Centralized logging configuration for the CV Creation System.

Provides a shared logger setup with support for both user-safe terminal output
and detailed debug logging. Debug messages are separated from user messages
to avoid exposing sensitive information.
"""

import logging
import os
import sys


# Default logger configuration
_logger = None
_debug_mode = os.environ.get('CV_DEBUG', '').lower() in ('true', '1', 'yes')


def get_logger(name="cv_system"):
    """
    Get or create the shared logger instance.
    
    Args:
        name: Logger name (typically module name via __name__)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    global _logger
    
    if _logger is None:
        _logger = logging.getLogger("cv_system")
        _logger.setLevel(logging.DEBUG if _debug_mode else logging.INFO)
        
        # Console handler - only shows WARNING and above by default
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.WARNING if not _debug_mode else logging.DEBUG)
        console_formatter = logging.Formatter(
            '[%(name)s] %(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler - detailed debug log
        log_file = os.path.join(os.getcwd(), "cv_system_debug.log")
        try:
            file_handler = logging.FileHandler(log_file, mode='a')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '[%(asctime)s] %(name)s %(levelname)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            _logger.addHandler(file_handler)
        except IOError:
            # If we can't write to file, just use console
            pass
        
        _logger.addHandler(console_handler)
    
    return _logger


def is_debug_mode():
    """
    Check if debug mode is enabled via CV_DEBUG environment variable.
    
    Returns:
        bool: True if CV_DEBUG=true/1/yes
    """
    return _debug_mode


def log_debug(logger, message, extra_context=None):
    """
    Log a debug message with optional context dict.
    
    Args:
        logger: Logger instance
        message: Debug message
        extra_context: Optional dict with additional debug info
    """
    if extra_context:
        logger.debug(f"{message} | context={extra_context}")
    else:
        logger.debug(message)


def log_error(logger, message, error=None, context=None):
    """
    Log an error with optional exception and context.
    
    Args:
        logger: Logger instance
        message: Error message
        error: Optional exception object
        context: Optional dict with debug context (not exposed to user)
    """
    if error:
        logger.error(f"{message} | error={type(error).__name__}: {str(error)}")
    else:
        logger.error(message)
    
    if context and _debug_mode:
        logger.debug(f"Error context: {context}")


def get_user_safe_message(error_obj, default_message="An unexpected error occurred."):
    """
    Extract user-safe message from CVSystemError.
    
    Args:
        error_obj: Exception object (ideally CVSystemError or subclass)
        default_message: Message to use if error_obj.message not available
    
    Returns:
        str: User-safe error message
    """
    if hasattr(error_obj, 'message'):
        return error_obj.message
    return default_message
