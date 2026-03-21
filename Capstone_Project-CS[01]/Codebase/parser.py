"""
Feature 2: Job Description Parsing
Parses job descriptions to extract requirements, responsibilities, and keywords
"""

import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()


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
    
    def read_job_description_from_file(self, filepath):
        """
        Feature 2a: Accept Job Descriptions (file input)
        Read job description from a text file
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"📄 Read job description from: {os.path.basename(filepath)}")
            return content
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")
    
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
        
        if not job_description.strip():
            raise ValueError("No job description provided")
        
        print("\n✅ Job description received")
        return job_description
    
    def parse_job_description(self, job_text):
        """
        Feature 2b: LLM-Based Extraction
        Use LangChain + GPT-4o-mini to parse job requirements
        """
        print("🔍 Parsing job description using LLM...")
        
        try:
            response = self.chain.invoke({"job_description": job_text})
            
            # Parse the response content as JSON
            content = response.content
            
            # Try to extract JSON from the response
            if isinstance(content, str):
                # Handle code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                parsed_data = json.loads(content)
            else:
                parsed_data = content
            
            return parsed_data
        except json.JSONDecodeError as e:
            print(f"⚠️  Warning: Could not parse JSON response. Error: {str(e)}")
            print(f"Raw response: {response.content[:500]}...")
            raise Exception("Failed to parse LLM response as JSON")
        except Exception as e:
            raise Exception(f"Error during parsing: {str(e)}")
    
    def save_to_json(self, data, output_path):
        """
        Feature 2c: JSON Storage
        Save parsed job data to JSON file
        """
        print(f"💾 Saving parsed job data to: {output_path}")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
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
        
        # Step 1: Get job description
        if input_filepath:
            job_text = self.read_job_description_from_file(input_filepath)
        elif job_text is None:
            job_text = self.read_job_description_from_input()
        
        if not job_text.strip():
            raise ValueError("Job description is empty")
        
        print(f"📝 Processing {len(job_text)} characters of job description text\n")
        
        # Step 2: Parse using LLM
        parsed_data = self.parse_job_description(job_text)
        
        # Step 3: Save to JSON
        if output_filepath is None:
            if input_filepath:
                filename = os.path.splitext(os.path.basename(input_filepath))[0]
            else:
                # Generate filename from job title if available
                job_title = parsed_data.get('job_title', 'job').replace(' ', '_').lower()
                filename = job_title
            output_filepath = f"output/{filename}_parsed.json"
        
        self.save_to_json(parsed_data, output_filepath)
        
        return parsed_data


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
