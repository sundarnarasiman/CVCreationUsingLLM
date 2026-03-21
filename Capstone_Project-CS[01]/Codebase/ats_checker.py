"""
Feature 4b: ATS Compatibility Checker
Provides real-time ATS scoring and feedback for resumes
"""

import os
import json
import re
from collections import Counter
from dotenv import load_dotenv

load_dotenv()


class ATSChecker:
    """Analyze resume content for ATS compatibility"""
    
    def __init__(self):
        """Initialize the ATS checker"""
        self.threshold = int(os.getenv("ATS_SCORE_THRESHOLD", "75"))
        
        # Common ATS-problematic elements
        self.problematic_patterns = {
            'tables': r'\|.*\|',  # Markdown tables
            'special_chars': r'[★☆●○■□▪▫◆◇]',  # Special bullets
            'complex_formatting': r'{|}|\\begin|\\end',  # LaTeX-like
        }
    
    def extract_text_from_resume(self, resume_content):
        """Extract all text content from resume JSON for analysis"""
        all_text = []
        
        # Extract from all sections
        if isinstance(resume_content, dict):
            sections = resume_content.get('resume_sections', {})
            
            # Professional summary
            if 'professional_summary' in sections:
                all_text.append(sections['professional_summary'])
            
            # Skills
            if 'skills' in sections:
                skills = sections['skills']
                for skill_type, skill_list in skills.items():
                    if isinstance(skill_list, list):
                        all_text.extend(skill_list)
            
            # Experience
            if 'experience' in sections:
                for exp in sections['experience']:
                    all_text.append(exp.get('title', ''))
                    all_text.append(exp.get('company', ''))
                    if 'bullets' in exp and isinstance(exp['bullets'], list):
                        all_text.extend(exp['bullets'])
            
            # Education
            if 'education' in sections:
                for edu in sections['education']:
                    all_text.append(edu.get('degree', ''))
                    all_text.append(edu.get('institution', ''))
            
            # Projects
            if 'projects' in sections:
                for proj in sections['projects']:
                    all_text.append(proj.get('name', ''))
                    all_text.append(proj.get('description', ''))
                    if 'technologies' in proj and isinstance(proj['technologies'], list):
                        all_text.extend(proj['technologies'])
            
            # Certifications
            if 'certifications' in sections:
                for cert in sections['certifications']:
                    all_text.append(cert.get('name', ''))
        
        return ' '.join(str(item) for item in all_text if item)
    
    def extract_keywords_from_text(self, text):
        """Extract meaningful keywords from text"""
        # Convert to lowercase and split into words
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#\.]*\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
        
        # Keep only significant words (length > 2 and not stopwords)
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        
        return keywords
    
    def calculate_keyword_match(self, resume_content, job_data):
        """Calculate keyword match percentage between resume and job"""
        # Extract job keywords
        job_keywords = set()
        
        if isinstance(job_data, dict):
            # Technical skills
            tech_skills = job_data.get('requirements', {}).get('technical_skills', [])
            for skill in tech_skills:
                job_keywords.update(self.extract_keywords_from_text(str(skill)))
            
            # Keywords section
            keywords_section = job_data.get('keywords', {})
            for keyword_type, keyword_list in keywords_section.items():
                if isinstance(keyword_list, list):
                    for kw in keyword_list:
                        job_keywords.update(self.extract_keywords_from_text(str(kw)))
            
            # Responsibilities
            responsibilities = job_data.get('responsibilities', [])
            for resp in responsibilities:
                job_keywords.update(self.extract_keywords_from_text(str(resp)))
        
        # Extract resume keywords
        resume_text = self.extract_text_from_resume(resume_content)
        resume_keywords = set(self.extract_keywords_from_text(resume_text))
        
        # Calculate match
        if not job_keywords:
            return 100.0, [], list(job_keywords)
        
        matched_keywords = job_keywords.intersection(resume_keywords)
        missing_keywords = job_keywords - resume_keywords
        
        match_percentage = (len(matched_keywords) / len(job_keywords)) * 100
        
        return match_percentage, sorted(list(matched_keywords)), sorted(list(missing_keywords))
    
    def check_formatting_issues(self, resume_content):
        """Check for ATS-problematic formatting"""
        issues = []
        
        # Convert resume to string for pattern matching
        resume_str = json.dumps(resume_content)
        
        for issue_type, pattern in self.problematic_patterns.items():
            if re.search(pattern, resume_str):
                issues.append(f"Detected {issue_type.replace('_', ' ')}")
        
        # Check for section headings
        if isinstance(resume_content, dict):
            sections = resume_content.get('resume_sections', {})
            required_sections = ['header', 'experience', 'education', 'skills']
            missing_sections = [s for s in required_sections if s not in sections]
            
            if missing_sections:
                issues.append(f"Missing sections: {', '.join(missing_sections)}")
        
        return issues
    
    def calculate_ats_score(self, resume_content, job_data):
        """
        Calculate comprehensive ATS score (0-100)
        
        Scoring breakdown:
        - Keyword match: 50 points
        - Formatting: 25 points
        - Section completeness: 15 points
        - Content quality: 10 points
        """
        score = 0
        details = {}
        
        # 1. Keyword match (50 points)
        keyword_match_pct, matched, missing = self.calculate_keyword_match(resume_content, job_data)
        keyword_score = (keyword_match_pct / 100) * 50
        score += keyword_score
        details['keyword_score'] = round(keyword_score, 2)
        details['keyword_match_percentage'] = round(keyword_match_pct, 2)
        details['matched_keywords_count'] = len(matched)
        details['missing_keywords_count'] = len(missing)
        
        # 2. Formatting (25 points)
        formatting_issues = self.check_formatting_issues(resume_content)
        formatting_score = max(0, 25 - (len(formatting_issues) * 5))
        score += formatting_score
        details['formatting_score'] = formatting_score
        details['formatting_issues'] = formatting_issues
        
        # 3. Section completeness (15 points)
        if isinstance(resume_content, dict):
            sections = resume_content.get('resume_sections', {})
            required_sections = ['header', 'professional_summary', 'experience', 'education', 'skills']
            present_sections = sum(1 for s in required_sections if s in sections and sections[s])
            section_score = (present_sections / len(required_sections)) * 15
            score += section_score
            details['section_score'] = round(section_score, 2)
            details['sections_present'] = present_sections
            details['sections_required'] = len(required_sections)
        
        # 4. Content quality (10 points)
        resume_text = self.extract_text_from_resume(resume_content)
        word_count = len(resume_text.split())
        
        # Ideal resume: 400-800 words
        if 400 <= word_count <= 800:
            content_score = 10
        elif 300 <= word_count < 400 or 800 < word_count <= 1000:
            content_score = 7
        else:
            content_score = 5
        
        score += content_score
        details['content_score'] = content_score
        details['word_count'] = word_count
        
        return round(score, 2), details, matched, missing
    
    def generate_improvement_suggestions(self, score, details, missing_keywords):
        """Generate actionable improvement suggestions"""
        suggestions = []
        
        # Keyword suggestions
        if details.get('keyword_match_percentage', 0) < 70:
            suggestions.append(f"⚠️  Low keyword match ({details['keyword_match_percentage']:.1f}%). Add more relevant keywords from the job description.")
            
            if missing_keywords:
                top_missing = missing_keywords[:10]
                suggestions.append(f"💡 Consider incorporating: {', '.join(top_missing)}")
        
        # Formatting suggestions
        if details.get('formatting_issues'):
            suggestions.append("⚠️  Formatting issues detected. Simplify formatting for better ATS compatibility.")
            for issue in details['formatting_issues']:
                suggestions.append(f"   - {issue}")
        
        # Section suggestions
        if details.get('section_score', 0) < 12:
            suggestions.append("⚠️  Missing key resume sections. Ensure all standard sections are included.")
        
        # Content length suggestions
        word_count = details.get('word_count', 0)
        if word_count < 400:
            suggestions.append(f"⚠️  Resume is too brief ({word_count} words). Add more detail to achievements and responsibilities.")
        elif word_count > 800:
            suggestions.append(f"⚠️  Resume is lengthy ({word_count} words). Consider condensing to key achievements.")
        
        # Overall score suggestions
        if score >= 85:
            suggestions.append("✅ Excellent ATS compatibility! Resume should pass most ATS systems.")
        elif score >= 70:
            suggestions.append("✓ Good ATS compatibility. Minor improvements could increase match rate.")
        else:
            suggestions.append("❌ ATS score needs improvement. Focus on keyword optimization and formatting.")
        
        return suggestions
    
    def check_resume(self, resume_content, job_data):
        """
        Complete ATS check workflow
        Returns: score, keyword_match_pct, missing_keywords, suggestions
        """
        score, details, matched, missing = self.calculate_ats_score(resume_content, job_data)
        suggestions = self.generate_improvement_suggestions(score, details, missing)
        
        return {
            'ats_score': score,
            'keyword_match_percentage': details.get('keyword_match_percentage', 0),
            'matched_keywords': matched,
            'missing_keywords': missing,
            'suggestions': suggestions,
            'details': details
        }
    
    def save_ats_feedback(self, feedback, output_path):
        """Save ATS feedback to JSON file"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(feedback, f, indent=2, ensure_ascii=False)


def main():
    """Test the ATS checker"""
    checker = ATSChecker()
    
    print("ATS Compatibility Checker - Feature 4b")
    print("="*60)
    
    resume_path = input("\nEnter path to resume JSON: ").strip()
    job_path = input("Enter path to job JSON: ").strip()
    
    try:
        with open(resume_path, 'r') as f:
            resume_content = json.load(f)
        
        with open(job_path, 'r') as f:
            job_data = json.load(f)
        
        feedback = checker.check_resume(resume_content, job_data)
        
        print("\n" + "="*60)
        print("ATS ANALYSIS RESULTS")
        print("="*60)
        print(f"\n📊 ATS Score: {feedback['ats_score']}/100")
        print(f"🎯 Keyword Match: {feedback['keyword_match_percentage']:.1f}%")
        print(f"✅ Matched Keywords: {len(feedback['matched_keywords'])}")
        print(f"❌ Missing Keywords: {len(feedback['missing_keywords'])}")
        
        if feedback['missing_keywords']:
            print(f"\n📝 Top Missing Keywords:")
            for kw in feedback['missing_keywords'][:15]:
                print(f"   - {kw}")
        
        print(f"\n💡 Suggestions:")
        for suggestion in feedback['suggestions']:
            print(f"   {suggestion}")
        
        # Save feedback
        output_path = resume_path.replace('.json', '_ats_feedback.json')
        checker.save_ats_feedback(feedback, output_path)
        print(f"\n💾 Feedback saved to: {output_path}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
