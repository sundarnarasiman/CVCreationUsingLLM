"""
Validation utilities for fail-fast input/file/schema checks.

This module provides reusable validators to catch errors early before
expensive operations (file I/O, LLM calls) and raise appropriate exceptions.
"""

import os
import json
from exceptions import FileValidationError, DataValidationError


def validate_existing_file(path, field_name="file"):
    """
    Validate that a file exists and is readable.
    
    Args:
        path: File path to validate
        field_name: Human-readable name for error messages (e.g., "resume", "job description")
    
    Raises:
        FileValidationError: If file doesn't exist or isn't readable
    
    Returns:
        str: The validated absolute path
    """
    if not path:
        raise FileValidationError(
            f"❌ {field_name} path is empty.",
            {"missing_field": field_name}
        )
    
    abs_path = os.path.abspath(path)
    
    if not os.path.exists(abs_path):
        raise FileValidationError(
            f"❌ {field_name} not found: {path}",
            {"path": path, "absolute_path": abs_path}
        )
    
    if not os.path.isfile(abs_path):
        raise FileValidationError(
            f"❌ {field_name} is not a file: {path}",
            {"path": path, "is_directory": os.path.isdir(abs_path)}
        )
    
    if not os.access(abs_path, os.R_OK):
        raise FileValidationError(
            f"❌ No permission to read {field_name}: {path}",
            {"path": path, "permission_error": True}
        )
    
    return abs_path


def validate_readable_file(path, field_name="file", encoding="utf-8"):
    """
    Validate file exists and can be read with specified encoding.
    
    Args:
        path: File path to validate
        field_name: Human-readable name for error messages
        encoding: Expected file encoding (default: utf-8)
    
    Raises:
        FileValidationError: If file can't be read or encoding fails
    
    Returns:
        str: The validated absolute path
    """
    abs_path = validate_existing_file(path, field_name)
    
    try:
        with open(abs_path, 'r', encoding=encoding) as f:
            f.read(1)  # Try reading one character
    except UnicodeDecodeError as e:
        raise FileValidationError(
            f"❌ {field_name} encoding error (expected {encoding}): {path}",
            {"path": path, "encoding": encoding, "error": str(e)}
        )
    except IOError as e:
        raise FileValidationError(
            f"❌ Cannot read {field_name}: {e}",
            {"path": path, "error": str(e)}
        )
    
    return abs_path


def validate_non_empty_text(text, field_name="text"):
    """
    Validate that text content is present and non-empty.
    
    Args:
        text: Text to validate
        field_name: Human-readable name for error messages (e.g., "extracted resume", "job description")
    
    Raises:
        DataValidationError: If text is None, empty, or only whitespace
    
    Returns:
        str: The validated (trimmed) text
    """
    if text is None:
        raise DataValidationError(
            f"❌ {field_name} is missing (None).",
            {"field": field_name, "is_none": True}
        )
    
    text_str = str(text).strip()
    
    if not text_str:
        raise DataValidationError(
            f"❌ {field_name} is empty.",
            {"field": field_name, "is_empty": True}
        )
    
    return text_str


def validate_required_keys(data, required_keys, context="object"):
    """
    Validate that a dict/object has all required keys.
    
    Args:
        data: Dict or object with __dict__ to check
        required_keys: List of required key names
        context: Human-readable context (e.g., "resume profile", "job description")
    
    Raises:
        DataValidationError: If data is None, not a dict, or missing required keys
    
    Returns:
        dict: The validated data (as dict)
    """
    if data is None:
        raise DataValidationError(
            f"❌ {context} is None.",
            {"context": context, "is_none": True}
        )
    
    # Convert object to dict if needed
    if not isinstance(data, dict):
        if hasattr(data, '__dict__'):
            data = data.__dict__
        else:
            raise DataValidationError(
                f"❌ {context} is not a valid data structure.",
                {"context": context, "type": type(data).__name__}
            )
    
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        raise DataValidationError(
            f"❌ {context} is missing required fields: {', '.join(missing_keys)}",
            {"context": context, "missing_keys": missing_keys, "available_keys": list(data.keys())}
        )
    
    return data


def validate_json_structure(data, expected_type="dict"):
    """
    Validate that parsed JSON matches expected structure.
    
    Args:
        data: Parsed JSON data
        expected_type: Expected type as string ("dict", "list", "str")
    
    Raises:
        DataValidationError: If type doesn't match
    
    Returns:
        The validated data
    """
    type_map = {"dict": dict, "list": list, "str": str}
    expected_class = type_map.get(expected_type, dict)
    
    if not isinstance(data, expected_class):
        raise DataValidationError(
            f"❌ JSON structure error: expected {expected_type}, got {type(data).__name__}",
            {"expected_type": expected_type, "actual_type": type(data).__name__}
        )
    
    return data
