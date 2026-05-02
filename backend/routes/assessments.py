from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from typing import Optional
from datetime import datetime, timedelta
import copy
import random
import re
from models import (
    Student, StudentSkill, SkillTaxonomy,
    QuestionBank, Assessment, AssessmentResponse,
    SkillScore, AssessmentScoreDetail
)
from ai_service import (
    generate_assessment, 
    score_assessment, 
    analyze_gaps,
    generate_enhanced_learning_plan,
)

assessments_bp = Blueprint('assessments', __name__)

REASSESSMENT_COOLDOWN_DAYS = 7


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_difficulty_config(difficulty: int) -> tuple:
    """
    Get test configuration based on difficulty level.
    Returns (num_questions, time_limit_minutes)
    MCQ count scales with difficulty so harder assessments are more thorough.
    """
    if difficulty <= 3:
        return (10, 20)
    elif difficulty <= 6:
        return (15, 30)
    elif difficulty <= 8:
        return (15, 35)
    else:
        return (20, 40)


def _safe_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_from_question_bank(skill_id: int, difficulty: Optional[int] = None) -> Optional[dict]:
    """
    Check Question Bank for existing questions for this skill.
    If difficulty is specified, filter by difficulty level.
    Returns question data dict or None if not cached.
    """
    query = QuestionBank.query.filter_by(
        skill_id=skill_id,
        question_type='FULL_ASSESSMENT'
    )
    if difficulty is not None:
        query = query.filter_by(difficulty_level=difficulty)
    
    entry = query.order_by(QuestionBank.created_at.desc()).first()
    return entry.question_data if entry else None


def _get_question_count(skill_id: int) -> int:
    """Get total count of cached questions for a skill."""
    entry = QuestionBank.query.filter_by(
        skill_id=skill_id,
        question_type='FULL_ASSESSMENT'
    ).first()
    return entry.question_count if entry else 0


def _save_to_question_bank(skill_id: int, question_data: dict, difficulty: int = 5):
    """Cache generated questions for future reuse."""
    mcq_count = len(question_data.get('mcq', [])) if isinstance(question_data, dict) else 0
    # Get existing entry to update question count
    existing = QuestionBank.query.filter_by(
        skill_id=skill_id,
        question_type='FULL_ASSESSMENT'
    ).first()
    
    if existing:
        # Update existing entry
        existing.question_data = question_data
        existing.difficulty_level = difficulty
        existing.question_count = (existing.question_count or 0) + mcq_count
    else:
        # Create new entry
        entry = QuestionBank(
            skill_id=skill_id,
            question_type='FULL_ASSESSMENT',
            question_data=question_data,
            difficulty_level=difficulty,
            question_count=mcq_count
        )
        db.session.add(entry)
    
    db.session.commit()


def _has_required_mcqs(question_data: Optional[dict], required_count: int) -> bool:
    if not question_data or not isinstance(question_data, dict):
        return False
    mcq = question_data.get('mcq', [])
    return isinstance(mcq, list) and len(mcq) >= required_count


