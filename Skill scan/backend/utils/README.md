# Gemini Model Client - Setup & Usage Guide

## 📋 Overview
This module provides a production-ready wrapper around Google Gemini 2.0 Flash API for SkillScan's AI-powered skill assessment platform.

## 🚀 Quick Start

### 1. Installation

```bash
cd backend
pip install -r utils/requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the backend directory:

```env
GEMINI_API_KEY=AIzaSyB9P_6sQDLh4bZYoFy_Fm3rSySaXdU7grw
```

Or set environment variable:
```bash
export GEMINI_API_KEY="AIzaSyB9P_6sQDLh4bZYoFy_Fm3rSySaXdU7grw"
```

### 3. Run Tests

```bash
# Run comprehensive test suite
python utils/test_model_integration.py

# Or import and use directly
from utils.model_client import GeminiClient

client = GeminiClient()
assessment = client.generate_assessment(
    skill="Python",
    proficiency=5,
    difficulty="medium",
    assessment_type="mcq"
)
```

## 📦 Module Structure

### `model_client.py` - Core Module

#### Main Class: `GeminiClient`

**Initialization:**
```python
from utils.model_client import GeminiClient

# Initialize with explicit API key
client = GeminiClient(api_key="your-api-key")

# Or load from environment
client = GeminiClient()
```

**Methods:**

##### 1. Generate Assessment
```python
assessment = client.generate_assessment(
    skill: str,              # e.g., "Python", "React", "SQL"
    proficiency: int,        # 1-10 scale
    difficulty: str,         # "easy", "medium", "hard"
    assessment_type: str     # "mcq", "coding", "case_study"
) -> dict
```

**Example Usage:**
```python
# Generate MCQ assessment
mcq = client.generate_assessment(
    skill="Python",
    proficiency=5,
    difficulty="medium",
    assessment_type="mcq"
)
# Returns: {
#   "questions": [...],
#   "metadata": {"skill": "Python", "type": "mcq", ...}
# }

# Generate coding challenge
coding = client.generate_assessment(
    skill="JavaScript",
    proficiency=6,
    difficulty="hard",
    assessment_type="coding"
)
# Returns: {
#   "problems": [...],
#   "metadata": {...}
# }

# Generate case study
case_study = client.generate_assessment(
    skill="System Design",
    proficiency=8,
    difficulty="hard",
    assessment_type="case_study"
)
# Returns: {
#   "case_studies": [...],
#   "metadata": {...}
# }
```

##### 2. Score Assessment
```python
scoring = client.score_assessment(
    assessment_type: str,    # "mcq", "coding", "case_study"
    questions: list,         # Original assessment questions
    responses: list,         # Student's responses
    skill: str              # Skill being assessed
) -> dict
```

**Example Usage:**
```python
questions = [
    {
        "id": 1,
        "question": "What is 2**3?",
        "options": ["A) 6", "B) 8", "C) 9", "D) 12"],
        "correct_answer": "B"
    }
]

responses = [
    {"question_id": 1, "selected_answer": "B"}
]

score = client.score_assessment(
    assessment_type="mcq",
    questions=questions,
    responses=responses,
    skill="Python"
)
# Returns: {
#   "overall_score": 9,
#   "score_breakdown": {"q1": 9},
#   "identified_gaps": [],
#   "confidence": 0.95,
#   ...
# }
```

##### 3. Generate Learning Plan
```python
learning_plan = client.generate_learning_plan(
    skill_gaps: list,        # List of gaps with metadata
    user_proficiency: dict,  # Current skill levels
    user_type: str          # "MBA_Analytics" or "BCA"
) -> dict
```

**Example Usage:**
```python
gaps = [
    {
        "gap": "Advanced SQL optimization",
        "severity": "high",
        "priority_score": 9
    },
    {
        "gap": "Python data manipulation",
        "severity": "medium",
        "priority_score": 7
    }
]

proficiency = {
    "SQL": 6,
    "Python": 5,
    "Excel": 8
}

plan = client.generate_learning_plan(
    skill_gaps=gaps,
    user_proficiency=proficiency,
    user_type="MBA_Analytics"
)
# Returns: {
#   "priority_gaps": [...],
#   "overall_timeline_weeks": 8,
#   "success_metrics": [...]
# }
```

## 📋 Response Structures

### MCQ Assessment Response
```json
{
  "questions": [
    {
      "id": 1,
      "question": "What is a list comprehension?",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_answer": "B",
      "explanation": "...",
      "difficulty": "medium",
      "topic": "Python Basics"
    }
  ],
  "metadata": {
    "skill": "Python",
    "type": "mcq",
    "difficulty": "medium",
    "estimated_time_minutes": 15,
    "total_questions": 5
  }
}
```

### Coding Challenge Response
```json
{
  "problems": [
    {
      "id": 1,
      "title": "Two Sum",
      "description": "...",
      "difficulty": "medium",
      "starter_code": "def solve(arr, target):\n    pass",
      "example_input": "[2, 7, 11, 15], target=9",
      "example_output": "[0, 1]",
      "edge_cases": ["Empty array", "No solution exists"],
      "estimated_time_minutes": 25
    }
  ],
  "metadata": {
    "skill": "Python",
    "type": "coding",
    "difficulty": "medium",
    "estimated_time_minutes": 50,
    "total_problems": 2
  }
}
```

### Scoring Response
```json
{
  "overall_score": 7,
  "score_breakdown": {
    "q1": 8,
    "q2": 7,
    "q3": 6
  },
  "identified_gaps": [
    {
      "gap": "Advanced Python concepts",
      "severity": "high",
      "impact": "Affects complex problem solving",
      "priority_score": 8
    }
  ],
  "strengths": ["Good fundamentals", "Problem solving"],
  "weaknesses": ["Edge case handling", "Optimization"],
  "reasoning": "Student shows good understanding...",
  "confidence": 0.85,
  "next_difficulty_recommended": "medium"
}
```

### Learning Plan Response
```json
{
  "priority_gaps": [
    {
      "gap": "Advanced SQL",
      "severity": "high",
      "estimated_hours": 20,
      "priority_score": 9,
      "recommendations": [
        {
          "type": "course",
          "title": "Advanced SQL Masterclass",
          "provider": "Udemy",
          "duration_hours": 15,
          "difficulty": "advanced",
          "url": "https://...",
          "why_recommended": "..."
        }
      ]
    }
  ],
  "overall_timeline_weeks": 8,
  "success_metrics": [
    "Complete all courses",
    "Build 2 projects",
    "Score 8+ on re-assessment"
  ]
}
```

## 🔧 Helper Functions

### Parse JSON Response
```python
from utils.model_client import _parse_json_response

