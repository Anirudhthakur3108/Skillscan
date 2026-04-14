"""
Gemini API Client Wrapper for SkillScan
Handles assessment generation, scoring, and learning plan creation
"""

import json
import os
import logging
import re
import time
from typing import Dict, List, Optional, Any
from functools import wraps
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gemini_client')


# ============================================================================
# Helper Functions
# ============================================================================

def _parse_json_response(response_text: str) -> Dict[str, Any]:
    """
    Extract and parse JSON from Gemini response.
    Handles markdown code blocks (```json ... ```)
    
    Args:
        response_text (str): Raw response from Gemini API
        
    Returns:
        dict: Parsed JSON response
        
    Raises:
        ValueError: If JSON cannot be parsed
    """
    try:
        # Try to extract JSON from markdown code blocks
        json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
        matches = re.findall(json_pattern, response_text)
        
        if matches:
            json_str = matches[0].strip()
        else:
            # Try to find JSON object directly
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
            else:
                raise ValueError("No JSON found in response")
        
        # Parse JSON
        parsed = json.loads(json_str)
        logger.info("✓ Successfully parsed JSON response")
        return parsed
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {str(e)}")
        raise ValueError(f"Failed to parse JSON: {str(e)}")


def _retry_with_backoff(max_retries: int = 3, base_wait: float = 1.0):
    """
    Decorator for retry logic with exponential backoff.
    
    Args:
        max_retries (int): Maximum number of retry attempts
        base_wait (float): Base wait time in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    logger.debug(f"Attempt {attempt + 1}/{max_retries} for {func.__name__}")
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        wait_time = base_wait * (2 ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {str(e)}. "
                            f"Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            
            raise last_exception
        
        return wrapper
    return decorator


def validate_assessment_response(assessment: Dict[str, Any], assessment_type: str) -> bool:
    """
    Validate assessment structure.
    
    Args:
        assessment (dict): Assessment response
        assessment_type (str): Type of assessment (mcq, coding, case_study)
        
    Returns:
        bool: True if valid, raises ValueError otherwise
    """
    try:
        # Check required top-level keys
        if assessment_type == "mcq":
            assert "questions" in assessment, "Missing 'questions' key"
            assert "metadata" in assessment, "Missing 'metadata' key"
            assert isinstance(assessment["questions"], list), "Questions must be a list"
            assert len(assessment["questions"]) > 0, "Questions list cannot be empty"
            
            # Validate each question
            for q in assessment["questions"]:
                assert "id" in q, "Question missing 'id'"
                assert "question" in q, "Question missing 'question' text"
                assert "options" in q, "Question missing 'options'"
                assert "correct_answer" in q, "Question missing 'correct_answer'"
                assert isinstance(q["options"], list), "Options must be a list"
                assert len(q["options"]) >= 4, "Must have at least 4 options"
        
        elif assessment_type == "coding":
            assert "problems" in assessment, "Missing 'problems' key"
            assert "metadata" in assessment, "Missing 'metadata' key"
            assert isinstance(assessment["problems"], list), "Problems must be a list"
            
            for p in assessment["problems"]:
                assert "id" in p, "Problem missing 'id'"
                assert "title" in p, "Problem missing 'title'"
                assert "description" in p, "Problem missing 'description'"
                assert "starter_code" in p, "Problem missing 'starter_code'"
        
        elif assessment_type == "case_study":
            assert "case_studies" in assessment, "Missing 'case_studies' key"
            assert "metadata" in assessment, "Missing 'metadata' key"
            assert isinstance(assessment["case_studies"], list), "Case studies must be a list"
            
            for cs in assessment["case_studies"]:
                assert "id" in cs, "Case study missing 'id'"
                assert "title" in cs, "Case study missing 'title'"
                assert "scenario" in cs, "Case study missing 'scenario'"
                assert "questions" in cs, "Case study missing 'questions'"
        
        logger.info(f"✓ Validation passed for {assessment_type} assessment")
        return True
        
    except AssertionError as e:
        logger.error(f"Validation failed: {str(e)}")
        raise ValueError(f"Invalid assessment response: {str(e)}")


def validate_scoring_response(scoring: Dict[str, Any]) -> bool:
    """
    Validate scoring response structure.
    
    Args:
        scoring (dict): Scoring response
        
    Returns:
        bool: True if valid, raises ValueError otherwise
    """
    try:
        assert "overall_score" in scoring, "Missing 'overall_score'"
        assert 1 <= scoring["overall_score"] <= 10, "Score must be between 1-10"
        assert "identified_gaps" in scoring, "Missing 'identified_gaps'"
        assert isinstance(scoring["identified_gaps"], list), "Gaps must be a list"
        assert "confidence" in scoring, "Missing 'confidence'"
        assert 0 <= scoring["confidence"] <= 1, "Confidence must be between 0-1"
        
        logger.info("✓ Validation passed for scoring response")
        return True
        
    except AssertionError as e:
        logger.error(f"Validation failed: {str(e)}")
        raise ValueError(f"Invalid scoring response: {str(e)}")


# ============================================================================
# Main GeminiClient Class
# ============================================================================

class GeminiClient:
    """
    Client for Google Gemini API integration with SkillScan.
    Handles assessment generation, scoring, and learning plan creation.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini API client with error handling.
        
        Args:
            api_key (str, optional): Gemini API key. If not provided, loads from environment
            
        Raises:
            ValueError: If API key is not found
        """
        try:
            # Get API key from parameter or environment
            self.api_key = api_key or os.getenv("GEMINI_API_KEY")
            
            if not self.api_key:
                raise ValueError(
                    "GEMINI_API_KEY not found. Please provide it as parameter "
                    "or set environment variable."
                )
            
            # Configure genai library
            genai.configure(api_key=self.api_key)
            
            # Set up model instance
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            
            logger.info("✓ Gemini API client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            raise
    
    @_retry_with_backoff(max_retries=3, base_wait=1.0)
    def generate_assessment(
        self,
        skill: str,
        proficiency: int,
        difficulty: str,
        assessment_type: str
    ) -> Dict[str, Any]:
        """
        Generate an assessment for a given skill.
        
        Args:
            skill (str): Skill name (e.g., "Python", "React")
            proficiency (int): Student's claimed proficiency (1-10)
            difficulty (str): Difficulty level ("easy", "medium", "hard")
            assessment_type (str): Type of assessment ("mcq", "coding", "case_study")
        
        Returns:
            dict: Assessment with questions and metadata
            
        Raises:
            ValueError: If assessment generation fails
        """
        try:
            logger.info(
                f"Generating {assessment_type} assessment for {skill} "
                f"(proficiency: {proficiency}/10, difficulty: {difficulty})"
            )
            
            # Build prompt based on assessment type
            prompt = self._build_assessment_prompt(
                skill, proficiency, difficulty, assessment_type
            )
            
            # Call Gemini API
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            logger.debug(f"API Response received: {len(response_text)} characters")
            
            # Parse response into structured format
            assessment = _parse_json_response(response_text)
            
            # Validate response structure
            validate_assessment_response(assessment, assessment_type)
            
            logger.info(
                f"✓ Successfully generated {assessment_type} assessment "
                f"with {len(assessment.get(self._get_content_key(assessment_type), []))} items"
            )
            
            return assessment
            
        except Exception as e:
            logger.error(f"Failed to generate assessment: {str(e)}")
            raise
    
    @_retry_with_backoff(max_retries=3, base_wait=1.0)
    def score_assessment(
        self,
        assessment_type: str,
        questions: List[Dict[str, Any]],
        responses: List[Dict[str, Any]],
        skill: str
    ) -> Dict[str, Any]:
        """
        Score a completed assessment using AI.
        
        Args:
            assessment_type (str): Type of assessment scored
            questions (list): Original assessment questions
            responses (list): Student's responses
            skill (str): Skill being assessed
        
        Returns:
            dict: Score (1-10), gaps identified, reasoning, confidence
            
        Raises:
            ValueError: If scoring fails
        """
        try:
            logger.info(f"Scoring {assessment_type} assessment for {skill}")
            
            # Build scoring prompt
            prompt = self._build_scoring_prompt(
                assessment_type, questions, responses, skill
            )
            
            # Call Gemini API
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Parse response
            scoring = _parse_json_response(response_text)
            
            # Validate response structure
            validate_scoring_response(scoring)
            
            logger.info(
                f"✓ Successfully scored assessment. "
                f"Overall score: {scoring['overall_score']}/10, "
                f"Confidence: {scoring['confidence']}"
            )
            
            return scoring
            
        except Exception as e:
            logger.error(f"Failed to score assessment: {str(e)}")
            raise
    
    @_retry_with_backoff(max_retries=3, base_wait=1.0)
    def generate_learning_plan(
        self,
        skill_gaps: List[Dict[str, Any]],
        user_proficiency: Dict[str, int],
        user_type: str
    ) -> Dict[str, Any]:
        """
        Generate personalized learning plan based on gaps.
        
        Args:
            skill_gaps (list): List of identified skill gaps with depth
            user_proficiency (dict): Current proficiency levels per skill
            user_type (str): "MBA_Analytics" or "BCA"
        
        Returns:
            dict: Recommendations with courses, projects, timeline
            
        Raises:
            ValueError: If learning plan generation fails
        """
        try:
            logger.info(
                f"Generating learning plan for {user_type} student "
                f"with {len(skill_gaps)} gaps"
            )
            
            # Build learning plan prompt
            prompt = self._build_learning_plan_prompt(
                skill_gaps, user_proficiency, user_type
            )
            
            # Call Gemini API
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Parse response
            learning_plan = _parse_json_response(response_text)
            
            logger.info(
                f"✓ Successfully generated learning plan. "
                f"Total timeline: {learning_plan.get('overall_timeline_weeks', 'N/A')} weeks"
            )
            
            return learning_plan
            
        except Exception as e:
            logger.error(f"Failed to generate learning plan: {str(e)}")
            raise
    
    # ========================================================================
    # Prompt Building Methods
    # ========================================================================
    
    def _build_assessment_prompt(
        self,
        skill: str,
        proficiency: int,
        difficulty: str,
        assessment_type: str
    ) -> str:
        """Build prompt for assessment generation based on type."""
        
        if assessment_type == "mcq":
            return self._mcq_prompt(skill, proficiency, difficulty)
        elif assessment_type == "coding":
            return self._coding_prompt(skill, proficiency, difficulty)
        elif assessment_type == "case_study":
            return self._case_study_prompt(skill, proficiency, difficulty)
        else:
            raise ValueError(f"Unknown assessment type: {assessment_type}")
    
    def _mcq_prompt(self, skill: str, proficiency: int, difficulty: str) -> str:
        """Generate MCQ assessment prompt."""
        
        difficulty_guidelines = {
            "easy": "Test basic concepts and foundational knowledge. Clear, unambiguous questions. Common real-world scenarios.",
            "medium": "Test intermediate understanding and practical application. Require some problem-solving. Common interview questions.",
            "hard": "Test advanced concepts and edge cases. Require deep understanding and design thinking. Advanced interview or specialized topics."
        }
        
        return f"""Difficulty: {difficulty}

