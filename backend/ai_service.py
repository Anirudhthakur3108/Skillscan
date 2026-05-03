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
import time
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
_client_timeout = int(os.getenv("MISTRAL_TIMEOUT_SECONDS", "120"))
client = MistralClient(api_key=_api_key, timeout=_client_timeout)

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


def _safe_parse_json(raw: str) -> Optional[Union[dict, list]]:
    """Attempt to parse JSON from a possibly-malformed LLM response.

    Strategies tried (in order):
    - _extract_json (handles ```json fences)
    - json.loads on raw
    - extract first balanced {...} substring and json.loads
    - remove trailing commas and json.loads

    Returns a Python object (dict/list) or None if parsing fails.
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

    return None


def _call_mistral(model_key: str, system_prompt: str, user_prompt: str, temperature: float = 0.3, max_tokens: int = 16384) -> str:
    """Call Mistral with the appropriate model tier. Returns raw text.

    Raises RuntimeError if the API key is missing or the call fails.
    No fallback to mock data — the caller decides how to handle errors.
    """
    if not _api_key or _api_key == "your_mistral_api_key_here":
        raise RuntimeError("MISTRAL_API_KEY is not configured. Set it in .env to enable AI generation.")

    model = MODELS[model_key]
    print(f"[Mistral] Calling model={model} tier={model_key} timeout={_client_timeout}s max_tokens={max_tokens} ...")

    t0 = time.time()
    response = client.chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    elapsed = time.time() - t0
    content = response.choices[0].message.content
    print(f"[Mistral] OK - Response received in {elapsed:.1f}s  ({len(content)} chars)")
    return content


def _coerce_int(value, default: int) -> int:
    try:
      return int(value)
    except (TypeError, ValueError):
      return default


def _difficulty_from_proficiency(proficiency: int, offset: int = 0) -> int:
    base = max(1, min(10, _coerce_int(proficiency, 5)))
    return max(1, min(10, base + offset))


def _normalize_assessment_payload(data: dict, skill_name: str, claimed_proficiency: int) -> dict:
    """Deduplicate and validate AI-generated questions. No fallback padding."""
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

    # Re-index ids sequentially
    for idx, item in enumerate(deduped_mcq, start=1):
      item["id"] = f"mcq_{idx}"

    # Normalize coding questions — coerce all fields to strings
    def _stringify(val) -> str:
      if val is None:
        return ""
      if isinstance(val, str):
        return val
      return json.dumps(val, indent=2)

    raw_coding = data.get("coding", []) if isinstance(data.get("coding", []), list) else []
    normalized_coding = []
    for item in raw_coding:
      if not isinstance(item, dict):
        continue
      normalized_coding.append({
        "id": str(item.get("id", f"code_{len(normalized_coding) + 1}")),
        "problem_statement": _stringify(item.get("problem_statement", "")),
        "constraints": _stringify(item.get("constraints", "")),
        "example_input": _stringify(item.get("example_input", "")),
        "example_output": _stringify(item.get("example_output", "")),
        "hints": [str(h) for h in item.get("hints", [])] if isinstance(item.get("hints", []), list) else [],
      })

    # Normalize case study questions
    raw_case = data.get("case_study", []) if isinstance(data.get("case_study", []), list) else []
    normalized_case = []
    for item in raw_case:
      if not isinstance(item, dict):
        continue
      normalized_case.append({
        "id": str(item.get("id", f"case_{len(normalized_case) + 1}")),
        "scenario": _stringify(item.get("scenario", "")),
        "question": _stringify(item.get("question", "")),
        "evaluation_criteria": [str(c) for c in item.get("evaluation_criteria", [])] if isinstance(item.get("evaluation_criteria", []), list) else [],
      })

    return {
      "skill_name": str(data.get("skill_name") or skill_name),
      "mcq": deduped_mcq,
      "coding": normalized_coding,
      "case_study": normalized_case,
    }


# ─── 1. Category-Aware Prompt Configuration ──────────────────────────────────

# Maps skill categories to their assessment strategy.
# "technical_categories" use the coding+case_study mix.
# All others get tailored alternatives that reuse the same JSON keys.
TECHNICAL_CATEGORIES = frozenset({
    "Frontend", "Backend", "Database", "Cloud", "DevOps", "Data Science",
    "Technical",  # manual-entry catch-all
})


def _get_category_type(category: str) -> str:
    """Classify a raw category string into one of four assessment types."""
    if not category:
        return "technical"  # safe default
    cat = category.strip()
    if cat in TECHNICAL_CATEGORIES:
        return "technical"
    cat_lower = cat.lower()
    if cat_lower in ("soft skill", "soft skills"):
        return "soft_skill"
    if cat_lower == "domain":
        return "domain"
    if cat_lower in ("tool", "tools"):
        return "tool"
    return "technical"  # fallback


def _build_category_prompt(skill_name: str, category_type: str, num_questions: int, claimed_proficiency: int) -> tuple:
    """Return (system_prompt, category_specific_instructions) for the AI."""

    # ── JSON schema is the same for every category (reuses mcq/coding/case_study keys)
    json_schema = f"""Return ONLY a JSON object matching this exact schema:
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
}}"""

    if category_type == "soft_skill":
        system_prompt = (
            "You are an expert behavioral and soft-skills assessor. "
            "You specialize in evaluating interpersonal, leadership, and communication competencies. "
            "You MUST respond with valid JSON ONLY — no preamble, no explanation outside the JSON object. "
            "Strictly follow the schema provided in the user message."
        )
        mix_instructions = f"""Generate exactly {num_questions} MCQ questions.
