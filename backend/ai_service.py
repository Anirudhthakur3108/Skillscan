"""
Mistral AI Service — Central AI integration layer.

Model Strategy (cost-aware):
  - mistral-small-latest  → Question generation (high volume, fast & cheap)
  - mistral-medium-latest → Scoring + gap analysis (deeper reasoning)
  - mistral-large-latest  → Learning plan generation (highest quality, used once per gap)
"""
import os
import json
import re
from mistralai.client import MistralClient
from schemas import AIAssessmentResponse, AIScoreResponse, AILearningPlanResponse

_api_key = os.getenv("MISTRAL_API_KEY", "")
client = MistralClient(api_key=_api_key)

# ─── Model Tier Selection ──────────────────────────────────────────────────────
MODELS = {
    "generation": "mistral-small-latest",   # Fast, cheap — question generation
    "scoring":    "mistral-medium-latest",  # Balanced — scoring & feedback
    "planning":   "mistral-large-latest",   # Most capable — learning plans
}


def _extract_json(text: str) -> dict:
    """Strip markdown code fences and parse raw JSON from LLM response."""
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        text = match.group(1)
    return json.loads(text.strip())


def _call_mistral(model_key: str, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
    """Call Mistral with the appropriate model tier. Returns raw text. Fallback to mock data if API key is missing or fails."""
    if not _api_key or _api_key == "your_mistral_api_key_here":
        return _get_mock_response(model_key, user_prompt)
        
    try:
        model = MODELS[model_key]
        response = client.chat(
          messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
          ],
          model=model,
          temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Mistral API failed: {e}. Falling back to mock data.")
        return _get_mock_response(model_key, user_prompt)

def _get_mock_response(model_key: str, user_prompt: str) -> str:
    import re
    # Extract skill name from prompt if possible
    skill_name = "Skill"
    match = re.search(r'\*\*(.*?)\*\*', user_prompt)
    if match:
        skill_name = match.group(1)
        
    if model_key == "generation":
        return f'''{{
          "skill_name": "{skill_name}",
          "mcq": [
            {{
              "id": "mcq_1",
              "question": "What is the primary benefit of {skill_name}?",
              "options": [
                {{"id": "A", "text": "Increased performance"}},
                {{"id": "B", "text": "Reduced security"}},
                {{"id": "C", "text": "Higher costs"}},
                {{"id": "D", "text": "Lower maintainability"}}
              ],
              "correct_option_id": "A",
              "explanation": "{skill_name} is known for improving overall system capabilities.",
              "difficulty": 5
            }},
            {{
              "id": "mcq_2",
              "question": "Which of the following is a core concept in {skill_name}?",
              "options": [
                {{"id": "A", "text": "Encapsulation"}},
                {{"id": "B", "text": "Randomness"}},
                {{"id": "C", "text": "Stagnation"}},
                {{"id": "D", "text": "Redundancy"}}
              ],
              "correct_option_id": "A",
              "explanation": "Core principles often include structured data management.",
              "difficulty": 6
            }}
          ],
          "coding": [],
          "case_study": []
        }}'''
    elif model_key == "scoring":
        return f'''{{
          "skill_name": "{skill_name}",
          "overall_score": 7,
          "questions": [
            {{
              "question_id": "mcq_1",
              "score": 10,
              "max_score": 10,
              "feedback": "Correctly identified the primary benefit."
            }}
          ],
          "strengths": ["Good fundamental knowledge", "Understands core concepts"],
          "weaknesses": ["Advanced optimization", "Edge case handling"],
          "gap_identified": true,
          "reasoning": "Student showed proficiency in basics but needs work on advanced topics."
        }}'''
    else: # planning
        return f'''{{
          "skill_name": "{skill_name}",
          "total_estimated_hours": 20,
          "summary": "A structured plan to master advanced concepts.",
          "phases": [
            {{
              "phase_number": 1,
              "title": "Advanced {skill_name} Concepts",
              "description": "Deep dive into performance and edge cases.",
              "duration_weeks": 2,
              "priority": "High",
              "resources": [
                {{
                  "title": "Advanced {skill_name} Masterclass",
                  "url": "https://example.com/course",
                  "type": "course",
                  "estimated_hours": 10,
                  "platform": "Example Academy"
                }}
              ],
              "milestones": ["Complete masterclass", "Build sample project"]
            }}
          ]
        }}'''


# ─── 1. Assessment Generation ─────────────────────────────────────────────────

def generate_assessment(skill_name: str, claimed_proficiency: int) -> AIAssessmentResponse:
    """
    Generate a skill assessment using Mistral Small (cheap + fast).
    Returns a strictly validated AIAssessmentResponse.
    """
    system_prompt = (
        "You are an expert technical skills assessor. "
        "You MUST respond with valid JSON ONLY — no preamble, no explanation outside the JSON object. "
        "Strictly follow the schema provided in the user message."
    )
    user_prompt = f"""Generate a comprehensive skill assessment for: **{skill_name}**
The student claims a proficiency level of {claimed_proficiency}/10.

Return ONLY a JSON object matching this exact schema:
{{
  "skill_name": "{skill_name}",
  "mcq": [
    {{
      "id": "mcq_1",
      "question": "...",
      "options": [
        {{"id": "A", "text": "..."}},
        {{"id": "B", "text": "..."}},
        {{"id": "C", "text": "..."}},
        {{"id": "D", "text": "..."}}
      ],
      "correct_option_id": "A",
      "explanation": "...",
      "difficulty": 3
    }}
  ],
  "coding": [
    {{
      "id": "code_1",
      "problem_statement": "...",
      "constraints": "...",
      "example_input": "...",
      "example_output": "...",
      "hints": ["hint 1", "hint 2"]
    }}
  ],
  "case_study": [
    {{
      "id": "case_1",
      "scenario": "...",
      "question": "...",
      "evaluation_criteria": ["criteria 1", "criteria 2"]
    }}
  ]
}}

Generate exactly 5 MCQ questions, 1 coding challenge, and 1 case study.
Calibrate difficulty to proficiency {claimed_proficiency}/10 (1=beginner, 10=expert).
"""
    raw = _call_mistral("generation", system_prompt, user_prompt)
    try:
        data = _extract_json(raw)
    except json.JSONDecodeError:
        # Fallback: try parsing the raw string directly
        data = json.loads(raw)
    return AIAssessmentResponse.model_validate(data)


# ─── 2. Assessment Scoring ────────────────────────────────────────────────────

def score_assessment(skill_name: str, questions: dict, student_answers: dict) -> AIScoreResponse:
    """
    Score a completed assessment using Mistral Medium.
    Returns a strictly validated AIScoreResponse.
    """
    system_prompt = (
        "You are an expert technical skills evaluator. "
        "Evaluate student answers carefully and fairly. "
        "You MUST respond with valid JSON ONLY."
    )
    user_prompt = f"""Score this skill assessment for: **{skill_name}**

Questions:
{json.dumps(questions, indent=2)}

Student's Answers:
{json.dumps(student_answers, indent=2)}

Return ONLY a JSON object with this exact schema:
{{
  "skill_name": "{skill_name}",
  "overall_score": <integer 0-10>,
  "questions": [
    {{
      "question_id": "mcq_1",
      "score": <integer 0-10>,
      "max_score": 10,
      "feedback": "..."
    }}
  ],
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "gap_identified": <true or false>,
  "reasoning": "..."
}}

Set gap_identified to true if overall_score < 6.
Be specific and constructive in feedback.
"""
    raw = _call_mistral("scoring", system_prompt, user_prompt)
    try:
        data = _extract_json(raw)
    except json.JSONDecodeError:
        data = json.loads(raw)
    return AIScoreResponse.model_validate(data)


# ─── 3. Learning Plan Generation ─────────────────────────────────────────────

def generate_learning_plan(skill_name: str, score: int, weaknesses: list) -> AILearningPlanResponse:
    """
    Generate a personalized learning plan using Mistral Large (highest quality).
    Returns a strictly validated AILearningPlanResponse.
    """
    system_prompt = (
        "You are an expert learning architect and career coach for tech students. "
        "Create actionable, specific, and realistic learning plans with real resources. "
        "You MUST respond with valid JSON ONLY."
    )
    weaknesses_str = "\n".join(f"- {w}" for w in weaknesses) if weaknesses else "- General skill gaps"
    user_prompt = f"""Create a personalized learning plan for a student improving: **{skill_name}**
Assessment score: {score}/10

Identified weaknesses:
{weaknesses_str}

Return ONLY a JSON object with this exact schema:
{{
  "skill_name": "{skill_name}",
  "total_estimated_hours": <integer>,
  "summary": "...",
  "phases": [
    {{
      "phase_number": 1,
      "title": "...",
      "description": "...",
      "duration_weeks": 2,
      "priority": "High",
      "resources": [
        {{
          "title": "Specific Course or Resource Title",
          "url": "https://actual-url.com",
          "type": "course",
          "estimated_hours": 10,
          "platform": "Coursera"
        }}
      ],
      "milestones": ["milestone 1", "milestone 2"]
    }}
  ]
}}

Include exactly 3 phases. Phase 1: High priority (foundational gaps). Phase 2: Medium (intermediate). Phase 3: Low (advanced/maintenance).
Use real, specific, preferably free or well-known resources.
"""
    raw = _call_mistral("planning", system_prompt, user_prompt)
    try:
        data = _extract_json(raw)
    except json.JSONDecodeError:
        data = json.loads(raw)
    return AILearningPlanResponse.model_validate(data)
