# AI HR Resume Shortlisting System

An intelligent AI-powered resume screening and candidate ranking system using Google Gemini for semantic analysis and Python for scoring calculations.

## Overview

This system automates the HR hiring pipeline by:

1. **Extracting** structured data from Job Descriptions
2. **Parsing** candidate resumes
3. **Analyzing** semantic fit using Gemini AI
4. **Scoring** candidates using a weighted rubric
5. **Ranking** and outputting candidates

## Architecture

### Core Modules

| Module         | Purpose                                             |
| -------------- | --------------------------------------------------- |
| **app.py**     | Main orchestrator - coordinates the entire pipeline |
| **parser.py**  | PDF extraction using PyMuPDF                        |
| **prompts.py** | Secure prompt templates for Gemini                  |
| **llm.py**     | Gemini API integration                              |
| **utils.py**   | Reusable utilities (JSON, file I/O, normalization)  |
| **scoring.py** | Weighted rubric-based candidate scoring             |

### Data Flow

```
uploads/
├── jd.pdf ──→ [Extract Text] ──→ [Gemini: Extract JD] ──→ jd_data
└── resume*.pdf ──→ [Extract Text] ──→ [Gemini: Extract Resume] ──→ resume_data
                                    ↓
                           [Gemini: Analyze]
                                    ↓
                              analysis_data
                                    ↓
                           [Python: Score]
                                    ↓
                         candidate_result
                                    ↓
outputs/
├── candidate_*_timestamp.json
└── shortlisting_results_timestamp.json
```

## Installation

### Prerequisites

- Python 3.8+
- Google Gemini API key

### Setup

```bash
# Clone repository
git clone <repo-url>
cd hr-ai-shortlisting-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

## Usage

### 1. Prepare PDFs

Create `uploads/` directory with:

- `jd.pdf` - Job description (must contain "jd" in filename)
- `resume_john_doe.pdf` - Candidate resumes (any other PDF files)

```
uploads/
├── jd.pdf
├── resume_john_doe.pdf
├── resume_jane_smith.pdf
└── resume_alex_brown.pdf
```

### 2. Run the Pipeline

```bash
python app.py
```

### 3. View Results

Output files are saved in `outputs/`:

- Individual candidate results: `candidate_name_timestamp.json`
- Batch rankings: `shortlisting_results_timestamp.json`

## Rubric Scoring

Candidates are scored on 5 dimensions with weighted contributions:

| Dimension         | Weight | Scoring                               |
| ----------------- | ------ | ------------------------------------- |
| **Skills Match**  | 30%    | 0-10 (keyword + embedding similarity) |
| **Experience**    | 25%    | 0-10 (domain relevance)               |
| **Education**     | 15%    | 0-10 (meets minimum + certifications) |
| **Projects**      | 20%    | 0-10 (portfolio relevance)            |
| **Communication** | 10%    | 0-10 (resume clarity)                 |

**Final Score** = (sum of weighted dimensions) × 10

### Scoring Rules

#### Skills (30% weight)

- **0 pts**: < 30% skills match
- **5 pts**: 50-70% skills match
- **10 pts**: > 85% skills match

#### Experience (25% weight)

- **0 pts**: Unrelated domain
- **5 pts**: Adjacent domain
- **10 pts**: Exact domain match

#### Education (15% weight)

- **0 pts**: Below minimum requirement
- **5 pts**: Meets minimum
- **10 pts**: Exceeds + certifications

#### Projects (20% weight)

- **0 pts**: No portfolio evidence
- **5 pts**: Generic projects
- **10 pts**: Highly relevant projects

#### Communication (10% weight)

- **0 pts**: Poor communication
- **5 pts**: Average
- **8 pts**: Good
- **10 pts**: Excellent

## Module Details

### parser.py

Extracts text from PDF files using PyMuPDF.

```python
from parser import extract_text_from_pdf, get_pdfs_from_uploads

# Extract single PDF
text = extract_text_from_pdf("path/to/file.pdf")