Generate exactly 2 items in the "coding" array — but these are NOT programming tasks.
Instead, each "coding" item must be a **Professional Writing Task** relevant to {skill_name}.
- "problem_statement" should describe a realistic workplace scenario requiring a written response (e.g., drafting an email to a difficult stakeholder, writing a team update, composing a conflict resolution message).
- "constraints" should list tone, audience, and length requirements.
- "example_input" should provide context or background information.
- "example_output" should be empty string "".
- "hints" should provide writing tips.
Generate exactly 1 case study that is a **Behavioral Scenario** — a detailed workplace conflict, leadership challenge, or team dynamics situation requiring a multi-step resolution plan.
MCQ questions should be Situational Judgement Tests ("What would you do if...") — NOT trivia about soft-skill definitions."""

    elif category_type == "domain":
        system_prompt = (
            "You are an expert domain-knowledge assessor specializing in industry-specific evaluation. "
            "You assess regulatory awareness, strategic thinking, and domain expertise. "
            "You MUST respond with valid JSON ONLY — no preamble, no explanation outside the JSON object. "
            "Strictly follow the schema provided in the user message."
        )
        mix_instructions = f"""Generate exactly {num_questions} MCQ questions focused on industry terminology, regulations, workflows, and best practices for {skill_name}.
Generate exactly 2 items in the "coding" array — but these are NOT programming tasks.
Instead, each "coding" item must be an **Analytical Scenario** relevant to {skill_name}.
- "problem_statement" should describe a business situation requiring analysis (e.g., identifying risks, evaluating a process bottleneck, proposing a compliance strategy).
- "constraints" should list regulatory or business requirements.
- "example_input" should provide sample data or context.
- "example_output" should be empty string "".
- "hints" should provide analytical frameworks or tips.
Generate exactly 1 case study that is a **Strategic Business Scenario** — a comprehensive industry situation requiring a detailed solution with compliance, stakeholder, and operational considerations.
MCQ questions should test applied domain knowledge, NOT generic definitions."""

    elif category_type == "tool":
        system_prompt = (
            "You are an expert tool-proficiency assessor. "
            "You evaluate practical knowledge of software tools, workflows, features, and integrations. "
            "You MUST respond with valid JSON ONLY — no preamble, no explanation outside the JSON object. "
            "Strictly follow the schema provided in the user message."
        )
        mix_instructions = f"""Generate exactly {num_questions} MCQ questions about {skill_name} features, shortcuts, settings, and best practices.
Generate exactly 2 items in the "coding" array — but these are NOT programming tasks.
Instead, each "coding" item must be a **Step-by-Step Workflow Task** for {skill_name}.
- "problem_statement" should describe a practical task the user must accomplish using {skill_name} (e.g., "Explain the steps to create a dynamic pivot table in Excel" or "Describe how to set up an automated Jira workflow").
- "constraints" should list specific tool versions or feature requirements.
- "example_input" should describe the starting state or context.
- "example_output" should be empty string "".
- "hints" should list relevant tool features or menu paths.
Generate exactly 1 case study that is a **Tool Integration / Workspace Setup Scenario** — a situation where the user must plan how to use {skill_name} in a team environment, configure it for a project, or integrate it with other tools.
MCQ questions should test practical feature knowledge, NOT generic software definitions."""

    else:  # technical (default)
        system_prompt = (
            "You are an expert technical skills assessor. "
            "You MUST respond with valid JSON ONLY — no preamble, no explanation outside the JSON object. "
            "Strictly follow the schema provided in the user message."
        )
        mix_instructions = f"""Generate exactly {num_questions} MCQ questions.
