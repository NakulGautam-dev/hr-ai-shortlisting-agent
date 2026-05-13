# 🤖 AI HR Resume Shortlisting System

> **Intelligent AI-powered resume screening with deterministic, explainable scoring**

An enterprise-grade resume shortlisting system that combines the semantic understanding power of Google Gemini with Python-based deterministic scoring to create a fair, reliable, and transparent hiring pipeline.

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-system-architecture)
- [Scoring Methodology](#-scoring-methodology)

### 🎬 Project Showcase
- [🎥 Demo Video & Screenshots](#-demo-video)

- [Installation](#-installation)
- [Environment Setup](#-environment-setup)
- [Running the Project](#-running-the-project)
- [Example Workflow](#-example-workflow)
- [Output Formats](#-output-formats)
- [Human Review System](#-human-review-system)
- [Analytics & Reporting](#-report-generation)
- [Future Improvements](#-future-improvements)
- [Why This Project Stands Out](#-why-this-project-stands-out)
- [Support](#-support)
- [Contributing](#-contributing)
- [Author](#-author)

---

## ✨ Overview

This system **automates intelligent candidate screening** by:

- 📄 **Parsing** Job Descriptions (JD) and Candidate Resumes
- 🧠 **Analyzing** semantic fit using Gemini AI + SentenceTransformers embeddings
- 🎯 **Scoring** candidates across 5 dimensions using deterministic Python rubrics
- 📊 **Ranking** and visualizing candidate performance
- ✅ **Supporting** human review and override capabilities
- 📋 **Generating** professional PDF/HTML/JSON reports

**Key Differentiator:** Unlike many AI screening systems, this project does **NOT** directly trust LLM outputs for numeric scoring. All final scores are calculated deterministically in Python using validated rubrics, making the system more **reliable**, **explainable**, and **fair**.

---

## ⚡ Quick Start (30 seconds)

```bash
# 1. Clone & Setup
git clone https://github.com/NakulGautam-dev/hr-ai-shortlisting-agent.git
cd hr-ai-shortlisting-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Add API Key
echo "GEMINI_API_KEY=your_api_key_here" > .env

# 3. Run Dashboard
cd frontend && streamlit run streamlit_app.py

# 4. Open Browser
# Dashboard opens automatically at http://localhost:8501
```

**First Time?** → Read the [Installation Guide](#-installation) for detailed setup

---

## ⭐ Key Features

| Feature                          | Description                                                         | Status |
| -------------------------------- | ------------------------------------------------------------------- | ------ |
| 📄 **JD & Resume Parsing**       | Extract text from PDF/DOCX files                                    | ✅     |
| 🧪 **Batch Processing**          | Process multiple resumes simultaneously                             | ✅     |
| 🔍 **Resume Validation**         | Detect non-resume documents (brochures, invoices, etc.)             | ✅     |
| 🎯 **Semantic Skill Matching**   | Match skills using embeddings + LLM reasoning                       | ✅     |
| 📊 **Multi-Dimensional Scoring** | Score across Skills, Experience, Education, Projects, Communication | ✅     |
| 🎓 **Fresher-Friendly Scoring**  | Special evaluation for freshers with strong project portfolios      | ✅     |
| 🏆 **Ranking System**            | Intelligent candidate ranking with detailed breakdowns              | ✅     |
| 👥 **Candidate Comparison**      | Side-by-side candidate analysis                                     | ✅     |
| ✏️ **Human Review System**       | HR override capabilities with audit trail                           | ✅     |
| 📈 **Real-Time Dashboard**       | Interactive Streamlit dashboard with live updates                   | ✅     |
| 📊 **Analytics & Charts**        | Visual performance metrics and insights                             | ✅     |
| 📄 **Report Generation**         | PDF, HTML, JSON exports for each candidate                          | ✅     |
| 📋 **Batch Reports**             | Collective ranking and summary reports                              | ✅     |
| 🔐 **Audit Trail**               | Track all AI decisions and human overrides                          | ✅     |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     INPUT LAYER                                  │
├─────────────────────────────────────────────────────────────────┤
│  Job Description (PDF) ──→ Resume Collection (PDFs/DOCSs)      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   EXTRACTION & PARSING                           │
├─────────────────────────────────────────────────────────────────┤
│  [PDFParser] ──→ [Text Extraction] ──→ [Structure Validation]  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│               LLM-ASSISTED SEMANTIC ANALYSIS                     │
├─────────────────────────────────────────────────────────────────┤
│  [Gemini: Extract JD] ──→ [Gemini: Extract Resume]             │
│             ↓                        ↓                           │
│         JD Data                Resume Data                        │
│             ↓                        ↓                           │
│        [Gemini: Analyze Fit & Strengths]                        │
│             ↓                                                    │
│       Semantic Insights (NOT numeric scores)                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│         DETERMINISTIC PYTHON-BASED SCORING ENGINE                │
├─────────────────────────────────────────────────────────────────┤
│  [Embedding Similarity] ──→ [Semantic Matching] ↘               │
│  [Keyword Matching] ──────────────────────────→ [Skill Score]   │
│  [Experience Analysis] ────────────────────→ [Experience Score] │
│  [Education Validation] ───────────────────→ [Education Score]  │
│  [Projects Evaluation] ────────────────────→ [Project Score]    │
│  [Communication Quality] ──────────────────→ [Communication]    │
│                                             ↓                    │
│                                    [Final Score: 0-100]          │
│                        (Explainable & Reproducible)             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    HUMAN REVIEW LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  [Dashboard] ──→ [HR Review] ──→ [Override if needed]           │
│                                        ↓                         │
│                                [Audit Trail Recorded]            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   OUTPUT & VISUALIZATION                         │
├─────────────────────────────────────────────────────────────────┤
│  [Rankings] ──→ [Candidate Reports] ──→ [Analytics Dashboard]  │
│      ↓              ↓                         ↓                  │
│    JSON          PDF/HTML              Streamlit UI             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧮 Scoring Methodology

### Architecture: Why This Approach?

Unlike many AI screening systems that directly trust LLM-generated scores, this project uses **hybrid scoring**:

```
AI Reasoning (Gemini)          +    Deterministic Rubric (Python)
- Semantic understanding              - Keyword matching
- Pattern recognition                 - Embedding similarity
- Context analysis                    - Experience calculation
- Strength/weakness analysis          - Education validation
         ↓                                    ↓
      INSIGHTS                          NUMERIC SCORES
         ↓ (Support Signal Only)           ↓ (Final Decision)
  ─────────────────────────────────────────────────
              Final Score = Python Calculation
                  (Explainable & Reproducible)
```

### Scoring Dimensions

#### 1️⃣ **Skills Score (0-10)**

- **Keyword Matching (15%):** Exact skill matches
- **Semantic Similarity (65%):** Using SentenceTransformers embeddings
  - Cosine similarity between JD and resume skills
  - Handles synonyms: "React" ↔ "React.js", "REST API" ↔ "API development"
- **Gemini Support (20%):** LLM reasoning about skill relevance (not direct scoring)

**Rubric:**

```
< 40% match → 2 points
40-60% match → 5 points
60-80% match → 8 points
≥ 80% match → 10 points
```

#### 2️⃣ **Experience Score (0-10)**

- **Professional Experience:** Years in relevant role
- **Fresher Special Handling:**
  - Strong project portfolios valued equally
  - Deployed projects, user impact, revenue generation recognized
  - Leadership roles weighted appropriately
- **Seniority Bonus:** Higher scores for senior/lead experience

**Rubric:**

```
Entry-level / Weak → 2-3 points
Mid-level / Average → 5 points
Senior / Strong → 8 points
Expert / Leadership → 10 points
```

#### 3️⃣ **Education Score (0-10)**

- Degree relevance to JD
- Specialized certifications
- Continuing education tracking

**Rubric:**

```
Non-relevant → 2 points
Partially relevant → 5 points
Relevant → 8 points
Highly relevant + certs → 10 points
```

#### 4️⃣ **Projects Score (0-10)**

- Number of relevant projects
- Project complexity & scope
- Deployment status & user impact
- Technologies demonstrated

**Rubric:**

```
No projects → 2 points
1-2 basic projects → 5 points
3+ deployed projects → 8 points
Production systems with users → 10 points
```

#### 5️⃣ **Communication Score (0-10)**

- Resume clarity & professionalism
- Grammar & formatting
- Information organization

**Rubric:**

```
Poor → 2 points
Average → 5 points
Good → 8 points
Excellent → 10 points
```

### Final Score Calculation

```python
final_score = (
    skills_score * 0.30 +           # 30% - Most important
    experience_score * 0.25 +       # 25%
    projects_score * 0.20 +         # 20%
    education_score * 0.15 +        # 15%
    communication_score * 0.10      # 10%
)
# Result: 0-100 scale

# Recommendation Tiers:
# 85-100 → 🟢 Strong Hire
# 70-84  → 🔵 Hire
# 55-69  → 🟡 Consider
# 0-54   → 🔴 Reject
```

### Why This Is Better

| Aspect              | Traditional LLM   | This System         |
| ------------------- | ----------------- | ------------------- |
| **Transparency**    | Black box         | Explainable rubric  |
| **Consistency**     | Varies by prompt  | Deterministic       |
| **Reproducibility** | Non-deterministic | 100% reproducible   |
| **Bias Control**    | Harder to audit   | Easy to audit & fix |
| **Fairness**        | Dependent on LLM  | Controlled weights  |
| **HR Trust**        | Lower confidence  | Higher confidence   |

---

## 📊 Tech Stack

<div align="center">

### 🔧 Technology Breakdown

</div>

### Backend & Core AI/ML

| Component             | Technology           | Version          | Purpose                         |
| --------------------- | -------------------- | ---------------- | ------------------------------- |
| **Language**          | Python               | 3.8+             | Core pipeline & scoring         |
| **LLM API**           | Google Gemini        | Latest           | Semantic reasoning & analysis   |
| **Embeddings**        | SentenceTransformers | all-MiniLM-L6-v2 | Semantic similarity (0-1 scale) |
| **Vector Operations** | scikit-learn + NumPy | Latest           | Cosine similarity calculations  |
| **Data Processing**   | Pandas               | Latest           | Structured data manipulation    |

### Document Processing

| Component          | Technology     | Purpose                        |
| ------------------ | -------------- | ------------------------------ |
| **PDF Extraction** | PyMuPDF (fitz) | PDF text & metadata extraction |
| **DOCX Support**   | python-docx    | Word document parsing          |
| **PDF Generation** | ReportLab      | Create PDF reports             |
| **HTML Templates** | Jinja2         | Dynamic HTML report generation |

### Frontend & Visualization

| Component             | Technology              | Purpose                    |
| --------------------- | ----------------------- | -------------------------- |
| **Dashboard**         | Streamlit               | Interactive web dashboard  |
| **Charts**            | Plotly                  | Interactive visualizations |
| **UI Components**     | Custom Streamlit        | Responsive design          |
| **Real-Time Updates** | Streamlit Session State | Live data updates          |

### Data Storage & Export

| Component           | Technology | Format                 |
| ------------------- | ---------- | ---------------------- |
| **Results Storage** | JSON       | Structured results     |
| **Report Export**   | PDF, HTML  | Professional documents |
| **Data Exchange**   | JSON       | API-ready format       |

### Dependencies Summary

```
📦 Production Dependencies (13):
  ├─ google-generativeai  (Gemini API)
  ├─ sentence-transformers (Embeddings)
  ├─ streamlit            (Dashboard)
  ├─ plotly               (Charts)
  ├─ pymupdf              (PDF parsing)
  ├─ python-docx          (DOCX parsing)
  ├─ reportlab            (PDF generation)
  ├─ jinja2               (Templates)
  ├─ scikit-learn         (ML utilities)
  ├─ numpy                (Numerical computing)
  ├─ pandas               (Data processing)
  ├─ python-dotenv        (Env config)
  └─ requests             (HTTP client)

⚙️ Development Tools:
  ├─ pytest               (Testing)
  ├─ black                (Code formatting)
  ├─ pylint               (Linting)
  └─ pytest-cov           (Coverage)
```

---

## 🎯 AI/ML Pipeline

### Step 1: Text Extraction

```python
# Extract text from PDF/DOCX files
text = extract_text_from_pdf(resume_path)
```

### Step 2: Structured Data Extraction

```python
# Use Gemini to extract structured information
jd_data = extract_jd_structure(jd_text)      # Skills, requirements, experience
resume_data = extract_resume_structure(resume_text)  # Skills, experience, education
```

### Step 3: Semantic Analysis

```python
# Get Gemini analysis (insights only, NOT numeric scores)
analysis = gemini_analyze_fit(jd_data, resume_data)
# Returns: strengths, weaknesses, missing skills, relevance assessment
```

### Step 4: Deterministic Scoring

```python
# All scores calculated in Python using validated rubrics
scores = score_candidate(
    jd_data,           # Job requirements
    resume_data,       # Candidate info
    analysis           # LLM insights (supporting signal)
)
# Returns: skill_score, experience_score, education_score, etc.
# Final numeric score is deterministic & reproducible
```

### Step 5: Ranking & Output

```python
# Rank all candidates
rankings = rank_candidates(all_scores)
# Generate reports
generate_reports(rankings)  # PDF, HTML, JSON
```

---

## ✅ Human Review System

The system includes a **human-in-the-loop** architecture:

### HR Override Capabilities

```
AI Score: 72/100 (🔵 Hire)
    ↓
[HR Reviews Candidate]
    ↓
HR Override: 85/100 (🟢 Strong Hire)
    ↓
[Reason Recorded] → "Exceptional communication skills"
    ↓
[Dashboard Updates] → Shows both AI & HR scores
    ↓
[Final Ranking] → Uses HR decision
```

### Features

- ✅ Override AI decisions with reasons
- ✅ Reverse decisions for HR-preferred candidates
- ✅ Audit trail of all changes
- ✅ Separate AI vs HR recommendation display
- ✅ Track override patterns for feedback

### Benefits

- Improves recruiter trust in the system
- Captures domain expertise
- Provides feedback loop for model improvement
- Maintains transparency

---

## 📄 Report Generation

### Individual Candidate Reports

Each candidate receives:

- **PDF Report**
  - Cover page with overall score
  - Detailed breakdown by dimension
  - Skills analysis with match percentages
  - Strengths and weaknesses
  - Hiring recommendation
- **HTML Report**
  - Interactive format
  - Shareable link format
  - Embedded charts
- **JSON Export**
  - Machine-readable format
  - API integration ready
  - Complete metadata

### Batch Reports

For all candidates:

- **Rankings Report** - All candidates ranked
- **Analytics Report** - Aggregate statistics
- **Comparison Report** - Top candidates side-by-side

---

## 📊 Analytics & Visualizations

### Dashboard Features

**Metrics:**

- 📈 Total candidates processed
- 🏆 Top candidate profile
- 📊 Average score across batch
- 💼 Strong hire percentage

**Charts:**

- Score distribution histogram
- Component breakdown (Skills, Experience, etc.)
- Recommendation tier pie chart
- Skill gap analysis

**Filters:**

- Score range (0-100)
- Recommendation tier
- Skills required
- Experience level

---

## 👥 Candidate Comparison System

Recruiters can **compare candidates side-by-side**:

```
┌──────────────────┬──────────────────┬──────────────────┐
│   John Smith     │   Jane Doe       │   Bob Johnson    │
├──────────────────┼──────────────────┼──────────────────┤
│  Score: 92.5     │  Score: 88.3     │  Score: 76.1     │
│  🟢 Strong Hire  │  🟢 Strong Hire  │  🔵 Hire         │
├──────────────────┼──────────────────┼──────────────────┤
│ Skills: 9.5/10   │ Skills: 8.7/10   │ Skills: 7.2/10   │
│ Experience: 9/10 │ Experience: 9.2  │ Experience: 7.5  │
│ Education: 9/10  │ Education: 8.5   │ Education: 7.8   │
│ Projects: 9.3/10 │ Projects: 8.9/10 │ Projects: 7.1/10 │
│ Comm: 9.2/10     │ Comm: 8.7/10     │ Comm: 7.9/10     │
├──────────────────┼──────────────────┼──────────────────┤
│ Top Skills:      │ Top Skills:      │ Top Skills:      │
│ • React (0.95)   │ • Python (0.92)  │ • Java (0.88)    │
│ • Node.js (0.93) │ • Django (0.90)  │ • SQL (0.86)     │
│ • TypeScript      │ • FastAPI        │ • Spring Boot    │
└──────────────────┴──────────────────┴──────────────────┘
```

---

## 📁 Folder Structure

```
hr-ai-shortlisting-agent/
├── README.md                          # Project documentation
├── requirements.txt                   # Python dependencies
│
├── Backend Core
│ ├── app.py                          # Main orchestrator
│ ├── parser.py                       # PDF/DOCX extraction
│ ├── llm.py                          # Gemini API integration
│ ├── prompts.py                      # LLM prompt templates
│ ├── scoring.py                      # Deterministic scoring logic
│ ├── utils.py                        # Helper utilities
│ ├── validation.py                   # Resume validation
│ └── report.py                       # Report generation
│
├── Frontend Dashboard (Streamlit)
│ └── frontend/
│     ├── streamlit_app.py            # Main dashboard
│     ├── dashboard_transparency.py   # AI vs HR transparency
│     ├── candidate_view.py           # Candidate detail view
│     ├── charts.py                   # Visualization components
│     ├── hr_override.py              # HR review system
│     ├── upload_section.py           # File upload UI
│     ├── report_generator.py         # Report export
│     └── styles.css                  # Dashboard styling
│
├── Data & Outputs
│ ├── uploads/                        # User-uploaded files
│ │ ├── jd.pdf                        # Job description
│ │ └── resume_*.pdf                  # Candidate resumes
│ │
│ ├── outputs/                        # Generated results
│ │ ├── candidate_*.json              # Individual scores
│ │ ├── shortlisting_results_*.json   # Batch rankings
│ │ ├── hr_overrides/                 # HR decision history
│ │ └── reports/                      # PDF/HTML exports
│ │
│ └── reports/                        # Generated reports
│     ├── *.pdf                       # PDF reports
│     └── *.html                      # HTML reports
│
└── Configuration
  └── .env                            # Environment variables
```

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Google Gemini API key
- 2GB RAM minimum

### Step 1: Clone Repository

```bash
git clone https://github.com/NakulGautam-dev/hr-ai-shortlisting-agent.git
cd hr-ai-shortlisting-agent
```

### Step 2: Create Virtual Environment

**On macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Environment Setup

### Step 1: Get Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Create new API key
3. Copy the key

### Step 2: Create `.env` File

```bash
# In project root directory
cat > .env << EOF
GEMINI_API_KEY=your_api_key_here
EOF
```

Or manually create `.env`:

```
GEMINI_API_KEY=sk-xxxxxxxxxxxxx
```

### Step 3: Verify Setup

```bash
python -c "import google.generativeai; print('✅ Gemini configured')"
```

---

## ▶️ Running the Project

### Option 1: Run Backend Pipeline (CLI)

```bash
# Process resumes from uploads/ folder
python app.py

# Output:
# ✅ JD loaded: Software Engineer - 5+ years
# ✅ Candidate 1: John Smith (92.5/100) - Strong Hire
# ✅ Candidate 2: Jane Doe (88.3/100) - Strong Hire
# ✅ Results saved to outputs/
```

### Option 2: Run Interactive Dashboard (Recommended)

```bash
cd frontend
streamlit run streamlit_app.py

# Dashboard opens at: http://localhost:8501
```

### Option 3: Process Single Resume

```bash
python << 'EOF'
from app import HRShortlistingPipeline

pipeline = HRShortlistingPipeline()
pipeline.load_and_extract_jd()
result = pipeline.process_resume("uploads/resume_john.pdf")
print(f"Score: {result['final_score']}/100")
EOF
```

---

## 🎥 Demo Video

<div align="center">

## 🎥 Project Demo Video

[![Google Drive Demo](https://img.shields.io/badge/Google%20Drive-Watch%20Demo-success?style=for-the-badge&logo=googledrive)](https://drive.google.com/file/d/1Yzh75bPJjFwJivx0v1s6OhL9C4OVAPqF/view?usp=sharing)

_A complete walkthrough of the AI HR Resume Shortlisting System showcasing JD parsing, semantic matching, candidate scoring, comparison system, human review workflow, and report generation._

</div>

---

## 📸 Screenshots

<div align="center">

### 🖼️ Visual Tour of the Dashboard

</div>

#### 1️⃣ Main Dashboard

**Real-time metrics and candidate rankings**

<img width="1457" height="867" alt="dashboard" src="https://github.com/user-attachments/assets/be56de33-0c5b-474d-aeec-6df5cd73806c" />





#### 2️⃣ Candidate Detail View

**Comprehensive analysis of individual candidate**

<img width="1470" height="873" alt="candidate1" src="https://github.com/user-attachments/assets/cf1bc08c-2528-41d0-83aa-0f6d86661740" />



<img width="1462" height="860" alt="candidate2" src="https://github.com/user-attachments/assets/f09363d6-ea97-41d9-8da0-6ecb3a03feea" />





#### 3️⃣ Analytics & Charts

**Visual performance metrics**

<img width="1468" height="861" alt="charts1" src="https://github.com/user-attachments/assets/e32580d8-c476-4927-b35a-f1169405ace6" />



<img width="1470" height="858" alt="charts2" src="https://github.com/user-attachments/assets/4a62239a-76da-4355-8a06-d6a407798ede" />




#### 4️⃣ HR Review System

**Human-in-the-loop override interface**

<img width="1470" height="877" alt="hr1" src="https://github.com/user-attachments/assets/940ea1ae-ca84-4b1d-8549-798f522aeb4a" />



<img width="1464" height="866" alt="hr2" src="https://github.com/user-attachments/assets/5d7e77a2-f01d-4e83-a6ce-3e36664dfe71" />



<img width="1450" height="860" alt="hr3" src="https://github.com/user-attachments/assets/149e2589-ce96-4397-8054-9cd0e557d489" />





#### 5️⃣ Candidate Comparison

**Side-by-side analysis of top candidates**




<img width="1468" height="870" alt="comparison" src="https://github.com/user-attachments/assets/49d3b484-55bf-4e62-b5ba-6dea310f1100" />






---

## 📖 Example Workflow

### Scenario: Hiring for Senior Backend Engineer

**1. Upload Job Description**

```
Role: Senior Backend Engineer
Requirements: 5+ years, Python, Django, PostgreSQL, AWS
```

**2. Upload Resumes**

```
resume_john.pdf (5.2MB)
resume_jane.pdf (3.1MB)
resume_bob.pdf (4.7MB)
```

**3. System Processing**

```
[JD Parser] Extracted: Python (required), Django (required), AWS (required)
[Resume Parser]
  → John: 6 years Python, 5 years Django, 4 years AWS
  → Jane: 3 years Python, 5 years FastAPI, 3 years AWS
  → Bob: 4 years Java, 2 years Django, 1 year AWS

[Scoring]
  → John: Skills 9.2, Experience 9.5, Education 8.5 → Total: 92.5 🟢
  → Jane: Skills 8.1, Experience 7.5, Education 9.0 → Total: 83.2 🔵
  → Bob:  Skills 7.2, Experience 6.5, Education 7.8 → Total: 71.5 🔵
```

**4. HR Review**

```
HR Notes: "Jane has FastAPI experience which is close to Django.
         Adding 10 points for exceptional communication."
Final Score: 93.2 🟢 Strong Hire
```

**5. Export Reports**

```
Final Rankings: John (92.5), Jane (93.2), Bob (71.5)
Reports Generated: PDF, HTML, JSON
```

---

## 📤 Output Formats

### JSON Format

```json
{
  "candidate_name": "John Smith",
  "final_score": 92.5,
  "rank": 1,
  "status": "VALID_RESUME",
  "recommendation": "🟢 Strong Hire",
  "components": {
    "skills": { "score": 9.2, "details": {...} },
    "experience": { "score": 9.5, "details": {...} },
    "education": { "score": 8.5, "details": {...} },
    "projects": { "score": 9.3, "details": {...} },
    "communication": { "score": 9.2, "details": {...} }
  },
  "matched_skills": ["Python", "Django", "PostgreSQL"],
  "missing_skills": ["Kubernetes"],
  "ai_recommendation": "String Hire",
  "hr_override": null,
  "strengths": [...],
  "weaknesses": [...]
}
```

### PDF Report

- Cover page with score
- Detailed dimension breakdown
- Skills analysis with match percentages
- Professional formatting
- Print-ready

### HTML Report

- Interactive elements
- Responsive design
- Share-friendly format
- Embedded visualizations

---

## 🔮 Future Improvements

- [ ] **Multi-language Support** - Parse resumes in multiple languages
- [ ] **Video Interview Integration** - Analyze interview clips for communication
- [ ] **Skill Proficiency Levels** - Junior, Mid, Senior classifications
- [ ] **Diversity Metrics** - Track hiring diversity across demographics
- [ ] **Predictive Analytics** - Predict candidate success post-hire
- [ ] **Integration APIs** - Connect with ATS systems (Workable, Greenhouse)
- [ ] **Machine Learning** - Fine-tune scoring based on hire outcomes
- [ ] **Mobile App** - iOS/Android dashboard
- [ ] **Advanced Filtering** - Location, salary range, visa sponsorship
- [ ] **Anonymous Screening** - Remove demographic info for bias reduction

---

## 🏆 Why This Project Stands Out

### ✨ Architectural Excellence

- **Hybrid AI**: Combines semantic reasoning with deterministic scoring
- **Transparent**: Every score is explainable and auditable
- **Reproducible**: Same input = Same output (deterministic)
- **Fair**: Controlled weights prevent AI bias

### 🎯 Practical Features

- **Human-in-Loop**: HR can override with reasoning
- **Fresher-Friendly**: Special handling for entry-level candidates
- **Multi-Format Output**: JSON, PDF, HTML exports
- **Resume Validation**: Rejects non-resume documents
- **Batch Processing**: Handle hundreds of resumes efficiently

### 💼 Production-Ready

- **Error Handling**: Robust validation and fallbacks
- **Audit Trail**: Track all decisions
- **Performance**: Process 100+ resumes in minutes
- **Scalability**: Designed for enterprise use

### 📊 Analytics-Driven

- **Real-Time Dashboard**: Live candidate metrics
- **Visual Analytics**: Charts and graphs
- **Candidate Comparison**: Side-by-side analysis
- **Performance Insights**: Distribution and trends

### 🎓 Learning Outcomes

- **AI Integration**: Practical use of LLM APIs
- **NLP**: Semantic matching with embeddings
- **Python Best Practices**: Clean, modular code
- **Full-Stack**: Backend + Frontend implementation
- **HR Knowledge**: Understanding hiring workflows

---

## 📜 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Nakul Gautam**

- 🎓 NIT Kurukshetra
- 💼 AI/ML Developer
- 📧 [GitHub](https://github.com/NakulGautam-dev)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📞 Support

For issues, questions, or suggestions:

- 📧 **Email:** [gautamnakul07@gmail.com](mailto:gautamnakul07@gmail.com)
- � **GitHub Issues:** [Open an Issue](https://github.com/NakulGautam-dev/hr-ai-shortlisting-agent/issues)
- 💬 **Discussions:** [Start a Discussion](https://github.com/NakulGautam-dev/hr-ai-shortlisting-agent/discussions)

---

## 🙏 Acknowledgments

- Google Gemini API for semantic reasoning
- SentenceTransformers for embeddings
- Streamlit for the dashboard framework
- The open-source community

---

<div align="center">

**[⬆ Back to Top](#-ai-hr-resume-shortlisting-system)**

Made with ❤️ by Nakul Gautam

</div>

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



## Support

For issues or questions, please create an issue on the repository.

---

**Last Updated**: May 11, 2026
