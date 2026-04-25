from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from typing import Optional
from models import (
    Student, StudentSkill, SkillTaxonomy,
    QuestionBank, Assessment, AssessmentResponse,
    SkillScore, LearningPlan
)
from ai_service import generate_assessment, score_assessment, generate_learning_plan

assessments_bp = Blueprint('assessments', __name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_from_question_bank(skill_id: int) -> Optional[dict]:
    """
    Check Question Bank for existing questions for this skill.
    Returns question data dict or None if not cached.
    """
    entry = QuestionBank.query.filter_by(
        skill_id=skill_id,
        question_type='FULL_ASSESSMENT'
    ).order_by(QuestionBank.created_at.desc()).first()
    return entry.question_data if entry else None


def _save_to_question_bank(skill_id: int, question_data: dict):
    """Cache generated questions for future reuse."""
    entry = QuestionBank(
        skill_id=skill_id,
        question_type='FULL_ASSESSMENT',
        question_data=question_data,
    )
    db.session.add(entry)
    db.session.commit()


# ─── Routes ───────────────────────────────────────────────────────────────────

@assessments_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate():
    """
    POST /assessments/generate
    Body: { student_id, skill_id }

    Checks Question Bank first to avoid unnecessary AI calls.
    If not cached, calls Mistral and caches the result.
    """
    try:
        current_user_id = int(get_jwt_identity())
    except Exception as e:
        return jsonify({"error": "Invalid token", "details": str(e)}), 401
    
    data = request.get_json() or {}
    student_id = data.get('student_id')
    skill_id = data.get('skill_id')

    if not student_id or not skill_id:
        return jsonify({"error": "student_id and skill_id are required"}), 400
    
    # Authorization check
    if int(current_user_id) != int(student_id):
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

    # ── Question Bank Check ──────────────────────────────────────────────────
    cached_questions = _get_from_question_bank(skill_id)
    if cached_questions:
        source = "question_bank"
        questions_data = cached_questions
    else:
        # ── AI Generation ────────────────────────────────────────────────────
        try:
            claimed_proficiency = student_skill.proficiency_claimed or 5
            ai_response = generate_assessment(taxonomy.skill_name, claimed_proficiency)
            questions_data = ai_response.model_dump()
            source = "ai_generated"
            _save_to_question_bank(skill_id, questions_data)
        except Exception as e:
            return jsonify({
                "error": "AI generation failed",
                "details": str(e)
            }), 502

    # Create Assessment record
    assessment = Assessment(
        student_id=student_id,
        skill_id=skill_id,
        assessment_type='FULL_ASSESSMENT',
        questions=questions_data,
        status='generated',
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
        "questions": questions_for_student,
    }), 201


def _strip_answers(questions_data: dict) -> dict:
    """Remove correct answers before sending to frontend."""
    import copy
    stripped = copy.deepcopy(questions_data)
    for q in stripped.get('mcq', []):
        q.pop('correct_option_id', None)
        q.pop('explanation', None)
    return stripped


@assessments_bp.route('/<int:assessment_id>/submit', methods=['POST'])
@jwt_required()
def submit(assessment_id: int):
    """
    POST /assessments/{id}/submit
    Body: { student_answers: { "mcq_1": "A", "code_1": "...", "case_1": "..." } }

    Scores the assessment via Mistral and saves results.
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    student_answers = data.get('student_answers', {})

    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404
    if current_user_id != assessment.student_id:
        return jsonify({"error": "Unauthorized"}), 403
    if assessment.status == 'completed':
        return jsonify({"error": "Assessment already submitted"}), 409

    taxonomy = db.session.get(SkillTaxonomy, assessment.skill_id)

    # ── AI Scoring ────────────────────────────────────────────────────────────
    try:
        score_result = score_assessment(
            skill_name=taxonomy.skill_name,
            questions=assessment.questions,
            student_answers=student_answers,
        )
    except Exception as e:
        return jsonify({"error": "AI scoring failed", "details": str(e)}), 502

    # Save response
    response_record = AssessmentResponse(
        assessment_id=assessment_id,
        student_response=student_answers,
        ai_feedback=score_result.model_dump(),
    )
    db.session.add(response_record)

    # Save skill score
    skill_score = SkillScore(
        student_id=assessment.student_id,
        skill_id=assessment.skill_id,
        assessment_id=assessment_id,
        score=score_result.overall_score,
        ai_reasoning=score_result.reasoning,
        gap_identified=score_result.gap_identified,
    )
    db.session.add(skill_score)

    # Update assessment status
    assessment.status = 'completed'
    db.session.commit()

    return jsonify({
        "status": "success",
        "assessment_id": assessment_id,
        "skill_name": taxonomy.skill_name,
        "overall_score": score_result.overall_score,
        "gap_identified": score_result.gap_identified,
        "strengths": score_result.strengths,
        "weaknesses": score_result.weaknesses,
        "reasoning": score_result.reasoning,
        "skill_score_id": skill_score.id,
    }), 200


@assessments_bp.route('/<int:assessment_id>', methods=['GET'])
@jwt_required()
def get_assessment(assessment_id: int):
    """GET /assessments/{id} — Get assessment details and results."""
    current_user_id = int(get_jwt_identity())
    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404
    if current_user_id != assessment.student_id:
        return jsonify({"error": "Unauthorized"}), 403

    taxonomy = db.session.get(SkillTaxonomy, assessment.skill_id)
    response = AssessmentResponse.query.filter_by(assessment_id=assessment_id).first()

    return jsonify({
        "assessment_id": assessment_id,
        "skill_name": taxonomy.skill_name if taxonomy else "Unknown",
        "status": assessment.status,
        "created_at": assessment.created_at.isoformat(),
        "questions": _strip_answers(assessment.questions) if assessment.status != 'completed' else None,
        "ai_feedback": response.ai_feedback if response else None,
    }), 200


@assessments_bp.route('/student/<int:student_id>', methods=['GET'])
@jwt_required()
def list_student_assessments(student_id: int):
    """GET /assessments/student/{id} — List all assessments for a student."""
    current_user_id = int(get_jwt_identity())
    if current_user_id != student_id:
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
