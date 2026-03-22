"""
Feature 3: Resume Tailoring and Generation
Generates tailored, ATS-friendly CVs based on profile data and job requirements
"""

import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from exceptions import FileValidationError, DataValidationError, LLMResponseError
from validators import validate_existing_file, validate_required_keys
from logging_config import get_logger
from messages import error_file_operation

load_dotenv()

logger = get_logger(__name__)


class ResumeGenerator:
    """Generate tailored, ATS-optimized resumes"""
    
    def __init__(self):
        """Initialize the generator with LangChain LLM"""
        self.llm = ChatOpenAI(
            model=os.getenv("GENERATION_MODEL", "gpt-4o"),
            temperature=float(os.getenv("GENERATION_TEMPERATURE", "0.7"))
        )
        
        # Step 1: Review and Analysis Prompt
        self.review_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert career coach and ATS optimization specialist.

Your task is to review a candidate's profile and a target job description, then create a strategic plan for tailoring the resume.

Analyze:
1. How well the candidate's experience matches the job requirements
2. Which skills and experiences should be emphasized
3. Which keywords from the job description must be incorporated
4. How to reorganize or reframe experiences for maximum impact
5. Any gaps that need to be addressed or downplayed
6. The best way to structure the resume for ATS optimization

Return a JSON object with this structure:
{{
    "match_score": "Percentage estimate of how well the candidate matches the job",
    "key_strengths": ["List of candidate's strongest matching points"],
    "gaps": ["List of requirements the candidate doesn't clearly meet"],
    "keyword_strategy": {{
        "must_include": ["Critical keywords that MUST appear in the resume"],
        "high_priority": ["Important keywords to include naturally"],
        "contextual": ["Keywords to weave into descriptions"]
    }},
    "content_strategy": {{
        "experiences_to_emphasize": [
            {{
                "experience": "Which experience to highlight",
                "reason": "Why it's relevant",
                "keywords_to_include": ["Keywords to incorporate"]
            }}
        ],
        "skills_to_highlight": ["Skills to put in prominent sections"],
        "suggested_summary": "Brief professional summary approach",
        "structural_recommendations": ["How to organize sections"]
    }},
    "reframing_suggestions": [
        {{
            "original_context": "Current framing of experience",
            "suggested_reframe": "How to reframe for this job"
        }}
    ]
}}

Be strategic and specific. Focus on ATS compatibility and keyword optimization."""),
            ("human", """CANDIDATE PROFILE:
{profile_data}

TARGET JOB DESCRIPTION:
{job_data}

