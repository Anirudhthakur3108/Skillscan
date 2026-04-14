# SkillScan MVP - AI Model Integration Guide

**Purpose:** Step-by-step setup for integrating free AI models into SkillScan  
**Models Covered:** Google Gemini, Groq, HuggingFace, OpenRouter  
**Status:** Ready for Implementation

---

## 1. Model Selection & API Setup

### 1.1 Recommended Model for MVP

**Primary Choice: Google Gemini 2.0 Flash**
- **Why:** Free tier, fast response times, good for text/code generation, reliable
- **API Key:** Free from [Google AI Studio](https://aistudio.google.com)
- **Rate Limit:** 15 requests/minute (free tier)
- **Cost:** Free (generous limits for MVP)

**Fallback: Groq**
- **Why:** Ultra-fast, also free tier
- **API Key:** Free from [Groq Console](https://console.groq.com)
- **Rate Limit:** Higher free tier limits
- **Cost:** Free

**Optional: OpenRouter (Multi-model)**
- **Why:** Access to multiple models (Claude, LLaMA, etc.)
- **API Key:** Free tier available
- **Rate Limit:** Depends on model

---

## 2. Setting Up Gemini (Recommended)

### Step 1: Get API Key

```bash
# Navigate to Google AI Studio
https://aistudio.google.com

# Click "Get API Key" → "Create API key in new project"
# Copy your API key
# Save to .env file:
GEMINI_API_KEY=your_key_here
```

### Step 2: Install Dependencies

```bash
# In your Flask project:
pip install google-generativeai python-dotenv
```

### Step 3: Create Model Client Wrapper

**File: `backend/utils/model_client.py`**

```python
import os
import json
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
    
    def generate_assessment(self, skill: str, proficiency: int, assessment_type: str) -> Dict[str, Any]:
        """
        Generate an assessment for a given skill.
        
        Args:
            skill: Skill name (e.g., "Python", "React")
            proficiency: Claimed proficiency (1-10)
            assessment_type: Type of assessment ("mcq", "coding", "case_study")
        
        Returns:
            Dictionary with assessment questions and metadata
        """
        prompt = self._build_assessment_prompt(skill, proficiency, assessment_type)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Parse response into JSON structure
            assessment_data = self._parse_assessment_response(
                response.text, 
                skill, 
                assessment_type
            )
            return assessment_data
        
        except Exception as e:
            logger.error(f"Error generating assessment: {str(e)}")
            raise
    
    def score_assessment(self, assessment_type: str, questions: list, responses: list, skill: str) -> Dict[str, Any]:
        """
        Score a completed assessment.
        
        Args:
            assessment_type: Type of assessment ("mcq", "coding", "case_study")
            questions: List of assessment questions
            responses: Student's responses
            skill: Skill being assessed
        
        Returns:
            Dictionary with score (1-10), reasoning, and gaps
        """
        prompt = self._build_scoring_prompt(assessment_type, questions, responses, skill)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Parse response into scoring structure
            scoring_data = self._parse_scoring_response(response.text, skill)
            return scoring_data
        
        except Exception as e:
            logger.error(f"Error scoring assessment: {str(e)}")
            raise
    
    def generate_learning_plan(self, skill_gaps: list, proficiency_levels: Dict) -> Dict[str, Any]:
        """
        Generate personalized learning plan based on skill gaps.
        
        Args:
            skill_gaps: List of identified skill gaps
            proficiency_levels: Dictionary of current proficiency levels per skill
        
        Returns:
            Dictionary with learning recommendations
        """
        prompt = self._build_learning_plan_prompt(skill_gaps, proficiency_levels)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Parse response into learning plan structure
            learning_plan = self._parse_learning_plan_response(response.text)
            return learning_plan
        
        except Exception as e:
            logger.error(f"Error generating learning plan: {str(e)}")
            raise
    
    # ===== PROMPT BUILDERS =====
    
    def _build_assessment_prompt(self, skill: str, proficiency: int, assessment_type: str) -> str:
        """Build prompt for assessment generation."""
        
        if assessment_type == "mcq":
            return f"""
            Generate a multiple-choice question assessment for the skill: {skill}
            
            Student's claimed proficiency level: {proficiency}/10
            
            Create 5 multiple-choice questions that:
            1. Match the proficiency level (higher = harder)
            2. Cover different aspects of {skill}
            3. Have clear right/wrong answers
            4. Are suitable for tier 2/3 college students
            
            Return as JSON:
            {{
                "questions": [
                    {{
                        "id": 1,
                        "question": "Question text here?",
                        "options": ["A", "B", "C", "D"],
                        "difficulty": "easy/medium/hard",
                        "topic": "Topic within {skill}"
                    }}
                ],
                "metadata": {{
                    "skill": "{skill}",
                    "type": "mcq",
                    "difficulty_average": "medium",
                    "estimated_time_minutes": 15
                }}
            }}
            """
        
        elif assessment_type == "coding":
            return f"""
            Generate a coding challenge for the skill: {skill}
            
            Student's claimed proficiency level: {proficiency}/10
            
            Create 2-3 coding problems that:
            1. Match the proficiency level
            2. Test practical {skill} knowledge
            3. Are solvable in 30-45 minutes
            4. Include starter code and expected output
            
            Return as JSON:
            {{
                "problems": [
                    {{
                        "id": 1,
                        "title": "Problem title",
                        "description": "Detailed problem description",
                        "starter_code": "code here",
                        "expected_output": "expected result",
                        "difficulty": "easy/medium/hard",
                        "time_limit_minutes": 20
                    }}
                ],
                "metadata": {{
                    "skill": "{skill}",
                    "type": "coding",
                    "language": "relevant language",
                    "estimated_time_minutes": 45
                }}
            }}
            """
        
        elif assessment_type == "case_study":
            return f"""
            Generate a case study assessment for the skill: {skill}
            
            Student's claimed proficiency level: {proficiency}/10
            
            Create 1-2 real-world case studies with 4-5 follow-up questions that:
            1. Test practical application of {skill}
            2. Require analysis and problem-solving
            3. Match proficiency level
            4. Reflect real industry scenarios
            
            Return as JSON:
            {{
                "case_studies": [
                    {{
                        "id": 1,
                        "scenario": "Real-world scenario description",
                        "context": "Background and constraints",
                        "questions": [
                            {{
                                "id": 1,
                                "question": "What would you do?",
                                "question_type": "open-ended"
                            }}
                        ]
                    }}
                ],
                "metadata": {{
                    "skill": "{skill}",
                    "type": "case_study",
                    "estimated_time_minutes": 30
                }}
            }}
            """
    
    def _build_scoring_prompt(self, assessment_type: str, questions: list, responses: list, skill: str) -> str:
        """Build prompt for assessment scoring."""
        
        return f"""
        Score the following {assessment_type} assessment for {skill}.
        
        Assessment Questions:
        {json.dumps(questions, indent=2)}
        
        Student Responses:
        {json.dumps(responses, indent=2)}
        
        Evaluate the responses and provide:
        1. Overall score (1-10 scale)
        2. Score breakdown per question
        3. Identified skill gaps
        4. Reasoning for the score
        5. Key strengths and weaknesses
        
        Return as JSON:
        {{
            "overall_score": 7,
            "score_breakdown": {{"q1": 8, "q2": 7, "q3": 6}},
            "identified_gaps": [
                {{"gap": "Advanced error handling", "priority": "high"}},
                {{"gap": "Performance optimization", "priority": "medium"}}
            ],
            "reasoning": "Student demonstrates solid fundamentals...",
            "strengths": ["Good understanding of basics", "Clear logic"],
            "weaknesses": ["Limited edge case handling", "Performance considerations"],
            "confidence": 0.85
        }}
        """
    
    def _build_learning_plan_prompt(self, skill_gaps: list, proficiency_levels: Dict) -> str:
        """Build prompt for learning plan generation."""
        
        return f"""
        Create a personalized learning plan to address these skill gaps:
        {json.dumps(skill_gaps, indent=2)}
        
        Current proficiency levels:
        {json.dumps(proficiency_levels, indent=2)}
        
        Generate recommendations that include:
        1. Top 3 priority gaps to address
        2. For each gap:
           - Recommended courses/resources
           - Estimated time to upskill
           - Projects to work on
           - Milestones and checkpoints
        3. Overall timeline
        4. Success metrics
        
        Return as JSON:
        {{
            "priority_gaps": [
                {{
                    "gap": "Advanced Python patterns",
                    "priority_score": 9,
                    "recommendations": [
                        {{
                            "type": "course",
                            "title": "Advanced Python Course",
                            "provider": "Udemy",
                            "duration_hours": 20,
                            "url": "link"
                        }},
                        {{
                            "type": "project",
                            "title": "Build a Python framework",
                            "difficulty": "hard",
                            "estimated_hours": 15
                        }}
                    ],
                    "estimated_upskill_weeks": 4
                }}
            ],
            "overall_timeline_weeks": 12,
            "success_metrics": ["Complete 2 courses", "Build 1 project", "Score 8+ on retake"]
        }}
        """
    
    # ===== RESPONSE PARSERS =====
    
    def _parse_assessment_response(self, response_text: str, skill: str, assessment_type: str) -> Dict:
        """Parse Gemini response into assessment structure."""
        try:
            # Extract JSON from response (Gemini may wrap it in markdown)
            json_str = response_text
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            
            assessment_data = json.loads(json_str)
            assessment_data["skill"] = skill
            assessment_data["type"] = assessment_type
            return assessment_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse assessment JSON: {str(e)}")
            # Return default assessment structure on failure
            return {
                "skill": skill,
                "type": assessment_type,
                "error": "Failed to parse response",
                "raw_response": response_text
            }
    
    def _parse_scoring_response(self, response_text: str, skill: str) -> Dict:
        """Parse Gemini response into scoring structure."""
        try:
            json_str = response_text
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            
            scoring_data = json.loads(json_str)
            scoring_data["skill"] = skill
            return scoring_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse scoring JSON: {str(e)}")
            return {
                "skill": skill,
                "overall_score": 5,
                "error": "Failed to parse response",
                "raw_response": response_text
            }
    
    def _parse_learning_plan_response(self, response_text: str) -> Dict:
        """Parse Gemini response into learning plan structure."""
        try:
            json_str = response_text
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            
            learning_plan = json.loads(json_str)
            return learning_plan
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse learning plan JSON: {str(e)}")
            return {
                "error": "Failed to parse response",
                "raw_response": response_text
            }


# Initialize and export client
def get_gemini_client():
    """Get or create Gemini client instance."""
    return GeminiClient()
```

---

## 3. Integration into Flask Endpoints

### Example: Assessment Generation Endpoint

**File: `backend/routes/assessments.py`**

```python
from flask import Blueprint, request, jsonify
from utils.model_client import get_gemini_client
from models import Assessment, Student
from database import db

assessments_bp = Blueprint('assessments', __name__, url_prefix='/assessments')

@assessments_bp.route('/generate', methods=['POST'])
def generate_assessments():
    """Generate 3 assessments for a student's skills."""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        
        # Fetch student and their skills
        student = Student.query.get(student_id)
        if not student:
            return jsonify({"error": "Student not found"}), 404
        
        skills = student.skills  # Assuming relationship exists
        client = get_gemini_client()
        
        generated_assessments = []
        
        # Generate MCQ, Coding, and Case Study for each skill (or top 3 skills)
        for skill in skills[:3]:
            assessment_types = ['mcq', 'coding', 'case_study']
            
            for assess_type in assessment_types:
                # Call Gemini API
                assessment_data = client.generate_assessment(
                    skill=skill.name,
                    proficiency=skill.proficiency_claimed,
                    assessment_type=assess_type
                )
                
                # Save to database
                assessment = Assessment(
                    student_id=student_id,
                    skill_id=skill.id,
                    assessment_type=assess_type,
                    questions=assessment_data.get('questions', []),
                    status='generated'
                )
                db.session.add(assessment)
                generated_assessments.append(assessment.to_dict())
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Assessments generated",
            "assessments": generated_assessments
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@assessments_bp.route('/<int:assessment_id>/submit', methods=['POST'])
def submit_assessment(assessment_id):
    """Submit assessment responses for scoring."""
    try:
        data = request.get_json()
        responses = data.get('responses')
        
        assessment = Assessment.query.get(assessment_id)
        if not assessment:
            return jsonify({"error": "Assessment not found"}), 404
        
        # Save responses
        assessment.responses = responses
        assessment.status = 'submitted'
        db.session.commit()
        
        # Trigger scoring asynchronously (or sync for MVP)
        client = get_gemini_client()
        scoring_result = client.score_assessment(
            assessment_type=assessment.assessment_type,
            questions=assessment.questions,
            responses=responses,
            skill=assessment.skill.name
        )
        
        # Save scoring results
        assessment.score = scoring_result.get('overall_score')
        assessment.scoring_data = scoring_result
        assessment.status = 'scored'
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Assessment scored",
            "score": assessment.score,
            "feedback": scoring_result
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

---

## 4. Environment Configuration

**File: `.env.example`**

```bash
# Gemini API Configuration
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your_secret_key_here

# Database Configuration
DATABASE_URL=sqlite:///skillscan.db
# For production:
# DATABASE_URL=postgresql://user:password@localhost/skillscan

# Frontend
REACT_APP_API_URL=http://localhost:5000

# Logging
LOG_LEVEL=INFO
```

---

## 5. Testing the Integration

### Test Script

**File: `backend/test_model_integration.py`**

```python
from utils.model_client import get_gemini_client
import json

def test_assessment_generation():
    """Test assessment generation."""
    client = get_gemini_client()
    
    print("Testing MCQ Generation...")
    mcq_assessment = client.generate_assessment(
        skill="Python",
        proficiency=5,
        assessment_type="mcq"
    )
    print(json.dumps(mcq_assessment, indent=2))
    
    print("\nTesting Coding Challenge Generation...")
    coding_assessment = client.generate_assessment(
        skill="Python",
        proficiency=5,
        assessment_type="coding"
    )
    print(json.dumps(coding_assessment, indent=2))
    
    print("\nTesting Case Study Generation...")
    case_assessment = client.generate_assessment(
        skill="Python",
        proficiency=5,
        assessment_type="case_study"
    )
    print(json.dumps(case_assessment, indent=2))


def test_scoring():
    """Test assessment scoring."""
    client = get_gemini_client()
    
    sample_responses = [
        {"q1": "A", "q2": "C", "q3": "B"},
    ]
    
    print("Testing Scoring...")
    score_result = client.score_assessment(
        assessment_type="mcq",
        questions=[
            {"id": 1, "question": "What is Python?"},
            {"id": 2, "question": "What is a list?"}
        ],
        responses=sample_responses,
        skill="Python"
    )
    print(json.dumps(score_result, indent=2))


def test_learning_plan():
    """Test learning plan generation."""
    client = get_gemini_client()
    
    print("Testing Learning Plan Generation...")
    learning_plan = client.generate_learning_plan(
        skill_gaps=["Advanced OOP", "Design Patterns", "Testing"],
        proficiency_levels={"Python": 6, "OOP": 5, "Testing": 3}
    )
    print(json.dumps(learning_plan, indent=2))


if __name__ == "__main__":
    test_assessment_generation()
    test_scoring()
    test_learning_plan()
```

**Run the test:**
```bash
cd backend
python test_model_integration.py
```

---

## 6. Alternative Models (Quick Setup)

### Groq Setup (Faster)

```bash
# Install
pip install groq

# Get API Key from https://console.groq.com

# In utils/model_client.py, add GroqClient class:
```

```python
from groq import Groq

class GroqClient:
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.client = Groq(api_key=self.api_key)
        self.model = "mixtral-8x7b-32768"  # Fast and free
    
    def generate_assessment(self, skill: str, proficiency: int, assessment_type: str):
        """Similar to Gemini but uses Groq API."""
        prompt = self._build_assessment_prompt(skill, proficiency, assessment_type)
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return self._parse_assessment_response(message.content[0].text, skill, assessment_type)
```

---

## 7. Error Handling & Fallbacks

```python
# In model_client.py
class ModelClient:
    def __init__(self):
        self.primary_client = GeminiClient()
        self.fallback_client = GroqClient()
    
    def generate_assessment_with_fallback(self, skill, proficiency, assessment_type):
        """Try primary model, fallback to secondary if needed."""
        try:
            return self.primary_client.generate_assessment(skill, proficiency, assessment_type)
        except Exception as e:
            logger.warning(f"Primary model failed: {str(e)}, trying fallback...")
            try:
                return self.fallback_client.generate_assessment(skill, proficiency, assessment_type)
            except Exception as fallback_error:
                logger.error(f"Both models failed: {str(fallback_error)}")
                raise
```

---

## 8. Rate Limiting & Caching

```python
# In utils/cache.py
from functools import lru_cache
import hashlib
import json

@lru_cache(maxsize=128)
def get_cached_assessment(skill: str, proficiency: int, assessment_type: str):
    """Cache assessments to avoid redundant API calls."""
    # Generate cache key
    key = hashlib.md5(f"{skill}_{proficiency}_{assessment_type}".encode()).hexdigest()
    
    # Check if in cache
    cached = redis_client.get(f"assessment:{key}")
    if cached:
        return json.loads(cached)
    
    # Generate new assessment
    client = get_gemini_client()
    assessment = client.generate_assessment(skill, proficiency, assessment_type)
    
    # Cache for 7 days
    redis_client.setex(f"assessment:{key}", 7*24*60*60, json.dumps(assessment))
    
    return assessment
```

---

## 9. Monitoring & Logging

```python
# In config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure logging for model API calls."""
    handler = RotatingFileHandler('logs/model_api.log', maxBytes=10000000, backupCount=5)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger('model_client')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Log all API calls:
# logger.info(f"Generated assessment for skill={skill}, proficiency={proficiency}")
# logger.error(f"API call failed: {error}")
```

---

## 10. Quick Checklist for Setup

- [ ] Get Gemini API key from Google AI Studio
- [ ] Create `.env` file with `GEMINI_API_KEY`
- [ ] Install dependencies: `pip install google-generativeai python-dotenv`
- [ ] Copy `model_client.py` to `backend/utils/`
- [ ] Update Flask routes to use `GeminiClient`
- [ ] Run test script to verify integration
- [ ] Configure error handling and fallbacks
- [ ] Set up logging
- [ ] (Optional) Add caching for frequently used assessments
- [ ] Document API usage for team

---

**Model Integration Guide Version:** 1.0  
**Status:** Ready for Implementation  
**Last Updated:** 2026-04-11
