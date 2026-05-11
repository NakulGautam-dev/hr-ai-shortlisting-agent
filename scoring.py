"""
Scoring engine for AI HR Resume Shortlisting System.

ALL numeric scoring happens in Python only.
Gemini/LLM is ONLY used for semantic analysis.

Uses embedding similarity from sentence-transformers for semantic skill matching.
Implements the internship rubric with weighted calculations.
"""

from typing import Optional, Dict, List, Any
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize the embedding model globally (do this once at import)
model = SentenceTransformer('all-MiniLM-L6-v2')


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def normalize_skill_name(skill: str) -> str:
    """
    Normalize skill name for comparison.
    
    Handles:
    - Lowercasing
    - Whitespace trimming
    - Removing common plural suffixes
    
    Args:
        skill (str): Skill name to normalize.
    
    Returns:
        str: Normalized skill name.
    """
    if not skill or not isinstance(skill, str):
        return ""
    
    normalized = skill.lower().strip()
    
    # Remove common plural 's' (but preserve important words)
    if normalized.endswith('s') and len(normalized) > 3:
        singular = normalized[:-1]
        # Only remove 's' if the word is likely a skill noun
        if singular in ['api', 'framework', 'tool', 'library', 'platform']:
            normalized = singular
    
    return normalized


def calculate_semantic_skill_match(
    jd_skills: List[str],
    resume_skills: List[str],
    threshold: float = 0.72
) -> Dict[str, Any]:
    """
    Calculate semantic skill match using skill-by-skill comparison.
    
    For each JD skill, compares against all resume skills and takes the
    highest cosine similarity. Uses embeddings for semantic understanding.
    
    Example:
    JD skill: "REST API"
    Resume has: "REST APIs", "API Development", "Backend"
    
    Compares "REST API" against each, takes highest match.
    
    Args:
        jd_skills (List[str]): Required skills from JD.
        resume_skills (List[str]): Skills listed in resume.
        threshold (float): Minimum similarity to count as match (default: 0.72 for fresher hiring).
    
    Returns:
        Dict with:
        - match_percentage: Percentage of JD skills matched (0-1)
        - matched_skills: List of (jd_skill, resume_skill, similarity)
        - unmatched_skills: List of JD skills that didn't match
    """
    if not jd_skills or not resume_skills:
        return {
            "match_percentage": 0.0,
            "matched_skills": [],
            "unmatched_skills": jd_skills if jd_skills else []
        }
    
    matched_skills = []
    unmatched_skills = []
    matched_resume_indices = set()  # Prevent duplicate matches
    
    try:
        # Generate embeddings for all resume skills once
        resume_embeddings = []
        resume_skills_normalized = []
        
        for skill in resume_skills:
            try:
                embedding = model.encode(skill.lower(), convert_to_tensor=False)
                resume_embeddings.append(embedding)
                resume_skills_normalized.append(skill.lower())
            except Exception:
                continue
        
        # For each JD skill, find best match in resume
        for jd_skill in jd_skills:
            jd_skill_normalized = normalize_skill_name(jd_skill)
            jd_embedding = model.encode(jd_skill_normalized, convert_to_tensor=False)
            
            best_similarity = 0.0
            best_match_idx = -1
            
            # Compare against all resume skills
            for idx, resume_embedding in enumerate(resume_embeddings):
                similarity = cosine_similarity(
                    [jd_embedding],
                    [resume_embedding]
                )[0][0]
                
                # Track best match (but don't use already matched skills)
                if similarity > best_similarity and idx not in matched_resume_indices:
                    best_similarity = similarity
                    best_match_idx = idx
            
            # If best match exceeds threshold, count as matched
            if best_similarity >= threshold and best_match_idx >= 0:
                matched_skills.append({
                    "jd_skill": jd_skill,
                    "resume_skill": resume_skills[best_match_idx],
                    "similarity": float(best_similarity)
                })
                matched_resume_indices.add(best_match_idx)
            else:
                unmatched_skills.append(jd_skill)
        
        # Calculate match percentage
        match_percentage = len(matched_skills) / len(jd_skills) if jd_skills else 0.0
        
        return {
            "match_percentage": match_percentage,
            "matched_skills": matched_skills,
            "unmatched_skills": unmatched_skills,
            "threshold_used": threshold
        }
    
    except Exception as e:
        print(f"Error in semantic skill matching: {e}")
        return {
            "match_percentage": 0.0,
            "matched_skills": [],
            "unmatched_skills": jd_skills if jd_skills else []
        }