Analyze this match and create a tailoring strategy.""")
        ])
        
        # Step 2: Generation Prompt
        self.generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert resume writer specializing in ATS-optimized, professional resumes.

Based on the strategic analysis provided, write a complete, professionally formatted resume that:
1. Incorporates all critical keywords naturally
2. Emphasizes the most relevant experiences and skills
3. Uses action verbs and quantified achievements
4. Follows ATS-friendly formatting guidelines
5. Maintains authenticity while optimizing for the role

IMPORTANT ATS FORMATTING RULES:
- Use standard section headings (Professional Summary, Experience, Education, Skills)
- Use simple, clean formatting without tables or complex layouts
- Include keywords naturally throughout
- Use bullet points for responsibilities and achievements
- Include relevant dates and locations
- List skills with proper keyword density

Return a JSON object with this structure:
{{
    "resume_sections": {{
        "header": {{
            "name": "Full name",
            "contact": ["email", "phone", "location", "linkedin", "portfolio"]
        }},
        "professional_summary": "2-3 sentence compelling summary with key keywords",
        "skills": {{
            "technical": ["List of technical skills with keywords"],
            "tools": ["Relevant tools and technologies"],
            "other": ["Other relevant skills"]
        }},
        "experience": [
            {{
                "title": "Job title",
                "company": "Company name",
                "location": "Location",
                "dates": "MM/YYYY - MM/YYYY or Present",
                "bullets": [
                    "Achievement-focused bullet using action verbs and metrics"
                ]
            }}
        ],
        "education": [
            {{
                "degree": "Degree name",
                "institution": "Institution name",
                "graduation_date": "Graduation date",
                "honors": "Honors (if applicable)"
            }}
        ],
        "certifications": [
            {{
                "name": "Certification name",
                "issuer": "Issuer",
                "date": "Date"
            }}
        ],
        "projects": [
            {{
                "name": "Project name",
                "description": "Brief description with keywords",
                "technologies": ["Technologies used"]
            }}
        ]
    }},
    "keyword_coverage": {{
        "included_keywords": ["List of job keywords incorporated"],
        "keyword_density": "Estimated keyword match percentage"
    }},
    "ats_optimization_notes": ["List of ATS-friendly elements included"]
}}

Write compelling, achievement-focused content that passes ATS while appealing to human readers."""),
            ("human", """STRATEGIC ANALYSIS:
{strategy}

CANDIDATE PROFILE:
{profile_data}

TARGET JOB:
{job_data}

Generate the optimized resume content.""")
        ])
        
        self.review_chain = self.review_prompt | self.llm
        self.generation_chain = self.generation_prompt | self.llm
    
    def load_profile_data(self, profile_filepath):
        """Load extracted profile data from JSON"""
        try:
            validate_existing_file(profile_filepath, "Profile file")
            with open(profile_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            validate_required_keys(data, ['personal_details'], "Resume profile")
            profile_name = data.get('personal_details', {}).get('name', 'Unknown')
            print(f"📄 Loaded profile: {profile_name}")
            logger.debug(f"Loaded profile from {profile_filepath}")
            return data
        except json.JSONDecodeError as e:
            raise DataValidationError(f"❌ Invalid JSON in profile file: {profile_filepath}", {"path": profile_filepath, "error": str(e)})
        except (FileValidationError, DataValidationError):
            raise
        except Exception as e:
            raise FileValidationError(error_file_operation(profile_filepath, "read", e), {"path": profile_filepath, "error": str(e)})
    
    def load_job_data(self, job_filepath):
        """Load parsed job description from JSON"""
        try:
            validate_existing_file(job_filepath, "Job description file")
            with open(job_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            validate_required_keys(data, ['job_title'], "Job description")
            job_title = data.get('job_title', 'Unknown')
            print(f"📄 Loaded job: {job_title}")
            logger.debug(f"Loaded job from {job_filepath}")
            return data
        except json.JSONDecodeError as e:
            raise DataValidationError(f"❌ Invalid JSON in job file: {job_filepath}", {"path": job_filepath, "error": str(e)})
        except (FileValidationError, DataValidationError):
            raise
        except Exception as e:
            raise FileValidationError(error_file_operation(job_filepath, "read", e), {"path": job_filepath, "error": str(e)})
    
    def review_and_strategize(self, profile_data, job_data, computed_match_score=None):
        """
        Feature 3c: Step 1 - Review Profile and Job Data
        LLM analyzes fit and creates tailoring strategy
        """
        print("\n🔍 Step 1: Analyzing profile-job match and creating strategy...")
        
        try:
            response = self.review_chain.invoke({
                "profile_data": json.dumps(profile_data, indent=2),
                "job_data": json.dumps(job_data, indent=2)
            })
            
            content = response.content
            
            if isinstance(content, str):
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                strategy = json.loads(content)
            else:
                strategy = content
            
            if computed_match_score is not None:
                match_score = f"{computed_match_score}/100"
                # Keep persisted strategy aligned with the deterministic matcher score.
                strategy['match_score'] = match_score
            else:
                match_score = strategy.get('match_score', 'N/A')
            print(f"   Match Score: {match_score}")
            print(f"   Key Strengths: {len(strategy.get('key_strengths', []))}")
            print(f"   Must-Include Keywords: {len(strategy.get('keyword_strategy', {}).get('must_include', []))}")
            
            return strategy
        except Exception as e:
            raise Exception(f"Error in strategy creation: {str(e)}")
    
    def generate_resume_content(self, strategy, profile_data, job_data):
        """
        Feature 3d: Step 2 - Synthesize Personalized Content
        LLM generates keyword-rich, tailored resume content
        """
        print("\n✍️  Step 2: Generating tailored resume content...")
        
        try:
            response = self.generation_chain.invoke({
                "strategy": json.dumps(strategy, indent=2),
                "profile_data": json.dumps(profile_data, indent=2),
                "job_data": json.dumps(job_data, indent=2)
            })
            
            content = response.content
            
            if isinstance(content, str):
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                resume_content = json.loads(content)
            else:
                resume_content = content
            
            keyword_coverage = resume_content.get('keyword_coverage', {})
            print(f"   Keywords Included: {len(keyword_coverage.get('included_keywords', []))}")
            print(f"   Keyword Density: {keyword_coverage.get('keyword_density', 'N/A')}")
            
            return resume_content
        except Exception as e:
            raise Exception(f"Error in content generation: {str(e)}")
    
    def save_resume_data(self, resume_content, output_path):
        """Save generated resume data to JSON"""
        print(f"\n💾 Saving resume data to: {output_path}")
        
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(resume_content, f, indent=2, ensure_ascii=False)
    
    def process_resume_generation(self, profile_filepath, job_filepath, output_filepath=None, computed_match_score=None):
        """
        Complete Feature 3 workflow:
        1. Load profile and job data
        2. Step 1: Review and strategize
        3. Step 2: Generate tailored content
        4. Save resume data
        """
        print("\n" + "="*60)
        print("FEATURE 3: RESUME TAILORING AND GENERATION")
        print("="*60 + "\n")
        
        try:
            # Load data
            profile_data = self.load_profile_data(profile_filepath)
            job_data = self.load_job_data(job_filepath)
            
            # Step 1: Strategic analysis
            strategy = self.review_and_strategize(profile_data, job_data, computed_match_score)
            
            # Step 2: Content generation
            resume_content = self.generate_resume_content(strategy, profile_data, job_data)
            
            # Save resume data
            if output_filepath is None:
                candidate_name = profile_data.get('personal_details', {}).get('name', 'candidate')
                if not candidate_name or candidate_name == 'None':
                    candidate_name = 'candidate'
                candidate_name = candidate_name.replace(' ', '_').lower()
                job_title = job_data.get('job_title', 'position')
                if not job_title or job_title == 'None':
                    job_title = 'position'
                job_title = job_title.replace(' ', '_').lower()
                output_filepath = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    f"{candidate_name}_{job_title}_resume.json"
                )
            
            self.save_resume_data(resume_content, output_filepath)
            
            # Also save the strategy for reference
            strategy_path = output_filepath.replace('_resume.json', '_strategy.json')
            with open(strategy_path, 'w', encoding='utf-8') as f:
                json.dump(strategy, f, indent=2, ensure_ascii=False)
            
            print("\n✅ Resume generation complete!")
            print(f"📊 Strategy saved to: {strategy_path}")
            
            logger.info(f"Resume generation succeeded: {output_filepath}")
            return resume_content, strategy, output_filepath
        except (FileValidationError, DataValidationError, LLMResponseError) as e:
            print(e.message)
            logger.error(f"Resume generation failed: {e.message}", extra={"debug": e.debug_info})
            raise
        except Exception as e:
            error_msg = f"❌ Unexpected error during resume generation: {str(e)}"
            print(error_msg)
            logger.error(error_msg, exc_info=True)
            raise


def main():
    """Test the generator with sample data"""
    generator = ResumeGenerator()
    
    print("Resume Generator - Feature 3")
    print("="*60)
    
    profile_path = input("\nEnter path to extracted profile JSON: ").strip()
    job_path = input("Enter path to parsed job JSON: ").strip()
    
    try:
        resume_content, strategy, resume_path = generator.process_resume_generation(profile_path, job_path)
        
        print("\n✨ Generation successful!")
        print(f"📄 Resume saved to: {resume_path}")
        print(f"\nMatch Score: {strategy.get('match_score', 'N/A')}")
        print(f"Keyword Coverage: {resume_content.get('keyword_coverage', {}).get('keyword_density', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
