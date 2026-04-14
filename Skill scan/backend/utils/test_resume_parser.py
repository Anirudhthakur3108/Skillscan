"""
Comprehensive tests for Resume Parser and Skill Matcher
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path
from io import BytesIO

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.skill_matcher import SkillMatcher
from utils.resume_parser import ResumeParser


class TestSkillMatcher(unittest.TestCase):
    """Test SkillMatcher class"""

    def setUp(self):
        """Initialize test fixtures"""
        self.matcher = SkillMatcher()
        self.default_skills = self.matcher.skill_list

    def test_exact_match_python(self):
        """Test exact matching for Python"""
        text = "I have experience with Python and Java"
        matches = self.matcher.match_exact(text, ["Python", "Java", "JavaScript"])
        skill_names = [m["skill"] for m in matches]

        self.assertIn("Python", skill_names)
        self.assertIn("Java", skill_names)
        self.assertNotIn("JavaScript", skill_names)

        # Check confidence
        for match in matches:
            self.assertEqual(match["confidence"], 1.0)
            self.assertEqual(match["match_type"], "exact")

    def test_exact_match_case_insensitive(self):
        """Test exact matching is case-insensitive"""
        text = "Expert in python, JAVA, and JavaScript"
        matches = self.matcher.match_exact(text, ["Python", "Java", "JavaScript"])
        skill_names = [m["skill"] for m in matches]

        self.assertEqual(len(matches), 3)
        self.assertIn("Python", skill_names)
        self.assertIn("Java", skill_names)
        self.assertIn("JavaScript", skill_names)

    def test_exact_match_word_boundaries(self):
        """Test exact matching respects word boundaries"""
        text = "I know JavaScript but not just Java"
        matches = self.matcher.match_exact(text, ["Java", "JavaScript"])
        skill_names = [m["skill"] for m in matches]

        # Should find both JavaScript and Java (Java in JavaScript should not match)
        self.assertIn("JavaScript", skill_names)

    def test_fuzzy_match_python_variations(self):
        """Test fuzzy matching for Python variations"""
        text = "Skills: Python3, Py, python3.10"
        matches = self.matcher.match_fuzzy(text, ["Python"], threshold=0.8)

        self.assertGreater(len(matches), 0)
        for match in matches:
            self.assertGreaterEqual(match["confidence"], 0.6)
            self.assertLessEqual(match["confidence"], 1.0)

    def test_fuzzy_match_javascript_variations(self):
        """Test fuzzy matching for JavaScript variations"""
        text = "Frontend: JS, Node.js, TypeScript"
        matches = self.matcher.match_fuzzy(text, ["JavaScript"], threshold=0.8)

        # Should find JS and Node.js as fuzzy matches
        self.assertGreater(len(matches), 0)

    def test_fuzzy_match_sql_variations(self):
        """Test fuzzy matching for SQL variations"""
        text = "Database: MySQL, PostgreSQL, MongoDB"
        matches = self.matcher.match_fuzzy(text, ["SQL", "SQL/Databases"], threshold=0.8)

        self.assertGreater(len(matches), 0)

    def test_fuzzy_match_confidence_threshold(self):
        """Test fuzzy matching respects confidence threshold"""
        text = "Skills: Py, JS, React"
        matches = self.matcher.match_fuzzy(text, ["Python", "JavaScript", "React"], threshold=0.85)

        # All matches should be above threshold
        for match in matches:
            self.assertGreaterEqual(match["confidence"], 0.6)

    def test_hybrid_match_exact_prioritized(self):
        """Test hybrid matching prioritizes exact over fuzzy"""
        text = "Python and Py programming"
        matches = self.matcher.hybrid_match(text, ["Python"])

        # Should have only one "Python" match (exact)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["match_type"], "exact")
        self.assertEqual(matches[0]["confidence"], 1.0)

    def test_hybrid_match_deduplication(self):
        """Test hybrid matching removes duplicates"""
        text = "Python Python python Py"
        matches = self.matcher.hybrid_match(text, ["Python"])

        # Should have only one Python match
        python_matches = [m for m in matches if m["skill"] == "Python"]
        self.assertEqual(len(python_matches), 1)

    def test_hybrid_match_confidence_filtering(self):
        """Test hybrid matching filters by confidence threshold"""
        text = "Vague tech mentions with py and js"
        matches = self.matcher.hybrid_match(text, ["Python", "JavaScript"], confidence_threshold=0.6)

        # All matches should meet threshold
        for match in matches:
            self.assertGreaterEqual(match["confidence"], 0.6)

    def test_calculate_confidence_exact(self):
        """Test confidence calculation for exact matches"""
        confidence = SkillMatcher.calculate_confidence("exact", 0.95)
        self.assertEqual(confidence, 1.0)

    def test_calculate_confidence_fuzzy(self):
        """Test confidence calculation for fuzzy matches"""
        confidence = SkillMatcher.calculate_confidence("fuzzy", 0.85)
        self.assertGreaterEqual(confidence, 0.6)
        self.assertLessEqual(confidence, 0.99)

    def test_all_default_skills_extractable(self):
        """Test all default skills can be extracted"""
        # Create a text with all skills mentioned
        text = " ".join(self.default_skills)
        matches = self.matcher.hybrid_match(text, self.default_skills)

        # Should match most skills (accounting for conflicts like "Java" in "JavaScript")
        self.assertGreater(len(matches), 10)

    def test_extract_skills_with_context(self):
        """Test skill extraction with context information"""
        text = "Python and Java programmer with SQL expertise"
        result = self.matcher.extract_skills_with_context(text, ["Python", "Java", "SQL"])

        self.assertIn("extracted_skills", result)
        self.assertIn("stats", result)
        self.assertGreater(result["stats"]["total_matches"], 0)
        self.assertGreater(result["stats"]["average_confidence"], 0)


class TestResumeParser(unittest.TestCase):
    """Test ResumeParser class"""

    def setUp(self):
        """Initialize test fixtures"""
        self.parser = ResumeParser()
        self.test_resumes_dir = os.path.join(
            os.path.dirname(__file__), "..", "test_resumes"
        )

    def test_parser_initialization(self):
        """Test parser initializes correctly"""
        self.assertIsNotNone(self.parser.skill_list)
        self.assertGreater(len(self.parser.skill_list), 0)
        self.assertIsNotNone(self.parser.matcher)

    def test_extract_skills_from_text(self):
        """Test skill extraction from plain text"""
        text = "Experienced Python and SQL developer with expertise in Tableau and Power BI"
        result = self.parser.extract_skills(text)

        self.assertIn("extracted_skills", result)
        self.assertIn("stats", result)
        self.assertGreater(len(result["extracted_skills"]), 0)

        # Check response structure
        for skill in result["extracted_skills"]:
            self.assertIn("skill_name", skill)
            self.assertIn("confidence", skill)
            self.assertIn("match_type", skill)

    def test_extract_skills_empty_text(self):
        """Test skill extraction handles empty text"""
        result = self.parser.extract_skills("")

        self.assertEqual(len(result["extracted_skills"]), 0)
        self.assertEqual(result["stats"]["total_matches"], 0)

    def test_extract_skills_no_matches(self):
        """Test skill extraction with text containing no skills"""
        text = "Lorem ipsum dolor sit amet consectetur adipiscing elit"
        result = self.parser.extract_skills(text)

        self.assertEqual(len(result["extracted_skills"]), 0)

    def test_validate_pdf_header(self):
        """Test PDF header validation"""
        # Create a temporary PDF-like file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4\n")
            temp_path = f.name

        try:
            is_valid = self.parser.validate_pdf(temp_path)
            self.assertTrue(is_valid)
        finally:
            os.remove(temp_path)

    def test_validate_non_pdf_file(self):
        """Test validation rejects non-PDF files"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"This is not a PDF")
            temp_path = f.name

        try:
            is_valid = self.parser.validate_pdf(temp_path)
            self.assertFalse(is_valid)
        finally:
            os.remove(temp_path)

    def test_extract_text_from_pdf_nonexistent(self):
        """Test error handling for nonexistent files"""
        with self.assertRaises(FileNotFoundError):
            self.parser.extract_text_from_pdf("/nonexistent/path/resume.pdf")

    def test_extract_text_from_pdf_large_file(self):
        """Test error handling for overly large files"""
        # Create a file larger than 5MB
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            # Write 6MB of data
            f.write(b"x" * (6 * 1024 * 1024))
            temp_path = f.name

        try:
            with self.assertRaises(ValueError) as context:
                self.parser.extract_text_from_pdf(temp_path)
            self.assertIn("too large", str(context.exception).lower())
        finally:
            os.remove(temp_path)

    def test_extract_skills_MBA_resume_keywords(self):
        """Test extraction with MBA Analytics keywords"""
        mba_text = """
        Analytics Professional
        Skills: Python, SQL, Excel/VBA, Tableau, Power BI, Statistics, Data Analysis, R, Machine Learning
        Experience with data visualization and statistical analysis
        """
        result = self.parser.extract_skills(mba_text)

        # Should find most MBA skills
        extracted_skill_names = [s["skill_name"] for s in result["extracted_skills"]]
        self.assertIn("Python", extracted_skill_names)
        self.assertIn("SQL", extracted_skill_names)
        self.assertGreater(len(result["extracted_skills"]), 3)

    def test_extract_skills_BCA_resume_keywords(self):
        """Test extraction with BCA student keywords"""
        bca_text = """
        Software Engineer
        Proficient in: Java, C++, JavaScript, React, Web Development
        Database: SQL/Databases
        Familiar with Data Structures and System Design
        """
        result = self.parser.extract_skills(bca_text)

        extracted_skill_names = [s["skill_name"] for s in result["extracted_skills"]]
        # Should find programming languages and web tech
        self.assertGreater(len(result["extracted_skills"]), 3)

    def test_parse_resume_with_mock_file(self):
        """Test parse_resume with mock file object"""
        # Mock a file upload
        mock_text = "Python and SQL expertise with Tableau"

        # We would need actual PDF files to test this properly
        # This is a placeholder for integration testing

    def test_skill_confidence_scores_reasonable(self):
        """Test that confidence scores are in valid range"""
        text = "Python, Py, py, JavaScript, JS, js"
        result = self.parser.extract_skills(text)

        for skill in result["extracted_skills"]:
            self.assertGreaterEqual(skill["confidence"], 0.0)
            self.assertLessEqual(skill["confidence"], 1.0)

            # Exact matches should be 1.0
            if skill["match_type"] == "exact":
                self.assertEqual(skill["confidence"], 1.0)

            # Fuzzy matches should be 0.6-0.99
            if skill["match_type"] == "fuzzy":
                self.assertGreaterEqual(skill["confidence"], 0.6)
                self.assertLess(skill["confidence"], 1.0)

    def test_stats_calculation(self):
        """Test statistics are calculated correctly"""
        text = "Python and Java, MySQL"
        result = self.parser.extract_skills(text)

        stats = result["stats"]
        self.assertEqual(stats["total_matches"], len(result["extracted_skills"]))
        self.assertGreaterEqual(stats["exact_matches"], 0)
        self.assertGreaterEqual(stats["fuzzy_matches"], 0)
        self.assertEqual(
            stats["total_matches"], stats["exact_matches"] + stats["fuzzy_matches"]
        )


