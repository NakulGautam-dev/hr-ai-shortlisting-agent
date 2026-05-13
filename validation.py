"""
Resume Validation Module for AI HR Resume Shortlisting System.

This module provides intelligent resume validation to detect whether an uploaded
document is actually a resume before semantic analysis and scoring.

Features:
- Validates resume structure and content
- Checks for required resume fields
- Prevents non-resume documents from being scored
- Returns clear validation results with reasons
- Integrates cleanly into the processing pipeline

Author: HR AI System
Date: 2026
"""

from typing import Dict, List, Any, Optional


# ==============================================================================
# VALIDATION LOGIC
# ==============================================================================

def is_valid_field(field_value: Any) -> bool:
    """
    Check if a field value is valid (non-empty, meaningful).
    
    Args:
        field_value: The value to check
    
    Returns:
        bool: True if field is meaningful, False otherwise
    """
    # Handle None
    if field_value is None:
        return False
    
    # Handle strings
    if isinstance(field_value, str):
        value = field_value.strip()
        # Check for empty or placeholder values
        if not value or value.lower() in ["", "unknown", "n/a", "none", "not specified", "n/a - not available"]:
            return False
        return True
    
    # Handle lists
    if isinstance(field_value, list):
        # List is valid only if it has meaningful elements
        if len(field_value) == 0:
            return False
        # Check if list contains only empty/placeholder values
        meaningful_items = [
            item for item in field_value
            if item and (not isinstance(item, str) or item.strip().lower() not in ["", "unknown", "n/a"])
        ]
        return len(meaningful_items) > 0
    
    # Handle dicts
    if isinstance(field_value, dict):
        return len(field_value) > 0
    
    return False


