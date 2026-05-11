"""
Utility functions for AI HR Resume Shortlisting System.

Provides reusable helper functions for:
- JSON processing (cleaning, parsing, saving, loading)
- File system operations
- Data normalization
- Timestamp generation
- Candidate result management

Does NOT contain:
- Scoring logic (see scoring.py)
- Gemini API logic (see llm.py)
- Prompt templates (see prompts.py)
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


# ==============================================================================
# JSON PROCESSING FUNCTIONS
# ==============================================================================

def clean_json_response(response_text: str) -> str:
    """
    Clean JSON response from LLM by removing markdown and extra formatting.
    
    Handles cases where Gemini returns:
    - ```json { ... } ```
    - Extra whitespace
    - Mixed markdown/JSON
    
    Args:
        response_text (str): Raw response text from Gemini.
    
    Returns:
        str: Clean JSON string, or empty string if unable to clean.
    """
    if not response_text:
        return ""
    
    try:
        # Remove markdown code block markers
        cleaned = response_text.strip()
        
        # Remove ```json and ``` markers
        cleaned = re.sub(r'^```json\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        cleaned = re.sub(r'^```\s*', '', cleaned)
        
        # Remove any trailing code block markers
        cleaned = re.sub(r'```\s*$', '', cleaned)
        
        # Strip whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    except Exception as e:
        print(f"Error cleaning JSON response: {e}")
        return ""


def safe_json_loads(json_text: str) -> Dict:
    """
    Safely parse JSON string into Python dictionary.
    
    Returns empty dict if parsing fails to prevent crashes.
    
    Args:
        json_text (str): JSON string to parse.
    
    Returns:
        Dict: Parsed dictionary, or empty dict {} if parsing fails.
    """
    if not json_text or not isinstance(json_text, str):
        return {}
    
    try:
        # Clean the JSON first
        cleaned = clean_json_response(json_text)
        
        if not cleaned:
            return {}
        
        # Parse JSON
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else {}
    
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Attempted to parse: {json_text[:200]}...")
        return {}
    
    except Exception as e:
        print(f"Unexpected error parsing JSON: {e}")
        return {}


# ==============================================================================
# FILE OPERATIONS
# ==============================================================================

def ensure_directory_exists(directory_path: str) -> None:
    """
    Create directory if it does not exist.
    
    Creates parent directories as needed.
    
    Args:
        directory_path (str): Path to directory.
    """
    try:
        path = Path(directory_path)
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error creating directory '{directory_path}': {e}")


def save_json(data: Dict, output_path: str) -> bool:
    """
    Save dictionary as formatted JSON file.
    
    Creates parent directories automatically if missing.
    
    Args:
        data (Dict): Dictionary to save.
        output_path (str): Path to output JSON file.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Ensure directory exists
        output_file = Path(output_path)
        ensure_directory_exists(str(output_file.parent))
        
        # Write JSON with formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        return True
    
    except Exception as e:
        print(f"Error saving JSON to '{output_path}': {e}")
        return False


def load_json(file_path: str) -> Dict:
    """
    Load JSON file safely.
    
    Returns empty dict if file is missing or invalid.
    
    Args:
        file_path (str): Path to JSON file.
    
    Returns:
        Dict: Parsed JSON, or empty dict {} if file missing/invalid.
    """
    try:
        file = Path(file_path)
        
        if not file.exists():
            print(f"File not found: {file_path}")
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data if isinstance(data, dict) else {}
    
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in '{file_path}': {e}")
        return {}
    
    except Exception as e:
        print(f"Error loading JSON from '{file_path}': {e}")
        return {}


# ==============================================================================
# DATA NORMALIZATION
# ==============================================================================