def calculate_embedding_similarity(jd_skills: List[str], resume_skills: List[str]) -> float:
    """
    Calculate semantic similarity between JD skills and resume skills using embeddings.
    
    Uses sentence-transformers to convert skills into embeddings,
    then computes cosine similarity between the skill sets.
    
    Args:
        jd_skills (List[str]): Skills required by the job description.
        resume_skills (List[str]): Skills listed in the resume.
    
    Returns:
        float: Similarity score between 0 and 1.
    """
    if not jd_skills or not resume_skills:
        return 0.0
    
    try:
        # Convert skill lists to text for embedding
        jd_text = " ".join(jd_skills)
        resume_text = " ".join(resume_skills)
        
        # Generate embeddings
        jd_embedding = model.encode(jd_text, convert_to_tensor=False)
        resume_embedding = model.encode(resume_text, convert_to_tensor=False)
        
        # Compute cosine similarity
        similarity = cosine_similarity(
            [jd_embedding],
            [resume_embedding]
        )[0][0]
        
        return float(similarity)
    except Exception as e:
        print(f"Error calculating embedding similarity: {e}")
        return 0.0


def calculate_keyword_skill_match(jd_skills: List[str], resume_skills: List[str]) -> float:
    """
    Calculate keyword-based skill match percentage.
    
    Counts how many required skills appear in resume (case-insensitive).
    
    Args:
        jd_skills (List[str]): Skills required by the job description.
        resume_skills (List[str]): Skills listed in the resume.
    
    Returns:
        float: Match percentage between 0 and 1.
    """
    if not jd_skills:
        return 1.0  # No requirements = 100% match
    
    if not resume_skills:
        return 0.0  # No skills listed = 0% match
    
    # Normalize to lowercase for comparison
    jd_skills_lower = [s.lower() for s in jd_skills]
    resume_skills_lower = [s.lower() for s in resume_skills]
    
    # Count matches
    matches = sum(1 for skill in jd_skills_lower if skill in resume_skills_lower)
    
    return matches / len(jd_skills_lower)


# ==============================================================================
# SCORING FUNCTIONS - RUBRIC IMPLEMENTATION
# ==============================================================================

def calculate_skill_score(
    jd_skills: List[str],
    matching_skills: List[str],
    resume_skills: List[str]
) -> Dict[str, Any]:
    """
    Score skills match using improved semantic skill-by-skill comparison.
    
    Uses two approaches:
    1. Keyword matching (40% weight) - Exact string matches
    2. Semantic matching (60% weight) - Skill-by-skill embeddings
    
    Rubric:
    - <30% → 0 points
    - 50-70% → 5 points
    - >85% → 10 points
    
    Args:
        jd_skills (List[str]): Required skills from JD.
        matching_skills (List[str]): Skills that match (from LLM analysis).
        resume_skills (List[str]): All skills listed in resume.
    
    Returns:
        Dict with score (0-10) and justification with matching details.
    """
    # Calculate keyword match percentage
    keyword_match = calculate_keyword_skill_match(jd_skills, resume_skills)
    
    # Calculate semantic match using skill-by-skill comparison
    semantic_result = calculate_semantic_skill_match(jd_skills, resume_skills, threshold=0.72)
    semantic_match = semantic_result["match_percentage"]
    
    # Combine: keyword (40% weight) + semantic (60% weight)
    # Semantic matching has higher weight because it's more accurate
    final_similarity = (keyword_match * 0.4) + (semantic_match * 0.6)
    
    # Apply rubric - three-tier system for skills scoring
    # Tier 1: <30% → 0 points (insufficient match)
    # Tier 2: 30-85% → 5 points (moderate match)
    # Tier 3: >85% → 10 points (excellent match)
    if final_similarity < 0.30:
        score = 0
        reasoning = f"Insufficient skills match ({final_similarity*100:.0f}%)"
    elif 0.30 <= final_similarity < 0.85:
        score = 5
        reasoning = f"Moderate skills match ({final_similarity*100:.0f}%)"
    else:  # >= 0.85
        score = 10
        reasoning = f"Excellent skills match ({final_similarity*100:.0f}%)"
    
    # Extract matched skill details
    matched_skill_pairs = [
        f"{m['jd_skill']} ← {m['resume_skill']} ({m['similarity']:.2f})"
        for m in semantic_result["matched_skills"]
    ]
    
    return {
        "score": score,
        "justification": reasoning,
        "details": {
            "keyword_match": f"{keyword_match*100:.1f}%",
            "semantic_match": f"{semantic_match*100:.1f}%",
            "final_match": f"{final_similarity*100:.1f}%",
            "matched_skills_count": len(semantic_result["matched_skills"]),
            "unmatched_skills_count": len(semantic_result["unmatched_skills"]),
            "matched_skill_pairs": matched_skill_pairs,
            "unmatched_skills": semantic_result["unmatched_skills"]
        }
    }


