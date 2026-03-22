"""Feature 4b: ATS Compatibility Checker (ENHANCED WITH SEMANTIC SIMILARITY)
Provides real-time ATS scoring and feedback for resumes

ENHANCEMENT: Semantic Similarity using OpenAI text-embedding-3-small
- Keyword matching uses semantic embeddings instead of exact matching
- Detects related technical terms (e.g., "python" similar to "java")
- Better accuracy for ATS scoring with semantic understanding
"""

import os
import json
import re
import time
from collections import Counter
from dotenv import load_dotenv
from openai import OpenAI

from exceptions import APIClientError
from logging_config import get_logger

load_dotenv()

logger = get_logger(__name__)

# Initialize OpenAI client with proper error handling
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    print(f"Warning: Error initializing OpenAI client: {str(e)}")
    client = None

# Embedding cache shared across instances
EMBEDDING_CACHE_ATS = {}

TECHNICAL_PHRASES = [
    'machine learning',
    'deep learning',
    'natural language',
    'natural language processing',
    'cloud infrastructure',
    'distributed systems',
    'data pipeline',
    'data engineering',
    'container orchestration',
    'continuous integration',
    'continuous delivery',
    'ci/cd',
    'rest api',
    'backend engineering',
    'software engineering',
    'microservices',
]


