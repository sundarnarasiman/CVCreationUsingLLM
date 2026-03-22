"""
Feature 1: Resume Data Extraction
Extracts structured information from unstructured resume documents (PDF/Word/TXT)
"""

import os
import json
import pdfplumber
from docx import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv

from exceptions import FileValidationError, DataValidationError, LLMResponseError
from validators import validate_existing_file, validate_non_empty_text
from logging_config import get_logger
from messages import print_error, error_file_operation

load_dotenv()

logger = get_logger(__name__)


class ResumeExtractor:
    """Extract structured data from resume documents"""
    
    def __init__(self):
        """Initialize the extractor with LangChain LLM"""
        self.llm = ChatOpenAI(
            model=os.getenv("EXTRACTION_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("EXTRACTION_TEMPERATURE", "0.3"))
        )
        
        # Define extraction prompt template
        self.extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert resume parser. Extract structured information from the resume text.
            
Return a JSON object with the following structure:
{{
    "personal_details": {{
        "name": "Full Name",
        "email": "email@example.com",
        "phone": "phone number",
        "location": "city, state/country",
        "linkedin": "LinkedIn URL (if available)",
        "portfolio": "Portfolio/Website URL (if available)"
    }},
    "education": [
        {{
            "degree": "Degree name",
            "institution": "Institution name",
            "graduation_date": "Graduation date or expected date",
            "gpa": "GPA (if mentioned)",
            "honors": "Honors or distinctions (if any)"
        }}
    ],
    "work_experience": [
        {{
            "job_title": "Job title",
            "company": "Company name",
            "location": "Location",
            "start_date": "Start date",
            "end_date": "End date or 'Present'",
            "responsibilities": ["List of responsibilities and achievements"]
        }}
    ],
    "skills": {{
        "technical": ["List of technical skills"],
        "soft": ["List of soft skills"],
        "languages": ["Programming/spoken languages"],
        "tools": ["Tools and technologies"]
    }},
    "projects": [
        {{
            "name": "Project name",
            "description": "Brief description",
            "technologies": ["Technologies used"],
            "achievements": ["Key achievements or outcomes"]
        }}
    ],
    "certifications": [
        {{
            "name": "Certification name",
            "issuer": "Issuing organization",
            "date": "Date obtained",
            "credential_id": "ID (if available)"
        }}
    ],
    "achievements": [
        "List of notable achievements, awards, publications, or other accomplishments"
    ]
}}

If any field is not present in the resume, use null or an empty array as appropriate.
Be thorough and extract all relevant information."""),
            ("human", "{resume_text}")
        ])
        
        self.chain = self.extraction_prompt | self.llm
    
    def extract_text_from_pdf(self, filepath):
        """Extract text from PDF file"""
        text = ""
        try:
            with pdfplumber.open(filepath) as pdf:
                if len(pdf.pages) == 0:
                    raise DataValidationError(
                        f"❌ PDF is empty: {filepath}",
                        {"path": filepath, "pages": 0}
                    )
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except pdfplumber.exceptions.PDFException as e:
            raise FileValidationError(
                f"❌ Invalid PDF file: {filepath}",
                {"path": filepath, "error": str(e)}
            )
        except Exception as e:
            raise FileValidationError(
                error_file_operation(filepath, "read", e),
                {"path": filepath, "error": str(e)}
            )
        return text
    
    def extract_text_from_docx(self, filepath):
        """Extract text from Word document"""
        text = ""
        try:
            doc = Document(filepath)
            if len(doc.paragraphs) == 0:
                logger.warning(f"DOCX document has no paragraphs: {filepath}")
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"
        except FileNotFoundError:
            raise FileValidationError(
                f"❌ File not found: {filepath}",
                {"path": filepath}
            )
        except Exception as e:
            raise FileValidationError(
                error_file_operation(filepath, "read", e),
                {"path": filepath, "error": str(e)}
            )
        return text
    
    def extract_text_from_txt(self, filepath):
        """Extract text from TXT file with encoding fallback"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    text = f.read()
                logger.debug(f"Successfully read {filepath} with encoding {encoding}")
                return text
            except UnicodeDecodeError:
                logger.debug(f"Failed to read {filepath} with encoding {encoding}, trying next...")
                continue
            except IOError as e:
                raise FileValidationError(
                    f"❌ Cannot read file: {filepath}",
                    {"path": filepath, "error": str(e)}
                )
        
        # If all encodings failed
        raise FileValidationError(
            f"❌ File encoding error (expected UTF-8): {filepath}",
            {"path": filepath, "tried_encodings": encodings}
        )
    
    def convert_document_to_text(self, filepath):
        """
        Feature 1a: Document Conversion
        Convert PDF, Word, or TXT to plain text
        """
        try:
            validate_existing_file(filepath, "Resume file")
        except FileValidationError as e:
            logger.error(f"File validation failed: {e.message}")
            raise
        
        file_extension = os.path.splitext(filepath)[1].lower()
        
        print(f"📄 Converting document: {os.path.basename(filepath)}")
        
        if file_extension == '.pdf':
            return self.extract_text_from_pdf(filepath)
        elif file_extension in ['.docx', '.doc']:
            return self.extract_text_from_docx(filepath)
        elif file_extension == '.txt':
            return self.extract_text_from_txt(filepath)
        else:
            raise FileValidationError(
                f"❌ Unsupported file format: {file_extension}. Supported: PDF, DOCX, TXT",
                {"path": filepath, "extension": file_extension}
            )
    
    def extract_structured_data(self, resume_text):
        """
        Feature 1b: LLM-Based Extraction
        Use LangChain + GPT-4o-mini to extract structured JSON
        """
        try:
            validate_non_empty_text(resume_text, "Extracted resume text")
        except DataValidationError as e:
            logger.error(f"Resume text validation failed: {e.message}")
            raise
        
        print("🔍 Extracting structured data using LLM...")
        
        try:
            response = self.chain.invoke({"resume_text": resume_text})
            
            # Parse the response content as JSON
            content = response.content
            
            if not content:
                raise LLMResponseError(
                    "❌ LLM returned empty response.",
                    {"response": None}
                )
            
            # Try to extract JSON from the response
            if isinstance(content, str):
                # Handle code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                try:
                    structured_data = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {str(e)}")
                    logger.debug(f"Raw response (first 500 chars): {response.content[:500]}")
                    raise LLMResponseError(
                        "❌ LLM returned invalid JSON. Please try again.",
                        {"json_error": str(e)}
                    )
            else:
                structured_data = content
            
            return structured_data
        except LLMResponseError:
            raise
        except Exception as e:
            logger.error(f"Extraction error: {str(e)}")
            raise LLMResponseError(
                f"❌ Error during extraction: {str(e)}",
                {"error": str(e)}
            )
    
    def save_to_json(self, data, output_path):
        """
        Feature 1c: JSON Output
        Save extracted data to JSON file
        """
        print(f"💾 Saving extracted data to: {output_path}")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("✅ Data extraction complete!")
    
    def process_resume(self, input_filepath, output_filepath=None):
        """
        Complete Feature 1 workflow:
        1. Convert document to text
        2. Extract structured data using LLM
        3. Save to JSON
        """
        print("\n" + "="*60)
        print("FEATURE 1: RESUME DATA EXTRACTION")
        print("="*60 + "\n")
        
        try:
            # Step 1: Document conversion
            resume_text = self.convert_document_to_text(input_filepath)
            
            try:
                validate_non_empty_text(resume_text, "Extracted resume text")
            except DataValidationError as e:
                print(e.message)
                logger.error(f"Resume text validation failed: {e.message}")
                raise
            
            print(f"📝 Extracted {len(resume_text)} characters of text\n")
            
            # Step 2: LLM extraction
            structured_data = self.extract_structured_data(resume_text)
            
            # Step 3: Save to JSON
            if output_filepath is None:
                filename = os.path.splitext(os.path.basename(input_filepath))[0]
                output_filepath = f"output/{filename}_extracted.json"
            
            self.save_to_json(structured_data, output_filepath)
            
            return structured_data
        except (FileValidationError, DataValidationError, LLMResponseError) as e:
            print(e.message)
            logger.error(f"Resume processing failed: {e.message}", extra={"debug": e.debug_info})
            raise
        except Exception as e:
            error_msg = f"❌ Unexpected error during resume extraction: {str(e)}"
            print(error_msg)
            logger.error(error_msg, exc_info=True)
            raise


def main():
    """Test the extractor with a sample resume"""
    extractor = ResumeExtractor()
    
    # Example usage
    print("Resume Extractor - Feature 1")
    print("Supported formats: PDF, DOCX, TXT\n")
    
    resume_path = input("Enter the path to your resume file: ").strip()
    
    try:
        structured_data = extractor.process_resume(resume_path)
        print("\n✨ Extraction successful!")
        print(f"Name: {structured_data.get('personal_details', {}).get('name', 'N/A')}")
        print(f"Skills: {len(structured_data.get('skills', {}).get('technical', []))} technical skills found")
        print(f"Experience: {len(structured_data.get('work_experience', []))} positions found")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