def calculate_experience_score(
    candidate_experience: List[Dict[str, Any]],
    strengths: List[str],
    projects: Optional[List[Dict[str, Any]]] = None,
    project_relevance: Optional[str] = None
) -> Dict[str, Any]:
    """
    Score experience relevance using multiple deterministic factors.
    
    Fresher-Friendly Rubric:
    - unrelated domain → 0 points
    - adjacent domain OR strong projects/portfolio → 5 points
    - exact domain and seniority → 10 points
    
    For freshers with no full-time experience:
    - Strong academic/project experience (projects list present) → 5 points
    - This compensates for lack of professional experience
    
    Factors analyzed:
    1. Years of experience (seniority level)
    2. Job title similarity (backend/frontend/etc)
    3. Domain keywords (relevant technologies)
    4. Projects/internships/hackathons/open source work (for freshers)
    5. LLM strengths as supporting signal only
    
    Args:
        candidate_experience (List[Dict]): Candidate's experience data.
        strengths (List[str]): Strengths identified by LLM analysis (supporting only).
        projects (Optional[List[Dict]]): Candidate's projects (for fresher compensation).
        project_relevance (Optional[str]): Project relevance assessment ("high", "medium", "low").
    
    Returns:
        Dict with score (0-10) and justification.
    """
    if not candidate_experience:
        # FRESHER LOGIC: No professional experience, but check for projects
        has_projects = projects and len(projects) > 0
        project_strength = project_relevance in ["high", "medium"]
        
        if has_projects and project_strength:
            return {
                "score": 5,
                "justification": "Strong academic/project experience for fresher role",
                "is_fresher": True,
                "experience_count": 0,
                "total_years": 0,
                "project_count": len(projects) if projects else 0,
                "compensated_by_projects": True
            }
        
        return {
            "score": 0,
            "justification": "No experience information provided",
            "is_fresher": True,
            "experience_count": 0,
            "total_years": 0,
            "project_count": len(projects) if projects else 0,
            "compensated_by_projects": False
        }
    
    # Extract experience details
    total_years = 0
    job_titles = []
    descriptions = []
    
    for exp in candidate_experience:
        job_titles.append(exp.get("job_title", "").lower() if exp.get("job_title") else "")
        descriptions.append(exp.get("description", "").lower() if exp.get("description") else "")
        
        # Try to extract years from duration (e.g., "2019-2023" = 4 years)
        duration = exp.get("duration", "")
        if duration and "-" in duration:
            try:
                parts = duration.split("-")
                if len(parts) == 2:
                    start = int(parts[0].strip()[:4])
                    end = int(parts[1].strip()[:4])
                    total_years += (end - start)
            except (ValueError, IndexError):
                pass
    
    # Analyze job titles for relevance
    backend_keywords = ["backend", "python", "server", "api", "engineer", "developer"]
    frontend_keywords = ["frontend", "react", "javascript", "ui", "web"]
    domain_keywords = ["software", "engineer", "developer", "architect"]
    
    titles_text = " ".join(job_titles)
    descriptions_text = " ".join(descriptions)
    
    # Determine domain match
    backend_match = any(kw in titles_text or kw in descriptions_text for kw in backend_keywords)
    frontend_match = any(kw in titles_text or kw in descriptions_text for kw in frontend_keywords)
    has_seniority = total_years >= 2 or any(kw in titles_text for kw in ["senior", "lead", "architect"])
    
    # Use Gemini strengths as supporting signal
    strengths_text = " ".join(strengths).lower() if strengths else ""
    gemini_exact = any(kw in strengths_text for kw in ["exact", "direct", "relevant"])
    
    # Score logic (deterministic + Gemini support)
    if (backend_match or frontend_match) and has_seniority and gemini_exact:
        score = 10
        reasoning = f"Exact domain match with {total_years}+ years relevant experience"
    elif (backend_match or frontend_match) and total_years >= 1:
        score = 5
        reasoning = f"Adjacent/related domain with {total_years} years experience"
    else:
        score = 0
        reasoning = "Experience from different domain or unclear relevance"
    
    return {
        "score": score,
        "justification": reasoning,
        "experience_count": len(candidate_experience),
        "total_years": total_years,
        "has_seniority": has_seniority,
        "is_fresher": False,
        "compensated_by_projects": False
    }