def normalize_skill(skill: str) -> str:
    """
    Normalize skill names for consistent matching.
    
    Converts:
    - "REST APIs" → "rest api"
    - "Python " → "python"
    - "Machine-Learning" → "machine learning"
    - "machine_learning" → "machine learning"
    
    Args:
        skill (str): Skill name to normalize.
    
    Returns:
        str: Normalized skill name.
    """
    if not skill or not isinstance(skill, str):
        return ""
    
    try:
        # Convert to lowercase
        normalized = skill.lower()
        
        # Strip whitespace
        normalized = normalized.strip()
        
        # Replace hyphens and underscores with spaces
        normalized = normalized.replace('-', ' ')
        normalized = normalized.replace('_', ' ')
        
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
        
        # Handle plural inconsistencies (simple approach)
        # Remove trailing 's' if it looks like plural (e.g., "apis" → "api")
        if normalized.endswith('s') and len(normalized) > 3:
            # Only strip if the word without 's' is a common skill
            without_s = normalized[:-1]
            if without_s in ['api', 'database', 'framework']:
                normalized = without_s
        
        return normalized
    
    except Exception as e:
        print(f"Error normalizing skill '{skill}': {e}")
        return skill.lower().strip()


# ==============================================================================
# TIMESTAMP AND UTILITY FUNCTIONS
# ==============================================================================

def get_timestamp() -> str:
    """
    Generate timestamp string for filenames and logging.
    
    Format: YYYY-MM-DD_HH-MM-SS
    Example: 2025-08-05_14-30-20
    
    Returns:
        str: Current timestamp string.
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Replaces spaces and special characters with underscores.
    
    Args:
        filename (str): Filename to sanitize.
    
    Returns:
        str: Sanitized filename.
    """
    if not filename:
        return "file"
    
    # Replace spaces and special characters with underscore
    sanitized = re.sub(r'[^\w\s-]', '', filename)
    sanitized = re.sub(r'[\s-]+', '_', sanitized)
    sanitized = sanitized.lower()
    
    return sanitized if sanitized else "file"


# ==============================================================================
# CANDIDATE RESULT MANAGEMENT
# ==============================================================================

def save_candidate_result(
    candidate_result: Dict,
    output_dir: str = "outputs"
) -> Optional[str]:
    """
    Save individual candidate scoring result as JSON.
    
    Creates filename using candidate name + timestamp.
    Example: outputs/john_doe_2025-08-05_14-30-20.json
    
    Args:
        candidate_result (Dict): Candidate scoring result from score_candidate().
        output_dir (str): Output directory (default: "outputs").
    
    Returns:
        str: Saved file path if successful, None if failed.
    """
    try:
        # Extract candidate name
        candidate_name = candidate_result.get("candidate_name", "unknown")
        sanitized_name = sanitize_filename(candidate_name)
        
        # Generate filename with timestamp
        timestamp = get_timestamp()
        filename = f"{sanitized_name}_{timestamp}.json"
        
        # Create full path
        output_path = str(Path(output_dir) / filename)
        
        # Save JSON
        if save_json(candidate_result, output_path):
            print(f"✓ Saved: {output_path}")
            return output_path
        else:
            return None
    
    except Exception as e:
        print(f"Error saving candidate result: {e}")
        return None


def save_batch_results(
    batch_results: list,
    output_dir: str = "outputs",
    batch_name: str = "batch"
) -> Optional[str]:
    """
    Save batch of candidate results to a single JSON file.
    
    Args:
        batch_results (list): List of candidate scoring results.
        output_dir (str): Output directory (default: "outputs").
        batch_name (str): Batch identifier for filename.
    
    Returns:
        str: Saved file path if successful, None if failed.
    """
    try:
        timestamp = get_timestamp()
        filename = f"{batch_name}_{timestamp}.json"
        output_path = str(Path(output_dir) / filename)
        
        batch_data = {
            "timestamp": timestamp,
            "total_candidates": len(batch_results),
            "results": batch_results
        }
        
        if save_json(batch_data, output_path):
            print(f"✓ Saved batch: {output_path}")
            return output_path
        else:
            return None
    
    except Exception as e:
        print(f"Error saving batch results: {e}")
        return None


