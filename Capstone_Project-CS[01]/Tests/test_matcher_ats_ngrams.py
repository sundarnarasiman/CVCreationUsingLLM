import sys
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
CODEBASE_DIR = TESTS_DIR.parent / "Codebase"
if str(CODEBASE_DIR) not in sys.path:
    sys.path.insert(0, str(CODEBASE_DIR))

from ats_checker import ATSChecker
from matcher import ProfileJobMatcher


class TestMatcherNGramSupport(unittest.TestCase):
    def setUp(self):
        self.matcher = ProfileJobMatcher()

    def test_extract_keywords_includes_curated_phrases(self):
        text = "Machine learning and deep learning are core to this data pipeline design."
        keywords = self.matcher.extract_keywords_from_text(text)
        self.assertIn("machine learning", keywords)
        self.assertIn("deep learning", keywords)
        self.assertIn("data pipeline", keywords)
        self.assertIn("machine", keywords)
        self.assertIn("learning", keywords)

    def test_extract_keywords_does_not_generate_arbitrary_bigrams(self):
        text = "customer success workflow improvement plan"
        keywords = self.matcher.extract_keywords_from_text(text)
        self.assertNotIn("customer success", keywords)
        self.assertNotIn("workflow improvement", keywords)

    def test_repeated_phrase_is_frequency_ranked(self):
        profile_data = {
            "skills": {
                "technical": ["machine learning", "machine learning", "python"],
                "soft": [],
                "languages": [],
                "tools": [],
            },
            "work_experience": [],
            "projects": [],
            "certifications": [],
        }
        keywords = self.matcher.extract_profile_keywords(profile_data)
        self.assertEqual(keywords[0], "machine learning")

    def test_three_word_phrase_is_detected(self):
        text = "Natural language processing powers the assistant."
        keywords = self.matcher.extract_keywords_from_text(text)
        self.assertIn("natural language processing", keywords)


class TestATSNGramSupport(unittest.TestCase):
    def setUp(self):
        self.ats = ATSChecker()

    def test_extract_keywords_includes_curated_phrases(self):
        text = "We need backend engineering expertise with REST API and CI/CD experience."
        keywords = self.ats.extract_keywords_from_text(text)
        self.assertIn("backend engineering", keywords)
        self.assertIn("rest api", keywords)
        self.assertIn("ci/cd", keywords)

    def test_calculate_keyword_match_prioritizes_phrase_keywords(self):
        resume_content = {
            "resume_sections": {
                "professional_summary": "Experienced in machine learning and data pipeline design.",
                "skills": {
                    "technical": ["machine learning", "data pipeline", "python"],
                    "tools": [],
                    "other": [],
                },
                "experience": [],
                "education": [],
                "projects": [],
                "certifications": [],
            }
        }
        job_data = {
            "requirements": {
                "technical_skills": ["machine learning", "data pipeline"],
            },
            "keywords": {
                "technical": ["machine learning", "data pipeline"],
                "domain": [],
                "action_verbs": [],
                "tools_technologies": [],
            },
            "responsibilities": [],
        }

        match_pct, matched_keywords, missing_keywords = self.ats.calculate_keyword_match(
            resume_content, job_data
        )

        self.assertGreater(match_pct, 0)
        self.assertIn("machine learning", matched_keywords)
        self.assertIn("data pipeline", matched_keywords)
        self.assertNotIn("machine learning", missing_keywords)


if __name__ == "__main__":
    unittest.main(verbosity=2)