def calculate_education_score(
    jd_education: Optional[str],
    candidate_education: List[Dict[str, Any]],
    certifications: List[str]
) -> Dict[str, Any]:
    """
    Score education and certifications based on relevance.
    
    Rubric:
    - below minimum → 0 points
    - meets minimum → 5 points
    - exceeds minimum + relevant certifications → 10 points
    
    Only recognizes industry-relevant certifications:
    AWS, Google Cloud, Azure, Meta, Oracle, Kubernetes, etc.
    
    Args:
        jd_education (str): Minimum education requirement from JD.
        candidate_education (List[Dict]): Candidate's education data.
        certifications (List[str]): Candidate's certifications.
    
    Returns:
        Dict with score (0-10) and justification.
    """
    if not candidate_education:
        return {
            "score": 0,
            "justification": "No education information provided"
        }
    
    # List of recognized tech certifications
    relevant_certs = [
        "aws", "amazon", "google cloud", "gcp", "azure", "microsoft",
        "kubernetes", "docker", "meta", "oracle", "salesforce",
        "cisco", "linux", "comptia", "cka", "certified"
    ]
    
    # Check for relevant certifications only
    relevant_certification_count = 0
    if certifications:
        certs_text = " ".join(c.lower() for c in certifications)
        for cert_keyword in relevant_certs:
            if cert_keyword in certs_text:
                relevant_certification_count += 1
                break  # Count only once per certification
    
    # Score based on education + relevant certifications
    has_education = len(candidate_education) > 0
    has_relevant_certs = relevant_certification_count > 0
    
    if has_education and has_relevant_certs:
        score = 10
        reasoning = f"Exceeds requirements with {len(certifications)} relevant certification(s)"
    elif has_education:
        score = 5
        reasoning = "Meets minimum education requirement"
    else:
        score = 0
        reasoning = "Does not meet minimum education requirement"
    
    return {
        "score": score,
        "justification": reasoning,
        "education_entries": len(candidate_education),
        "total_certifications": len(certifications) if certifications else 0,
        "relevant_certifications": relevant_certification_count
    }


def calculate_project_score(
    projects: List[Dict[str, Any]],
    project_relevance: Optional[str]
) -> Dict[str, Any]:
    """
    Score candidate's project/portfolio relevance.
    
    Rubric:
    - no projects → 0 points
    - generic projects → 5 points
    - highly relevant projects → 10 points
    
    Args:
        projects (List[Dict]): Candidate's projects.
        project_relevance (str): Project relevance assessment ("high", "medium", "low", null).
    
    Returns:
        Dict with score (0-10) and justification.
    """
    if not projects:
        return {
            "score": 0,
            "justification": "No projects or portfolio evidence"
        }
    
    # Map project relevance to score
    if project_relevance == "high":
        score = 10
        reasoning = "Strong relevant portfolio with directly applicable projects"
    elif project_relevance == "medium":
        score = 5
        reasoning = f"Generic or partially relevant projects ({len(projects)} projects)"
    elif project_relevance == "low":
        score = 0
        reasoning = "Projects are not relevant to the job requirements"
    else:
        # Default: if projects exist but no relevance assessment, assume moderate
        score = 5
        reasoning = f"Projects present but relevance unclear ({len(projects)} projects)"
    
    return {
        "score": score,
        "justification": reasoning,
        "project_count": len(projects)
    }