Generate exactly 5 multiple-choice questions for {skill} at {difficulty} level.
Student's proficiency: {proficiency}/10

For {difficulty.upper()} difficulty:
{difficulty_guidelines.get(difficulty, "")}

Return as JSON (no markdown, just the JSON object):
{{
  "questions": [
    {{
      "id": 1,
      "question": "Question text?",
      "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
      "correct_answer": "B",
      "explanation": "Why this is correct...",
      "difficulty": "{difficulty}",
      "topic": "Specific topic within {skill}"
    }}
  ],
  "metadata": {{
    "skill": "{skill}",
    "type": "mcq",
    "difficulty": "{difficulty}",
    "estimated_time_minutes": 15,
    "total_questions": 5
  }}
}}

IMPORTANT: Return ONLY valid JSON, starting with {{ and ending with }}, no additional text."""
    
    def _coding_prompt(self, skill: str, proficiency: int, difficulty: str) -> str:
        """Generate coding challenge prompt."""
        
        difficulty_specs = {
            "easy": "15-20 minutes each - Simple implementation tasks with clear problem statements",
            "medium": "20-30 minutes each - Moderate complexity requiring algorithms",
            "hard": "30-45 minutes each - Complex problems requiring optimization and design patterns"
        }
        
        return f"""Difficulty: {difficulty}

