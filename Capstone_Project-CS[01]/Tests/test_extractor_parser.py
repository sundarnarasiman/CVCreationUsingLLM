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

    def test_split_resume_into_sections(self):
        extractor = bare_extractor()
        text = (
            "John Doe\n"
            "PROFESSIONAL SUMMARY\nSummary text\n"
            "EXPERIENCE\nExperience text\n"
            "SKILLS\nPython, SQL\n"
        )
        sections = extractor.split_text_into_sections(text)
        self.assertGreaterEqual(len(sections), 3)
        self.assertTrue(any("PROFESSIONAL SUMMARY" in section for section in sections))

    def test_chunk_text_by_size_creates_multiple_chunks(self):
        extractor = bare_extractor()
        text = ("Paragraph one.\n\n" * 40).strip()
        chunks = extractor.chunk_text_by_size(text, max_chars=120, overlap_chars=20)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 140 for chunk in chunks))

    def test_maybe_chunk_document_bypasses_small_resume(self):
        extractor = bare_extractor()
        chunks = extractor.maybe_chunk_document("short resume")
        self.assertEqual(chunks, ["short resume"])

    def test_merge_structured_data_combines_chunk_outputs(self):
        extractor = bare_extractor()
        merged = extractor.merge_structured_data([
            {
                "personal_details": {"name": "John Doe", "email": "john@example.com"},
                "education": [{"degree": "BSCS"}],
                "skills": {"technical": ["Python"], "soft": [], "languages": [], "tools": []},
                "projects": [],
                "certifications": [],
                "achievements": [],
                "work_experience": [],
            },
            {
                "personal_details": {"phone": "+1-555-0101"},
                "education": [{"degree": "BSCS"}],
                "skills": {"technical": ["SQL"], "soft": ["Communication"], "languages": [], "tools": []},
                "projects": [{"name": "Project A"}],
                "certifications": [],
                "achievements": ["Award"],
                "work_experience": [{"job_title": "Engineer"}],
            },
        ])
        self.assertEqual(merged["personal_details"]["name"], "John Doe")
        self.assertEqual(merged["personal_details"]["phone"], "+1-555-0101")
        self.assertEqual(merged["skills"]["technical"], ["Python", "SQL"])
        self.assertEqual(len(merged["education"]), 1)

    def test_extract_structured_data_merges_multiple_chunks(self):
        extractor = bare_extractor()
        long_text = (
            "PROFESSIONAL SUMMARY\n" + ("Summary line. " * 250) + "\n"
            "EXPERIENCE\n" + ("Experience line. " * 250)
        )

        def resume_chunk_response(payload):
            chunk = payload["resume_text"]
            if "EXPERIENCE" in chunk or "Experience line." in chunk:
                return SimpleNamespace(content='{"work_experience": [{"job_title": "Engineer"}], "skills": {"technical": ["SQL"], "soft": [], "languages": [], "tools": []}}')
            return SimpleNamespace(content='{"personal_details": {"name": "John Doe"}, "skills": {"technical": ["Python"], "soft": [], "languages": [], "tools": []}}')

        extractor.chain.invoke.side_effect = resume_chunk_response
        result = extractor.extract_structured_data(long_text)
        self.assertEqual(result["personal_details"]["name"], "John Doe")
        self.assertEqual(result["skills"]["technical"], ["Python", "SQL"])
        self.assertEqual(result["work_experience"][0]["job_title"], "Engineer")
        self.assertGreater(extractor.chain.invoke.call_count, 1)


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

    def test_split_job_into_sections(self):
        parser = bare_parser()
        text = (
            "Senior Backend Engineer\n"
            "REQUIREMENTS\nPython\n"
            "RESPONSIBILITIES\nBuild services\n"
            "BENEFITS\nRemote work\n"
        )
        sections = parser.split_text_into_sections(text)
        self.assertGreaterEqual(len(sections), 3)
        self.assertTrue(any("REQUIREMENTS" in section for section in sections))

    def test_chunk_job_text_by_size_creates_multiple_chunks(self):
        parser = bare_parser()
        text = ("Requirement paragraph.\n\n" * 40).strip()
        chunks = parser.chunk_text_by_size(text, max_chars=120, overlap_chars=20)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 140 for chunk in chunks))

    def test_merge_parsed_data_combines_chunk_outputs(self):
        parser = bare_parser()
        merged = parser.merge_parsed_data([
            {
                "job_title": "Senior Backend Engineer",
                "requirements": {"technical_skills": ["Python"], "education": [], "experience": [], "soft_skills": [], "certifications": [], "other": []},
                "responsibilities": ["Build APIs"],
                "keywords": {"technical": ["Python"], "domain": [], "action_verbs": [], "tools_technologies": []},
            },
            {
                "company": "Tech Corp",
                "requirements": {"technical_skills": ["Docker"], "education": [], "experience": [], "soft_skills": ["Communication"], "certifications": [], "other": []},
                "responsibilities": ["Build APIs", "Review code"],
                "keywords": {"technical": ["Docker"], "domain": ["Cloud"], "action_verbs": [], "tools_technologies": []},
            },
        ])
        self.assertEqual(merged["job_title"], "Senior Backend Engineer")
        self.assertEqual(merged["company"], "Tech Corp")
        self.assertEqual(merged["requirements"]["technical_skills"], ["Python", "Docker"])
        self.assertEqual(merged["responsibilities"], ["Build APIs", "Review code"])

    def test_parse_job_description_merges_multiple_chunks(self):
        parser = bare_parser()
        long_text = (
            "REQUIREMENTS\n" + ("Python and Docker required. " * 220) + "\n"
            "RESPONSIBILITIES\n" + ("Build services and mentor engineers. " * 220)
        )

        def job_chunk_response(payload):
            chunk = payload["job_description"]
            if "RESPONSIBILITIES" in chunk or "Build services" in chunk:
                return SimpleNamespace(content='{"company": "Tech Corp", "requirements": {"technical_skills": ["Docker"], "education": [], "experience": [], "soft_skills": [], "certifications": [], "other": []}, "responsibilities": ["Build services"], "keywords": {"technical": ["Docker"], "domain": [], "action_verbs": [], "tools_technologies": []}}')
            return SimpleNamespace(content='{"job_title": "Senior Backend Engineer", "requirements": {"technical_skills": ["Python"], "education": [], "experience": [], "soft_skills": [], "certifications": [], "other": []}, "responsibilities": [], "keywords": {"technical": ["Python"], "domain": [], "action_verbs": [], "tools_technologies": []}}')

        parser.chain.invoke.side_effect = job_chunk_response
        result = parser.parse_job_description(long_text)
        self.assertEqual(result["job_title"], "Senior Backend Engineer")
        self.assertEqual(result["company"], "Tech Corp")
        self.assertEqual(result["requirements"]["technical_skills"], ["Python", "Docker"])
        self.assertGreater(parser.chain.invoke.call_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
