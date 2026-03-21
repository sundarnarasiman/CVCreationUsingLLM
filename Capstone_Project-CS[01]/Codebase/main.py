"""
CV Creation Using LLM - Main Orchestration
A dual-LLM system for creating tailored, ATS-optimized CVs

Features:
1. Resume Data Extraction (GPT-4o-mini)
2. Job Description Parsing (GPT-4o-mini)
3. Resume Tailoring and Generation (GPT-4o)
4. User Review and Iterative Revision (GPT-4o + ATS feedback)
"""

import os
import sys
from dotenv import load_dotenv

# Import all modules
from extractor import ResumeExtractor
from parser import JobDescriptionParser
from generator import ResumeGenerator
from reviser import ResumeReviser
from ats_checker import ATSChecker
from formatters import format_resume
from matcher import ProfileJobMatcher

# Load environment variables
load_dotenv()


class CVCreationSystem:
    """Main orchestration class for CV creation workflow"""
    
    def __init__(self):
        """Initialize all components"""
        self.extractor = ResumeExtractor()
        self.parser = JobDescriptionParser()
        self.generator = ResumeGenerator()
        self.reviser = ResumeReviser()
        self.ats_checker = ATSChecker()
        self.matcher = ProfileJobMatcher()
    
    def display_banner(self):
        """Display welcome banner"""
        print("\n" + "="*70)
        print(" "*15 + "CV CREATION USING DUAL-LLM SYSTEM")
        print("="*70)
        print("\n✨ Features:")
        print("   1. Resume Data Extraction (from PDF/Word/TXT)")
        print("   2. Job Description Parsing")
        print("   3. AI-Powered Resume Tailoring & Generation")
        print("   4. Iterative Revision with ATS Feedback")
        print("\n💡 Powered by: GPT-4o-mini (extraction) + GPT-4o (generation)")
        print("="*70 + "\n")
    
    def check_api_key(self):
        """Verify OpenAI API key is configured"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            print("❌ ERROR: OpenAI API key not configured!")
            print("\nPlease follow these steps:")
            print("1. Copy .env.example to .env")
            print("2. Edit .env and add your OpenAI API key")
            print("3. Run the program again")
            return False
        return True
    
    def get_menu_choice(self):
        """Display main menu and get user choice"""
        print("\n" + "="*70)
        print("MAIN MENU")
        print("="*70)
        print("\n📋 Workflow Options:")
        print("   1. Complete Workflow (Extract → Parse → Generate → Revise → Export)")
        print("   2. Quick Match (Check profile-job fit before creating resume)")
        print("\n🔧 Individual Features:")
        print("   3. Feature 1: Extract Resume Data")
        print("   4. Feature 2: Parse Job Description")
        print("   5. Feature 3: Generate Tailored Resume")
        print("   6. Feature 4: Revise Resume with ATS Feedback")
        print("   7. Export Resume (PDF/DOCX)")
        print("\n   0. Exit")
        print("\n" + "="*70)
        
        choice = input("\nSelect option (0-7): ").strip()
        return choice
    
    def complete_workflow(self):
        """Execute complete CV creation workflow"""
        print("\n" + "="*70)
        print("COMPLETE CV CREATION WORKFLOW")
        print("="*70)
        
        try:
            # Step 1: Extract resume data
            print("\n📍 STEP 1/5: Resume Data Extraction")
            print("-" * 70)
            resume_file = input("\nEnter path to your resume (PDF/DOCX/TXT): ").strip()
            
            if not os.path.exists(resume_file):
                print(f"❌ File not found: {resume_file}")
                return
            
            extracted_data = self.extractor.process_resume(resume_file)
            profile_json = f"output/{os.path.splitext(os.path.basename(resume_file))[0]}_extracted.json"
            
            # Step 2: Parse job description
            print("\n📍 STEP 2/5: Job Description Parsing")
            print("-" * 70)
            print("\nOptions:")
            print("  1. Load job description from file")
            print("  2. Paste job description")
            
            job_choice = input("\nSelect (1/2): ").strip()
            
            if job_choice == '1':
                job_file = input("Enter path to job description file: ").strip()
                parsed_job = self.parser.process_job_description(input_filepath=job_file)
            else:
                parsed_job = self.parser.process_job_description()
            
            job_json = f"output/job_parsed.json"
            
            # Step 3: Check match score
            print("\n📍 STEP 3/5: Profile-Job Matching")
            print("-" * 70)
            match_result = self.matcher.calculate_match_score(extracted_data, parsed_job)
            
            print(f"\n📊 Match Score: {match_result['overall_score']}/100")
            
            if match_result['overall_score'] < 40:
                print("\n⚠️  Warning: Low match score. This position may not be a good fit.")
                proceed = input("Continue anyway? (y/n): ").strip().lower()
                if proceed != 'y':
                    print("❌ Workflow cancelled.")
                    return
            
            # Step 4: Generate tailored resume
            print("\n📍 STEP 4/5: Resume Generation")
            print("-" * 70)
            resume_content, strategy = self.generator.process_resume_generation(
                profile_json, job_json
            )
            
            resume_json = f"output/{os.path.splitext(os.path.basename(resume_file))[0]}_tailored.json"
            
            # Step 5: Iterative revision
            print("\n📍 STEP 5/5: Review & Revision")
            print("-" * 70)
            print("\nWould you like to review and revise the resume?")
            revise_choice = input("(y/n): ").strip().lower()
            
            if revise_choice == 'y':
                final_resume, history = self.reviser.iterative_revision_workflow(
                    resume_json, job_json
                )
                final_json = resume_json.replace('.json', '_final.json')
            else:
                final_json = resume_json
                # Still run ATS check
                ats_feedback = self.ats_checker.check_resume(resume_content, parsed_job)
                print(f"\n📊 Final ATS Score: {ats_feedback['ats_score']}/100")
                print(f"🎯 Keyword Match: {ats_feedback['keyword_match_percentage']:.1f}%")
            
            # Export to PDF/DOCX
            print("\n📍 FINAL STEP: Export Resume")
            print("-" * 70)
            print("\nExport format:")
            print("  1. PDF only")
            print("  2. DOCX only")
            print("  3. Both PDF and DOCX")
            
            export_choice = input("\nSelect (1/2/3): ").strip()
            format_map = {'1': 'pdf', '2': 'docx', '3': 'both'}
            output_format = format_map.get(export_choice, 'both')
            
            pdf_path, docx_path = format_resume(final_json, output_format)
            
            # Workflow complete
            print("\n" + "="*70)
            print("✅ WORKFLOW COMPLETE!")
            print("="*70)
            print("\n📁 Generated Files:")
            print(f"   • Profile Data: {profile_json}")
            print(f"   • Job Data: {job_json}")
            print(f"   • Final Resume JSON: {final_json}")
            if output_format in ['pdf', 'both']:
                print(f"   • Resume PDF: {pdf_path}")
            if output_format in ['docx', 'both']:
                print(f"   • Resume DOCX: {docx_path}")
            print("\n🎉 Your tailored, ATS-optimized resume is ready!")
            
        except Exception as e:
            print(f"\n❌ Error in workflow: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def quick_match(self):
        """Quick profile-job matching"""
        print("\n" + "="*70)
        print("QUICK PROFILE-JOB MATCH")
        print("="*70)
        
        try:
            profile_path = input("\nEnter path to profile JSON: ").strip()
            job_path = input("Enter path to job JSON: ").strip()
            
            match_result = self.matcher.match_profile_to_job(profile_path, job_path)
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
    
    def feature_1_extract(self):
        """Run Feature 1: Resume Data Extraction"""
        print("\n" + "="*70)
        print("FEATURE 1: RESUME DATA EXTRACTION")
        print("="*70)
        
        try:
            resume_file = input("\nEnter path to your resume (PDF/DOCX/TXT): ").strip()
            self.extractor.process_resume(resume_file)
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
    
    def feature_2_parse(self):
        """Run Feature 2: Job Description Parsing"""
        print("\n" + "="*70)
        print("FEATURE 2: JOB DESCRIPTION PARSING")
        print("="*70)
        
        try:
            print("\nOptions:")
            print("  1. Load from file")
            print("  2. Paste job description")
            
            choice = input("\nSelect (1/2): ").strip()
            
            if choice == '1':
                job_file = input("Enter path to job description file: ").strip()
                self.parser.process_job_description(input_filepath=job_file)
            else:
                self.parser.process_job_description()
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
    
    def feature_3_generate(self):
        """Run Feature 3: Resume Tailoring and Generation"""
        print("\n" + "="*70)
        print("FEATURE 3: RESUME TAILORING AND GENERATION")
        print("="*70)
        
        try:
            profile_path = input("\nEnter path to extracted profile JSON: ").strip()
            job_path = input("Enter path to parsed job JSON: ").strip()
            
            self.generator.process_resume_generation(profile_path, job_path)
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
    
    def feature_4_revise(self):
        """Run Feature 4: User Review and Iterative Revision"""
        print("\n" + "="*70)
        print("FEATURE 4: USER REVIEW AND ITERATIVE REVISION")
        print("="*70)
        
        try:
            resume_path = input("\nEnter path to resume JSON: ").strip()
            job_path = input("Enter path to job JSON: ").strip()
            
            self.reviser.iterative_revision_workflow(resume_path, job_path)
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
    
    def export_resume(self):
        """Export resume to PDF/DOCX"""
        print("\n" + "="*70)
        print("EXPORT RESUME")
        print("="*70)
        
        try:
            resume_path = input("\nEnter path to resume JSON: ").strip()
            
            print("\nExport format:")
            print("  1. PDF only")
            print("  2. DOCX only")
            print("  3. Both PDF and DOCX")
            
            choice = input("\nSelect (1/2/3): ").strip()
            format_map = {'1': 'pdf', '2': 'docx', '3': 'both'}
            output_format = format_map.get(choice, 'both')
            
            format_resume(resume_path, output_format)
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
    
    def run(self):
        """Main application loop"""
        self.display_banner()
        
        # Check API key
        if not self.check_api_key():
            return
        
        while True:
            choice = self.get_menu_choice()
            
            if choice == '0':
                print("\n👋 Thank you for using CV Creation System!")
                print("="*70 + "\n")
                break
            elif choice == '1':
                self.complete_workflow()
            elif choice == '2':
                self.quick_match()
            elif choice == '3':
                self.feature_1_extract()
            elif choice == '4':
                self.feature_2_parse()
            elif choice == '5':
                self.feature_3_generate()
            elif choice == '6':
                self.feature_4_revise()
            elif choice == '7':
                self.export_resume()
            else:
                print("\n❌ Invalid choice. Please select 0-7.")
            
            input("\n📌 Press Enter to return to main menu...")


def main():
    """Entry point for the application"""
    try:
        system = CVCreationSystem()
        system.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Application interrupted by user.")
        print("="*70 + "\n")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
