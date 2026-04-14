"""
Resume Parser Module
Extracts text from PDF resumes and identifies skills using hybrid matching
"""

import os
import tempfile
from pathlib import Path
from typing import Tuple, Dict, Optional, List
import logging
import PyPDF2
import pdfplumber

from skill_matcher import SkillMatcher

logger = logging.getLogger(__name__)


class ResumeParser:
    """
    Resume parsing with PDF extraction and skill identification
    """

    def __init__(self, skill_list: Optional[List[str]] = None):
        """
        Initialize ResumeParser

        Args:
            skill_list: List of canonical skill names to match against
        """
        self.skill_list = skill_list or SkillMatcher._get_default_skills()
        self.matcher = SkillMatcher(self.skill_list)
        self.max_file_size = 5 * 1024 * 1024  # 5 MB
        logger.info(f"ResumeParser initialized with {len(self.skill_list)} skills")

    def extract_text_from_pdf(self, file_path: str) -> Tuple[str, str]:
        """
        Extract text from PDF using PyPDF2, fallback to pdfplumber

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple of (extracted_text, method_used) or raises ValueError

        Raises:
            ValueError: If both extraction methods fail
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            logger.error(f"File too large: {file_size} bytes (max: {self.max_file_size})")
            raise ValueError(f"File too large (max 5MB), received {file_size / 1024 / 1024:.1f}MB")

        # Try PyPDF2 first (lighter, faster)
        try:
            logger.info(f"Attempting PDF extraction with PyPDF2: {file_path}")
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)

                # Check if PDF is encrypted
                if reader.is_encrypted:
                    logger.warning("PDF is encrypted, attempting decryption...")
                    if not reader.decrypt(""):
                        raise ValueError("PDF is password protected")

                text = ""
                for page_num, page in enumerate(reader.pages):
                    try:
                        text += page.extract_text()
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num}: {str(e)}")
                        continue

                if not text.strip():
                    raise ValueError("No text extracted from PDF using PyPDF2")

                logger.info(f"Successfully extracted text using PyPDF2 ({len(text)} chars)")
                return text, "pypdf2"

        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {str(e)}, trying pdfplumber...")

            # Fallback to pdfplumber (better accuracy, slower)
            try:
                logger.info(f"Attempting PDF extraction with pdfplumber: {file_path}")
                with pdfplumber.open(file_path) as pdf:
                    text = ""
                    for page_num, page in enumerate(pdf.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text
                        except Exception as e:
                            logger.warning(f"Error extracting page {page_num}: {str(e)}")
                            continue

                    if not text.strip():
                        raise ValueError("No text extracted from PDF using pdfplumber")

                    logger.info(f"Successfully extracted text using pdfplumber ({len(text)} chars)")
                    return text, "pdfplumber"

            except Exception as e2:
                logger.error(f"Both PDF parsing methods failed: {str(e2)}")
                raise ValueError(
                    f"Failed to parse PDF. Please ensure the file is a valid, "
                    f"non-encrypted PDF. Error: {str(e2)}"
                )

    def extract_skills(self, text: str) -> Dict:
        """
        Extract skills from resume text using hybrid matching

        Args:
            text: Resume text content

        Returns:
            Dictionary with extracted skills and confidence scores
                {
                    "extracted_skills": [
                        {
                            "skill_name": "Python",
                            "confidence": 1.0,
                            "match_type": "exact"
                        },
                        ...
                    ],
                    "stats": {
                        "total_matches": int,
                        "exact_matches": int,
                        "fuzzy_matches": int,
                        "average_confidence": float
                    }
                }
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for skill extraction")
            return {
                "extracted_skills": [],
                "stats": {
                    "total_matches": 0,
                    "exact_matches": 0,
                    "fuzzy_matches": 0,
                    "average_confidence": 0,
                },
            }

        logger.info(f"Extracting skills from {len(text)} character resume")

        # Use hybrid matching
        matches = self.matcher.hybrid_match(text, self.skill_list)

        # Rename 'skill' to 'skill_name' for API response
        extracted_skills = [
            {
                "skill_name": match["skill"],
                "confidence": round(match["confidence"], 2),
                "match_type": match["match_type"],
            }
            for match in matches
        ]

        # Calculate statistics
        exact_count = sum(1 for m in extracted_skills if m["match_type"] == "exact")
        fuzzy_count = sum(1 for m in extracted_skills if m["match_type"] == "fuzzy")
        avg_confidence = (
            sum(m["confidence"] for m in extracted_skills) / len(extracted_skills)
            if extracted_skills
            else 0
        )

        result = {
            "extracted_skills": extracted_skills,
            "stats": {
                "total_matches": len(extracted_skills),
                "exact_matches": exact_count,
                "fuzzy_matches": fuzzy_count,
                "average_confidence": round(avg_confidence, 2),
            },
        }

        logger.info(f"Extraction complete: {len(extracted_skills)} skills found")
        return result

    def parse_resume(self, file, temp_dir: Optional[str] = None) -> Dict:
        """
        Complete resume parsing pipeline

        Args:
            file: Uploaded file object (from Flask request.files)
            temp_dir: Temporary directory for file storage (uses system temp if None)

        Returns:
            Dictionary with parsed resume data
                {
                    "extracted_skills": [...],
                    "stats": {...},
                    "source": "resume",
                    "extraction_method": "pypdf2" or "pdfplumber"
                }

        Raises:
            ValueError: If file validation or parsing fails
        """
        if not file or file.filename == "":
            logger.error("No file provided")
            raise ValueError("No file provided")

        # Validate file extension
        if not file.filename.lower().endswith(".pdf"):
            logger.error(f"Invalid file type: {file.filename}")
            raise ValueError("Only PDF files are accepted")

        # Use system temp directory if not provided
        if temp_dir is None:
            temp_dir = tempfile.gettempdir()

        # Save uploaded file temporarily
        try:
            temp_path = os.path.join(temp_dir, f"resume_{Path(file.filename).stem}.pdf")
            file.save(temp_path)
            logger.info(f"File saved temporarily: {temp_path}")
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise ValueError(f"Error saving uploaded file: {str(e)}")

        try:
            # Extract text from PDF
            text, extraction_method = self.extract_text_from_pdf(temp_path)

            # Extract skills
            skills_result = self.extract_skills(text)

            # Build response
            response = {
                "extracted_skills": skills_result["extracted_skills"],
                "stats": skills_result["stats"],
                "source": "resume",
                "extraction_method": extraction_method,
            }

            if not skills_result["extracted_skills"]:
                logger.warning("No skills extracted from resume")
                response["warning"] = "No skills were found in the resume. Please add skills manually."

            logger.info(f"Resume parsing complete: {response['stats']['total_matches']} skills found")
            return response

        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.debug(f"Temporary file cleaned up: {temp_path}")
            except Exception as e:
                logger.warning(f"Error cleaning up temp file: {str(e)}")

    def validate_pdf(self, file_path: str) -> bool:
        """
        Validate if file is a valid PDF

        Args:
            file_path: Path to file to validate

        Returns:
            True if valid PDF, False otherwise
        """
        try:
            with open(file_path, "rb") as f:
                header = f.read(4)
                return header == b"%PDF"
        except Exception as e:
            logger.warning(f"PDF validation failed: {str(e)}")
            return False