Generate exactly 2 coding questions with real algorithmic or functional programming problems.
Generate exactly 1 case study question about system design, architecture, or debugging.
Questions must be directly relevant to {skill_name}, with a balanced mix of conceptual, applied, troubleshooting, and best-practice scenarios."""

    return system_prompt, json_schema, mix_instructions


# ─── 1. Assessment Generation ─────────────────────────────────────────────────

def generate_assessment(skill_name: str, claimed_proficiency: int, num_questions: int = 10, skill_category: str = "") -> AIAssessmentResponse:
    """
    Generate a skill assessment using Mistral AI.
    The question mix adapts based on skill_category:
      - Technical (Frontend/Backend/etc): MCQ + Coding + Case Study
      - Soft Skill: MCQ (SJTs) + Writing Tasks + Behavioral Scenarios
      - Domain: MCQ (Industry) + Analytical Tasks + Strategic Scenarios
      - Tool: MCQ (Features) + Workflow Tasks + Integration Scenarios
    Returns a strictly validated AIAssessmentResponse.
    Raises RuntimeError if AI generation fails.
    """
    category_type = _get_category_type(skill_category)
    system_prompt, json_schema, mix_instructions = _build_category_prompt(
        skill_name, category_type, num_questions, claimed_proficiency
    )

    user_prompt = f"""Generate a comprehensive skill assessment for: **{skill_name}**
Skill category: {skill_category or 'Technical'}
The student claims a proficiency level of {claimed_proficiency}/10.

{json_schema}

{mix_instructions}
Calibrate difficulty to proficiency {claimed_proficiency}/10 (1=beginner, 10=expert).
All MCQ questions must be unique and non-repetitive.
"""
    raw = _call_mistral("generation", system_prompt, user_prompt)
    data = _safe_parse_json(raw)

    if data is None or not isinstance(data, dict):
        # Debug: try direct parse to get the actual error
        parse_error = "unknown"
        try:
            json.loads(raw)
        except Exception as e:
            parse_error = str(e)
        print(f"[Mistral] PARSE FAILED - raw length={len(raw)}, last 100 chars: ...{raw[-100:]}")
        print(f"[Mistral] Parse error: {parse_error}")
        raise RuntimeError(
            f"Mistral returned unparseable JSON for assessment generation. "
            f"Raw response (first 500 chars): {raw[:500]}"
        )

    normalized = _normalize_assessment_payload(
        data=data,
        skill_name=skill_name,
        claimed_proficiency=claimed_proficiency,
    )

    if not normalized.get("mcq"):
        raise RuntimeError("Mistral returned zero valid MCQ questions.")

    return AIAssessmentResponse.model_validate(normalized)


# ─── 2. Assessment Scoring ────────────────────────────────────────────────────

def score_assessment(skill_name: str, questions: dict, student_answers: dict) -> AIScoreResponse:
    """
    Score a completed assessment using Mistral.
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
    data = _safe_parse_json(raw)
    if data is None or not isinstance(data, dict):
        raise RuntimeError(f"Mistral returned unparseable JSON for scoring. Raw: {raw[:500]}")
    return AIScoreResponse.model_validate(data)


# ─── 3. Learning Plan Generation ─────────────────────────────────────────────

def generate_learning_plan(skill_name: str, score: int, weaknesses: list) -> AILearningPlanResponse:
    """
    Generate a personalized learning plan using Mistral.
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
    data = _safe_parse_json(raw)
    if data is None or not isinstance(data, dict):
        raise RuntimeError(f"Mistral returned unparseable JSON for learning plan. Raw: {raw[:500]}")
    return AILearningPlanResponse.model_validate(data)


# ─── 4. Gap Analysis ──────────────────────────────────────────────────────────

def analyze_gaps(skill_name: str, mcq_performance: dict, long_answer_feedback: dict, overall_score: int) -> AIGapAnalysisResponse:
    """
    Analyze specific gaps using Mistral (reasoning model).
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
    data = _safe_parse_json(raw)
    if data is None or not isinstance(data, dict):
        raise RuntimeError(f"Mistral returned unparseable JSON for gap analysis. Raw: {raw[:500]}")
    return AIGapAnalysisResponse.model_validate(data)


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
    data = _safe_parse_json(raw)
    if data is None or not isinstance(data, dict):
        raise RuntimeError(f"Mistral returned unparseable JSON for enhanced learning plan. Raw: {raw[:500]}")
    return AILearningPlanResponseEnhanced.model_validate(data)
