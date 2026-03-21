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

load_dotenv()


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
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
        return text
    
    def extract_text_from_docx(self, filepath):
        """Extract text from Word document"""
        text = ""
        try:
            doc = Document(filepath)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")
        return text
    
    def extract_text_from_txt(self, filepath):
        """Extract text from TXT file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            raise Exception(f"Error reading TXT: {str(e)}")
        return text
    
    def convert_document_to_text(self, filepath):
        """
        Feature 1a: Document Conversion
        Convert PDF, Word, or TXT to plain text
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        file_extension = os.path.splitext(filepath)[1].lower()
        
        print(f"📄 Converting document: {os.path.basename(filepath)}")
        
        if file_extension == '.pdf':
            return self.extract_text_from_pdf(filepath)
        elif file_extension in ['.docx', '.doc']:
            return self.extract_text_from_docx(filepath)
        elif file_extension == '.txt':
            return self.extract_text_from_txt(filepath)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Supported: PDF, DOCX, TXT")
    
    def extract_structured_data(self, resume_text):
        """
        Feature 1b: LLM-Based Extraction
        Use LangChain + GPT-4o-mini to extract structured JSON
        """
        print("🔍 Extracting structured data using LLM...")
        
        try:
            response = self.chain.invoke({"resume_text": resume_text})
            
            # Parse the response content as JSON
            content = response.content
            
            # Try to extract JSON from the response
            if isinstance(content, str):
                # Handle code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                structured_data = json.loads(content)
            else:
                structured_data = content
            
            return structured_data
        except json.JSONDecodeError as e:
            print(f"⚠️  Warning: Could not parse JSON response. Error: {str(e)}")
            print(f"Raw response: {response.content[:500]}...")
            raise Exception("Failed to parse LLM response as JSON")
        except Exception as e:
            raise Exception(f"Error during extraction: {str(e)}")
    
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
        
        # Step 1: Document conversion
        resume_text = self.convert_document_to_text(input_filepath)
        
        if not resume_text.strip():
            raise ValueError("No text could be extracted from the document")
        
        print(f"📝 Extracted {len(resume_text)} characters of text\n")
        
        # Step 2: LLM extraction
        structured_data = self.extract_structured_data(resume_text)
        
        # Step 3: Save to JSON
        if output_filepath is None:
            filename = os.path.splitext(os.path.basename(input_filepath))[0]
            output_filepath = f"output/{filename}_extracted.json"
        
        self.save_to_json(structured_data, output_filepath)
        
        return structured_data


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