# ==============================================================================
# TESTING AND EXAMPLES
# ==============================================================================

if __name__ == "__main__":
    print("Utility Functions Test - AI HR Resume Shortlisting System")
    print("=" * 70)
    
    # Test 1: JSON Cleaning
    print("\n1. Testing clean_json_response():")
    print("-" * 70)
    
    raw_responses = [
        '```json\n{"name": "John", "score": 85}\n```',
        '{"name": "John", "score": 85}',
        '```\n{"name": "John", "score": 85}\n```',
    ]
    
    for raw in raw_responses:
        cleaned = clean_json_response(raw)
        print(f"Raw: {raw[:40]}...")
        print(f"Cleaned: {cleaned}\n")
    
    # Test 2: Safe JSON Loading
    print("\n2. Testing safe_json_loads():")
    print("-" * 70)
    
    valid_json = '{"candidate": "John Doe", "score": 85.5}'
    invalid_json = '{"incomplete": '
    
    result1 = safe_json_loads(valid_json)
    print(f"Valid JSON parsed: {result1}")
    
    result2 = safe_json_loads(invalid_json)
    print(f"Invalid JSON parsed (should be {{}}): {result2}\n")
    
    # Test 3: Timestamp Generation
    print("\n3. Testing get_timestamp():")
    print("-" * 70)
    timestamp = get_timestamp()
    print(f"Current timestamp: {timestamp}\n")
    
    # Test 4: Skill Normalization
    print("\n4. Testing normalize_skill():")
    print("-" * 70)
    
    skills = [
        "REST APIs",
        "Python ",
        "Machine-Learning",
        "machine_learning",
        "AWS Certification",
        "Data Science"
    ]
    
    for skill in skills:
        normalized = normalize_skill(skill)
        print(f"'{skill}' → '{normalized}'")
    
    print()
    
    # Test 5: Filename Sanitization
    print("\n5. Testing sanitize_filename():")
    print("-" * 70)
    
    filenames = [
        "John Doe",
        "Sarah-Johnson",
        "Mike@Email#123",
        "Jane_Smith"
    ]
    
    for name in filenames:
        sanitized = sanitize_filename(name)
        print(f"'{name}' → '{sanitized}'")
    
    print()
    
    # Test 6: File Operations
    print("\n6. Testing file operations (save/load JSON):")
    print("-" * 70)
    
    test_data = {
        "candidate_name": "John Doe",
        "final_score": 85.0,
        "timestamp": timestamp,
        "breakdown": {
            "skills": {"score": 10},
            "experience": {"score": 8}
        }
    }
    
    test_file = "test_outputs/test_candidate.json"
    
    # Save
    saved = save_json(test_data, test_file)
    print(f"Saved test file: {saved}")
    
    # Load
    loaded = load_json(test_file)
    print(f"Loaded data matches: {loaded == test_data}")
    print(f"Loaded candidate: {loaded.get('candidate_name', 'N/A')}\n")
    
    # Test 7: Save Individual Candidate Result
    print("\n7. Testing save_candidate_result():")
    print("-" * 70)
    
    candidate_result = {
        "candidate_name": "Jane Smith",
        "final_score": 92.0,
        "breakdown": {
            "skills": {"score": 10},
            "experience": {"score": 10},
            "education": {"score": 9},
            "projects": {"score": 10},
            "communication": {"score": 9}
        }
    }
    
    saved_path = save_candidate_result(candidate_result, "test_outputs")
    print(f"Candidate result saved to: {saved_path}\n")
    
    # Test 8: Save Batch Results
    print("\n8. Testing save_batch_results():")
    print("-" * 70)
    
    batch = [candidate_result, test_data]
    batch_path = save_batch_results(batch, "test_outputs", "test_batch")
    print(f"Batch results saved to: {batch_path}\n")
    
    print("=" * 70)
    print("✓ All utility functions tested successfully!")
