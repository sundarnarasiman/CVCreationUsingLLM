import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
CODEBASE_DIR = TESTS_DIR.parent / "Codebase"
if str(CODEBASE_DIR) not in sys.path:
    sys.path.insert(0, str(CODEBASE_DIR))

from exceptions import APIClientError, CVSystemError, DataValidationError, FileValidationError
from logging_config import get_logger, get_user_safe_message, is_debug_mode
from messages import error_api_operation, error_file_operation, get_message
from validators import (
    validate_existing_file,
    validate_json_structure,
    validate_non_empty_text,
    validate_readable_file,
    validate_required_keys,
)


class TestExceptions(unittest.TestCase):
    def test_base_exception_retains_message_and_debug_info(self):
        error = CVSystemError("boom", {"source": "test"})
        self.assertEqual(error.message, "boom")
        self.assertEqual(error.debug_info["source"], "test")

    def test_subclass_inheritance(self):
        error = APIClientError("timeout")
        self.assertIsInstance(error, CVSystemError)
        self.assertEqual(str(error), "timeout")


class TestValidators(unittest.TestCase):
    def test_validate_existing_file_success(self):
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write("ok")
            path = handle.name
        try:
            result = validate_existing_file(path, "fixture")
            self.assertTrue(result.endswith(Path(path).name))
        finally:
            os.remove(path)

    def test_validate_existing_file_raises_for_missing_file(self):
        with self.assertRaises(FileValidationError):
            validate_existing_file("/definitely/missing/file.txt", "fixture")

    def test_validate_readable_file_success(self):
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write("hello")
            path = handle.name
        try:
            self.assertTrue(validate_readable_file(path, "fixture"))
        finally:
            os.remove(path)

    def test_validate_non_empty_text_rejects_empty_and_none(self):
        with self.assertRaises(DataValidationError):
            validate_non_empty_text("   ", "field")
        with self.assertRaises(DataValidationError):
            validate_non_empty_text(None, "field")

    def test_validate_required_keys_detects_missing_fields(self):
        with self.assertRaises(DataValidationError) as context:
            validate_required_keys({"name": "John"}, ["name", "email"], "profile")
        self.assertIn("email", context.exception.message)

    def test_validate_required_keys_accepts_object_with_dict(self):
        class SampleObject:
            def __init__(self):
                self.required = "value"

        result = validate_required_keys(SampleObject(), ["required"], "sample")
        self.assertEqual(result["required"], "value")

    def test_validate_json_structure_rejects_wrong_type(self):
        with self.assertRaises(DataValidationError):
            validate_json_structure([1, 2, 3], "dict")


class TestMessagesAndLogging(unittest.TestCase):
    def test_get_message_formats_expected_fields(self):
        message = get_message("file_not_found", path="resume.txt")
        self.assertIn("resume.txt", message)
        self.assertTrue(message.startswith("❌"))

    def test_unknown_message_type_falls_back(self):
        message = get_message("does_not_exist")
        self.assertIn("unexpected", message.lower())

    def test_error_file_operation_maps_common_errors(self):
        not_found = error_file_operation("resume.txt", error_obj=FileNotFoundError())
        denied = error_file_operation("resume.txt", error_obj=PermissionError())
        self.assertIn("File not found", not_found)
        self.assertIn("Permission denied", denied)

    def test_error_api_operation_maps_timeout_and_auth(self):
        timeout = error_api_operation(error_obj=TimeoutError("request timeout"))
        auth = error_api_operation(error_obj=Exception("401 Unauthorized"))
        self.assertIn("timed out", timeout.lower())
        self.assertIn("authentication", auth.lower())

    def test_logger_and_user_safe_message_helpers(self):
        logger = get_logger("tests.framework")
        self.assertEqual(logger.name, "cv_system")
        self.assertIsInstance(is_debug_mode(), bool)
        error = FileValidationError("safe message", {"path": "x"})
        self.assertEqual(get_user_safe_message(error), "safe message")


if __name__ == "__main__":
    unittest.main(verbosity=2)
