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
import ast
import os as _os
import concurrent.futures
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any, Callable, Union
from mistralai.client import MistralClient
from schemas import (
    AIAssessmentResponse, 
    AIScoreResponse, 
    AILearningPlanResponse,
    AILearningPlanResponseEnhanced,
    AIGapAnalysisResponse
)
load_dotenv()

_api_key = os.getenv("MISTRAL_API_KEY", "")
client = MistralClient(api_key=_api_key)

# ─── Model Tier Selection ──────────────────────────────────────────────────────
MODELS = {
    "generation": "mistral-small-latest",   # Fast, cheap — question generation
    "scoring":    "mistral-small-latest",   # Fast for MVP
    "planning":   "mistral-small-latest",   # Fast for MVP
}


def _extract_json(text: str) -> dict:
    """Strip markdown code fences and parse raw JSON from LLM response."""
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        text = match.group(1)
    return json.loads(text.strip())


def _safe_parse_json(raw: str, *, fallback_getter: Optional[Callable[[], Any]] = None, skill_name: Optional[str] = None, claimed_proficiency: int = 5, num_questions: int = 5, model_key: Optional[str] = None) -> Optional[Union[dict, list]]:
    """Attempt to parse JSON from a possibly-malformed LLM response.

    Strategies tried (in order):
    - `_extract_json` (handles ```json fences)
    - `json.loads` on raw
    - extract first balanced {...} substring and `json.loads`
    - remove trailing commas and `json.loads`
    - `ast.literal_eval` as a last-ditch tolerant parser
    - if provided, call `fallback_getter()` to obtain a safe response and parse that

    Returns a Python object (dict/list) or None if parsing ultimately fails.
    """
    # 1) strip fences and try
    try:
        return _extract_json(raw)
    except Exception:
        pass

    # 2) direct json.loads
    try:
        return json.loads(raw)
    except Exception:
        pass

    # 3) try to find a balanced JSON object in the text
    try:
        start = raw.find('{')
        if start != -1:
            stack = 0
            end = -1
            for i in range(start, len(raw)):
                ch = raw[i]
                if ch == '{':
                    stack += 1
                elif ch == '}':
                    stack -= 1
                if stack == 0:
                    end = i
                    break
            if end != -1:
                candidate = raw[start:end+1]
                try:
                    return json.loads(candidate)
                except Exception:
                    pass
    except Exception:
        pass

    # 4) remove trailing commas (common LLM issue)
    try:
        candidate = re.sub(r',\s*([}\]])', r'\1', raw)
        return json.loads(candidate)
    except Exception:
        pass

    # 5) ast.literal_eval as tolerant fallback (handles single quotes etc.)
    try:
        obj = ast.literal_eval(raw)
        if isinstance(obj, (dict, list)):
            return obj
    except Exception:
        pass

    # 6) use provided fallback_getter to obtain safe content then parse
    if fallback_getter:
        try:
            fb = fallback_getter()
            if isinstance(fb, (dict, list)):
                return fb
            if isinstance(fb, str):
                try:
                    return _safe_parse_json(fb, fallback_getter=None)
                except Exception:
                    pass
        except Exception:
            pass

    # Give up — return None to let caller handle fallback
    return None


def _call_mistral(model_key: str, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
    """Call Mistral with the appropriate model tier. Returns raw text. Fallback to mock data if API key is missing or fails."""
    if not _api_key or _api_key == "your_mistral_api_key_here":
        return _get_mock_response(model_key, user_prompt)

    # Use a short, configurable timeout to avoid blocking gunicorn workers.
    timeout_seconds = int(_os.getenv("MISTRAL_TIMEOUT_SECONDS", "8"))

    def _do_chat():
        model = MODELS[model_key]
        return client.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            model=model,
            temperature=temperature,
        )

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(_do_chat)
            try:
                response = fut.result(timeout=timeout_seconds)
            except concurrent.futures.TimeoutError:
                fut.cancel()
                print(f"Mistral API timed out after {timeout_seconds}s; falling back to mock data.")
                return _get_mock_response(model_key, user_prompt)

        # success
        try:
            return response.choices[0].message.content
        except Exception as e:
            print(f"Mistral response parsing failed: {e}. Falling back to mock data.")
            return _get_mock_response(model_key, user_prompt)
    except Exception as e:
        print(f"Mistral API failed: {e}. Falling back to mock data.")
        return _get_mock_response(model_key, user_prompt)


def _coerce_int(value, default: int) -> int:
    try:
      return int(value)
    except (TypeError, ValueError):
      return default


