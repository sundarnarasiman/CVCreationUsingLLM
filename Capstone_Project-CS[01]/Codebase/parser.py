"""
Feature 2: Job Description Parsing
Parses job descriptions to extract requirements, responsibilities, and keywords
"""

import os
import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from exceptions import FileValidationError, DataValidationError, LLMResponseError
from validators import validate_existing_file, validate_non_empty_text
from logging_config import get_logger
from messages import error_file_operation

load_dotenv()

logger = get_logger(__name__)

PARSER_CHUNKING_THRESHOLD = int(os.getenv("PARSER_CHUNKING_THRESHOLD", "5000"))
PARSER_CHUNK_SIZE = int(os.getenv("PARSER_CHUNK_SIZE", "3000"))
PARSER_CHUNK_OVERLAP = int(os.getenv("PARSER_CHUNK_OVERLAP", "250"))
JOB_SECTION_HEADERS = [
    "requirements",
    "responsibilities",
    "preferred qualifications",
    "qualifications",
    "benefits",
    "company culture",
    "application requirements",
]


class JobDescriptionParser:
    """Parse job descriptions to extract structured requirements"""
    
    def __init__(self):
        """Initialize the parser with LangChain LLM"""
        self.llm = ChatOpenAI(
            model=os.getenv("EXTRACTION_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("EXTRACTION_TEMPERATURE", "0.3"))
        )
        
        # Define parsing prompt template
        self.parsing_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert job description analyst. Extract and structure key information from job postings.

Return a JSON object with the following structure:
{{
    "job_title": "Job title",
    "company": "Company name (if mentioned)",
    "location": "Location (if mentioned)",
    "job_type": "Full-time/Part-time/Contract/etc (if mentioned)",
    "experience_level": "Entry/Mid/Senior/etc (if mentioned)",
    "requirements": {{
        "education": ["Educational requirements"],
        "experience": ["Years and type of experience required"],
        "technical_skills": ["Required technical skills"],
        "soft_skills": ["Required soft skills"],
        "certifications": ["Required certifications"],
        "other": ["Any other specific requirements"]
    }},
    "responsibilities": [
        "List of key responsibilities and duties"
    ],
    "preferred_qualifications": [
        "Nice-to-have skills or qualifications"
    ],
    "keywords": {{
        "technical": ["Technical keywords and buzzwords"],
        "domain": ["Domain-specific terms"],
        "action_verbs": ["Action verbs used in the description"],
        "tools_technologies": ["Specific tools, frameworks, or technologies mentioned"]
    }},
    "benefits": [
        "Benefits and perks mentioned (if any)"
    ],
    "company_culture": "Brief description of company culture or values (if mentioned)",
    "application_requirements": [
        "Specific application requirements (portfolio, cover letter, etc.)"
    ]
}}

Be thorough and extract all relevant keywords and requirements. Pay special attention to:
- Specific technologies, frameworks, and tools
- Years of experience requirements
- Required vs preferred qualifications
- Action verbs that describe responsibilities
- Domain-specific terminology

If any field is not present in the job description, use null or an empty array as appropriate."""),
            ("human", "{job_description}")
        ])
        
        self.chain = self.parsing_prompt | self.llm
    
    def split_text_into_sections(self, text, section_headers=None):
        """Split job text into semantic sections using common job-posting headings."""
        if not text or not isinstance(text, str):
            return []

        section_headers = section_headers or JOB_SECTION_HEADERS
        normalized_headers = {header.lower() for header in section_headers}
        sections = []
        current_lines = []

        for line in text.splitlines():
            stripped = line.strip()
            normalized = stripped.rstrip(':').lower()

            if normalized in normalized_headers:
                if current_lines:
                    section_text = "\n".join(current_lines).strip()
                    if section_text:
                        sections.append(section_text)
                current_lines = [stripped]
                continue

            if stripped or current_lines:
                current_lines.append(line)

        if current_lines:
            section_text = "\n".join(current_lines).strip()
            if section_text:
                sections.append(section_text)

        return sections if len(sections) > 1 else []

    def chunk_text_by_size(self, text, max_chars=None, overlap_chars=None):
        """Split oversized job text into bounded chunks with small overlap."""
        if not text or not isinstance(text, str):
            return []

        max_chars = max_chars or PARSER_CHUNK_SIZE
        overlap_chars = overlap_chars if overlap_chars is not None else PARSER_CHUNK_OVERLAP

        if len(text) <= max_chars:
            return [text.strip()]

        paragraphs = [paragraph.strip() for paragraph in re.split(r'\n\s*\n', text) if paragraph.strip()]
        if not paragraphs:
            paragraphs = [text.strip()]

        chunks = []
        current = ""

        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if len(candidate) <= max_chars:
                current = candidate
                continue

            if current:
                chunks.append(current)
                overlap = current[-overlap_chars:].strip() if overlap_chars > 0 else ""
                current = f"{overlap}\n\n{paragraph}".strip() if overlap else paragraph
            else:
                start = 0
                while start < len(paragraph):
                    end = min(start + max_chars, len(paragraph))
                    chunk = paragraph[start:end].strip()
                    if chunk:
                        chunks.append(chunk)
                    if end >= len(paragraph):
                        current = ""
                        break
                    start = max(0, end - overlap_chars)

        if current:
            chunks.append(current)

        return chunks

    def maybe_chunk_document(self, text):
        """Chunk large job descriptions by section first, then by bounded size if needed."""
        if len(text) <= PARSER_CHUNKING_THRESHOLD:
            return [text]

        sections = self.split_text_into_sections(text)
        candidate_sections = sections or [text]
        chunks = []

        for section in candidate_sections:
            if len(section) <= PARSER_CHUNK_SIZE:
                chunks.append(section)
            else:
                chunks.extend(self.chunk_text_by_size(section))

        return chunks or [text]

    def _parse_llm_response(self, response):
        """Parse and validate a single LLM response payload."""
        if not response or not hasattr(response, 'content'):
            raise LLMResponseError(
                "❌ Invalid response from LLM.",
                {"response_missing": True}
            )

        content = response.content

        if not content:
            raise LLMResponseError(
                "❌ LLM returned empty response.",
                {"response": None}
            )

        if isinstance(content, str):
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            try:
                parsed_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {str(e)}")
                logger.debug(f"Parse error at line {e.lineno}, column {e.colno}")
                raise LLMResponseError(
                    "❌ LLM returned invalid JSON. Please try again.",
                    {"json_error": str(e), "error_line": e.lineno}
                )
        else:
            parsed_data = content

        if not isinstance(parsed_data, dict):
            raise LLMResponseError(
                "❌ Unexpected response format from LLM.",
                {"expected_type": "dict", "actual_type": type(parsed_data).__name__}
            )

        return parsed_data

    def _merge_unique(self, existing, new_items):
        merged = []
        seen = set()

        for item in (existing or []) + (new_items or []):
            key = json.dumps(item, sort_keys=True, ensure_ascii=False) if isinstance(item, (dict, list)) else str(item)
            if key not in seen:
                seen.add(key)
                merged.append(item)

        return merged

    def merge_parsed_data(self, chunk_results):
        """Merge chunked job parsing results into one structured object."""
        merged = {
            "job_title": None,
            "company": None,
            "location": None,
            "job_type": None,
            "experience_level": None,
            "requirements": {
                "education": [],
                "experience": [],
                "technical_skills": [],
                "soft_skills": [],
                "certifications": [],
                "other": [],
            },
            "responsibilities": [],
            "preferred_qualifications": [],
            "keywords": {
                "technical": [],
                "domain": [],
                "action_verbs": [],
                "tools_technologies": [],
            },
            "benefits": [],
            "company_culture": None,
            "application_requirements": [],
        }

        for result in chunk_results:
            if not isinstance(result, dict):
                continue

            for scalar_key in ["job_title", "company", "location", "job_type", "experience_level", "company_culture"]:
                if result.get(scalar_key) and not merged.get(scalar_key):
                    merged[scalar_key] = result.get(scalar_key)

            requirements = result.get("requirements") or {}
            for req_key in merged["requirements"]:
                merged["requirements"][req_key] = self._merge_unique(
                    merged["requirements"][req_key],
                    requirements.get(req_key) or []
                )

            keywords = result.get("keywords") or {}
            for keyword_key in merged["keywords"]:
                merged["keywords"][keyword_key] = self._merge_unique(
                    merged["keywords"][keyword_key],
                    keywords.get(keyword_key) or []
                )

            merged["responsibilities"] = self._merge_unique(merged["responsibilities"], result.get("responsibilities") or [])
            merged["preferred_qualifications"] = self._merge_unique(merged["preferred_qualifications"], result.get("preferred_qualifications") or [])
            merged["benefits"] = self._merge_unique(merged["benefits"], result.get("benefits") or [])
            merged["application_requirements"] = self._merge_unique(
                merged["application_requirements"],
                result.get("application_requirements") or []
            )

        return merged
    
    def read_job_description_from_file(self, filepath):
        """
        Feature 2a: Accept Job Descriptions (file input)
        Read job description from a text file
        """
        try:
            validate_existing_file(filepath, "Job description file")
        except FileValidationError as e:
            logger.error(f"File validation failed: {e.message}")
            raise
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                validate_non_empty_text(content, "Job description")
            except DataValidationError:
                raise
            
            print(f"📄 Read job description from: {os.path.basename(filepath)}")
            logger.debug(f"Loaded job description from {filepath} ({len(content)} chars)")
            return content
        except FileValidationError:
            raise
        except DataValidationError:
            raise
        except Exception as e:
            raise FileValidationError(
                error_file_operation(filepath, "read", e),
                {"path": filepath, "error": str(e)}
            )
    
    def read_job_description_from_input(self):
        """
        Feature 2a: Accept Job Descriptions (terminal paste)
        Read job description from terminal input
        """
        print("\n📋 Paste the job description below.")
        print("When finished, press Enter, type 'END' on a new line, and press Enter again:\n")
        
        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == 'END':
                    break
                lines.append(line)
            except EOFError:
                break
        
        job_description = '\n'.join(lines)
        
        try:
            validate_non_empty_text(job_description, "Job description")
        except DataValidationError as e:
            logger.error(f"Job description validation failed: {e.message}")
            raise
        
        print("\n✅ Job description received")
        return job_description
    
    def parse_job_description(self, job_text):
        """
        Feature 2b: LLM-Based Extraction
        Use LangChain + GPT-4o-mini to parse job requirements
        """
        try:
            validate_non_empty_text(job_text, "Job description text")
        except DataValidationError as e:
            logger.error(f"Job text validation failed: {e.message}")
            raise
        
        print("🔍 Parsing job description using LLM...")
        
        try:
            chunks = self.maybe_chunk_document(job_text)
            if len(chunks) > 1:
                logger.info(f"Chunking large job description into {len(chunks)} chunks for parsing")
            
            chunk_results = []
            for chunk in chunks:
                response = self.chain.invoke({"job_description": chunk})
                chunk_results.append(self._parse_llm_response(response))
            
            parsed_data = chunk_results[0] if len(chunk_results) == 1 else self.merge_parsed_data(chunk_results)
            logger.debug(f"Successfully parsed job description with {len(parsed_data)} top-level keys")
            return parsed_data
        except LLMResponseError:
            raise
        except Exception as e:
            logger.error(f"Parsing error: {str(e)}")
            raise LLMResponseError(
                f"❌ Error during job parsing: {str(e)}",
                {"error": str(e)}
            )
    
    def save_to_json(self, data, output_path):
        """
        Feature 2c: JSON Storage
        Save parsed job data to JSON file
        """
        print(f"💾 Saving parsed job data to: {output_path}")
        
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("✅ Job description parsing complete!")
    
    def process_job_description(self, job_text=None, input_filepath=None, output_filepath=None):
        """
        Complete Feature 2 workflow:
        1. Accept job description (from file or input)
        2. Parse using LLM
        3. Save to JSON
        """
        print("\n" + "="*60)
        print("FEATURE 2: JOB DESCRIPTION PARSING")
        print("="*60 + "\n")
        
        try:
            # Step 1: Get job description
            if input_filepath:
                job_text = self.read_job_description_from_file(input_filepath)
            elif job_text is None:
                job_text = self.read_job_description_from_input()
            
            try:
                validate_non_empty_text(job_text, "Job description")
            except DataValidationError as e:
                print(e.message)
                logger.error(f"Job text validation failed: {e.message}")
                raise
            
            print(f"📝 Processing {len(job_text)} characters of job description text\n")
            
            # Step 2: Parse using LLM
            parsed_data = self.parse_job_description(job_text)
            
            # Step 3: Save to JSON
            if output_filepath is None:
                if input_filepath:
                    filename = os.path.splitext(os.path.basename(input_filepath))[0]
                else:
                    # Generate filename from job title if available
                    job_title = parsed_data.get('job_title', 'job')
                    if job_title:
                        filename = job_title.replace(' ', '_').lower()
                    else:
                        filename = 'job'
                output_filepath = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    f"{filename}_parsed.json"
                )
            
            self.save_to_json(parsed_data, output_filepath)
            
            return parsed_data
        except (FileValidationError, DataValidationError, LLMResponseError) as e:
            print(e.message)
            logger.error(f"Job parsing failed: {e.message}", extra={"debug": e.debug_info})
            raise
        except Exception as e:
            error_msg = f"❌ Unexpected error during job parsing: {str(e)}"
            print(error_msg)
            logger.error(error_msg, exc_info=True)
            raise


def main():
    """Test the parser with a sample job description"""
    parser = JobDescriptionParser()
    
    print("Job Description Parser - Feature 2")
    print("\nOptions:")
    print("1. Load from file")
    print("2. Paste job description")
    
    choice = input("\nSelect option (1/2): ").strip()
    
    try:
        if choice == '1':
            filepath = input("Enter the path to the job description file: ").strip()
            parsed_data = parser.process_job_description(input_filepath=filepath)
        elif choice == '2':
            parsed_data = parser.process_job_description()
        else:
            print("❌ Invalid choice")
            return
        
        print("\n✨ Parsing successful!")
        print(f"Job Title: {parsed_data.get('job_title', 'N/A')}")
        
        tech_skills = parsed_data.get('requirements', {}).get('technical_skills', [])
        print(f"Technical Skills Required: {len(tech_skills)}")
        
        keywords = parsed_data.get('keywords', {})
        total_keywords = sum(len(v) if isinstance(v, list) else 0 for v in keywords.values())
        print(f"Keywords Identified: {total_keywords}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