json_data = _parse_json_response(gemini_response_text)
```

### Validate Assessment
```python
from utils.model_client import validate_assessment_response

validate_assessment_response(assessment_dict, "mcq")  # Raises ValueError if invalid
```

### Validate Scoring
```python
from utils.model_client import validate_scoring_response

validate_scoring_response(score_dict)  # Raises ValueError if invalid
```

## 🛡️ Error Handling

The client automatically handles:
- API connection failures (3 retries with exponential backoff)
- Malformed JSON responses
- Rate limiting
- Invalid response structures

**Example Error Handling:**
```python
try:
    assessment = client.generate_assessment(
        skill="Python",
        proficiency=5,
        difficulty="medium",
        assessment_type="mcq"
    )
except ValueError as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"API error (will retry): {e}")
```

## 📊 Logging

All operations are logged to `gemini_client` logger:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Check logs
logger = logging.getLogger('gemini_client')
```

**Log Output Example:**
```
2026-04-14 23:32:00 - gemini_client - INFO - ✓ Gemini API client initialized successfully
2026-04-14 23:32:01 - gemini_client - INFO - Generating mcq assessment for Python (proficiency: 5/10, difficulty: medium)
2026-04-14 23:32:05 - gemini_client - INFO - ✓ Successfully generated mcq assessment with 5 items
```

## 🧪 Testing

### Run Full Test Suite
```bash
python utils/test_model_integration.py
```

### Test Individual Functions
```python
from utils.model_client import GeminiClient

client = GeminiClient()

# Test MCQ
assessment = client.generate_assessment(
    skill="Python",
    proficiency=5,
    difficulty="easy",
    assessment_type="mcq"
)
print(f"✓ MCQ: {len(assessment['questions'])} questions")

# Test Coding
assessment = client.generate_assessment(
    skill="Python",
    proficiency=6,
    difficulty="medium",
    assessment_type="coding"
)
print(f"✓ Coding: {len(assessment['problems'])} problems")

# Test Case Study
assessment = client.generate_assessment(
    skill="SQL",
    proficiency=7,
    difficulty="hard",
    assessment_type="case_study"
)
print(f"✓ Case Study: {len(assessment['case_studies'])} studies")
```

## 📈 Performance Notes

- Average API response time: 3-10 seconds per assessment
- Rate limit: ~500 requests per minute
- Retry strategy: Exponential backoff (1s, 2s, 4s)
- Recommended batch size: 10 assessments per minute

## 🔐 Security

- API key should never be committed to git
- Always use environment variables or .env files
- Use `python-dotenv` to load `.env` file safely

## 📚 Assessment Types Reference

### MCQ (Multiple Choice Questions)
- **Questions:** 5 per assessment
- **Time:** 15 minutes
- **Scoring:** Automatic validation against correct answers
- **Best for:** Quick skill validation, conceptual understanding

### Coding Challenges
- **Problems:** 2 per assessment
- **Time:** 45 minutes total
- **Scoring:** Code execution validation, efficiency analysis
- **Best for:** Practical coding skills, algorithm understanding

### Case Studies
- **Scenarios:** 1-2 per assessment
- **Questions:** 4-5 follow-up questions per scenario
- **Time:** 30-45 minutes
- **Scoring:** Analysis depth, reasoning quality
- **Best for:** Real-world application, strategic thinking

## 💡 Best Practices

1. **Cache Assessments:** Store generated assessments to reduce API calls
2. **Batch Processing:** Generate multiple assessments in sequence
3. **Error Recovery:** Always use try-except blocks around API calls
4. **Logging:** Enable logging for production debugging
5. **Rate Limiting:** Implement request throttling for high traffic

## 🐛 Troubleshooting

### "GEMINI_API_KEY not found"
- Check `.env` file exists in backend directory
- Verify environment variable is set: `echo $GEMINI_API_KEY`
- API key should start with `AIzaSy...`

### "Failed to parse JSON"
- Check Gemini response doesn't contain code block markers
- Verify JSON structure matches expected format
- Check for special characters in skill names

### "Rate limit exceeded"
- Reduce request frequency
- Implement exponential backoff (already built-in)
- Batch requests efficiently

## 📞 Support

For issues or questions:
1. Check logs: `logging.getLogger('gemini_client')`
2. Run test suite: `python utils/test_model_integration.py`
3. Verify API key and network connection

---

**Last Updated:** 2026-04-14
**Version:** 1.0.0
**Status:** Production Ready ✅
