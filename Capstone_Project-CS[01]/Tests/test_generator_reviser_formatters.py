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

from exceptions import DataValidationError
from formatters import ResumePDFFormatter, format_resume
from generator import ResumeGenerator
from reviser import MAX_ITERATIONS, ResumeReviser


def bare_generator():
    generator = ResumeGenerator.__new__(ResumeGenerator)
    generator.review_chain = Mock()
    generator.generation_chain = Mock()
    return generator


class TestGenerator(unittest.TestCase):
    def test_load_profile_data_reads_fixture(self):
        generator = bare_generator()
        data = generator.load_profile_data(str(FIXTURES_DIR / "sample_profile.json"))
        self.assertEqual(data["personal_details"]["name"], "John Doe")

    def test_load_job_data_rejects_invalid_json(self):
        generator = bare_generator()
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
            handle.write("{invalid")
            path = handle.name
        try:
            with self.assertRaises(DataValidationError):
                generator.load_job_data(path)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_review_and_strategize_parses_fenced_json(self):
        generator = bare_generator()
        generator.review_chain.invoke.return_value = SimpleNamespace(
            content="```json\n{\"match_score\": \"82%\", \"key_strengths\": [], \"keyword_strategy\": {\"must_include\": []}}\n```"
        )
        result = generator.review_and_strategize({"a": 1}, {"b": 2})
        self.assertEqual(result["match_score"], "82%")

    def test_generate_resume_content_parses_json(self):
        generator = bare_generator()
        generator.generation_chain.invoke.return_value = SimpleNamespace(
            content='{"resume_sections": {"header": {"name": "John Doe"}}, "keyword_coverage": {"included_keywords": [], "keyword_density": "50%"}}'
        )
        result = generator.generate_resume_content({"match_score": "80%"}, {"x": 1}, {"y": 2})
        self.assertEqual(result["resume_sections"]["header"]["name"], "John Doe")

    def test_save_resume_data_writes_output_file(self):
        generator = bare_generator()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "resume_output.json"
            generator.save_resume_data({"ok": True}, str(output_path))
            self.assertTrue(output_path.exists())
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8"))["ok"], True)


class TestReviser(unittest.TestCase):
    def test_max_iterations_constant_is_enforced_value(self):
        self.assertEqual(MAX_ITERATIONS, 5)

    def test_load_resume_reads_fixture(self):
        reviser = ResumeReviser.__new__(ResumeReviser)
        data = reviser.load_resume(str(FIXTURES_DIR / "sample_resume_output.json"))
        self.assertIn("resume_sections", data)

    def test_load_resume_rejects_missing_resume_sections(self):
        reviser = ResumeReviser.__new__(ResumeReviser)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
            json.dump({"header": {"name": "John"}}, handle)
            path = handle.name
        try:
            with self.assertRaises(DataValidationError):
                reviser.load_resume(path)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_save_revision_writes_versioned_file(self):
        reviser = ResumeReviser.__new__(ResumeReviser)
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "resume.json"
            base.write_text("{}", encoding="utf-8")
            output = reviser.save_revision({"resume_sections": {}}, str(base), "2")
            self.assertTrue(Path(output).exists())
            self.assertTrue(output.endswith("_v2.json"))

    def test_save_revision_history_writes_history_file(self):
        reviser = ResumeReviser.__new__(ResumeReviser)
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "resume.json"
            base.write_text("{}", encoding="utf-8")
            history_path = reviser.save_revision_history([{"iteration": 1}], str(base))
            self.assertTrue(Path(history_path).exists())


class TestFormatters(unittest.TestCase):
    def test_pdf_formatter_uses_linux_safe_font(self):
        with patch("platform.system", return_value="Linux"):
            formatter = ResumePDFFormatter()
        self.assertEqual(formatter.font_family, "Helvetica")

    def test_format_resume_returns_expected_output_paths(self):
        resume_fixture = str(FIXTURES_DIR / "sample_resume_output.json")
        with patch("formatters.ResumePDFFormatter.create_pdf") as create_pdf, patch(
            "formatters.ResumeDOCXFormatter.create_docx"
        ) as create_docx:
            pdf_path, docx_path = format_resume(resume_fixture, output_format="both")
        self.assertTrue(pdf_path.endswith("sample_resume_output.pdf"))
        self.assertTrue(docx_path.endswith("sample_resume_output.docx"))
        create_pdf.assert_called_once()
        create_docx.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