Generate 2 coding problems for {skill} at {difficulty} level.
Student's proficiency: {proficiency}/10

{difficulty_specs.get(difficulty, "")}

For each problem provide:
- Problem title and description
- Starter code
- Example input/output
- Edge cases to consider

Return as JSON (no markdown, just the JSON object):
{{
  "problems": [
    {{
      "id": 1,
      "title": "Problem Title",
      "description": "Detailed problem description...",
      "difficulty": "{difficulty}",
      "starter_code": "def solve():\\n    pass",
      "example_input": "Example input here",
      "example_output": "Expected output here",
      "edge_cases": ["Edge case 1", "Edge case 2"],
      "estimated_time_minutes": 25
    }}
  ],
  "metadata": {{
    "skill": "{skill}",
    "type": "coding",
    "difficulty": "{difficulty}",
    "estimated_time_minutes": 45,
    "total_problems": 2,
    "language_context": "{skill}"
  }}
}}

IMPORTANT: Return ONLY valid JSON, starting with {{ and ending with }}, no additional text."""
    
    def _case_study_prompt(self, skill: str, proficiency: int, difficulty: str) -> str:
        """Generate case study prompt."""
        
        difficulty_specs = {
            "easy": "15-20 minutes - Straightforward real-world scenarios with clear requirements",
            "medium": "20-30 minutes - More complex scenarios with multiple considerations",
            "hard": "30-45 minutes - Complex scenarios requiring strategic thinking and multiple valid approaches"
        }
        
        return f"""Difficulty: {difficulty}

Generate 1 case study scenario for {skill} at {difficulty} level.
Student's proficiency: {proficiency}/10

{difficulty_specs.get(difficulty, "")}

For the case study provide:
- Real-world scenario
- Business context and constraints
- 4-5 follow-up questions testing analysis and decision-making

