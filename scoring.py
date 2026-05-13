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
    threshold: float = 0.65
) -> Dict[str, Any]:
    """
    Calculate semantic skill match using skill-by-skill comparison with continuous scoring.
    
    IMPROVED LOGIC (v2.0):
    Instead of binary matched/unmatched, returns continuous similarity scores.
    For each JD skill, finds the best matching resume skill and captures the similarity.
    
    Example:
    JD: ["React", "Node.js", "MongoDB"]
    Resume: ["React.js", "Express.js", "MongoDB Atlas"]
    
    Results:
    - React → React.js: 0.92 similarity
    - Node.js → Express.js: 0.71 similarity  
    - MongoDB → MongoDB Atlas: 0.89 similarity
    
    Average similarity: (0.92 + 0.71 + 0.89) / 3 = 0.84 (CONTINUOUS, not binary)
    
    Args:
        jd_skills (List[str]): Required skills from JD.
        resume_skills (List[str]): Skills listed in resume.
        threshold (float): Used ONLY for reporting matched/unmatched (default: 0.65).
                          Does NOT affect final similarity score calculation.
    
    Returns:
        Dict with:
        - semantic_average: Average similarity across all JD skills (0-1, CONTINUOUS)
        - matched_skills: List of (jd_skill, resume_skill, similarity) where similarity >= threshold
        - unmatched_skills: List of JD skills where best similarity < threshold
        - top_skill_similarities: All JD skills with their best matches (for transparency)
        - threshold_used: Threshold value used for reporting
    """
    if not jd_skills or not resume_skills:
        return {
            "semantic_average": 0.0,
            "matched_skills": [],
            "unmatched_skills": jd_skills if jd_skills else [],
            "top_skill_similarities": [],
            "threshold_used": threshold
        }
    
    matched_skills = []
    unmatched_skills = []
    all_similarities = []  # Store ALL similarities for averaging
    top_skill_similarities = []  # For transparency
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
            
            # IMPROVED: Always collect similarity (even if below threshold)
            # This contributes to the continuous scoring
            all_similarities.append(best_similarity)
            
            # Track best match for transparency
            if best_match_idx >= 0:
                top_skill_similarities.append({
                    "jd_skill": jd_skill,
                    "best_resume_skill": resume_skills[best_match_idx],
                    "similarity": float(best_similarity)
                })
            
            # Use threshold ONLY for reporting matched vs unmatched
            if best_similarity >= threshold and best_match_idx >= 0:
                matched_skills.append({
                    "jd_skill": jd_skill,
                    "resume_skill": resume_skills[best_match_idx],
                    "similarity": float(best_similarity)
                })
                matched_resume_indices.add(best_match_idx)
            else:
                unmatched_skills.append(jd_skill)
        
        # IMPROVED: Calculate semantic_average from ALL similarities
        # This gives continuous scoring instead of binary
        semantic_average = sum(all_similarities) / len(all_similarities) if all_similarities else 0.0
        
        return {
            "semantic_average": float(semantic_average),  # CONTINUOUS scoring (0-1)
            "matched_skills": matched_skills,             # For reporting only
            "unmatched_skills": unmatched_skills,         # For reporting only
            "top_skill_similarities": top_skill_similarities,  # Full transparency
            "threshold_used": threshold
        }
    
    except Exception as e:
        print(f"Error in semantic skill matching: {e}")
        return {
            "semantic_average": 0.0,
            "matched_skills": [],
            "unmatched_skills": jd_skills if jd_skills else [],
            "top_skill_similarities": [],
            "threshold_used": threshold
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
    resume_skills: List[str],
    analysis_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Score skills match using improved semantic skill-by-skill comparison (v2.0).
    
    IMPROVEMENTS IN v2.0:
    =====================
    
    1. CONTINUOUS SEMANTIC SCORING
       - Old: Binary matched/unmatched only
       - New: Average similarity from 0-1 across all skills
       - Benefits: Strong candidates no longer get unfair 0
    
    2. SOFTER WEIGHTED FORMULA
       - Old: (keyword * 0.2) + (semantic * 0.8)
       - New: (keyword * 0.15) + (semantic_avg * 0.65) + (gemini_support * 0.20)
       - Benefits: More realistic, more HR-friendly
    
    3. IMPROVED RUBRIC (more forgiving)
       - Old: <30%→0, 30-85%→5, >85%→10
       - New: <40%→2, 40-60%→5, 60-80%→8, >=80%→10
       - Benefits: Rewards partial matches, prevents harsh zeros
    
    4. GEMINI AS SUPPORT SIGNAL ONLY
       - Gemini does not directly score
       - Only acts as supporting signal (max 20% weight)
       - Python remains the decision maker
    
    Example of improvement:
    
    JD: ["React", "Node.js", "MongoDB"]
    Resume: ["React.js", "Express.js", "MongoDB Atlas"]
    
    OLD LOGIC:
    - Only React matched (threshold 0.65)
    - Match percentage: 1/3 = 33% → Score: 5 points
    - Candidate unfairly scored even though skills are semantically related
    
    NEW LOGIC:
    - Similarities: 0.92, 0.71, 0.89
    - semantic_average: (0.92 + 0.71 + 0.89)/3 = 0.84
    - final_similarity: (0.15*keyword) + (0.65*0.84) + (0.20*0.84) = 0.83
    - Score: 8 points (fair for strong candidate)
    - Plus transparent output showing all 3 matched skills
    
    Args:
        jd_skills (List[str]): Required skills from JD.
        matching_skills (List[str]): Skills that match (from LLM analysis).
        resume_skills (List[str]): All skills listed in resume.
        analysis_data (Optional[Dict]): LLM analysis data with optional semantic_relevance_score.
    
    Returns:
        Dict with score (0-10) and comprehensive justification with:
        - semantic_average: Continuous similarity score
        - gemini_support: Supporting signal value
        - top_skill_similarities: All matched skills with similarities
        - matched_skill_pairs: Human-readable matched pairs
        - unmatched_skills: Skills not matched (for reference)
    """
    # Calculate keyword match percentage (0-1)
    keyword_match = calculate_keyword_skill_match(jd_skills, resume_skills)
    
    # Calculate semantic match using improved skill-by-skill comparison
    semantic_result = calculate_semantic_skill_match(jd_skills, resume_skills, threshold=0.65)
    semantic_average = semantic_result["semantic_average"]  # CONTINUOUS (0-1), not binary
    
    # IMPROVED: Extract or calculate Gemini support signal (0-1)
    # If analysis_data provided with semantic_relevance_score, use it
    # Otherwise, use semantic_average as fallback (conservative approach)
    gemini_support = 0.0
    if analysis_data and "semantic_relevance_score" in analysis_data:
        gemini_support = float(analysis_data.get("semantic_relevance_score", 0.0))
        # Ensure it's in valid range
        gemini_support = max(0.0, min(1.0, gemini_support))
    else:
        # Fallback: use semantic_average (Gemini not provided)
        # This ensures consistent scoring even without explicit Gemini input
        gemini_support = semantic_average
    
    # IMPROVED: New weighted formula (softer, more realistic)
    # Old: (keyword * 0.2) + (semantic * 0.8)
    # New: Balanced between keywords, semantic understanding, and LLM support
    final_similarity = (keyword_match * 0.15) + (semantic_average * 0.65) + (gemini_support * 0.20)
    
    # IMPROVED: Softer rubric (more forgiving than old harsh tier system)
    # Old: <30%→0, 30-85%→5, >85%→10
    # New: <40%→2, 40-60%→5, 60-80%→8, >=80%→10
    # This prevents unfair zeros for candidates with partial matches
    if final_similarity < 0.40:
        score = 2
        reasoning = f"Limited skills match ({final_similarity*100:.0f}%)"
    elif 0.40 <= final_similarity < 0.60:
        score = 5
        reasoning = f"Moderate skills match ({final_similarity*100:.0f}%)"
    elif 0.60 <= final_similarity < 0.80:
        score = 8
        reasoning = f"Good skills match ({final_similarity*100:.0f}%)"
    else:  # >= 0.80
        score = 10
        reasoning = f"Excellent skills match ({final_similarity*100:.0f}%)"
    
    # Extract matched skill details
    matched_skill_pairs = [
        f"{m['jd_skill']} ← {m['resume_skill']} ({m['similarity']:.2f})"
        for m in semantic_result["matched_skills"]
    ]
    
    # NEW: Include top skill similarities for full transparency
    top_skill_matches = semantic_result.get("top_skill_similarities", [])
    
    return {
        "score": score,
        "justification": reasoning,
        "details": {
            "keyword_match": f"{keyword_match*100:.1f}%",
            "semantic_average": f"{semantic_average*100:.1f}%",  # NEW: Continuous score
            "gemini_support": f"{gemini_support*100:.1f}%",       # NEW: LLM support signal
            "final_match": f"{final_similarity*100:.1f}%",
            "matched_skills_count": len(semantic_result["matched_skills"]),
            "unmatched_skills_count": len(semantic_result["unmatched_skills"]),
            "matched_skill_pairs": matched_skill_pairs,
            "unmatched_skills": semantic_result["unmatched_skills"],
            "top_skill_similarities": top_skill_matches  # NEW: Full transparency
        }
    }


def _detect_fresher_status(total_years: float) -> bool:
    """Detect if candidate is a fresher (no or minimal professional experience)."""
    return total_years < 1.0


def _detect_project_strength_indicators(project: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a project for strength indicators showing production-level work.
    
    Indicators analyzed:
    - deployment status (deployed, live, production, live)
    - real users or impact (users, visitors, downloads, revenue)
    - scalability (scalable, scaling, performance, optimization)
    - real-time features (real-time, live, streaming, analytics)
    - advanced tech (AI-powered, ML, dashboard, analytics, authentication)
    - cloud/DevOps (Docker, cloud, AWS, GCP, Azure, Kubernetes)
    - full-stack (full-stack, end-to-end, backend, frontend)
    
    Returns:
        Dict with indicators found and overall strength level.
    """
    if not project:
        return {
            "deployed": False,
            "real_users": False,
            "measurable_impact": False,
            "scalable": False,
            "advanced_tech": False,
            "cloud_devops": False,
            "full_stack": False,
            "strength_level": 0
        }
    
    # Combine all project text for analysis
    project_text = " ".join([
        project.get("title", ""),
        project.get("description", ""),
        project.get("technologies", ""),
        project.get("details", "")
    ]).lower()
    
    indicators = {
        "deployed": False,
        "real_users": False,
        "measurable_impact": False,
        "scalable": False,
        "advanced_tech": False,
        "cloud_devops": False,
        "full_stack": False,
        "strength_level": 0
    }
    
    # Check for deployment indicators
    deployment_keywords = ["deployed", "live", "production", "live on", "published", "hosted"]
    indicators["deployed"] = any(kw in project_text for kw in deployment_keywords)
    
    # Check for real users/impact
    user_impact_keywords = [
        "users", "visitors", "downloads", "revenue", "₹", "$", "payments", 
        "subscribers", "active", "traffic", "requests", "deployed for"
    ]
    indicators["real_users"] = any(kw in project_text for kw in user_impact_keywords)
    
    # Check for numeric metrics (e.g., "1000+ users", "15K visitors", "₹4000 revenue")
    import re
    numeric_pattern = r'\d+[K+%]*\s*(?:users|visitors|downloads|revenue|subscribers|active|visits|requests)'
    indicators["measurable_impact"] = bool(re.search(numeric_pattern, project_text))
    
    # Check for scalability keywords
    scalability_keywords = ["scalable", "scaling", "performance", "optimization", "efficient", "latency"]
    indicators["scalable"] = any(kw in project_text for kw in scalability_keywords)
    
    # Check for advanced tech
    advanced_tech_keywords = ["ai", "ml", "machine learning", "dashboard", "analytics", 
                             "authentication", "real-time", "streaming", "recommendation"]
    indicators["advanced_tech"] = any(kw in project_text for kw in advanced_tech_keywords)
    
    # Check for cloud/DevOps
    cloud_devops_keywords = ["docker", "kubernetes", "cloud", "aws", "gcp", "azure", 
                            "ci/cd", "deployment", "containerized"]
    indicators["cloud_devops"] = any(kw in project_text for kw in cloud_devops_keywords)
    
    # Check for full-stack
    fullstack_keywords = ["full-stack", "end-to-end", "backend", "frontend", "mern", "mean"]
    indicators["full_stack"] = any(kw in project_text for kw in fullstack_keywords)
    
    # Calculate strength level based on indicators (0-7 range)
    strength_count = sum([
        indicators["deployed"],
        indicators["real_users"],
        indicators["scalable"],
        indicators["advanced_tech"],
        indicators["cloud_devops"],
        indicators["full_stack"]
    ])
    
    indicators["strength_level"] = min(strength_count, 7)
    
    return indicators


def _evaluate_fresher_projects(projects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate fresher's projects for experience credit.
    
    Fresher Project Rubric:
    - No/weak projects → 0-3 points
    - Basic academic projects → 4-5 points
    - Good deployed projects → 6-7 points
    - Strong production-level → 8-9 points
    - Exceptional real-world impact → 10 points
    
    Returns:
        Dict with fresher_strength_level, details, and score recommendation.
    """
    if not projects or len(projects) == 0:
        return {
            "fresher_strength_level": 0,
            "project_count": 0,
            "deployment_detected": False,
            "measurable_impact_detected": False,
            "top_project_strength": 0,
            "average_project_strength": 0,
            "score": 0,
            "reasoning": "No projects provided"
        }
    
    # Analyze each project
    project_analyses = []
    total_strength = 0
    deployed_count = 0
    impact_count = 0
    
    for project in projects:
        analysis = _detect_project_strength_indicators(project)
        project_analyses.append(analysis)
        total_strength += analysis["strength_level"]
        
        if analysis["deployed"]:
            deployed_count += 1
        if analysis["measurable_impact"]:
            impact_count += 1
    
    # Calculate metrics
    project_count = len(projects)
    average_strength = total_strength / project_count if project_count > 0 else 0
    top_strength = max([p["strength_level"] for p in project_analyses]) if project_analyses else 0
    
    # Determine fresher strength level and score
    deployment_detected = deployed_count > 0
    measurable_impact_detected = impact_count > 0
    
    # Score mapping for freshers:
    # 0-1 average strength + no deployment → 0-3 (weak/no projects)
    # 1-2 average strength → 4-5 (basic academic)
    # 2-3 average strength + deployment → 6-7 (good deployed)
    # 4-5 average strength + deployment → 8-9 (strong production)
    # 5+ average strength + impact → 10 (exceptional)
    
    if average_strength < 1.0:
        score = 2 if project_count > 0 else 0
        reasoning = "Weak or minimal project experience"
    elif average_strength < 2.0:
        score = 5
        reasoning = "Basic academic/hobby projects without deployment"
    elif average_strength < 3.0 and deployment_detected:
        score = 7
        reasoning = "Good deployed projects with production-level features"
    elif average_strength >= 4.0 and deployment_detected:
        if measurable_impact_detected:
            score = 10
            reasoning = f"Exceptional real-world impact: {project_count} projects with {deployed_count} deployed and measurable metrics"
        else:
            score = 9
            reasoning = f"Strong production-level projects: {project_count} deployed projects with advanced features"
    elif deployment_detected:
        score = 8
        reasoning = f"Strong deployed projects: {project_count} projects with advanced technology stack"
    else:
        score = 5
        reasoning = "Projects present but lack deployment/production indicators"
    
    return {
        "fresher_strength_level": min(top_strength, 10),  # Cap at 10 for rubric compatibility
        "project_count": project_count,
        "deployment_detected": deployment_detected,
        "measurable_impact_detected": measurable_impact_detected,
        "deployed_count": deployed_count,
        "impact_count": impact_count,
        "top_project_strength": top_strength,
        "average_project_strength": round(average_strength, 2),
        "score": score,
        "reasoning": reasoning,
        "project_analyses": project_analyses
    }


def calculate_experience_score(
    candidate_experience: List[Dict[str, Any]],
    strengths: List[str],
    projects: Optional[List[Dict[str, Any]]] = None,
    project_relevance: Optional[str] = None
) -> Dict[str, Any]:
    """
    Score experience relevance using intelligent fresher-aware evaluation.
    
    IMPROVED LOGIC (v3.0 - Fresher-Friendly):
    
    For professionals (>= 1 year experience):
    - unrelated domain → 0-3 points
    - adjacent domain OR relevant projects → 5 points
    - exact domain with seniority → 8-10 points
    
    For freshers (< 1 year experience):
    - Evaluate projects for production-level indicators
    - Weak/no projects → 0-3 points
    - Basic academic projects → 4-5 points
    - Good deployed projects → 6-7 points
    - Strong production-level → 8-9 points
    - Exceptional real-world impact → 10 points
    
    Real-world indicators for freshers:
    - Deployed/live/production status
    - Real users or measurable impact
    - Advanced tech (AI, ML, real-time, cloud)
    - Full-stack or DevOps (Docker, Kubernetes)
    - Leadership or team management
    - Revenue generation or scaling metrics
    
    Factors analyzed:
    1. Years of professional experience (determines fresher status)
    2. Job title & domain relevance (for professionals)
    3. Project portfolio strength (for freshers + professionals)
    4. Deployment & real-world indicators (projects)
    5. Measurable impact (users, revenue, metrics)
    6. LLM strengths as supporting signal only
    
    Args:
        candidate_experience (List[Dict]): Candidate's professional experience data.
        strengths (List[str]): Strengths identified by LLM analysis (supporting only).
        projects (Optional[List[Dict]]): Candidate's projects/portfolio.
        project_relevance (Optional[str]): Project relevance assessment ("high", "medium", "low").
    
    Returns:
        Dict with score (0-10), justification, and fresher evaluation details.
    """
    # Extract experience details
    total_years = 0.0
    job_titles = []
    descriptions = []
    internships = 0
    
    if candidate_experience:
        for exp in candidate_experience:
            job_title = exp.get("job_title", "").lower() if exp.get("job_title") else ""
            job_titles.append(job_title)
            descriptions.append(exp.get("description", "").lower() if exp.get("description") else "")
            
            # Check for internship indicators
            if any(kw in job_title for kw in ["intern", "trainee", "apprentice"]):
                internships += 1
            
            # Try to extract years from duration (e.g., "2019-2023" = 4 years)
            duration = exp.get("duration", "")
            if duration and "-" in duration:
                try:
                    parts = duration.split("-")
                    if len(parts) == 2:
                        start = int(parts[0].strip()[:4])
                        end = int(parts[1].strip()[:4])
                        total_years += max(0, (end - start))
                except (ValueError, IndexError):
                    pass
    
    # Determine fresher status
    is_fresher = _detect_fresher_status(total_years)
    
    # ========================================================================
    # FRESHER EVALUATION LOGIC
    # ========================================================================
    if is_fresher:
        # For freshers, project portfolio is the primary evaluation criterion
        fresher_eval = _evaluate_fresher_projects(projects)
        
        return {
            "score": fresher_eval["score"],
            "justification": fresher_eval["reasoning"],
            "is_fresher": True,
            "experience_count": len(candidate_experience) if candidate_experience else 0,
            "total_years": total_years,
            "internships": internships,
            "project_count": fresher_eval["project_count"],
            "deployment_detected": fresher_eval["deployment_detected"],
            "measurable_impact_detected": fresher_eval["measurable_impact_detected"],
            "fresher_strength_level": fresher_eval["fresher_strength_level"],
            "top_project_strength": fresher_eval["top_project_strength"],
            "average_project_strength": fresher_eval["average_project_strength"],
            "compensated_by_projects": fresher_eval["score"] >= 5
        }
    
    # ========================================================================
    # PROFESSIONAL EVALUATION LOGIC
    # ========================================================================
    # Analyze job titles and descriptions for relevance
    backend_keywords = ["backend", "python", "server", "api", "engineer", "developer", "devops"]
    frontend_keywords = ["frontend", "react", "javascript", "ui", "web", "vue", "angular"]
    fullstack_keywords = ["full-stack", "full stack", "mern", "mean"]
    domain_keywords = ["software", "engineer", "developer", "architect"]
    
    titles_text = " ".join(job_titles)
    descriptions_text = " ".join(descriptions)
    combined_text = titles_text + " " + descriptions_text
    
    # Determine domain match strength
    backend_match = any(kw in combined_text for kw in backend_keywords)
    frontend_match = any(kw in combined_text for kw in frontend_keywords)
    fullstack_match = any(kw in combined_text for kw in fullstack_keywords)
    has_seniority = total_years >= 2 or any(kw in titles_text for kw in ["senior", "lead", "architect", "manager"])
    has_leadership = any(kw in combined_text for kw in ["lead", "manager", "head", "architect", "mentor"])
    
    # Use Gemini strengths as supporting signal only
    strengths_text = " ".join(strengths).lower() if strengths else ""
    gemini_exact = any(kw in strengths_text for kw in ["exact", "direct", "highly relevant", "perfectly suited"])
    gemini_strong = any(kw in strengths_text for kw in ["strong", "good", "relevant"])
    
    # Evaluate projects as bonus for professionals
    has_strong_projects = False
    project_boost = 0
    if projects and len(projects) > 0:
        fresher_eval = _evaluate_fresher_projects(projects)
        # If professional has strong projects, add a small boost
        if fresher_eval["score"] >= 8:
            has_strong_projects = True
            project_boost = 1
    
    # Score logic (deterministic with Gemini support)
    if (backend_match or frontend_match or fullstack_match) and has_seniority and gemini_exact:
        score = 10
        reasoning = f"Exact domain match ({total_years:.1f}+ years) with seniority and leadership"
    elif (backend_match or frontend_match or fullstack_match) and has_seniority and gemini_strong:
        score = 9
        reasoning = f"Strong domain match ({total_years:.1f}+ years) with seniority"
    elif (backend_match or frontend_match or fullstack_match) and total_years >= 1 and gemini_strong:
        score = 8
        reasoning = f"Good domain match ({total_years:.1f} years) in relevant technology stack"
    elif (backend_match or frontend_match or fullstack_match) and total_years >= 1:
        score = 6 + project_boost
        reasoning = f"Related domain experience ({total_years:.1f} years) in relevant field"
    elif has_strong_projects and total_years >= 1:
        score = 7
        reasoning = f"Experience from adjacent domain ({total_years:.1f} years) with strong portfolio projects"
    elif total_years >= 1 and internships > 0:
        score = 5
        reasoning = f"Limited professional experience ({total_years:.1f} years) but includes internships"
    elif total_years >= 0.5:
        score = 4
        reasoning = f"Minimal professional experience ({total_years:.1f} years)"
    else:
        score = 0
        reasoning = "Experience from different domain or unclear relevance"
    
    return {
        "score": score,
        "justification": reasoning,
        "is_fresher": False,
        "experience_count": len(candidate_experience) if candidate_experience else 0,
        "total_years": total_years,
        "internships": internships,
        "backend_match": backend_match,
        "frontend_match": frontend_match,
        "fullstack_match": fullstack_match,
        "has_seniority": has_seniority,
        "has_leadership": has_leadership,
        "project_count": len(projects) if projects else 0,
        "has_strong_projects": has_strong_projects,
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
        skills_result = calculate_skill_score(
            jd_skills,
            matching_skills,
            resume_skills,
            analysis_data  # NEW: Pass analysis_data with optional semantic_relevance_score
        )
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
