"""
Main orchestrator for AI HR Resume Shortlisting System.

This file coordinates the complete hiring pipeline:
1. Load Job Description PDF
2. Load Resume PDFs
3. Extract text and structure
4. Perform semantic analysis
5. Calculate candidate scores
6. Rank and output results

Business logic is delegated to specialized modules:
- parser.py: PDF extraction
- prompts.py: Prompt generation
- llm.py: Gemini API integration
- utils.py: JSON handling and utilities
- scoring.py: Candidate scoring and ranking
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import json

# Import modules
from parser import extract_text_from_pdf, get_pdfs_from_uploads
from prompts import (
    get_jd_extraction_prompt,
    get_resume_extraction_prompt,
    get_analysis_prompt
)
from llm import ask_llm
from utils import (
    safe_json_loads,
    save_candidate_result,
    save_batch_results,
    get_timestamp
)
from scoring import score_candidate, rank_candidates


# ==============================================================================
# PIPELINE ORCHESTRATION
# ==============================================================================

class HRShortlistingPipeline:
    """Main orchestrator for the HR Resume Shortlisting System."""
    
    def __init__(self, uploads_dir: str = "uploads", outputs_dir: str = "outputs"):
        """
        Initialize the pipeline.
        
        Args:
            uploads_dir (str): Directory containing PDF files.
            outputs_dir (str): Directory for output results.
        """
        self.uploads_dir = uploads_dir
        self.outputs_dir = outputs_dir
        self.jd_data = {}
        self.candidate_results = []
        self.timestamp = get_timestamp()
        
        # Statistics
        self.stats = {
            "resumes_processed": 0,
            "resumes_successful": 0,
            "resumes_failed": 0,
            "jd_found": False
        }
    
    def print_header(self) -> None:
        """Print application header."""
        print("\n" + "=" * 70)
        print("AI HR Resume Shortlisting System")
        print("=" * 70)
        print(f"Timestamp: {self.timestamp}\n")
    
    def print_separator(self) -> None:
        """Print separator line."""
        print("-" * 70)
    
    # ==========================================================================
    # STEP 1-2: LOAD AND EXTRACT JD
    # ==========================================================================
    
    def load_and_extract_jd(self) -> bool:
        """
        Load Job Description PDF and extract structured data.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        print("STEP 1: Loading Job Description")
        self.print_separator()
        
        # Get all PDFs from uploads
        all_pdfs = get_pdfs_from_uploads(self.uploads_dir)
        
        if not all_pdfs:
            print("✗ No PDF files found in uploads folder")
            return False
        
        # Find JD PDF - prioritize from jd/ subdirectory, fallback to filename check
        jd_pdf = None
        jd_dir = Path(self.uploads_dir) / "jd"
        
        # First, look for PDFs in uploads/jd/ directory
        for pdf_path in all_pdfs:
            if str(jd_dir) in str(pdf_path):
                jd_pdf = pdf_path
                break
        
        # Fallback: look for 'jd', 'job', or 'description' in filename
        if not jd_pdf:
            for pdf_path in all_pdfs:
                filename = Path(pdf_path).name.lower()
                if "jd" in filename or "job" in filename or "description" in filename:
                    jd_pdf = pdf_path
                    break
        
        if not jd_pdf:
            print("✗ No Job Description PDF found (should be in uploads/jd/ or filename with 'jd')")
            return False
        
        # Extract JD text
        print(f"Loading: {Path(jd_pdf).name}")
        jd_text = extract_text_from_pdf(jd_pdf)
        
        if not jd_text:
            print("✗ Failed to extract text from JD PDF")
            return False
        
        print("✓ JD text extracted")
        
        # Generate and send extraction prompt
        print("Extracting structured JD data...")
        jd_prompt = get_jd_extraction_prompt(jd_text)
        jd_response = ask_llm(jd_prompt)
        
        if not jd_response:
            print("✗ Failed to get JD extraction from Gemini")
            return False
        
        # Parse response
        self.jd_data = safe_json_loads(jd_response)
        
        if not self.jd_data:
            print("✗ Failed to parse JD JSON response")
            return False
        
        print("✓ JD structured data extracted\n")
        self.stats["jd_found"] = True
        return True
    
    # ==========================================================================
    # STEP 3-7: PROCESS RESUMES
    # ==========================================================================
    
    def process_resume(self, resume_path: str) -> Optional[Dict[str, Any]]:
        """
        Process a single resume through the complete pipeline.
        
        Args:
            resume_path (str): Path to resume PDF.
        
        Returns:
            Dict with candidate result or None if failed.
        """
        resume_filename = Path(resume_path).name
        print(f"\n## Processing Resume: {resume_filename}")
        self.print_separator()
        
        # Step 1: Extract resume text
        print("Extracting resume text...")
        resume_text = extract_text_from_pdf(resume_path)
        
        if not resume_text:
            print("✗ Failed to extract text from resume")
            self.stats["resumes_failed"] += 1
            return None
        
        print("✓ Resume text extracted")
        
        # Step 2: Extract structured resume data
        print("Extracting structured resume data...")
        resume_prompt = get_resume_extraction_prompt(resume_text)
        resume_response = ask_llm(resume_prompt)
        
        if not resume_response:
            print("✗ Failed to extract resume data from Gemini")
            self.stats["resumes_failed"] += 1
            return None
        
        resume_data = safe_json_loads(resume_response)
        
        if not resume_data:
            print("✗ Failed to parse resume JSON")
            self.stats["resumes_failed"] += 1
            return None
        
        print("✓ Resume structured data extracted")
        
        # Step 3: Perform semantic analysis
        print("Performing semantic analysis...")
        analysis_prompt = get_analysis_prompt(self.jd_data, resume_data)
        analysis_response = ask_llm(analysis_prompt)
        
        if not analysis_response:
            print("✗ Failed to perform semantic analysis")
            self.stats["resumes_failed"] += 1
            return None
        
        analysis_data = safe_json_loads(analysis_response)
        
        if not analysis_data:
            print("✗ Failed to parse analysis JSON")
            self.stats["resumes_failed"] += 1
            return None
        
        print("✓ Semantic analysis complete")
        
        # Step 4: Calculate score
        print("Calculating candidate score...")
        candidate_result = score_candidate(
            self.jd_data,
            resume_data,
            analysis_data
        )
        
        if not candidate_result or "final_score" not in candidate_result:
            print("✗ Failed to score candidate")
            self.stats["resumes_failed"] += 1
            return None
        
        print("✓ Candidate scored")
        
        # Step 5: Save individual result
        saved_path = save_candidate_result(candidate_result, self.outputs_dir)
        
        if saved_path:
            print(f"✓ Result saved: {Path(saved_path).name}")
        
        # Print candidate summary
        self._print_candidate_summary(candidate_result)
        
        self.stats["resumes_successful"] += 1
        return candidate_result
    
    def _print_candidate_summary(self, result: Dict[str, Any]) -> None:
        """Print candidate summary to console."""
        candidate_name = result.get("candidate_name", "Unknown")
        final_score = result.get("final_score", 0)
        breakdown = result.get("breakdown", {})
        
        print(f"\nCandidate: {candidate_name}")
        print(f"Final Score: {final_score}/100")
        print("\nBreakdown:")
        
        for category, data in breakdown.items():
            score = data.get("score", "N/A")
            justification = data.get("justification", "")
            print(f"  • {category.capitalize()}: {score}/10")
            print(f"    → {justification}")
    
    # ==========================================================================
    # STEP 8-9: RANK AND SAVE RESULTS
    # ==========================================================================
    
    def rank_and_save_results(self) -> None:
        """Rank candidates and save batch results."""
        if not self.candidate_results:
            print("\nNo candidates to rank")
            return
        
        print("\n" + "=" * 70)
        print("FINAL RANKINGS")
        print("=" * 70)
        
        # Rank candidates
        ranked_results = rank_candidates(self.candidate_results)
        
        # Print rankings
        for result in ranked_results:
            rank = result.get("rank", "N/A")
            name = result.get("candidate_name", "Unknown")
            score = result.get("final_score", 0)
            print(f"{rank}. {name} → {score}/100")
        
        # Save batch results
        batch_path = save_batch_results(
            ranked_results,
            self.outputs_dir,
            "shortlisting_results"
        )
        
        if batch_path:
            print(f"\n✓ Batch results saved: {Path(batch_path).name}")
    
    # ==========================================================================
    # MAIN PIPELINE
    # ==========================================================================
    
    def run(self) -> None:
        """Execute the complete pipeline."""
        self.print_header()
        
        # Step 1-2: Load JD
        if not self.load_and_extract_jd():
            print("\n✗ Failed to load Job Description. Exiting.")
            self._print_summary()
            return
        
        # Step 3-7: Process resumes
        all_pdfs = get_pdfs_from_uploads(self.uploads_dir)
        resume_pdfs = []
        resumes_dir = Path(self.uploads_dir) / "resumes"
        jd_dir = Path(self.uploads_dir) / "jd"
        
        # Filter resumes - prioritize from resumes/ subdirectory, fallback to filename check
        for pdf_path in all_pdfs:
            pdf_path_str = str(pdf_path)
            
            # Include PDFs from uploads/resumes/ directory
            if str(resumes_dir) in pdf_path_str:
                resume_pdfs.append(pdf_path)
            # Exclude PDFs from uploads/jd/ directory
            elif str(jd_dir) in pdf_path_str:
                continue
            # Fallback: exclude by filename check
            else:
                filename = Path(pdf_path).name.lower()
                if not ("jd" in filename or "job" in filename or "description" in filename):
                    resume_pdfs.append(pdf_path)
        
        if not resume_pdfs:
            print("✗ No resume PDFs found in uploads folder")
            self._print_summary()
            return
        
        print(f"Found {len(resume_pdfs)} resume(s) to process\n")
        
        # Process each resume
        for resume_path in resume_pdfs:
            self.stats["resumes_processed"] += 1
            result = self.process_resume(resume_path)
            
            if result:
                self.candidate_results.append(result)
        
        # Step 8-9: Rank and save
        self.rank_and_save_results()
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self) -> None:
        """Print execution summary."""
        print("\n" + "=" * 70)
        print("EXECUTION SUMMARY")
        print("=" * 70)
        print(f"Job Description: {'✓ Found' if self.stats['jd_found'] else '✗ Not found'}")
        print(f"Resumes Processed: {self.stats['resumes_processed']}")
        print(f"Resumes Successful: {self.stats['resumes_successful']}")
        print(f"Resumes Failed: {self.stats['resumes_failed']}")
        print(f"Output Directory: {self.outputs_dir}")
        print("=" * 70 + "\n")


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main() -> None:
    """Main entry point for the application."""
    try:
        pipeline = HRShortlistingPipeline(
            uploads_dir="uploads",
            outputs_dir="outputs"
        )
        pipeline.run()
    
    except KeyboardInterrupt:
        print("\n\n✗ Pipeline interrupted by user")
    
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