Return as JSON (no markdown, just the JSON object):
{{
  "case_studies": [
    {{
      "id": 1,
      "title": "Case Study Title",
      "scenario": "Detailed scenario description...",
      "context": "Business context and constraints...",
      "difficulty": "{difficulty}",
      "questions": [
        {{
          "id": 1,
          "question": "What approach would you take?",
          "question_type": "analysis",
          "hints": ["Hint 1", "Hint 2"]
        }}
      ],
      "estimated_time_minutes": 30
    }}
  ],
  "metadata": {{
    "skill": "{skill}",
    "type": "case_study",
    "difficulty": "{difficulty}",
    "estimated_time_minutes": 30,
    "total_case_studies": 1
  }}
}}

IMPORTANT: Return ONLY valid JSON, starting with {{ and ending with }}, no additional text."""
    
    def _build_scoring_prompt(
        self,
        assessment_type: str,
        questions: List[Dict[str, Any]],
        responses: List[Dict[str, Any]],
        skill: str
    ) -> str:
        """Build prompt for assessment scoring."""
        
        questions_json = json.dumps(questions, indent=2)
        responses_json = json.dumps(responses, indent=2)
        
        return f"""Score this {assessment_type} assessment for {skill}.

Assessment Questions:
{questions_json}

Student Responses:
{responses_json}

Evaluation Criteria:
- Correctness: Does the response answer the question?
- Completeness: Is the answer thorough?
- Proficiency: Does it demonstrate the claimed skill level?
- For coding: Does code compile and work correctly?
- For case study: Is analysis thoughtful and well-reasoned?

Provide detailed scoring:
1. Score each question (1-10)
2. Overall skill score (1-10)
3. Identified skill gaps (areas of weakness)
4. Reasoning for score
5. Confidence level (0-1)

Return as JSON (no markdown, just the JSON object):
{{
  "overall_score": 7,
  "score_breakdown": {{
    "q1": 8,
    "q2": 7
  }},
  "identified_gaps": [
    {{
      "gap": "Gap description",
      "severity": "high/medium/low",
      "impact": "Why this gap matters",
      "priority_score": 9
    }}
  ],
  "strengths": ["Strength 1", "Strength 2"],
  "weaknesses": ["Weakness 1", "Weakness 2"],
  "reasoning": "Overall reasoning for the score...",
  "confidence": 0.85,
  "next_difficulty_recommended": "easy/medium/hard"
}}

IMPORTANT: Return ONLY valid JSON, starting with {{ and ending with }}, no additional text."""
    
    def _build_learning_plan_prompt(
        self,
        skill_gaps: List[Dict[str, Any]],
        user_proficiency: Dict[str, int],
        user_type: str
    ) -> str:
        """Build prompt for learning plan generation."""
        
        gaps_json = json.dumps(skill_gaps, indent=2)
        proficiency_json = json.dumps(user_proficiency, indent=2)
        
        user_context = {
            "MBA_Analytics": "MBA Analytics student - focus on data analysis, SQL, Python, statistics, business intelligence",
            "BCA": "BCA (Bachelor of Computer Applications) student - focus on programming fundamentals, DSA, web development, databases"
        }
        
        return f"""Generate a personalized learning plan for {user_context.get(user_type, user_type)} student.

Identified Gaps:
{gaps_json}

Current Proficiency:
{proficiency_json}

For each gap, recommend:
1. Best online courses (Udemy, Coursera, etc.) - prioritized by relevance
2. YouTube channels/tutorials
3. Books or ebooks
4. Hands-on projects
5. GitHub repositories to study

Priority based on:
- Gap severity (how bad the gap is)
- Industry importance (how much it matters for jobs)
- Time to upskill (estimated hours needed)

Return as JSON (no markdown, just the JSON object):
{{
  "priority_gaps": [
    {{
      "gap": "Gap name",
      "severity": "high/medium/low",
      "estimated_hours": 20,
      "priority_score": 9,
      "recommendations": [
        {{
          "type": "course",
          "title": "Course Title",
          "provider": "Udemy/Coursera/etc",
          "duration_hours": 20,
          "difficulty": "intermediate",
          "url": "https://...",
          "why_recommended": "Why this for this gap"
        }}
      ]
    }}
  ],
  "overall_timeline_weeks": 8,
  "success_metrics": [
    "Complete all recommended courses",
    "Build 2 projects",
    "Score 8+ on re-assessment",
    "Master all gap areas"
  ]
}}

IMPORTANT: Return ONLY valid JSON, starting with {{ and ending with }}, no additional text."""
    
    def _get_content_key(self, assessment_type: str) -> str:
        """Get the main content key for different assessment types."""
        mapping = {
            "mcq": "questions",
            "coding": "problems",
            "case_study": "case_studies"
        }
        return mapping.get(assessment_type, "questions")