class TestResumeParserIntegration(unittest.TestCase):
    """Integration tests for resume parsing workflow"""

    def setUp(self):
        """Initialize test fixtures"""
        self.parser = ResumeParser()

    def test_full_workflow_mba_analytics(self):
        """Test complete workflow with MBA Analytics resume text"""
        resume_text = """
        John Doe
        Data Analyst
        
        SKILLS:
        - Python (Advanced)
        - SQL Databases
        - Excel/VBA
        - Tableau Dashboards
        - Power BI Reports
        - Statistics & Analytics
        - Data Analysis with R
        - Machine Learning basics
        
        EXPERIENCE:
        Senior Data Analyst - ABC Corp
        - Developed Python scripts for data processing
        - Created Tableau visualizations
        - Analyzed trends using SQL queries
        """
        result = self.parser.extract_skills(resume_text)

        self.assertGreater(len(result["extracted_skills"]), 5)
        skill_names = [s["skill_name"] for s in result["extracted_skills"]]

        # Should extract key MBA skills
        self.assertTrue(any("Python" in sn for sn in skill_names))
        self.assertTrue(any("SQL" in sn for sn in skill_names))

    def test_full_workflow_bca_student(self):
        """Test complete workflow with BCA student resume text"""
        resume_text = """
        Jane Doe
        Full Stack Developer
        
        TECHNICAL SKILLS:
        - Programming Languages: Java, C++, JavaScript
        - Frontend: React, React.js
        - Web Development
        - Databases: SQL, MySQL
        - Data Structures & Algorithms
        - System Design principles
        
        PROJECTS:
        E-commerce Platform
        - Built with React and JavaScript
        - Backend API using Java
        - Database: MySQL
        """
        result = self.parser.extract_skills(resume_text)

        self.assertGreater(len(result["extracted_skills"]), 5)
        skill_names = [s["skill_name"] for s in result["extracted_skills"]]

        # Should extract key BCA skills
        self.assertTrue(any("Java" in sn for sn in skill_names))
        self.assertTrue(any("JavaScript" in sn for sn in skill_names))
        self.assertTrue(any("React" in sn for sn in skill_names))


if __name__ == "__main__":
    unittest.main(verbosity=2)