class ATSChecker:
    """Analyze resume content for ATS compatibility
    
    Enhanced with OpenAI Semantic Similarity for better keyword matching
    """
    
    def __init__(self):
        """Initialize the ATS checker"""
        self.threshold = int(os.getenv("ATS_SCORE_THRESHOLD", "75"))
        self.embedding_model = "text-embedding-3-small"
        self.semantic_threshold = 0.7
        self.embedding_cache = EMBEDDING_CACHE_ATS
        
        # Common ATS-problematic elements
        self.problematic_patterns = {
            'tables': r'\|.*\|',  # Markdown tables
            'special_chars': r'[★☆●○■□▪▫◆◇]',  # Special bullets
            'complex_formatting': r'{|}|\\begin|\\end',  # LaTeX-like
        }
    
    def get_embedding(self, text, max_retries=3):
        """Get OpenAI embedding for text with retry logic and error recovery"""
        if client is None:
            return None
        
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                response = client.embeddings.create(
                    input=text,
                    model=self.embedding_model,
                    timeout=10  # 10 second timeout per request
                )
                embedding = response.data[0].embedding
                self.embedding_cache[text] = embedding
                return embedding
            
            except TimeoutError as e:
                wait_time = 2 ** attempt
                if attempt < max_retries - 1:
                    print(f"⏱️  ATS API timeout - retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ ATS API timeout failed after {max_retries} retries")
                    return None
            
            except Exception as e:
                error_type = type(e).__name__
                if 'rate' in str(e).lower():
                    wait_time = 2 ** attempt
                    if attempt < max_retries - 1:
                        print(f"🔄 Rate limit hit - retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                
                print(f"⚠️  Error getting embedding: {error_type} - {str(e)[:80]}")
                if attempt == max_retries - 1:
                    print(f"   → Skipping semantic analysis for this keyword")
                    return None
        
        return None
    
    def cosine_similarity(self, vec_a, vec_b):
        """Calculate cosine similarity between embedding vectors"""
        if vec_a is None or vec_b is None:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        magnitude_a = sum(a ** 2 for a in vec_a) ** 0.5
        magnitude_b = sum(b ** 2 for b in vec_b) ** 0.5
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)
    
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
        technical_phrases = self.extract_technical_phrases(text)
        keywords = technical_phrases + keywords
        
        return keywords

    def extract_technical_phrases(self, text):
        """Extract curated 2-3 word technical phrases from text."""
        if not text or not isinstance(text, str):
            return []

        text_lower = text.lower()
        found_phrases = []

        for phrase in TECHNICAL_PHRASES:
            pattern = rf'(?<!\w){re.escape(phrase)}(?!\w)'
            matches = re.findall(pattern, text_lower)
            if matches:
                found_phrases.extend([phrase] * len(matches))

        return found_phrases
    
    def calculate_keyword_match(self, resume_content, job_data):
        """Calculate keyword match using HYBRID approach: fast exact + semantic + TF-WEIGHTED
        
        OPTIMIZATION: Two-stage matching with TF (Term Frequency) weighting
        Stage 1: Fast exact/fuzzy match (instant)
        Stage 2: Semantic similarity only if needed (uses API)
        Stage 0: Use frequency weighting to prioritize important keywords
        
        Returns: (match_percentage, matched_keywords, missing_keywords)
        """
        # Extract job keywords with frequency weighting
        job_keywords = Counter()
        
        if isinstance(job_data, dict):
            # Technical skills (high importance - double weight)
            tech_skills = job_data.get('requirements', {}).get('technical_skills', [])
            if tech_skills:
                for skill in tech_skills:
                    skill_kws = self.extract_keywords_from_text(str(skill))
                    job_keywords.update(skill_kws)
                    job_keywords.update(skill_kws)  # Double-weight required technical skills
            
            # Keywords section
            keywords_section = job_data.get('keywords', {})
            if keywords_section:
                for keyword_type, keyword_list in keywords_section.items():
                    if isinstance(keyword_list, list):
                        for kw in keyword_list:
                            job_keywords.update(self.extract_keywords_from_text(str(kw)))
            
            # Responsibilities
            responsibilities = job_data.get('responsibilities', [])
            if responsibilities:
                for resp in responsibilities:
                    job_keywords.update(self.extract_keywords_from_text(str(resp)))
        
        # Extract resume keywords with frequency weighting
        resume_text = self.extract_text_from_resume(resume_content)
        resume_kws_extracted = self.extract_keywords_from_text(resume_text)
        resume_keywords = Counter(resume_kws_extracted)  # Count frequency
        
        if not job_keywords:
            return 100.0, [], list(job_keywords)
        
        # OPTIMIZATION: Limit to top 30 keywords (by frequency, not position!)
        MAX_KEYWORDS = 30
        job_kws_limited = [kw for kw, _ in job_keywords.most_common(MAX_KEYWORDS)]
        resume_kws_limited = [kw for kw, _ in resume_keywords.most_common(MAX_KEYWORDS)]
        
        # STAGE 1: Fast exact match (instant, no API calls)
        resume_set = set(kw.lower() for kw in resume_kws_limited)
        matched_keywords = []
        missing_keywords = []
        
        for job_kw in job_kws_limited:
            if job_kw.lower() in resume_set:
                matched_keywords.append(job_kw)
        
        exact_match_pct = (len(matched_keywords) / len(job_kws_limited)) * 100 if job_kws_limited else 0
        
        # STAGE 2: If exact match is good enough (>60%), return quickly
        if exact_match_pct >= 60:
            print(f"    ℹ️  ATS Quick match: {exact_match_pct:.1f}% exact (skipping semantic)")
            missing_keywords = [k for k in job_kws_limited if k not in matched_keywords]
            return min(exact_match_pct + 15, 100), matched_keywords, missing_keywords
        
        # STAGE 2: Semantic matching for more accuracy
        print(f"    🔍 ATS Semantic analysis ({exact_match_pct:.1f}% exact → checking semantics)...")
        
        job_embeddings = {}
        for kw in job_kws_limited:
            embedding = self.get_embedding(kw.lower())
            if embedding:
                job_embeddings[kw] = embedding
        
        resume_embeddings = {}
        for kw in resume_kws_limited:
            embedding = self.get_embedding(kw.lower())
            if embedding:
                resume_embeddings[kw] = embedding
        
        # Calculate semantic similarity for each job keyword
        matched_keywords = []
        missing_keywords = []
        similarity_scores = []
        
        for job_kw, job_embedding in job_embeddings.items():
            if job_embedding is None:
                continue
            
            # Find best match in resume keywords
            best_similarity = 0.0
            for resume_kw, resume_embedding in resume_embeddings.items():
                if resume_embedding is None:
                    continue
                
                similarity = self.cosine_similarity(job_embedding, resume_embedding)
                best_similarity = max(best_similarity, similarity)
            
            # Determine match strength
            match_strength = 0.0
            if best_similarity >= 0.85:
                match_strength = 1.0
            elif best_similarity >= self.semantic_threshold:
                match_strength = best_similarity
            
            # Categorize
            if match_strength > 0:
                matched_keywords.append(job_kw)
                similarity_scores.append(match_strength)
            else:
                missing_keywords.append(job_kw)
        
        # Calculate match percentage combining both stages
        if similarity_scores:
            semantic_match_pct = (sum(similarity_scores) / len(job_kws_limited)) * 100
        else:
            semantic_match_pct = 0.0
        
        # Blend exact and semantic scores
        final_match_pct = (exact_match_pct * 0.4) + (semantic_match_pct * 0.6)
        print(
            f"    ℹ️  Exact keyword match: {exact_match_pct:.1f}%, "
            f"then semantic expansion started, final keyword match: {final_match_pct:.1f}%."
        )
        
        return final_match_pct, sorted(matched_keywords), sorted(missing_keywords)
    
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
        - Keyword match (SEMANTIC): 50 points
        - Formatting: 25 points
        - Section completeness: 15 points
        - Content quality: 10 points
        
        Algorithm: OpenAI text-embedding-3-small for keyword matching
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
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
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
        print("ATS ANALYSIS RESULTS (SEMANTIC SIMILARITY)")
        print("="*60)
        print(f"\n📊 ATS Score: {feedback['ats_score']}/100")
        print(f"🎯 Semantic Keyword Match: {feedback['keyword_match_percentage']:.1f}%")
        print(f"✅ Matched Keywords: {len(feedback['matched_keywords'])}")
        print(f"❌ Missing Keywords: {len(feedback['missing_keywords'])}")
        print(f"\n🔬 Algorithm: OpenAI text-embedding-3-small (semantic matching)")
        
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