def _dedupe_mcqs(mcq_list: list) -> list:
    deduped = []
    seen = set()
    for item in mcq_list:
        if not isinstance(item, dict):
            continue
        question = str(item.get('question', '')).strip()
        if not question:
            continue
        key = re.sub(r'\s+', ' ', question.lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _is_relevant_to_skill(question_text: str, skill_name: str) -> bool:
    question = (question_text or '').lower()
    tokens = [t for t in re.split(r'\W+', skill_name.lower()) if len(t) > 2]
    if not tokens:
        return True
    return any(token in question for token in tokens)


def _is_quality_question_set(question_data: Optional[dict], required_count: int, skill_name: str) -> bool:
    if not question_data or not isinstance(question_data, dict):
        return False
    mcq = question_data.get('mcq', [])
    if not isinstance(mcq, list):
        return False

    deduped = _dedupe_mcqs(mcq)
    if len(deduped) < required_count:
        return False

    relevance_hits = 0
    for item in deduped:
        if _is_relevant_to_skill(str(item.get('question', '')), skill_name):
            relevance_hits += 1

    # Require at least 60% of questions to be explicitly skill-relevant.
    min_relevance = max(1, int(required_count * 0.6))
    return relevance_hits >= min_relevance


def _select_diverse_questions(question_data: dict, required_count: int, exclude_mcq_ids: set = None) -> dict:
    selected_payload = copy.deepcopy(question_data)
    mcq = selected_payload.get('mcq', []) if isinstance(selected_payload.get('mcq', []), list) else []
    deduped = _dedupe_mcqs(mcq)
    if exclude_mcq_ids:
        deduped = [q for q in deduped if q.get('id') not in exclude_mcq_ids]
    random.shuffle(deduped)
    selected_payload['mcq'] = deduped[:required_count]
    return selected_payload


def _randomize_mcq_option_order(question_data: dict) -> dict:
    randomized = copy.deepcopy(question_data)
    option_ids = ['A', 'B', 'C', 'D', 'E', 'F']

    for question in randomized.get('mcq', []):
        options = question.get('options', []) if isinstance(question.get('options', []), list) else []
        if not options:
            continue

        original_map = {str(opt.get('id')): str(opt.get('text', '')) for opt in options if isinstance(opt, dict)}
        correct_id = str(question.get('correct_option_id', '')).strip()
        correct_text = original_map.get(correct_id)

        option_texts = [str(opt.get('text', '')) for opt in options if isinstance(opt, dict) and opt.get('text')]
        if len(option_texts) < 2:
            continue

        random.shuffle(option_texts)
        reassigned = []
        new_correct_id = None
        for index, text in enumerate(option_texts):
            if index >= len(option_ids):
                break
            new_id = option_ids[index]
            reassigned.append({"id": new_id, "text": text})
            if correct_text is not None and text == correct_text and new_correct_id is None:
                new_correct_id = new_id

        if reassigned:
            question['options'] = reassigned
            if new_correct_id:
                question['correct_option_id'] = new_correct_id

    return randomized


def _resolve_question_set(skill_id: int, skill_name: str, difficulty: int, proficiency_claimed: int, num_questions: int, exclude_mcq_ids: set = None):
    """Resolve a set of assessment questions — cached or AI-generated.

    Returns (question_data, source_label).  Raises RuntimeError if AI
    generation fails and there are no cached questions to fall back to.
    """
    cached_questions = _get_from_question_bank(skill_id, difficulty)
    if not cached_questions:
        cached_questions = _get_from_question_bank(skill_id)

    # Serve from cache if we have enough quality questions
    if _is_quality_question_set(cached_questions, num_questions, skill_name):
        selected = _select_diverse_questions(cached_questions, num_questions, exclude_mcq_ids)
        return _randomize_mcq_option_order(selected), "question_bank"

    # Start with existing cached questions
    generated = {"mcq": [], "coding": [], "case_study": []}
    if cached_questions:
        generated["mcq"] = cached_questions.get("mcq", [])
        generated["coding"] = cached_questions.get("coding", [])
        generated["case_study"] = cached_questions.get("case_study", [])

    # Generate fresh questions from Mistral AI
    ai_response = generate_assessment(
        skill_name,
        proficiency_claimed,
        num_questions=num_questions,
    )
    batch = ai_response.model_dump()
    generated["mcq"].extend(batch.get("mcq", []))
    generated["coding"].extend(batch.get("coding", []))
    generated["case_study"].extend(batch.get("case_study", []))

    # Deduplicate MCQs
    generated["mcq"] = _dedupe_mcqs(generated["mcq"])

    _save_to_question_bank(skill_id, generated, difficulty)

    selected = _select_diverse_questions(generated, num_questions, exclude_mcq_ids)
    return _randomize_mcq_option_order(selected), "ai_generated"


def _get_reassessment_status(assessment: Assessment, study_completed: bool = False) -> dict:
    response_record = AssessmentResponse.query.filter_by(assessment_id=assessment.id).first()
    base_time = (
        response_record.submitted_at
        if response_record and response_record.submitted_at
        else assessment.updated_at or assessment.created_at or datetime.utcnow()
    )
    next_eligible_at = base_time + timedelta(days=REASSESSMENT_COOLDOWN_DAYS)
    now = datetime.utcnow()

    time_eligible = now >= next_eligible_at
    eligible = bool(study_completed) or time_eligible

    if eligible:
        reason = "Eligible via study completion" if study_completed and not time_eligible else "Eligible via cooldown"
    else:
        reason = f"Reassessment available after {REASSESSMENT_COOLDOWN_DAYS} days or when study is marked complete"

    return {
        "eligible": eligible,
        "reason": reason,
        "cooldown_days": REASSESSMENT_COOLDOWN_DAYS,
        "next_eligible_at": next_eligible_at.isoformat(),
        "time_eligible": time_eligible,
        "study_completed": bool(study_completed),
    }


# ─── Routes ───────────────────────────────────────────────────────────────────

@assessments_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate():
    """
    POST /assessments/generate
    Body: { student_id, skill_id, difficulty, proficiency_claimed }

    Checks Question Bank first. If >= 30 questions cached, uses those.
    Otherwise generates new questions up to 30 total.
    """
    try:
        current_user_id = str(get_jwt_identity())
    except Exception as e:
        return jsonify({"error": "Invalid token", "details": str(e)}), 401
    
    data = request.get_json() or {}
    student_id = data.get('student_id')
    skill_id = data.get('skill_id')
    difficulty = data.get('difficulty')
    proficiency_claimed = data.get('proficiency_claimed')

    if not student_id or not skill_id:
        return jsonify({"error": "student_id and skill_id are required"}), 400
    
    # Authorization check
    if str(current_user_id) != str(student_id):
        return jsonify({"error": "Unauthorized - User can only generate assessment for themselves"}), 403

    # Validate student exists
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    # Validate student and skill exist
    student_skill = StudentSkill.query.filter_by(
        student_id=student_id, skill_id=skill_id
    ).first()
    if not student_skill:
        return jsonify({"error": "Skill not found in student profile"}), 404

    taxonomy = db.session.get(SkillTaxonomy, skill_id)
    if not taxonomy:
        return jsonify({"error": "Skill taxonomy not found"}), 404

    skill_settings = ((student.profile_data or {}).get('skill_settings') or {}) if isinstance(student.profile_data or {}, dict) else {}
    saved_setting = skill_settings.get(str(skill_id), {}) if isinstance(skill_settings, dict) else {}

    if difficulty is None:
        difficulty = saved_setting.get('difficulty')
    if proficiency_claimed is None:
        proficiency_claimed = saved_setting.get('proficiency_claimed', student_skill.proficiency_claimed)

    difficulty = _safe_int(difficulty, 0)
    proficiency_claimed = _safe_int(proficiency_claimed, 0)

    if not (1 <= difficulty <= 10):
        return jsonify({"error": "difficulty must be configured per skill (1-10) before generating assessments"}), 400
    if not (1 <= proficiency_claimed <= 10):
        return jsonify({"error": "proficiency_claimed must be configured per skill (1-10) before generating assessments"}), 400

    # Get difficulty-based test configuration
    num_questions, time_limit_minutes = _get_difficulty_config(difficulty)
    
    try:
        questions_data, source = _resolve_question_set(
            skill_id=skill_id,
            skill_name=taxonomy.skill_name,
            difficulty=difficulty,
            proficiency_claimed=proficiency_claimed,
            num_questions=num_questions,
        )
    except Exception as e:
        return jsonify({
            "error": "AI generation failed",
            "details": str(e)
        }), 502

    # Create Assessment record with new fields
    assessment = Assessment(
        student_id=student_id,
        skill_id=skill_id,
        assessment_type='FULL_ASSESSMENT',
        questions=questions_data,
        status='generated',
        difficulty_level=difficulty,
        num_questions=num_questions,
        time_limit_minutes=time_limit_minutes,
        proficiency_claimed=proficiency_claimed,
    )
    db.session.add(assessment)
    db.session.commit()

    # Return questions WITHOUT correct answers (strip them for the frontend)
    questions_for_student = _strip_answers(questions_data)

    return jsonify({
        "status": "success",
        "assessment_id": assessment.id,
        "skill_name": taxonomy.skill_name,
        "source": source,
        "difficulty": difficulty,
        "num_questions": num_questions,
        "time_limit_minutes": time_limit_minutes,
        "questions": questions_for_student,
    }), 201


def _strip_answers(questions_data: dict) -> dict:
    """Remove correct answers before sending to frontend."""
    import copy
    stripped = copy.deepcopy(questions_data)
    for q in stripped.get('mcq', []):
        q.pop('correct_option_id', None)
        q.pop('explanation', None)
    for q in stripped.get('coding', []):
        q.pop('example_output', None)
    for q in stripped.get('case_study', []):
        q.pop('evaluation_criteria', None)
    return stripped


@assessments_bp.route('/<int:assessment_id>/submit', methods=['POST'])
@jwt_required()
def submit(assessment_id: int):
    """
    POST /assessments/{id}/submit
    Body: { student_answers: { "mcq": {...}, "coding": {...}, "case_study": {...} } }

    Hybrid Scoring:
    - MCQ: Auto-scored by fetching correct answers from DB
    - Long answers + case studies: Sent to AI for evaluation
    - Overall: 40% MCQ + 60% AI scores
    """
    current_user_id = str(get_jwt_identity())
    data = request.get_json() or {}
    student_answers_raw = data.get('student_answers', {})

    if not isinstance(student_answers_raw, dict):
        return jsonify({"error": "student_answers must be a JSON object"}), 400

    # Backward-compatible normalization:
    # - New format: { mcq: {...}, coding: {...}, case_study: {...} }
    # - Legacy format: { "mcq_1": "A", "mcq_2": "B" }
    if any(k in student_answers_raw for k in ("mcq", "coding", "case_study")):
        student_answers = {
            "mcq": student_answers_raw.get("mcq", {}) or {},
            "coding": student_answers_raw.get("coding", {}) or {},
            "case_study": student_answers_raw.get("case_study", {}) or {},
        }
    else:
        student_answers = {
            "mcq": student_answers_raw,
            "coding": {},
            "case_study": {},
        }

    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404
    if current_user_id != str(assessment.student_id):
        return jsonify({"error": "Unauthorized"}), 403
    if assessment.status == 'completed':
        return jsonify({"error": "Assessment already submitted"}), 409

    taxonomy = db.session.get(SkillTaxonomy, assessment.skill_id)

    # ─── 1. MCQ AUTO-SCORING ──────────────────────────────────────────────────
    mcq_questions = assessment.questions.get('mcq', [])
    mcq_answers = student_answers.get('mcq', {})
    mcq_correct = 0
    mcq_feedback_items = []
    
    for mcq in mcq_questions:
        question_id = mcq['id']
        student_answer = mcq_answers.get(question_id)
        correct_answer = mcq['correct_option_id']
        is_correct = student_answer == correct_answer
        
        if is_correct:
            mcq_correct += 1
        
        mcq_feedback_items.append({
            "question_id": question_id,
            "correct": is_correct,
            "feedback": mcq['explanation'] if is_correct else f"Correct answer: {correct_answer}"
        })
    
    mcq_total = len(mcq_questions)
    mcq_score = int((mcq_correct / mcq_total * 10)) if mcq_total > 0 else 0
    mcq_percentage = int((mcq_correct / mcq_total * 100)) if mcq_total > 0 else 0
    
    mcq_feedback_dict = {
        "total": mcq_total,
        "correct": mcq_correct,
        "percentage": mcq_percentage,
        "items": mcq_feedback_items
    }

    # ─── 2. LONG ANSWER + CASE STUDY AI SCORING ───────────────────────────────
    long_answer_score = None
    case_study_score = None
    long_answer_feedback = None
    case_study_feedback = None
    
    coding_questions = assessment.questions.get('coding', [])
    case_study_questions = assessment.questions.get('case_study', [])
    
    if coding_questions or case_study_questions:
        try:
            # Prepare long answer questions for AI
            long_answer_eval = {
                "coding": {
                    "questions": coding_questions,
                    "answers": student_answers.get('coding', {})
                },
                "case_study": {
                    "questions": case_study_questions,
                    "answers": student_answers.get('case_study', {})
                }
            }
            
            # Call AI to score long answers
            ai_score_response = score_assessment(
                skill_name=taxonomy.skill_name,
                questions=long_answer_eval,
                student_answers={"coding": student_answers.get('coding', {}), "case_study": student_answers.get('case_study', {})}
            )
            
            long_answer_score = int(ai_score_response.overall_score)
            case_study_score = long_answer_score
            long_answer_feedback = {
                "score": long_answer_score,
                "feedback": ai_score_response.reasoning,
                "strengths": ai_score_response.strengths,
                "weaknesses": ai_score_response.weaknesses
            }
            case_study_feedback = long_answer_feedback  # Same AI evaluation covers both
        except Exception as e:
            print(f"AI scoring failed: {e}")
            # Continue with MCQ-only scoring if AI fails

    # ─── 3. CALCULATE OVERALL SCORE ───────────────────────────────────────────
    # If long-answer sections are absent or scoring failed, use MCQ score only.
    if long_answer_score is None:
        overall_score = mcq_score
    else:
        overall_score = int(round(mcq_score * 0.4 + long_answer_score * 0.6))

    # ─── 4. ANALYZE GAPS ───────────────────────────────────────────────────────
    mcq_performance = {"correct": mcq_correct, "total": mcq_total}
    gap_analysis_input = {
        "long_answer_score": long_answer_score if long_answer_score is not None else mcq_score,
        "feedback": long_answer_feedback.get('feedback', '') if long_answer_feedback else ""
    }
    
    proficiency_target = int(assessment.proficiency_claimed or 5)
    performance_gap = int(proficiency_target - overall_score)
    gap_identified = overall_score < proficiency_target

    try:
        gap_analysis = analyze_gaps(
            skill_name=taxonomy.skill_name,
            mcq_performance=mcq_performance,
            long_answer_feedback=gap_analysis_input,
            overall_score=overall_score
        )
        # Only use identified gaps if the AI returned specific, actionable gaps.
        identified_gaps = gap_analysis.identified_gaps if gap_identified and getattr(gap_analysis, 'identified_gaps', None) else []
    except Exception as e:
        # If gap analysis fails, don't invent generic gaps — keep identified_gaps empty.
        print(f"Gap analysis failed: {e}")
        identified_gaps = []

    # ─── 5. SAVE DETAILED SCORE DETAILS ────────────────────────────────────────
    score_detail = AssessmentScoreDetail(
        assessment_id=assessment_id,
        mcq_count=mcq_total,
        mcq_correct=mcq_correct,
        mcq_score=mcq_score,
        long_answer_score=long_answer_score,
        case_study_score=case_study_score,
        mcq_feedback=mcq_feedback_dict,
        long_answer_feedback=long_answer_feedback,
        case_study_feedback=case_study_feedback
    )
    db.session.add(score_detail)

    # ─── 6. SAVE RESPONSE AND SKILL SCORE ──────────────────────────────────────
    response_record = AssessmentResponse(
        assessment_id=assessment_id,
        student_response=student_answers,
        ai_feedback={
            "overall_score": overall_score,
            "selected_proficiency": proficiency_target,
            "performance_gap": performance_gap,
            "mcq_feedback": mcq_feedback_dict,
            "long_answer_feedback": long_answer_feedback,
            "case_study_feedback": case_study_feedback,
            "identified_gaps": [
                {
                    "gap_name": g.gap_name if hasattr(g, 'gap_name') else g.get('gap_name'),
                    "severity": g.severity if hasattr(g, 'severity') else g.get('severity'),
                    "reason": g.reason if hasattr(g, 'reason') else g.get('reason')
                }
                for g in identified_gaps
            ],
            "gap_identified": gap_identified
        }
    )
    db.session.add(response_record)

    # Save skill score
    skill_score = SkillScore(
        student_id=assessment.student_id,
        skill_id=assessment.skill_id,
        assessment_id=assessment_id,
        score=overall_score,
        ai_reasoning=f"MCQ: {mcq_score}/10, Long Answer: {long_answer_score}/10, Overall: {overall_score}/10",
        gap_identified=gap_identified,
    )
    db.session.add(skill_score)

    # Update assessment status
    assessment.status = 'completed'
    db.session.commit()

    return jsonify({
        "status": "success",
        "assessment_id": assessment_id,
        "skill_name": taxonomy.skill_name,
        "overall_score": overall_score,
        "selected_proficiency": proficiency_target,
        "performance_gap": performance_gap,
        "mcq_score": mcq_score,
        "long_answer_score": long_answer_score,
        "gap_identified": gap_identified,
        "score_detail_id": score_detail.id,
        "skill_score_id": skill_score.id,
        "mcq_feedback": mcq_feedback_dict,
        "long_answer_feedback": long_answer_feedback,
        "identified_gaps": [
            {
                "gap_name": g.gap_name if hasattr(g, 'gap_name') else g.get('gap_name'),
                "severity": g.severity if hasattr(g, 'severity') else g.get('severity'),
                "reason": g.reason if hasattr(g, 'reason') else g.get('reason')
            }
            for g in identified_gaps
        ],
    }), 200


@assessments_bp.route('/<int:assessment_id>', methods=['GET'])
@jwt_required()
def get_assessment(assessment_id: int):
    """GET /assessments/{id} — Get assessment details and results."""
    current_user_id = str(get_jwt_identity())
    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404
    if current_user_id != str(assessment.student_id):
        return jsonify({"error": "Unauthorized"}), 403

    taxonomy = db.session.get(SkillTaxonomy, assessment.skill_id)
    response = AssessmentResponse.query.filter_by(assessment_id=assessment_id).first()
    score_detail = AssessmentScoreDetail.query.filter_by(assessment_id=assessment_id).first()
    skill_score = SkillScore.query.filter_by(assessment_id=assessment_id).first()

    return jsonify({
        "assessment_id": assessment_id,
        "skill_name": taxonomy.skill_name if taxonomy else "Unknown",
        "status": assessment.status,
        "skill_score_id": skill_score.id if skill_score else None,
        "gap_identified": skill_score.gap_identified if skill_score else None,
        "difficulty": assessment.difficulty_level,
        "num_questions": assessment.num_questions,
        "time_limit_minutes": assessment.time_limit_minutes,
        "created_at": assessment.created_at.isoformat(),
        "questions": _strip_answers(assessment.questions) if assessment.status != 'completed' else None,
        "ai_feedback": response.ai_feedback if response else None,
        "score_detail": {
            "mcq_feedback": score_detail.mcq_feedback,
            "long_answer_feedback": score_detail.long_answer_feedback,
            "case_study_feedback": score_detail.case_study_feedback,
        } if score_detail else None,
    }), 200


@assessments_bp.route('/student/<student_id>', methods=['GET'])
@jwt_required()
def list_student_assessments(student_id: str):
    """GET /assessments/student/{id} — List all assessments for a student."""
    current_user_id = str(get_jwt_identity())
    if current_user_id != str(student_id):
        return jsonify({"error": "Unauthorized"}), 403

    assessments = (
        db.session.query(Assessment, SkillTaxonomy, SkillScore)
        .join(SkillTaxonomy, Assessment.skill_id == SkillTaxonomy.id)
        .outerjoin(SkillScore, SkillScore.assessment_id == Assessment.id)
        .filter(Assessment.student_id == student_id)
        .all()
    )

    result = [
        {
            "assessment_id": a.id,
            "skill_name": t.skill_name,
            "category": t.category,
            "status": a.status,
            "score": s.score if s else None,
            "gap_identified": s.gap_identified if s else None,
            "created_at": a.created_at.isoformat(),
        }
        for a, t, s in assessments
    ]

    return jsonify({"assessments": result}), 200


@assessments_bp.route('/<int:assessment_id>/reassessment-eligibility', methods=['GET'])
@jwt_required()
def reassessment_eligibility(assessment_id: int):
    """GET /assessments/{id}/reassessment-eligibility — Check reassessment gate."""
    current_user_id = str(get_jwt_identity())
    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404
    if current_user_id != str(assessment.student_id):
        return jsonify({"error": "Unauthorized"}), 403

    study_completed = str(request.args.get('study_completed', 'false')).lower() in ('1', 'true', 'yes')
    status = _get_reassessment_status(assessment, study_completed=study_completed)
    return jsonify(status), 200


@assessments_bp.route('/<int:assessment_id>/reassess', methods=['POST'])
@jwt_required()
def reassess(assessment_id: int):
    """POST /assessments/{id}/reassess — Create a new reassessment when eligible."""
    current_user_id = str(get_jwt_identity())
    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404
    if current_user_id != str(assessment.student_id):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json() or {}
    study_completed = bool(data.get('study_completed', False))
    status = _get_reassessment_status(assessment, study_completed=study_completed)
    if not status['eligible']:
        return jsonify({
            "error": status['reason'],
            "next_eligible_at": status['next_eligible_at'],
            "cooldown_days": status['cooldown_days'],
        }), 400

    taxonomy = db.session.get(SkillTaxonomy, assessment.skill_id)
    if not taxonomy:
        return jsonify({"error": "Skill taxonomy not found"}), 404

    student = db.session.get(Student, assessment.student_id)
    student_skill = StudentSkill.query.filter_by(
        student_id=assessment.student_id,
        skill_id=assessment.skill_id,
    ).first()

    skill_settings = ((student.profile_data or {}).get('skill_settings') or {}) if student and isinstance(student.profile_data or {}, dict) else {}
    saved_setting = skill_settings.get(str(assessment.skill_id), {}) if isinstance(skill_settings, dict) else {}

    difficulty = _safe_int(saved_setting.get('difficulty', assessment.difficulty_level or 5), 5)
    proficiency_claimed = _safe_int(
        saved_setting.get('proficiency_claimed', assessment.proficiency_claimed or (student_skill.proficiency_claimed if student_skill else 5)),
        5,
    )

    num_questions, time_limit_minutes = _get_difficulty_config(difficulty)

    previous_assessments = Assessment.query.filter_by(
        student_id=assessment.student_id,
        skill_id=assessment.skill_id
    ).all()
    
    exclude_mcq_ids = set()
    for prev_a in previous_assessments:
        if isinstance(prev_a.questions, dict):
            for mcq in prev_a.questions.get('mcq', []):
                if isinstance(mcq, dict) and mcq.get('id'):
                    exclude_mcq_ids.add(mcq['id'])

    try:
        questions_data, source = _resolve_question_set(
            skill_id=assessment.skill_id,
            skill_name=taxonomy.skill_name,
            difficulty=difficulty,
            proficiency_claimed=proficiency_claimed,
            num_questions=num_questions,
            exclude_mcq_ids=exclude_mcq_ids
        )
    except Exception as e:
        return jsonify({"error": "AI generation failed", "details": str(e)}), 502

    new_assessment = Assessment(
        student_id=assessment.student_id,
        skill_id=assessment.skill_id,
        assessment_type='FULL_ASSESSMENT',
        questions=questions_data,
        status='generated',
        difficulty_level=difficulty,
        num_questions=num_questions,
        time_limit_minutes=time_limit_minutes,
        proficiency_claimed=proficiency_claimed,
    )
    db.session.add(new_assessment)
    db.session.commit()

    return jsonify({
        "status": "success",
        "assessment_id": new_assessment.id,
        "source": source,
        "difficulty": difficulty,
        "num_questions": num_questions,
        "time_limit_minutes": time_limit_minutes,
    }), 201