def _difficulty_from_proficiency(proficiency: int, offset: int = 0) -> int:
    base = max(1, min(10, _coerce_int(proficiency, 5)))
    return max(1, min(10, base + offset))


def _build_fallback_mcq_templates(skill_name: str, claimed_proficiency: int) -> List[Dict]:
    return [
      {
        "question": f"Which scenario best demonstrates elasticity in {skill_name}?",
        "options": [
          {"id": "A", "text": "Automatically scaling resources up and down based on demand"},
          {"id": "B", "text": "Keeping a single server online all year"},
          {"id": "C", "text": "Deploying code without version control"},
          {"id": "D", "text": "Storing all logs in local text files"},
        ],
        "correct_option_id": "A",
        "explanation": "Elastic systems adjust resources dynamically to match workload.",
        "difficulty": _difficulty_from_proficiency(claimed_proficiency, -1),
      },
      {
        "question": f"What is the strongest reason to use monitoring and observability in {skill_name}?",
        "options": [
          {"id": "A", "text": "To diagnose failures quickly and improve reliability"},
          {"id": "B", "text": "To remove all security controls"},
          {"id": "C", "text": "To avoid writing tests"},
          {"id": "D", "text": "To prevent CI/CD usage"},
        ],
        "correct_option_id": "A",
        "explanation": "Observability shortens incident resolution and improves service quality.",
        "difficulty": _difficulty_from_proficiency(claimed_proficiency),
      },
      {
        "question": f"In {skill_name}, why is least-privilege access considered a best practice?",
        "options": [
          {"id": "A", "text": "It limits blast radius if credentials are compromised"},
          {"id": "B", "text": "It guarantees zero downtime"},
          {"id": "C", "text": "It removes the need for encryption"},
          {"id": "D", "text": "It eliminates software bugs"},
        ],
        "correct_option_id": "A",
        "explanation": "Least privilege minimizes exposure by restricting unnecessary permissions.",
        "difficulty": _difficulty_from_proficiency(claimed_proficiency),
      },
      {
        "question": f"Which choice most directly improves cost control in {skill_name} workloads?",
        "options": [
          {"id": "A", "text": "Tagging resources and enforcing budget alerts"},
          {"id": "B", "text": "Running all instances at maximum size"},
          {"id": "C", "text": "Ignoring idle resources"},
          {"id": "D", "text": "Disabling autoscaling"},
        ],
        "correct_option_id": "A",
        "explanation": "Tagging and budget controls make spend visible and easier to optimize.",
        "difficulty": _difficulty_from_proficiency(claimed_proficiency, 1),
      },
      {
        "question": f"What is the main benefit of immutable deployments in {skill_name}?",
        "options": [
          {"id": "A", "text": "Consistent, repeatable releases with easier rollbacks"},
          {"id": "B", "text": "No need for testing"},
          {"id": "C", "text": "Guaranteed perfect performance"},
          {"id": "D", "text": "Manual patching on production servers"},
        ],
        "correct_option_id": "A",
        "explanation": "Immutable artifacts reduce configuration drift and deployment variance.",
        "difficulty": _difficulty_from_proficiency(claimed_proficiency, 1),
      },
      {
        "question": f"Why are redundancy and multi-zone design important in {skill_name}?",
        "options": [
          {"id": "A", "text": "They increase resilience against localized failures"},
          {"id": "B", "text": "They remove all network latency"},
          {"id": "C", "text": "They replace application monitoring"},
          {"id": "D", "text": "They avoid backup requirements"},
        ],
        "correct_option_id": "A",
        "explanation": "Redundancy prevents single points of failure and improves availability.",
        "difficulty": _difficulty_from_proficiency(claimed_proficiency, 1),
      },
      {
        "question": f"Which design decision best supports secure data handling in {skill_name}?",
        "options": [
          {"id": "A", "text": "Encrypting data in transit and at rest"},
          {"id": "B", "text": "Sharing credentials across teams"},
          {"id": "C", "text": "Disabling audit logs"},
          {"id": "D", "text": "Hardcoding secrets in source code"},
        ],
        "correct_option_id": "A",
        "explanation": "Encryption protects confidentiality across storage and communication paths.",
        "difficulty": _difficulty_from_proficiency(claimed_proficiency, 2),
      },
      {
        "question": f"What is a key advantage of infrastructure as code in {skill_name}?",
        "options": [
          {"id": "A", "text": "Versioned, reviewable, and reproducible infrastructure changes"},
          {"id": "B", "text": "No need for access controls"},
          {"id": "C", "text": "Permanent lock-in to one deployment"},
          {"id": "D", "text": "Manual drift as a preferred strategy"},
        ],
        "correct_option_id": "A",
        "explanation": "IaC brings software engineering discipline to infrastructure lifecycle.",
        "difficulty": _difficulty_from_proficiency(claimed_proficiency, 2),
      },
      {
        "question": f"For {skill_name}, which metric is most useful for service reliability tracking?",
        "options": [
          {"id": "A", "text": "Error rate and latency percentiles over time"},
          {"id": "B", "text": "Number of desktop wallpapers"},
          {"id": "C", "text": "Count of local screenshots"},
          {"id": "D", "text": "Total email signatures"},
        ],
        "correct_option_id": "A",
        "explanation": "Reliability is measured via user-impacting indicators like errors and latency.",
        "difficulty": _difficulty_from_proficiency(claimed_proficiency, 2),
      },
      {
        "question": f"What is the most effective way to reduce deployment risk in {skill_name}?",
        "options": [
          {"id": "A", "text": "Use canary or blue-green rollout strategies"},
          {"id": "B", "text": "Deploy all changes Friday evening"},
          {"id": "C", "text": "Skip rollback planning"},
          {"id": "D", "text": "Disable health checks"},
        ],
        "correct_option_id": "A",
        "explanation": "Progressive rollouts reduce blast radius and support safe reversions.",
        "difficulty": _difficulty_from_proficiency(claimed_proficiency, 3),
      },
    ]


