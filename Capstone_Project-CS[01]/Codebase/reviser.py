"""
Feature 4: User Review and Iterative Revision
Allows users to edit resumes and get LLM-powered refinements with ATS feedback
"""

import os
import json
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from ats_checker import ATSChecker

load_dotenv()


class ResumeReviser:
    """Handle user edits and iterative refinement of resumes"""
    
    def __init__(self):
        """Initialize the reviser with LangChain LLM and ATS checker"""
        self.llm = ChatOpenAI(
            model=os.getenv("GENERATION_MODEL", "gpt-4o"),
            temperature=float(os.getenv("GENERATION_TEMPERATURE", "0.7"))
        )
        
        self.ats_checker = ATSChecker()
        
        # Revision prompt template
        self.revision_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert resume editor and ATS optimization specialist.

Your task is to refine a resume based on:
1. User's specific edits and feedback
2. Missing keywords from the job description
3. Opportunities to strengthen achievements
4. ATS optimization needs

IMPORTANT GUIDELINES:
- Preserve the user's edits and intent
- Naturally incorporate missing keywords where appropriate
- Enhance achievement statements with metrics and impact
- Maintain professional tone and ATS-friendly formatting
- Don't add false information
- Keep the overall structure intact

User edits take priority. Your role is to:
- Polish the language
- Add missing keywords naturally
- Strengthen weak points
- Ensure ATS compatibility

Return the complete revised resume in the same JSON structure as the input.
Include all sections, even if unchanged."""),
            ("human", """CURRENT RESUME:
{current_resume}

USER EDITS/FEEDBACK:
{user_edits}

MISSING KEYWORDS TO INCORPORATE:
{missing_keywords}

ATS FEEDBACK:
{ats_feedback}

JOB REQUIREMENTS:
{job_data}