def validate_resume_data(resume_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate whether extracted resume data represents a real resume.
    
    Checks for presence of key resume fields. A resume is considered VALID
    if at least 2 important fields exist with meaningful content.
    
    Required fields check:
    - candidate_name: Non-empty, non-placeholder string
    - skills: Non-empty list
    - education: Non-empty list
    - experience: Non-empty list
    - projects: Non-empty list
    - certifications: Non-empty list
    
    Args:
        resume_data (Dict[str, Any]): Extracted resume data structure
    
    Returns:
        Dict with validation result:
        {
            "is_valid_resume": bool,
            "valid_fields": int,  # Number of valid fields found
            "valid_fields_list": list,  # Names of valid fields
            "reason": str,  # Human-readable reason
            "field_details": dict  # Details for each field
        }
    """
    # List of important resume fields to validate
    required_fields = [
        "candidate_name",
        "skills",
        "education",
        "experience",
        "projects",
        "certifications"
    ]
    
    # Track validation results
    valid_fields = 0
    valid_fields_list = []
    field_details = {}
    
    # Check each field
    for field_name in required_fields:
        field_value = resume_data.get(field_name)
        
        # Special handling for candidate_name
        if field_name == "candidate_name":
            is_valid = is_valid_field(field_value)
            field_details[field_name] = {
                "value": field_value,
                "is_valid": is_valid,
                "reason": "Valid candidate name" if is_valid else "Missing or invalid candidate name"
            }
            if is_valid:
                valid_fields += 1
                valid_fields_list.append(field_name)
        
        # For list fields (skills, education, experience, projects, certifications)
        else:
            is_valid = is_valid_field(field_value)
            
            # Get count for logging
            count = len(field_value) if isinstance(field_value, list) else 0
            
            field_details[field_name] = {
                "value": field_value if not isinstance(field_value, list) else f"[{count} items]",
                "is_valid": is_valid,
                "count": count,
                "reason": f"Found {count} entries" if is_valid else "Empty or missing"
            }
            
            if is_valid:
                valid_fields += 1
                valid_fields_list.append(field_name)
    
    # Validation decision: need at least 2 valid fields
    is_valid_resume = valid_fields >= 2
    
    # Generate reason
    if is_valid_resume:
        reason = f"Resume structure detected ({valid_fields} valid fields found)"
    else:
        reason = f"Document does not appear to be a valid resume ({valid_fields} valid field(s) found, minimum 2 required)"
    
    return {
        "is_valid_resume": is_valid_resume,
        "valid_fields": valid_fields,
        "valid_fields_list": valid_fields_list,
        "reason": reason,
        "field_details": field_details
    }


def create_invalid_resume_result(
    resume_data: Dict[str, Any],
    validation_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a result object for an invalid resume.
    
    This function generates a properly formatted result for resumes that fail
    validation, ensuring the pipeline doesn't crash and the invalid document
    is properly recorded.
    
    Args:
        resume_data (Dict[str, Any]): Original extracted resume data
        validation_result (Dict[str, Any]): Result from validate_resume_data()
    
    Returns:
        Dict with invalid resume result object
    """
    candidate_name = resume_data.get("candidate_name", "Unknown")
    
    # Sanitize candidate name if still invalid
    if not is_valid_field(candidate_name):
        candidate_name = "Unknown"
    
    return {
        "candidate_name": candidate_name,
        "status": "INVALID_RESUME",
        "is_valid_resume": False,
        "final_score": 0,
        "rank": None,
        "validation_reason": validation_result.get("reason", "Document validation failed"),
        "valid_fields_count": validation_result.get("valid_fields", 0),
        "field_details": validation_result.get("field_details", {}),
        "breakdown": {},
        "recommendation": "Not Evaluated - Invalid Resume",
        "ai_analysis": "",
        "ai_justification": "",
        "ai_score": 0,
        "semantic_analysis": {}
    }


def print_validation_result(validation_result: Dict[str, Any], resume_filename: str = "") -> None:
    """
    Print validation result to console in a professional format.
    
    Args:
        validation_result (Dict[str, Any]): Result from validate_resume_data()
        resume_filename (str): Name of the resume file being validated
    """
    is_valid = validation_result.get("is_valid_resume", False)
    reason = validation_result.get("reason", "")
    valid_fields = validation_result.get("valid_fields", 0)
    valid_fields_list = validation_result.get("valid_fields_list", [])
    
    if is_valid:
        print(f"✓ Resume validation PASSED")
        print(f"  Valid fields: {valid_fields} - {', '.join(valid_fields_list)}")
    else:
        print(f"⚠ Invalid resume detected")
        print(f"  Reason: {reason}")
        print(f"  Valid fields: {valid_fields}/6")
        if valid_fields_list:
            print(f"  Found: {', '.join(valid_fields_list)}")
        print(f"  Action: Skipping semantic analysis and scoring...")


# ==============================================================================
# INTEGRATION HELPERS
# ==============================================================================

def should_process_candidate(validation_result: Dict[str, Any]) -> bool:
    """
    Determine whether to continue processing this candidate.
    
    Args:
        validation_result (Dict[str, Any]): Result from validate_resume_data()
    
    Returns:
        bool: True if candidate should be processed, False otherwise
    """
    return validation_result.get("is_valid_resume", False)


if __name__ == "__main__":
    # Test the validation module
    
    # Test case 1: Valid resume
    valid_resume = {
        "candidate_name": "John Doe",
        "skills": ["Python", "JavaScript", "React"],
        "education": [{"degree": "B.Tech", "institution": "MIT"}],
        "experience": [{"title": "Software Engineer", "company": "Google"}],
        "projects": [{"name": "Project A"}],
        "certifications": ["AWS Certified"]
    }
    
    result1 = validate_resume_data(valid_resume)
    print("Test 1 - Valid Resume:")
    print_validation_result(result1)
    print()
    
    # Test case 2: Invalid resume (too few fields)
    invalid_resume = {
        "candidate_name": "Jane Smith",
        "skills": [],
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": []
    }
    
    result2 = validate_resume_data(invalid_resume)
    print("Test 2 - Invalid Resume (empty fields):")
    print_validation_result(result2)
    print()
    
    # Test case 3: Non-resume document
    non_resume = {
        "candidate_name": "Unknown",
        "skills": [],
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": []
    }
    
    result3 = validate_resume_data(non_resume)
    print("Test 3 - Non-Resume Document:")
    print_validation_result(result3)
    invalid_result = create_invalid_resume_result(non_resume, result3)
    print(f"Invalid result status: {invalid_result.get('status')}")
    print()
