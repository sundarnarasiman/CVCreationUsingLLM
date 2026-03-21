"""
Profile-to-Job Matcher
Scores how well a candidate profile matches a job description
"""

import os
import json
import re
from collections import Counter


class ProfileJobMatcher:
    """Match candidate profiles to job descriptions"""
    
    def __init__(self):
        """Initialize matcher"""
        pass
    
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
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        return keywords
    
    def extract_profile_keywords(self, profile_data):
        """Extract all keywords from a profile"""
        keywords = set()
        
        # Skills
        skills = profile_data.get('skills', {})
        for skill_type, skill_list in skills.items():
            if isinstance(skill_list, list):
                for skill in skill_list:
                    keywords.update(self.extract_keywords_from_text(str(skill)))
        
        # Work experience
        experiences = profile_data.get('work_experience', [])
        for exp in experiences:
            keywords.add(exp.get('job_title', '').lower())
            keywords.update(self.extract_keywords_from_text(exp.get('job_title', '')))
            
            responsibilities = exp.get('responsibilities', [])
            for resp in responsibilities:
                keywords.update(self.extract_keywords_from_text(str(resp)))
        
        # Projects
        projects = profile_data.get('projects', [])
        for proj in projects:
            technologies = proj.get('technologies', [])
            for tech in technologies:
                keywords.update(self.extract_keywords_from_text(str(tech)))
            
            description = proj.get('description', '')
            keywords.update(self.extract_keywords_from_text(description))
        
        # Certifications
        certifications = profile_data.get('certifications', [])
        for cert in certifications:
            keywords.update(self.extract_keywords_from_text(cert.get('name', '')))
        
        return keywords
    
    def extract_job_keywords(self, job_data):
        """Extract all keywords from a job description"""
        keywords = set()
        
        # Technical skills
        tech_skills = job_data.get('requirements', {}).get('technical_skills', [])
        for skill in tech_skills:
            keywords.update(self.extract_keywords_from_text(str(skill)))
        
        # All keywords
        keywords_section = job_data.get('keywords', {})
        for keyword_type, keyword_list in keywords_section.items():
            if isinstance(keyword_list, list):
                for kw in keyword_list:
                    keywords.update(self.extract_keywords_from_text(str(kw)))
        
        # Responsibilities
        responsibilities = job_data.get('responsibilities', [])
        for resp in responsibilities:
            keywords.update(self.extract_keywords_from_text(str(resp)))
        
        return keywords
    
    def calculate_keyword_overlap(self, profile_keywords, job_keywords):
        """Calculate keyword overlap percentage"""
        if not job_keywords:
            return 100.0
        
        overlap = profile_keywords.intersection(job_keywords)
        overlap_percentage = (len(overlap) / len(job_keywords)) * 100
        
        return overlap_percentage
    
    def calculate_experience_match(self, profile_data, job_data):
        """Calculate experience level match"""
        # Extract years of experience from profile
        experiences = profile_data.get('work_experience', [])
        total_months = 0
        
        for exp in experiences:
            # Simple heuristic: count each position as contributing to experience
            # In a real system, you'd parse dates
            total_months += 12  # Assume 1 year per position as baseline
        
        years_experience = total_months / 12
        
        # Extract required experience from job
        experience_reqs = job_data.get('requirements', {}).get('experience', [])
        required_years = 0
        
        for req in experience_reqs:
            # Look for numbers in experience requirements
            numbers = re.findall(r'\d+', str(req))
            if numbers:
                required_years = max(required_years, int(numbers[0]))
        
        # Calculate match
        if required_years == 0:
            return 100.0  # No specific requirement
        
        if years_experience >= required_years:
            return 100.0
        else:
            return (years_experience / required_years) * 100
    
    def calculate_education_match(self, profile_data, job_data):
        """Calculate education match"""
        # Extract education from profile
        profile_education = profile_data.get('education', [])
        profile_degrees = set()
        
        for edu in profile_education:
            degree = edu.get('degree', '').lower()
            profile_degrees.add(degree)
            
            # Extract degree type (bachelor's, master's, etc.)
            if 'bachelor' in degree or 'bs' in degree or 'ba' in degree:
                profile_degrees.add('bachelor')
            if 'master' in degree or 'ms' in degree or 'ma' in degree:
                profile_degrees.add('master')
            if 'phd' in degree or 'doctorate' in degree:
                profile_degrees.add('doctorate')
        
        # Extract education requirements from job
        education_reqs = job_data.get('requirements', {}).get('education', [])
        
        if not education_reqs:
            return 100.0  # No specific requirement
        
        # Check if any requirement is met
        for req in education_reqs:
            req_lower = str(req).lower()
            if any(degree in req_lower for degree in profile_degrees):
                return 100.0
            
            # Check for degree types
            if 'bachelor' in req_lower and 'bachelor' in profile_degrees:
                return 100.0
            if 'master' in req_lower and ('master' in profile_degrees or 'doctorate' in profile_degrees):
                return 100.0
        
        return 50.0  # Partial match
    
    def calculate_match_score(self, profile_data, job_data):
        """
        Calculate overall match score (0-100)
        
        Scoring breakdown:
        - Keyword overlap: 60%
        - Experience match: 20%
        - Education match: 20%
        """
        # Extract keywords
        profile_keywords = self.extract_profile_keywords(profile_data)
        job_keywords = self.extract_job_keywords(job_data)
        
        # Calculate component scores
        keyword_score = self.calculate_keyword_overlap(profile_keywords, job_keywords)
        experience_score = self.calculate_experience_match(profile_data, job_data)
        education_score = self.calculate_education_match(profile_data, job_data)
        
        # Weighted average
        overall_score = (
            keyword_score * 0.6 +
            experience_score * 0.2 +
            education_score * 0.2
        )
        
        # Identify strengths and gaps
        matched_keywords = profile_keywords.intersection(job_keywords)
        missing_keywords = job_keywords - profile_keywords
        
        return {
            'overall_score': round(overall_score, 2),
            'keyword_score': round(keyword_score, 2),
            'experience_score': round(experience_score, 2),
            'education_score': round(education_score, 2),
            'matched_keywords': sorted(list(matched_keywords))[:20],
            'missing_keywords': sorted(list(missing_keywords))[:20],
            'total_matched': len(matched_keywords),
            'total_missing': len(missing_keywords)
        }
    
    def match_profile_to_job(self, profile_filepath, job_filepath):
        """
        Complete matching workflow
        """
        print("\n" + "="*60)
        print("PROFILE-JOB MATCHING")
        print("="*60 + "\n")
        
        # Load data
        with open(profile_filepath, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        
        with open(job_filepath, 'r', encoding='utf-8') as f:
            job_data = json.load(f)
        
        # Calculate match
        match_result = self.calculate_match_score(profile_data, job_data)
        
        # Display results
        print(f"📊 Overall Match Score: {match_result['overall_score']}/100")
        print(f"\nScore Breakdown:")
        print(f"  🎯 Keyword Match: {match_result['keyword_score']:.1f}%")
        print(f"  💼 Experience Match: {match_result['experience_score']:.1f}%")
        print(f"  🎓 Education Match: {match_result['education_score']:.1f}%")
        
        print(f"\n✅ Matched Keywords: {match_result['total_matched']}")
        if match_result['matched_keywords']:
            print(f"   Top matches: {', '.join(match_result['matched_keywords'][:10])}")
        
        print(f"\n❌ Missing Keywords: {match_result['total_missing']}")
        if match_result['missing_keywords']:
            print(f"   Key gaps: {', '.join(match_result['missing_keywords'][:10])}")
        
        # Recommendation
        score = match_result['overall_score']
        if score >= 80:
            print(f"\n💚 STRONG MATCH - Highly recommended to apply")
        elif score >= 60:
            print(f"\n💛 GOOD MATCH - Recommended to apply with tailored resume")
        elif score >= 40:
            print(f"\n🧡 MODERATE MATCH - Consider applying with significant resume tailoring")
        else:
            print(f"\n❤️  WEAK MATCH - May need additional skills or experience")
        
        # Save results
        output_path = profile_filepath.replace('.json', '_match_result.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(match_result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Match results saved to: {output_path}")
        
        return match_result


def main():
    """Test the matcher"""
    matcher = ProfileJobMatcher()
    
    print("Profile-Job Matcher")
    print("="*60)
    
    profile_path = input("\nEnter path to profile JSON: ").strip()
    job_path = input("Enter path to job JSON: ").strip()
    
    try:
        match_result = matcher.match_profile_to_job(profile_path, job_path)
        print("\n✨ Matching complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