Revise the resume incorporating the user's edits and improving ATS compatibility.""")
        ])
        
        self.chain = self.revision_prompt | self.llm
    
    def load_resume(self, resume_filepath):
        """Load current resume version"""
        if not os.path.exists(resume_filepath):
            raise FileNotFoundError(f"Resume file not found: {resume_filepath}")
        
        with open(resume_filepath, 'r', encoding='utf-8') as f:
            resume = json.load(f)
        
        return resume
    
    def load_job_data(self, job_filepath):
        """Load job description data"""
        if not os.path.exists(job_filepath):
            raise FileNotFoundError(f"Job file not found: {job_filepath}")
        
        with open(job_filepath, 'r', encoding='utf-8') as f:
            job_data = json.load(f)
        
        return job_data
    
    def display_resume_summary(self, resume_content):
        """Display a summary of the current resume"""
        print("\n" + "="*60)
        print("CURRENT RESUME SUMMARY")
        print("="*60)
        
        sections = resume_content.get('resume_sections', {})
        
        # Header
        if 'header' in sections:
            header = sections['header']
            print(f"\n👤 {header.get('name', 'N/A')}")
            if 'contact' in header:
                print(f"   {', '.join(header['contact'][:2])}")
        
        # Professional summary
        if 'professional_summary' in sections:
            summary = sections['professional_summary']
            print(f"\n📝 Summary: {summary[:100]}...")
        
        # Experience
        if 'experience' in sections:
            print(f"\n💼 Experience: {len(sections['experience'])} positions")
            for i, exp in enumerate(sections['experience'][:3], 1):
                print(f"   {i}. {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}")
        
        # Skills
        if 'skills' in sections:
            skills = sections['skills']
            tech_count = len(skills.get('technical', []))
            print(f"\n🛠️  Skills: {tech_count} technical skills listed")
        
        # Education
        if 'education' in sections:
            print(f"\n🎓 Education: {len(sections['education'])} degrees")
        
        print("\n" + "="*60)
    
    def get_user_edits(self):
        """
        Feature 4a: Collect user edits through terminal
        """
        print("\n" + "="*60)
        print("USER EDITS")
        print("="*60)
        print("\nDescribe the changes you'd like to make to your resume.")
        print("Examples:")
        print("  - Add more detail to the first bullet point of my current role")
        print("  - Change my professional summary to emphasize leadership")
        print("  - Add Python and machine learning to my skills")
        print("  - Make my project descriptions more concise")
        print("\nPress Enter, type 'DONE' on a new line, and press Enter when finished:\n")
        
        edits = []
        while True:
            try:
                line = input()
                if line.strip().upper() == 'DONE':
                    break
                if line.strip():
                    edits.append(line.strip())
            except EOFError:
                break
        
        if not edits:
            print("\n⚠️  No edits provided. Resume will be optimized based on ATS feedback only.")
            return "No specific user edits. Focus on ATS optimization and keyword incorporation."
        
        return '\n'.join(edits)
    
    def perform_ats_check(self, resume_content, job_data):
        """
        Feature 4b: Get real-time ATS feedback
        """
        print("\n🔍 Running ATS compatibility check...")
        
        feedback = self.ats_checker.check_resume(resume_content, job_data)
        
        print(f"\n📊 ATS Score: {feedback['ats_score']}/100")
        print(f"🎯 Keyword Match: {feedback['keyword_match_percentage']:.1f}%")
        
        if feedback['missing_keywords']:
            print(f"\n❌ Missing {len(feedback['missing_keywords'])} important keywords")
            print("   Top 10:", ', '.join(feedback['missing_keywords'][:10]))
        
        return feedback
    
    def revise_resume(self, current_resume, user_edits, ats_feedback, job_data):
        """
        Apply LLM-powered revision based on user edits and ATS feedback
        """
        print("\n✍️  Applying revisions with LLM refinement...")
        
        try:
            response = self.chain.invoke({
                "current_resume": json.dumps(current_resume, indent=2),
                "user_edits": user_edits,
                "missing_keywords": ', '.join(ats_feedback.get('missing_keywords', [])[:20]),
                "ats_feedback": json.dumps({
                    'score': ats_feedback['ats_score'],
                    'suggestions': ats_feedback['suggestions'][:5]
                }, indent=2),
                "job_data": json.dumps(job_data, indent=2)
            })
            
            content = response.content
            
            if isinstance(content, str):
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                revised_resume = json.loads(content)
            else:
                revised_resume = content
            
            return revised_resume
        except Exception as e:
            raise Exception(f"Error during revision: {str(e)}")
    
    def save_revision(self, revised_resume, original_path, version=None):
        """Save revised resume with version tracking"""
        if version is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = original_path.replace('.json', f'_v{timestamp}.json')
        else:
            output_path = original_path.replace('.json', f'_v{version}.json')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(revised_resume, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Revised resume saved to: {output_path}")
        return output_path
    
    def save_revision_history(self, history, base_path):
        """Save revision history log"""
        history_path = base_path.replace('.json', '_revision_history.json')
        
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        
        return history_path
    
    def iterative_revision_workflow(self, resume_filepath, job_filepath):
        """
        Complete Feature 4 workflow with iterative refinement
        """
        print("\n" + "="*60)
        print("FEATURE 4: USER REVIEW AND ITERATIVE REVISION")
        print("="*60)
        
        # Load data
        current_resume = self.load_resume(resume_filepath)
        job_data = self.load_job_data(job_filepath)
        
        revision_history = []
        iteration = 0
        
        while True:
            iteration += 1
            print(f"\n\n{'='*60}")
            print(f"ITERATION {iteration}")
            print('='*60)
            
            # Display current state
            self.display_resume_summary(current_resume)
            
            # Get ATS feedback
            ats_feedback = self.perform_ats_check(current_resume, job_data)
            
            # Show suggestions
            print("\n💡 ATS Suggestions:")
            for suggestion in ats_feedback['suggestions'][:5]:
                print(f"   {suggestion}")
            
            # Ask if user wants to make edits
            print("\n" + "="*60)
            choice = input("\nOptions:\n  1. Make edits\n  2. Accept current version\n  3. View ATS details\n\nSelect (1/2/3): ").strip()
            
            if choice == '2':
                print("\n✅ Finalizing resume...")
                break
            elif choice == '3':
                # Show detailed ATS feedback
                print("\n" + "="*60)
                print("DETAILED ATS ANALYSIS")
                print("="*60)
                print(f"\nScore Breakdown:")
                details = ats_feedback.get('details', {})
                print(f"  Keyword Score: {details.get('keyword_score', 0)}/50")
                print(f"  Formatting Score: {details.get('formatting_score', 0)}/25")
                print(f"  Section Score: {details.get('section_score', 0)}/15")
                print(f"  Content Score: {details.get('content_score', 0)}/10")
                
                if ats_feedback.get('missing_keywords'):
                    print(f"\n❌ All Missing Keywords ({len(ats_feedback['missing_keywords'])}):")
                    for i, kw in enumerate(ats_feedback['missing_keywords'], 1):
                        print(f"   {i}. {kw}")
                
                input("\nPress Enter to continue...")
                continue
            elif choice != '1':
                print("❌ Invalid choice. Please try again.")
                continue
            
            # Get user edits
            user_edits = self.get_user_edits()
            
            # Record in history
            revision_entry = {
                'iteration': iteration,
                'timestamp': datetime.now().isoformat(),
                'ats_score_before': ats_feedback['ats_score'],
                'keyword_match_before': ats_feedback['keyword_match_percentage'],
                'user_edits': user_edits,
                'missing_keywords': ats_feedback['missing_keywords'][:10]
            }
            
            # Revise resume
            revised_resume = self.revise_resume(current_resume, user_edits, ats_feedback, job_data)
            
            # Check new ATS score
            new_feedback = self.perform_ats_check(revised_resume, job_data)
            revision_entry['ats_score_after'] = new_feedback['ats_score']
            revision_entry['keyword_match_after'] = new_feedback['keyword_match_percentage']
            
            # Show improvement
            score_change = new_feedback['ats_score'] - ats_feedback['ats_score']
            keyword_change = new_feedback['keyword_match_percentage'] - ats_feedback['keyword_match_percentage']
            
            print(f"\n📈 Score Change: {score_change:+.1f} points (now {new_feedback['ats_score']}/100)")
            print(f"📈 Keyword Match Change: {keyword_change:+.1f}% (now {new_feedback['keyword_match_percentage']:.1f}%)")
            
            revision_history.append(revision_entry)
            
            # Save intermediate version
            version_path = self.save_revision(revised_resume, resume_filepath, f"{iteration}")
            
            # Update current resume for next iteration
            current_resume = revised_resume
            
            # Save updated ATS feedback
            ats_feedback_path = version_path.replace('.json', '_ats_feedback.json')
            self.ats_checker.save_ats_feedback(new_feedback, ats_feedback_path)
        
        # Save final version
        final_path = resume_filepath.replace('.json', '_final.json')
        with open(final_path, 'w', encoding='utf-8') as f:
            json.dump(current_resume, f, indent=2, ensure_ascii=False)
        
        # Save history
        history_path = self.save_revision_history(revision_history, resume_filepath)
        
        print("\n" + "="*60)
        print("✅ REVISION COMPLETE")
        print("="*60)
        print(f"\n📄 Final resume: {final_path}")
        print(f"📊 Revision history: {history_path}")
        print(f"🔄 Total iterations: {iteration}")
        
        if revision_history:
            initial_score = revision_history[0]['ats_score_before']
            final_score = revision_history[-1]['ats_score_after']
            print(f"📈 Score improvement: {initial_score:.1f} → {final_score:.1f} ({final_score-initial_score:+.1f})")
        
        return current_resume, revision_history


def main():
    """Test the reviser"""
    reviser = ResumeReviser()
    
    print("Resume Reviser - Feature 4")
    print("="*60)
    
    resume_path = input("\nEnter path to resume JSON: ").strip()
    job_path = input("Enter path to job JSON: ").strip()
    
    try:
        final_resume, history = reviser.iterative_revision_workflow(resume_path, job_path)
        print("\n✨ Revision workflow complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
