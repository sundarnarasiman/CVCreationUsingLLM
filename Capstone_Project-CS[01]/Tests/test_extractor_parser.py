import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


TESTS_DIR = Path(__file__).resolve().parent
CODEBASE_DIR = TESTS_DIR.parent / "Codebase"
FIXTURES_DIR = TESTS_DIR / "fixtures"
if str(CODEBASE_DIR) not in sys.path:
    sys.path.insert(0, str(CODEBASE_DIR))

from exceptions import DataValidationError, FileValidationError, LLMResponseError
from extractor import ResumeExtractor
from parser import JobDescriptionParser


def bare_extractor():
    extractor = ResumeExtractor.__new__(ResumeExtractor)
    extractor.chain = Mock()
    return extractor


def bare_parser():
    parser = JobDescriptionParser.__new__(JobDescriptionParser)
    parser.chain = Mock()
    return parser


class TestExtractorEdgeCases(unittest.TestCase):
    def test_convert_document_to_text_reads_fixture_txt(self):
        extractor = bare_extractor()
        text = extractor.convert_document_to_text(str(FIXTURES_DIR / "sample_resume.txt"))
        self.assertIn("John Doe", text)
        self.assertIn("Python", text)

    def test_convert_document_to_text_rejects_unsupported_extension(self):
        extractor = bare_extractor()
        with tempfile.NamedTemporaryFile("w", suffix=".xyz", delete=False, encoding="utf-8") as handle:
            handle.write("unsupported")
            path = handle.name
        try:
            with self.assertRaises(FileValidationError):
                extractor.convert_document_to_text(path)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_extract_text_from_txt_supports_encoding_fallback(self):
        extractor = bare_extractor()
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="cp1252") as handle:
            handle.write("Resume for José")
            path = handle.name
        try:
            text = extractor.extract_text_from_txt(path)
            self.assertIn("José", text)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_extract_structured_data_rejects_empty_text(self):
        extractor = bare_extractor()
        with self.assertRaises(DataValidationError):
            extractor.extract_structured_data("   ")

    def test_extract_structured_data_parses_fenced_json(self):
        extractor = bare_extractor()
        extractor.chain.invoke.return_value = SimpleNamespace(
            content="```json\n{\"personal_details\": {\"name\": \"John Doe\"}}\n```"
        )
        result = extractor.extract_structured_data("resume text")
        self.assertEqual(result["personal_details"]["name"], "John Doe")

    def test_extract_structured_data_raises_for_invalid_json(self):
        extractor = bare_extractor()
        extractor.chain.invoke.return_value = SimpleNamespace(content="{invalid json}")
        with self.assertRaises(LLMResponseError):
            extractor.extract_structured_data("resume text")


class TestParserEdgeCases(unittest.TestCase):
    def test_read_job_description_from_file_reads_fixture(self):
        parser = bare_parser()
        content = parser.read_job_description_from_file(str(FIXTURES_DIR / "sample_job.txt"))
        self.assertIn("Senior Backend Engineer", content)

    def test_read_job_description_from_file_rejects_empty_file(self):
        parser = bare_parser()
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as handle:
            handle.write("")
            path = handle.name
        try:
            with self.assertRaises(DataValidationError):
                parser.read_job_description_from_file(path)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_job_description_rejects_empty_text(self):
        parser = bare_parser()
        with self.assertRaises(DataValidationError):
            parser.parse_job_description("\n\t")

    def test_parse_job_description_parses_string_json(self):
        parser = bare_parser()
        parser.chain.invoke.return_value = SimpleNamespace(content='{"job_title": "Senior Backend Engineer"}')
        result = parser.parse_job_description("job text")
        self.assertEqual(result["job_title"], "Senior Backend Engineer")

    def test_parse_job_description_rejects_non_dict_json(self):
        parser = bare_parser()
        parser.chain.invoke.return_value = SimpleNamespace(content='["unexpected", "list"]')
        with self.assertRaises(LLMResponseError):
            parser.parse_job_description("job text")

    def test_read_job_description_from_input_collects_until_end_marker(self):
        parser = bare_parser()
        with patch("builtins.input", side_effect=["line 1", "line 2", "END"]):
            result = parser.read_job_description_from_input()
        self.assertEqual(result, "line 1\nline 2")


if __name__ == "__main__":
    unittest.main(verbosity=2)