def calculate_communication_score(communication_quality: Optional[str]) -> Dict[str, Any]:
    """
    Score communication quality based on resume presentation.
    
    Mapping:
    - poor → 0 points
    - average → 5 points
    - good → 8 points
    - excellent → 10 points
    
    Args:
        communication_quality (str): Quality assessment ("excellent", "good", "average", "poor", null).
    
    Returns:
        Dict with score (0-10) and justification.
    """
    quality_mapping = {
        "excellent": (10, "Excellent written communication - clear, professional, well-organized"),
        "good": (8, "Good written communication - mostly clear with minor issues"),
        "average": (5, "Average communication - readable but could be clearer"),
        "poor": (0, "Poor communication - difficult to follow or unclear"),
        None: (5, "Communication quality not assessed - assuming average")
    }
    
    quality_lower = communication_quality.lower() if communication_quality else None
    score, reasoning = quality_mapping.get(quality_lower, (5, "Communication quality: not specified"))
    
    return {
        "score": score,
        "justification": reasoning
    }


def calculate_final_score(
    skills_score: int,
    experience_score: int,
    education_score: int,
    projects_score: int,
    communication_score: int
) -> float:
    """
    Calculate final weighted score using the rubric weights.
    
    Weights:
    - Skills: 30%
    - Experience: 25%
    - Education: 15%
    - Projects: 20%
    - Communication: 10%
    
    Formula:
    final_percentage = (s*0.30 + e*0.25 + ed*0.15 + p*0.20 + c*0.10) * 10
    
    Scores are out of 10, final result is out of 100.
    
    Args:
        skills_score (int): Skills match score (0-10).
        experience_score (int): Experience score (0-10).
        education_score (int): Education score (0-10).
        projects_score (int): Projects score (0-10).
        communication_score (int): Communication score (0-10).
    
    Returns:
        float: Final score out of 100.
    """
    weighted_sum = (
        skills_score * 0.30 +
        experience_score * 0.25 +
        education_score * 0.15 +
        projects_score * 0.20 +
        communication_score * 0.10
    )
    
    final_percentage = weighted_sum * 10
    
    return round(final_percentage, 1)


# ==============================================================================
# MAIN SCORING FUNCTION
# ==============================================================================