def _fallback_assessment_payload(skill_name: str, claimed_proficiency: int, num_questions: int) -> Dict:
    templates = _build_fallback_mcq_templates(skill_name, claimed_proficiency)
    mcq_items: List[Dict] = []
    for idx in range(num_questions):
      template = dict(templates[idx % len(templates)])
      template["id"] = f"mcq_{idx + 1}"
      if idx >= len(templates):
        template["question"] = f"{template['question']} (variant {idx + 1})"
        template["difficulty"] = _difficulty_from_proficiency(claimed_proficiency, idx // len(templates))
      mcq_items.append(template)

    return {
      "skill_name": skill_name,
      "mcq": mcq_items,
      "coding": [],
      "case_study": [],
    }


def build_fallback_assessment_payload(skill_name: str, claimed_proficiency: int, num_questions: int) -> Dict:
    """Public helper for a guaranteed non-empty assessment payload."""
    return _fallback_assessment_payload(skill_name, claimed_proficiency, num_questions)


def _normalize_assessment_payload(data: dict, skill_name: str, claimed_proficiency: int, num_questions: int) -> dict:
    # Deduplicate questions by normalized text and keep the first valid occurrence.
    deduped_mcq: List[Dict] = []
    seen_questions = set()
    for item in data.get("mcq", []) if isinstance(data.get("mcq", []), list) else []:
      if not isinstance(item, dict):
        continue
      question_text = str(item.get("question", "")).strip()
      if not question_text:
        continue
      key = question_text.lower()
      if key in seen_questions:
        continue
      seen_questions.add(key)

      options = item.get("options", []) if isinstance(item.get("options", []), list) else []
      valid_options = [
        opt for opt in options
        if isinstance(opt, dict) and opt.get("id") and opt.get("text")
      ]
      if len(valid_options) < 4:
        valid_options = [
          {"id": "A", "text": "Option A"},
          {"id": "B", "text": "Option B"},
          {"id": "C", "text": "Option C"},
          {"id": "D", "text": "Option D"},
        ]

      correct_option_id = str(item.get("correct_option_id", "A")).strip() or "A"
      if correct_option_id not in {opt["id"] for opt in valid_options}:
        correct_option_id = "A"

      deduped_mcq.append({
        "id": item.get("id") or f"mcq_{len(deduped_mcq) + 1}",
        "question": question_text,
        "options": valid_options,
        "correct_option_id": correct_option_id,
        "explanation": str(item.get("explanation", "Generated answer explanation.")).strip(),
        "difficulty": _difficulty_from_proficiency(item.get("difficulty", claimed_proficiency)),
      })

    if len(deduped_mcq) < num_questions:
      fallback = _fallback_assessment_payload(skill_name, claimed_proficiency, num_questions)
      for extra in fallback["mcq"]:
        if len(deduped_mcq) >= num_questions:
          break
        key = str(extra.get("question", "")).strip().lower()
        if key in seen_questions:
          continue
        seen_questions.add(key)
        deduped_mcq.append(extra)

    deduped_mcq = deduped_mcq[:num_questions]
    for idx, item in enumerate(deduped_mcq, start=1):
      item["id"] = f"mcq_{idx}"

    return {
      "skill_name": str(data.get("skill_name") or skill_name),
      "mcq": deduped_mcq,
      "coding": data.get("coding", []) if isinstance(data.get("coding", []), list) else [],
      "case_study": data.get("case_study", []) if isinstance(data.get("case_study", []), list) else [],
    }

def _get_mock_response(model_key: str, user_prompt: str) -> str:
    # Extract skill name from prompt if possible
    skill_name = "Skill"
    match = re.search(r'\*\*(.*?)\*\*', user_prompt)
    if match:
        skill_name = match.group(1)

    proficiency_match = re.search(r'proficiency level of\s*(\d+)\/10', user_prompt, flags=re.IGNORECASE)
    claimed_proficiency = _coerce_int(proficiency_match.group(1), 5) if proficiency_match else 5

    question_count_match = re.search(r'Generate exactly\s*(\d+)\s*MCQ', user_prompt, flags=re.IGNORECASE)
    num_questions = _coerce_int(question_count_match.group(1), 5) if question_count_match else 5
        
    if model_key == "generation":
      payload = _fallback_assessment_payload(skill_name, claimed_proficiency, num_questions)
      return json.dumps(payload)
    elif model_key == "scoring":
        # Gap-analysis calls share the scoring model tier but require a different schema.
        if "Analyze skill gaps for" in user_prompt:
            return f'''{{
              "identified_gaps": [
                {{
                  "gap_name": "Core Concepts",
                  "severity": "medium",
                  "reason": "Inconsistent accuracy on foundational questions"
                }},
                {{
                  "gap_name": "Applied Problem Solving",
                  "severity": "high",
                  "reason": "Needs stronger reasoning on scenario-based items"
                }}
              ],
              "focus_areas": ["Fundamentals", "Architecture Patterns", "Hands-on Practice"],
              "improvement_potential": 7
            }}'''
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
        # Enhanced learning-plan calls require total_weeks + phase resource arrays.
        if '"total_weeks"' in user_prompt or "youtube_resources" in user_prompt:
            return f'''{{
              "skill_name": "{skill_name}",
              "total_weeks": 6,
              "summary": "A focused plan to close priority gaps and build production confidence.",
              "phases": [
                {{
                  "phase_number": 1,
                  "title": "Rebuild Foundations",
                  "description": "Reinforce core concepts and terminology.",
                  "timeline_weeks": 2,
                  "focus_gaps": ["Core Concepts"],
                  "youtube_resources": [
                    {{
                      "title": "{skill_name} Fundamentals Crash Course",
                      "url": "https://www.youtube.com/results?search_query={skill_name}+fundamentals+course",
                      "duration_minutes": 45
                    }}
                  ],
                  "website_resources": [
                    {{
                      "title": "{skill_name} Documentation and Courses",
                      "url": "https://www.coursera.org/search?query={skill_name}+documentation",
                      "category": "documentation",
                      "estimated_hours": 3
                    }}
                  ],
                  "milestones": ["Complete fundamentals notes", "Pass 20 practice questions"]
                }},
                {{
                  "phase_number": 2,
                  "title": "Applied Practice",
                  "description": "Solve practical tasks and scenario questions.",
                  "timeline_weeks": 2,
                  "focus_gaps": ["Applied Problem Solving"],
                  "youtube_resources": [
                    {{
                      "title": "{skill_name} Real-world Walkthrough",
                      "url": "https://www.youtube.com/results?search_query={skill_name}+real+world+project",
                      "duration_minutes": 60
                    }}
                  ],
                  "website_resources": [
                    {{
                      "title": "Hands-on Practice Set",
                      "url": "https://www.geeksforgeeks.org/?s={skill_name}+practice",
                      "category": "practice",
                      "estimated_hours": 4
                    }}
                  ],
                  "milestones": ["Finish 3 labs", "Write one mini-project summary"]
                }},
                {{
                  "phase_number": 3,
                  "title": "Validation and Retention",
                  "description": "Consolidate knowledge and prepare for reassessment.",
                  "timeline_weeks": 2,
                  "focus_gaps": ["Speed and Accuracy"],
                  "youtube_resources": [
                    {{
                      "title": "{skill_name} Interview/Assessment Prep",
                      "url": "https://www.youtube.com/results?search_query={skill_name}+interview+prep",
                      "duration_minutes": 35
                    }}
                  ],
                  "website_resources": [
                    {{
                      "title": "Revision Checklist",
                      "url": "https://www.freecodecamp.org/news/search/?query={skill_name}+checklist",
                      "category": "tutorial",
                      "estimated_hours": 2
                    }}
                  ],
                  "milestones": ["Mock assessment attempt", "Document final weak areas"]
                }}
              ]
            }}'''
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
                  "url": "https://www.coursera.org/search?query=advanced+{skill_name}",
                  "type": "course",
                  "estimated_hours": 10,
                  "platform": "Coursera"
                }}
              ],
              "milestones": ["Complete masterclass", "Build sample project"]
            }}
          ]
        }}'''


# ─── 1. Assessment Generation ─────────────────────────────────────────────────

def generate_assessment(skill_name: str, claimed_proficiency: int, num_questions: int = 5) -> AIAssessmentResponse:
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

Generate exactly {num_questions} MCQ questions.
Generate exactly 2 coding questions.
Generate exactly 1 case study question.
Calibrate difficulty to proficiency {claimed_proficiency}/10 (1=beginner, 10=expert).
All MCQ questions must be unique and non-repetitive.
Questions must be directly relevant to {skill_name}, with a balanced mix of conceptual, applied, troubleshooting, and best-practice scenarios.
"""
    raw = _call_mistral("generation", system_prompt, user_prompt)
    data = _safe_parse_json(
      raw,
      fallback_getter=lambda: json.dumps(build_fallback_assessment_payload(skill_name, claimed_proficiency, num_questions)),
      skill_name=skill_name,
      claimed_proficiency=claimed_proficiency,
      num_questions=num_questions,
      model_key="generation",
    )
    if data is None or not isinstance(data, dict):
      data = build_fallback_assessment_payload(skill_name, claimed_proficiency, num_questions)
    normalized = _normalize_assessment_payload(
        data=data,
        skill_name=skill_name,
        claimed_proficiency=claimed_proficiency,
        num_questions=max(1, _coerce_int(num_questions, 5)),
    )
    return AIAssessmentResponse.model_validate(normalized)


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
    data = _safe_parse_json(raw, fallback_getter=lambda: _get_mock_response("scoring", user_prompt), model_key="scoring")
    if data is None or not isinstance(data, dict):
      fb = _get_mock_response("scoring", user_prompt)
      try:
        parsed = _safe_parse_json(fb)
        data = parsed if isinstance(parsed, dict) else json.loads(fb)
      except Exception:
        data = json.loads(fb)
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
    data = _safe_parse_json(raw, fallback_getter=lambda: _get_mock_response("planning", user_prompt), model_key="planning")
    if data is None or not isinstance(data, dict):
      fb = _get_mock_response("planning", user_prompt)
      try:
        parsed = _safe_parse_json(fb)
        data = parsed if isinstance(parsed, dict) else json.loads(fb)
      except Exception:
        data = json.loads(fb)
    return AILearningPlanResponse.model_validate(data)


# ─── 4. Gap Analysis ──────────────────────────────────────────────────────────

def analyze_gaps(skill_name: str, mcq_performance: dict, long_answer_feedback: dict, overall_score: int) -> AIGapAnalysisResponse:
    """
    Analyze specific gaps using Mistral Medium (reasoning model).
    Input: MCQ performance + AI feedback on long answers.
    Output: Specific gaps, severity levels, and recommended focus areas.
    """
    system_prompt = (
        "You are an expert skill gap analyzer for technical assessments. "
        "Identify specific gaps with severity levels based on performance data. "
        "You MUST respond with valid JSON ONLY."
    )
    user_prompt = f"""Analyze skill gaps for: **{skill_name}**

MCQ Performance: {mcq_performance['correct']}/{mcq_performance['total']} correct
Long Answer Feedback: {json.dumps(long_answer_feedback, indent=2)}
Overall Score: {overall_score}/10

Return ONLY a JSON object with this exact schema:
{{
  "identified_gaps": [
    {{
      "gap_name": "Gap Name",
      "severity": "high",
      "reason": "Explanation of why this is a gap"
    }}
  ],
  "focus_areas": ["area1", "area2", "area3"],
  "improvement_potential": <integer 0-10>
}}

For each gap:
- Use "high" severity if related to weak MCQ performance or low long-answer score
- Use "medium" severity for moderate weaknesses
- Use "low" severity for minor gaps

Focus areas should be actionable and specific to {skill_name}.
Improvement potential is 0-10, where 10 means user can improve significantly with focused effort.
"""
    raw = _call_mistral("scoring", system_prompt, user_prompt)
    data = _safe_parse_json(raw, fallback_getter=lambda: _get_mock_response("scoring", user_prompt), model_key="scoring")
    try:
      if data is None or not isinstance(data, dict):
        fb = _get_mock_response("scoring", user_prompt)
        try:
            parsed = _safe_parse_json(fb)
            data = parsed if isinstance(parsed, dict) else json.loads(fb)
        except Exception:
            data = json.loads(fb)
      return AIGapAnalysisResponse.model_validate(data)
    except Exception as e:
      print(f"Gap analysis schema validation failed: {e}. Falling back to deterministic gaps.")
      fallback_raw = _get_mock_response("scoring", f"Analyze skill gaps for: **{skill_name}**")
      try:
        fallback_data = _extract_json(fallback_raw)
      except json.JSONDecodeError:
        fallback_data = json.loads(fallback_raw)
      try:
        return AIGapAnalysisResponse.model_validate(fallback_data)
      except Exception:
        severity = "high" if overall_score < 4 else "medium" if overall_score < 7 else "low"
        return AIGapAnalysisResponse.model_validate({
          "identified_gaps": [
            {
              "gap_name": "Foundational Knowledge",
              "severity": severity,
              "reason": "Fallback gap analysis used due to invalid AI response schema.",
            }
          ],
          "focus_areas": ["Core Concepts", "Practice Questions", "Scenario-based Reasoning"],
          "improvement_potential": max(1, min(10, 10 - int(overall_score))),
        })


# ─── 5. Enhanced Learning Plan Generation with Resources ───────────────────────

def generate_enhanced_learning_plan(skill_name: str, score: int, identified_gaps: list, improvement_potential: int) -> AILearningPlanResponseEnhanced:
    """
    Generate an enhanced learning plan with YouTube and website resources.
    Uses specific gaps to create more targeted recommendations.
    """
    system_prompt = (
        "You are an expert learning architect for tech skills. "
        "Create detailed, actionable learning plans with specific YouTube and website resources. "
        "You MUST respond with valid JSON ONLY."
    )
    gaps_str = "\n".join(f"- {gap['gap_name']} (severity: {gap['severity']})" for gap in identified_gaps) if identified_gaps else "- General skill gaps"
    
    user_prompt = f"""Create an enhanced learning plan for: **{skill_name}**

Assessment Score: {score}/10
Improvement Potential: {improvement_potential}/10

Identified Gaps:
{gaps_str}

Return ONLY a JSON object with this exact schema:
{{
  "skill_name": "{skill_name}",
  "total_weeks": <integer>,
  "summary": "...",
  "phases": [
    {{
      "phase_number": 1,
      "title": "...",
      "description": "...",
      "timeline_weeks": 2,
      "focus_gaps": ["gap1", "gap2"],
      "youtube_resources": [
        {{
          "title": "Video Title",
          "url": "https://youtube.com/watch?v=...",
          "duration_minutes": 45
        }}
      ],
      "website_resources": [
        {{
          "title": "Resource Title",
          "url": "https://example.com/tutorial",
          "category": "tutorial",
          "estimated_hours": 2
        }}
      ],
      "milestones": ["milestone 1", "milestone 2"]
    }}
  ]
}}

For each phase:
1. Phase 1 should focus on high-severity gaps (High priority)
2. Phase 2 on medium-severity gaps (Medium priority)
3. Phase 3 on low-severity gaps and advanced topics (Low priority)

YouTube resources should be specific, real videos (include actual URLs when possible).
Website resources should include tutorials, documentation, and articles from reputable sources.
Categories: "tutorial", "documentation", "article", "practice", "interactive"
Total plan should be realistic and achievable in the total_weeks timeframe.
"""
    raw = _call_mistral("planning", system_prompt, user_prompt)
    try:
        data = _extract_json(raw)
    except json.JSONDecodeError:
        data = json.loads(raw)
    try:
      return AILearningPlanResponseEnhanced.model_validate(data)
    except Exception as e:
      print(f"Enhanced learning-plan schema validation failed: {e}. Falling back to deterministic plan.")
      fallback_raw = _get_mock_response("planning", user_prompt)
      try:
        fallback_data = _extract_json(fallback_raw)
      except json.JSONDecodeError:
        fallback_data = json.loads(fallback_raw)
      return AILearningPlanResponseEnhanced.model_validate(fallback_data)

