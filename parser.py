"""
PDF parsing utility using PyMuPDF (fitz).

Provides reusable functions to extract text from PDF files and process PDFs from uploads folder.
"""
from typing import Optional, Dict, List
from pathlib import Path
import fitz  # PyMuPDF


def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """
    Extract and return text from the given PDF file.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        Optional[str]: Extracted text as a single string, or None if an error occurs.
    """
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        print(f"Failed to open PDF '{file_path}': {type(e).__name__} - {e}")
        return None

    extracted_pages = []

    try:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            if text:
                # Normalize whitespace
                cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
                extracted_pages.append(cleaned)

        doc.close()
    except Exception as e:
        print(f"Error reading PDF '{file_path}': {type(e).__name__} - {e}")
        try:
            doc.close()
        except Exception:
            pass
        return None

    # Join pages with a page break marker and return
    return "\n\n---PAGE BREAK---\n\n".join(extracted_pages)


def get_pdfs_from_uploads(uploads_dir: str = "uploads") -> List[str]:
    """
    Get a list of all PDF files in the uploads directory and subdirectories.
    
    Supports both flat structure (uploads/*.pdf) and nested structure 
    (uploads/jd/*.pdf, uploads/resumes/*.pdf) for frontend compatibility.

    Args:
        uploads_dir (str): Path to the uploads directory (default: "uploads").

    Returns:
        List[str]: List of absolute paths to PDF files.
    """
    uploads_path = Path(uploads_dir)
    if not uploads_path.exists():
        print(f"Uploads directory '{uploads_dir}' does not exist.")
        return []

    # Search for PDFs recursively in all subdirectories
    pdf_files = list(uploads_path.rglob("*.pdf"))
    return [str(pdf.resolve()) for pdf in pdf_files]


def extract_text_from_uploads(uploads_dir: str = "uploads") -> Dict[str, Optional[str]]:
    """
    Extract text from all PDF files in the uploads directory.

    Args:
        uploads_dir (str): Path to the uploads directory (default: "uploads").

    Returns:
        Dict[str, Optional[str]]: Dictionary with PDF filenames as keys and extracted text as values.
    """
    pdf_files = get_pdfs_from_uploads(uploads_dir)
    results = {}

    for pdf_path in pdf_files:
        filename = Path(pdf_path).name
        text = extract_text_from_pdf(pdf_path)
        results[filename] = text

    return results


# Small test example
if __name__ == "__main__":
    print("PDF Parser - List PDFs from uploads folder\n")
    print("=" * 50)

    # Get list of PDFs in uploads folder
    pdf_list = get_pdfs_from_uploads("uploads")

    if pdf_list:
        print(f"Found {len(pdf_list)} PDF file(s):\n")
        for i, pdf_path in enumerate(pdf_list, 1):
            print(f"{i}. {Path(pdf_path).name}")

        print("\n" + "=" * 50)
        print("\nExtracting text from all PDFs...\n")

        # Extract text from all PDFs
        results = extract_text_from_uploads("uploads")

        for filename, text in results.items():
            print(f"\n--- {filename} ---")
            if text:
                print(text[:500] + "..." if len(text) > 500 else text)
            else:
                print("(Failed to extract text)")
    else:
        print("No PDF files found in uploads folder.")