def score_candidate(
    jd_data: Dict[str, Any],
    resume_data: Dict[str, Any],
    analysis_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Score a candidate comprehensively using JD, resume, and semantic analysis.
    
    Args:
        jd_data (Dict): Extracted JD data with required_skills, education, etc.
        resume_data (Dict): Extracted resume data with skills, experience, education.
        analysis_data (Dict): LLM semantic analysis with matching_skills, strengths, etc.
    
    Returns:
        Dict: Comprehensive scoring result with breakdown.
    """
    try:
        # Extract data with safe defaults
        jd_skills = jd_data.get("required_skills", [])
        resume_skills = resume_data.get("skills", [])
        candidate_name = resume_data.get("candidate_name", "Unknown")
        
        matching_skills = analysis_data.get("matching_skills", [])
        strengths = analysis_data.get("strengths", [])
        project_relevance = analysis_data.get("project_relevance")
        communication_quality = analysis_data.get("communication_quality")
        
        candidate_experience = resume_data.get("experience", [])
        candidate_education = resume_data.get("education", [])
        certifications = resume_data.get("certifications", [])
        projects = resume_data.get("projects", [])
        
        # Calculate individual scores
        skills_result = calculate_skill_score(jd_skills, matching_skills, resume_skills)
        experience_result = calculate_experience_score(
            candidate_experience,
            strengths,
            projects,
            project_relevance
        )
        education_result = calculate_education_score(
            jd_data.get("education"),
            candidate_education,
            certifications
        )
        projects_result = calculate_project_score(projects, project_relevance)
        communication_result = calculate_communication_score(communication_quality)
        
        # Calculate final score
        final_score = calculate_final_score(
            skills_result["score"],
            experience_result["score"],
            education_result["score"],
            projects_result["score"],
            communication_result["score"]
        )
        
        return {
            "candidate_name": candidate_name,
            "final_score": final_score,
            "breakdown": {
                "skills": skills_result,
                "experience": experience_result,
                "education": education_result,
                "projects": projects_result,
                "communication": communication_result
            }
        }
    
    except Exception as e:
        print(f"Error scoring candidate: {e}")
        return {
            "candidate_name": resume_data.get("candidate_name", "Unknown"),
            "final_score": 0.0,
            "error": str(e)
        }


def rank_candidates(candidate_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank candidates by their final scores in descending order.
    
    Args:
        candidate_results (List[Dict]): List of scoring results from score_candidate().
    
    Returns:
        List[Dict]: Candidates sorted by final_score (highest first).
    """
    sorted_results = sorted(
        candidate_results,
        key=lambda x: x.get("final_score", 0),
        reverse=True
    )
    
    # Add ranking
    for rank, result in enumerate(sorted_results, 1):
        result["rank"] = rank
    
    return sorted_results


# ==============================================================================
# TESTING AND EXAMPLES
# ==============================================================================

if __name__ == "__main__":
    print("AI HR Resume Shortlisting - Scoring Engine Test")
    print("=" * 70)
    
    # Sample JD data
    sample_jd = {
        "required_skills": ["Python", "Django", "PostgreSQL", "Docker", "REST API"],
        "preferred_skills": ["AWS", "Kubernetes"],
        "education": "Bachelor's in Computer Science",
        "experience_required": "5+ years backend development",
        "responsibilities": ["Design scalable services", "Mentor developers"]
    }
    
    # Sample Resume data
    sample_resume = {
        "candidate_name": "John Doe",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis", "REST APIs"],
        "experience": [
            {
                "job_title": "Senior Backend Engineer",
                "company": "TechCorp",
                "duration": "2021-2023",
                "description": "Built microservices using Python and FastAPI"
            },
            {
                "job_title": "Backend Engineer",
                "company": "StartupXYZ",
                "duration": "2018-2021",
                "description": "Developed REST APIs using Django"
            }
        ],
        "education": [
            {
                "degree": "BS",
                "field": "Computer Science",
                "institution": "State University",
                "graduation_year": 2018
            }
        ],
        "certifications": ["AWS Solutions Architect Associate"],
        "projects": [
            {
                "name": "Microservices Platform",
                "description": "Built scalable microservices architecture using Python and Docker"
            },
            {
                "name": "REST API Gateway",
                "description": "Designed and implemented high-performance API gateway"
            }
        ]
    }
    
    # Sample LLM analysis data
    sample_analysis = {
        "matching_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "REST API design"],
        "missing_skills": ["Kubernetes"],
        "strengths": [
            "5+ years of relevant backend development experience",
            "Hands-on microservices architecture experience",
            "Leadership experience demonstrated"
        ],
        "weaknesses": [
            "No Kubernetes or container orchestration experience"
        ],
        "project_relevance": "high",
        "communication_quality": "good",
        "overall_summary": "Strong backend candidate with excellent relevant experience"
    }
    
    # Score the candidate
    print("\nScoring candidate...\n")
    result = score_candidate(sample_jd, sample_resume, sample_analysis)
    
    # Display results
    print(f"Candidate: {result['candidate_name']}")
    print(f"Final Score: {result['final_score']}/100")
    print("\nBreakdown:")
    print("-" * 70)
    
    for category, data in result['breakdown'].items():
        score = data.get('score', 'N/A')
        justification = data.get('justification', 'N/A')
        print(f"\n{category.upper()}: {score}/10")
        print(f"  → {justification}")
    
    print("\n" + "=" * 70)
    print("✓ Scoring engine test completed successfully!")