# Get all PDFs from directory
pdfs = get_pdfs_from_uploads("uploads")
```

### prompts.py

Generates secure prompts that:

- Prevent prompt injection attacks
- Return strict JSON only
- Handle missing data with nulls
- Ignore malicious instructions

```python
from prompts import (
    get_jd_extraction_prompt,
    get_resume_extraction_prompt,
    get_analysis_prompt
)
```

### llm.py

Gemini API integration with safety features.

```python
from llm import ask_llm

response = ask_llm("Your prompt here")
```

### utils.py

Utility functions for JSON, file I/O, and normalization.

```python
from utils import (
    clean_json_response,
    safe_json_loads,
    save_json,
    load_json,
    normalize_skill,
    save_candidate_result,
    save_batch_results
)
```

### scoring.py

Implements the weighted rubric scoring system.

```python
from scoring import score_candidate, rank_candidates

# Score a candidate
result = score_candidate(jd_data, resume_data, analysis_data)

# Rank all candidates
ranked = rank_candidates(all_results)
```

## Output Format

### Individual Candidate Result

```json
{
  "candidate_name": "John Doe",
  "final_score": 87.5,
  "breakdown": {
    "skills": {
      "score": 10,
      "justification": "Matched 90% required skills"
    },
    "experience": {
      "score": 10,
      "justification": "Exact backend engineering domain match"
    },
    "education": {
      "score": 5,
      "justification": "Meets bachelor's requirement"
    },
    "projects": {
      "score": 10,
      "justification": "Strong relevant backend projects"
    },
    "communication": {
      "score": 8,
      "justification": "Good written communication"
    }
  }
}
```

### Batch Results

```json
{
  "timestamp": "2026-05-11_14-30-20",
  "total_candidates": 3,
  "results": [
    { "rank": 1, "candidate_name": "John Doe", "final_score": 87.5 },
    { "rank": 2, "candidate_name": "Jane Smith", "final_score": 82.0 },
    { "rank": 3, "candidate_name": "Alex Brown", "final_score": 74.5 }
  ]
}
```

## Configuration

### Environment Variables

Create `.env` file:

```bash
GEMINI_API_KEY=your_api_key_here
```

### Directories

- `uploads/` - Input PDF files (Job Description + Resumes)
- `outputs/` - Output JSON results
- `reports/` - Generated reports (optional)

## Key Features

✅ **Security**

- Prompt injection prevention
- Malicious instruction filtering
- Safe JSON parsing

✅ **Reliability**

- Error recovery for failed resumes
- Batch processing continuation
- Safe null handling

✅ **Semantic Analysis**

- Embedding-based skill similarity
- Context-aware matching
- Domain relevance detection

✅ **Production Ready**

- Type hints throughout
- Comprehensive error handling
- Modular, testable code
- Clear separation of concerns

## Error Handling

The system gracefully handles:

- Missing or corrupted PDFs
- Invalid Gemini responses
- Malformed JSON
- Missing JD file
- Empty uploads folder

Processing continues even if individual resumes fail.

## Testing

### Test Individual Modules

```bash
# Test LLM integration
python llm.py

# Test PDF parsing
python parser.py

# Test scoring engine
python scoring.py

# Test utilities
python utils.py

# Test prompts
python prompts.py
```

### Test Full Pipeline

```bash
python app.py
```

## Performance Considerations

- **Embedding Model**: `all-MiniLM-L6-v2` (lightweight, fast)
- **Cosine Similarity**: Optimized with scikit-learn
- **Batch Processing**: Sequential with error recovery

## Limitations

- Maximum PDF file size: Limited by Gemini API
- API rate limits apply
- Embedding quality depends on skill descriptions
- Scores are relative to job requirements

## Future Enhancements

- [ ] Batch API integration
- [ ] Custom rubric configuration
- [ ] Multi-language support
- [ ] Interview scheduling integration
- [ ] Candidate feedback generation
- [ ] Resume recommendation engine

## License

[Your License Here]

## Support

For issues or questions, please create an issue on the repository.

---

**Last Updated**: May 11, 2026
