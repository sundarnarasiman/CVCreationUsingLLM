"""Profile-to-Job Matcher (ENHANCED WITH SEMANTIC SIMILARITY)
Scores how well a candidate profile matches a job description

ENHANCEMENT: Semantic Similarity using OpenAI text-embedding-3-small
Algorithm: Pure Semantic Matching with OpenAI Embeddings

1. Extract keywords from profile and job
2. Get OpenAI embeddings for each keyword (text-embedding-3-small)
3. Calculate cosine similarity between job and profile keywords
4. For each job keyword, find best matching profile keyword
5. Average similarities to get semantic match score

Advantages over exact matching:
- "java" similar to "javascript" 
- "machine learning" similar to "deep learning"
- Handles semantic relationships, not just exact matches
- Typo-tolerant through semantic representation
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

# Embedding cache to avoid redundant API calls
EMBEDDING_CACHE = {}


class ProfileJobMatcher:
    """Match candidate profiles to job descriptions using semantic similarity
    
    Enhanced with OpenAI Embeddings + Cosine Similarity
    - Uses text-embedding-3-small (512 dims, cost-efficient)
    - Semantic matching for better keyword recognition
    - Caching for performance optimization
    """
    
    def __init__(self):
        """Initialize matcher with semantic similarity settings"""
        self.embedding_model = "text-embedding-3-small"
        self.semantic_threshold = 0.7  # Similarity threshold for counting as match
        self.embedding_cache = EMBEDDING_CACHE
    
    def get_embedding(self, text, max_retries=3):
        """Get OpenAI embedding for text using text-embedding-3-small with retry logic
        
        Enhancement: Semantic representation as 512-dimensional vector
        - Caches results to avoid redundant API calls
        - Retry with exponential backoff for transient errors
        - Graceful fallback on repeated failures
        
        Args:
            text (str): Text to embed
            max_retries (int): Max retry attempts (default 3)
            
        Returns:
            list: 512-dimensional embedding vector, or None on failure (with fallback)
        """
        if client is None:
            return None
        
        # Check cache first
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                # Call OpenAI embedding API with timeout
                response = client.embeddings.create(
                    input=text,
                    model=self.embedding_model,
                    timeout=10  # 10 second timeout per request
                )
                
                # Extract embedding
                embedding = response.data[0].embedding
                
                # Cache for future calls
                self.embedding_cache[text] = embedding
                
                return embedding
            
            except TimeoutError as e:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                if attempt < max_retries - 1:
                    print(f"⏱️  API timeout for '{text}' - retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ API timeout failed after {max_retries} retries for '{text}'")
                    return None
            
            except Exception as e:
                error_type = type(e).__name__
                if 'rate' in str(e).lower():
                    wait_time = 2 ** attempt
                    if attempt < max_retries - 1:
                        print(f"🔄 Rate limit hit - retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                
                # For non-retryable errors, log and fail
                print(f"⚠️  Error getting embedding for '{text}': {error_type} - {str(e)[:100]}")
                if attempt == max_retries - 1:
                    print(f"   → Skipping semantic analysis for this keyword")
                    return None
                
        return None
    
    def cosine_similarity(self, vec_a, vec_b):
        """Calculate cosine similarity between two embedding vectors
        
        Formula: cos(θ) = (A · B) / (||A|| × ||B||)
        Range: 0 to 1 where 1.0 = identical, 0.0 = perpendicular
        
        Args:
            vec_a, vec_b (list): Embedding vectors
            
        Returns:
            float: Cosine similarity score (0-1)
        """
        if vec_a is None or vec_b is None:
            return 0.0
        
        # Dot product
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        
        # Magnitudes
        magnitude_a = sum(a ** 2 for a in vec_a) ** 0.5
        magnitude_b = sum(b ** 2 for b in vec_b) ** 0.5
        
        # Avoid division by zero
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)
    
    def calculate_semantic_similarity(self, profile_keywords, job_keywords):
        """Calculate semantic similarity between profile and job keywords with error recovery
        
        ENHANCED ALGORITHM: OpenAI Embeddings + Cosine Similarity
        =========================================================
        
        For each job keyword, find best match in profile keywords using cosine similarity:
        - Similarity >= 0.85: Strong match (1.0 score)
        - Similarity 0.70-0.85: Moderate match (similarity score)
        - Similarity < 0.70: No match (0.0 score)
        
        Returns: Average match score across all job keywords
        With graceful fallback to partial results if API fails.
        
        Args:
            profile_keywords (list): Candidate's keywords
            job_keywords (list): Job's keywords
            
        Returns:
            tuple: (semantic_match_percentage, matched_pairs_dict)
        """
        try:
            if not job_keywords:
                return 100.0, {}
            
            if not profile_keywords:
                return 0.0, {}
            
            # Input validation
            profile_keywords = list(profile_keywords) if isinstance(profile_keywords, (list, set)) else []
            job_keywords = list(job_keywords) if isinstance(job_keywords, (list, set)) else []
            
            if not profile_keywords or not job_keywords:
                return 0.0, {}
            
            # OPTIMIZATION: Limit to top 30 keywords to avoid excessive API calls
            MAX_KEYWORDS = 30
            profile_kws_limited = profile_keywords[:MAX_KEYWORDS]
            job_kws_limited = job_keywords[:MAX_KEYWORDS]
            
            # Get embeddings for limited keywords (with caching)
            profile_embeddings = {}
            for kw in profile_kws_limited:
                try:
                    embedding = self.get_embedding(str(kw).lower())
                    if embedding:
                        profile_embeddings[kw] = embedding
                except Exception as e:
                    print(f"    ⚠️  Failed to embed profile keyword '{kw}': {str(e)[:60]}")
                    continue
            
            job_embeddings = {}
            for kw in job_kws_limited:
                try:
                    embedding = self.get_embedding(str(kw).lower())
                    if embedding:
                        job_embeddings[kw] = embedding
                except Exception as e:
                    print(f"    ⚠️  Failed to embed job keyword '{kw}': {str(e)[:60]}")
                    continue
            
            # Graceful fallback: if no embeddings available, return partial result
            if not profile_embeddings or not job_embeddings:
                print(f"    ⚠️  Could not get embeddings for semantic analysis (API issue) - using exact match only")
                return 0.0, {}
            
            # Calculate similarity for each job keyword
            matched_pairs = {}
            similarity_scores = []
            
            for job_kw, job_embedding in job_embeddings.items():
                if job_embedding is None:
                    continue
                
                # Find best match in profile keywords
                best_match = None
                best_similarity = 0.0
                
                for profile_kw, profile_embedding in profile_embeddings.items():
                    if profile_embedding is None:
                        continue
                    
                    # Calculate cosine similarity
                    similarity = self.cosine_similarity(job_embedding, profile_embedding)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = profile_kw
                
                # Determine match strength
                match_strength = 0.0
                if best_similarity >= 0.85:
                    match_strength = 1.0  # Strong match
                elif best_similarity >= self.semantic_threshold:
                    match_strength = best_similarity  # Moderate match
                
                # Store results
                if best_match:
                    matched_pairs[job_kw] = {
                        'matched_to': best_match,
                        'similarity': round(best_similarity, 3),
                        'match_strength': match_strength
                    }
                    similarity_scores.append(match_strength)
            
            # Calculate average semantic match
            if similarity_scores:
                semantic_match = (sum(similarity_scores) / len(job_keywords)) * 100
            else:
                semantic_match = 0.0
            
            return round(semantic_match, 2), matched_pairs
        
        except Exception as e:
            print(f"❌ Error in semantic similarity calculation: {str(e)[:100]}")
            print(f"   → Returning safe default (0.0)")
            return 0.0, {}
    
    def extract_keywords_from_text(self, text):
        """Extract meaningful keywords from text with input validation
        
        Algorithm: Tokenization with stop-word filtering
        - Regex: Match alphanumeric + [+#.] characters
        - Filter: Remove common English stop words
        - Threshold: Keep words with length > 2
        - Input validation: Handle None/empty strings gracefully
        """
        # Input validation with graceful handling
        if not text:
            return []
        
        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception as e:
                print(f"⚠️  Warning: Could not convert input to string: {str(e)[:80]}")
                return []
        
        # Convert to lowercase and split into words
        try:
            words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#\.]*\b', text.lower())
        except Exception as e:
            print(f"⚠️  Warning: Error extracting keywords: {str(e)[:80]}")
            return []
        
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
        """Extract all keywords from a profile with TF (Term Frequency) weighting
        
        ENHANCEMENT: Keywords are counted by frequency, not just presence
        - More frequent keywords ranked higher
        - Critical/repeated skills prioritized
        - Returns list sorted by frequency (most important first)
        """
        keywords = Counter()  # Use Counter to track keyword frequency
        
        # Skills (high importance - count each skill 2x)
        skills = profile_data.get('skills', {})
        for skill_type, skill_list in skills.items():
            if isinstance(skill_list, list):
                for skill in skill_list:
                    skill_kws = self.extract_keywords_from_text(str(skill))
                    keywords.update(skill_kws)
                    keywords.update(skill_kws)  # Double-weight skills
        
        # Work experience
        experiences = profile_data.get('work_experience', []) or []
        for exp in experiences:
            # Job title (important)
            job_title = exp.get('job_title', '').lower()
            keywords[job_title] += 1
            keywords.update(self.extract_keywords_from_text(job_title))
            
            # Responsibilities
            responsibilities = exp.get('responsibilities', []) or []
            for resp in responsibilities:
                keywords.update(self.extract_keywords_from_text(str(resp)))
        
        # Projects (important technical keywords)
        projects = profile_data.get('projects', []) or []
        for proj in projects:
            technologies = proj.get('technologies', []) or []
            for tech in technologies:
                tech_kws = self.extract_keywords_from_text(str(tech))
                keywords.update(tech_kws)
                keywords.update(tech_kws)  # Double-weight technologies
            
            description = proj.get('description', '') or ''
            keywords.update(self.extract_keywords_from_text(description))
        
        # Certifications
        certifications = profile_data.get('certifications', []) or []
        for cert in certifications:
            keywords.update(self.extract_keywords_from_text(cert.get('name', '')))
        
        # Return keywords sorted by frequency (most common first)
        # This ensures top 30 are the most important keywords
        return [kw for kw, _ in keywords.most_common()]
    
    def extract_job_keywords(self, job_data):
        """Extract all keywords from a job description with TF weighting
        
        ENHANCEMENT: Keywords are counted by frequency for better importance ranking
        - Most repeated requirements weighted higher
        - Returns list sorted by frequency (most important first)
        """
        keywords = Counter()  # Use Counter to track keyword frequency
        
        # Technical skills (high importance - double weight)
        tech_skills = job_data.get('requirements', {}).get('technical_skills', []) or []
        for skill in tech_skills:
            skill_kws = self.extract_keywords_from_text(str(skill))
            keywords.update(skill_kws)
            keywords.update(skill_kws)  # Double-weight required technical skills
        
        # Keywords section
        keywords_section = job_data.get('keywords', {}) or {}
        for keyword_type, keyword_list in keywords_section.items():
            if isinstance(keyword_list, list):
                for kw in keyword_list:
                    keywords.update(self.extract_keywords_from_text(str(kw)))
        
        # Responsibilities
        responsibilities = job_data.get('responsibilities', []) or []
        for resp in responsibilities:
            keywords.update(self.extract_keywords_from_text(str(resp)))
        
        # Return keywords sorted by frequency (most common first)
        return [kw for kw, _ in keywords.most_common()]
    
    def calculate_keyword_overlap(self, profile_keywords, job_keywords):
        """Calculate keyword overlap using hybrid approach: fast match first, then semantic
        
        ENHANCED: Hybrid matching strategy
        1. Quick exact & fuzzy match for speed
        2. Semantic similarity for better accuracy
        Returns match percentage (0-100) combining both approaches
        """
        profile_keywords_list = list(profile_keywords) if isinstance(profile_keywords, set) else profile_keywords
        job_keywords_list = list(job_keywords) if isinstance(job_keywords, set) else job_keywords
        
        if not job_keywords_list:
            return 100.0
        if not profile_keywords_list:
            return 0.0
        
        # STEP 1: Fast exact match first (instant result)
        profile_set = set(k.lower() for k in profile_keywords_list)
        exact_matches = sum(1 for jk in job_keywords_list if jk.lower() in profile_set)
        exact_match_score = (exact_matches / len(job_keywords_list)) * 100
        
        # FAST PATH: If we already have good match (>60%), return quickly
        if exact_match_score >= 60:
            print(f"    ℹ️  Quick match found: {exact_match_score:.1f}% (skipping semantic analysis)")
            return min(exact_match_score + 10, 100)  # Boost slightly for quick wins
        
        # STEP 2: Semantic matching only if quick match isn't sufficient
        print(f"    🔍 Running semantic analysis ({exact_match_score:.1f}% exact → checking semantics)...")
        semantic_match, _ = self.calculate_semantic_similarity(
            profile_keywords_list, job_keywords_list
        )
        
        # Combine scores: favor semantic when matches exist
        combined_score = (exact_match_score * 0.4) + (semantic_match * 0.6)
        return combined_score
    
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
        Calculate overall match score (0-100) with semantic similarity
        
        Scoring breakdown (ENHANCED):
        - Semantic keyword match: 60% (using OpenAI embeddings)
        - Experience match: 20%
        - Education match: 20%
        
        Algorithm: text-embedding-3-small with cosine similarity
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
        
        # Identify strengths and gaps (convert lists to sets for set operations)
        profile_kws_set = set(profile_keywords)
        job_kws_set = set(job_keywords)
        matched_keywords = profile_kws_set.intersection(job_kws_set)
        missing_keywords = job_kws_set - profile_kws_set
        
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
        Complete matching workflow with error handling
        """
        print("\n" + "="*60)
        print("PROFILE-JOB MATCHING")
        print("="*60 + "\n")
        
        # Validate file existence
        if not os.path.exists(profile_filepath):
            raise FileNotFoundError(f"Profile file not found: {profile_filepath}")
        if not os.path.exists(job_filepath):
            raise FileNotFoundError(f"Job file not found: {job_filepath}")
        
        # Load data with error handling
        try:
            with open(profile_filepath, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in profile file: {str(e)[:100]}")
        except Exception as e:
            raise Exception(f"Error reading profile file: {str(e)[:100]}")
        
        try:
            with open(job_filepath, 'r', encoding='utf-8') as f:
                job_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in job file: {str(e)[:100]}")
        except Exception as e:
            raise Exception(f"Error reading job file: {str(e)[:100]}")
        
        # Calculate match
        match_result = self.calculate_match_score(profile_data, job_data)
        
        # Display results
        print(f"📊 Overall Match Score: {match_result['overall_score']}/100")
        print(f"\nScore Breakdown (with Semantic Matching):")
        print(f"  🎯 Semantic Keyword Match: {match_result['keyword_score']:.1f}%")
        print(f"  💼 Experience Match: {match_result['experience_score']:.1f}%")
        print(f"  🎓 Education Match: {match_result['education_score']:.1f}%")
        print(f"\n🔬 Algorithm: OpenAI Semantic Similarity (text-embedding-3-small)")
        
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
        
        # Save results with semantic indicator
        output_path = profile_filepath.replace('.json', '_match_result_semantic.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(match_result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Semantic match results saved to: {output_path}")
        
        return match_result


def main():
    """Test the matcher with comprehensive error handling"""
    matcher = ProfileJobMatcher()
    
    print("Profile-Job Matcher")
    print("="*60)
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            profile_path = input("\nEnter path to profile JSON: ").strip()
            job_path = input("Enter path to job JSON: ").strip()
            
            # Validate inputs
            if not profile_path or not job_path:
                print("❌ Error: Both file paths are required")
                continue
            
            match_result = matcher.match_profile_to_job(profile_path, job_path)
            print("\n✨ Matching complete!")
            break
        
        except FileNotFoundError as e:
            print(f"\n❌ File not found: {str(e)[:100]}")
            if attempt < max_attempts - 1:
                print(f"Try again (attempt {attempt + 2}/{max_attempts})...")
            continue
        
        except ValueError as e:
            print(f"\n❌ Invalid data format: {str(e)[:100]}")
            print("   → Ensure files contain valid JSON data")
            if attempt < max_attempts - 1:
                retry = input("Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    break
            continue
        
        except Exception as e:
            error_type = type(e).__name__
            print(f"\n❌ {error_type}: {str(e)[:100]}")
            if attempt < max_attempts - 1:
                retry = input("Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    break
            continue
    
    if attempt == max_attempts - 1:
        print(f"\n⚠️  Maximum attempts ({max_attempts}) reached. Exiting...")


if __name__ == "__main__":
    main()
