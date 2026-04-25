from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import SkillScore, LearningPlan, SkillTaxonomy
from ai_service import generate_learning_plan

learning_bp = Blueprint('learning', __name__)


@learning_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate():
    """
    POST /learning-plan/generate
    Body: { skill_score_id }

    Generates a personalized learning plan using Mistral Large
    for a specific identified skill gap.
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    skill_score_id = data.get('skill_score_id')

    if not skill_score_id:
        return jsonify({"error": "skill_score_id is required"}), 400

    skill_score = db.session.get(SkillScore, skill_score_id)
    if not skill_score:
        return jsonify({"error": "Skill score not found"}), 404
    if current_user_id != skill_score.student_id:
        return jsonify({"error": "Unauthorized"}), 403
    if not skill_score.gap_identified:
        return jsonify({"error": "No gap identified for this skill — learning plan not needed"}), 400

    taxonomy = db.session.get(SkillTaxonomy, skill_score.skill_id)

    # Check if plan already exists for this score
    existing = LearningPlan.query.filter_by(skill_gap_id=skill_score_id).first()
    if existing:
        return jsonify({
            "status": "exists",
            "learning_plan_id": existing.id,
            "plan": existing.recommendations,
        }), 200

    # ── AI Learning Plan Generation (Mistral Large) ───────────────────────────
    # Extract weaknesses from the scored assessment feedback
    from models import AssessmentResponse
    response_record = AssessmentResponse.query.filter_by(
        assessment_id=skill_score.assessment_id
    ).first()
    weaknesses = []
    if response_record and response_record.ai_feedback:
        weaknesses = response_record.ai_feedback.get('weaknesses', [])

    try:
        plan_result = generate_learning_plan(
            skill_name=taxonomy.skill_name,
            score=skill_score.score,
            weaknesses=weaknesses,
        )
    except Exception as e:
        return jsonify({"error": "Learning plan generation failed", "details": str(e)}), 502

    # Save plan to DB
    plan_data = plan_result.model_dump()
    learning_plan = LearningPlan(
        student_id=skill_score.student_id,
        skill_gap_id=skill_score_id,
        recommendations=plan_data,
        estimated_hours=plan_result.total_estimated_hours,
        priority=1,  # High by default since it's gap-identified
    )
    db.session.add(learning_plan)
    db.session.commit()

    return jsonify({
        "status": "success",
        "learning_plan_id": learning_plan.id,
        "skill_name": taxonomy.skill_name,
        "total_estimated_hours": plan_result.total_estimated_hours,
        "summary": plan_result.summary,
        "plan": plan_data,
    }), 201


@learning_bp.route('/student/<int:student_id>', methods=['GET'])
@jwt_required()
def list_plans(student_id: int):
    """GET /learning-plan/student/{id} — All learning plans for a student."""
    current_user_id = int(get_jwt_identity())
    if current_user_id != student_id:
        return jsonify({"error": "Unauthorized"}), 403

    plans = (
        db.session.query(LearningPlan, SkillTaxonomy, SkillScore)
        .join(SkillScore, LearningPlan.skill_gap_id == SkillScore.id)
        .join(SkillTaxonomy, SkillScore.skill_id == SkillTaxonomy.id)
        .filter(LearningPlan.student_id == student_id)
        .all()
    )

    result = [
        {
            "learning_plan_id": lp.id,
            "skill_name": tax.skill_name,
            "score": ss.score,
            "estimated_hours": lp.estimated_hours,
            "priority": lp.priority,
            "summary": lp.recommendations.get('summary', ''),
            "phases_count": len(lp.recommendations.get('phases', [])),
            "created_at": lp.created_at.isoformat(),
        }
        for lp, tax, ss in plans
    ]

    return jsonify({"learning_plans": result}), 200


@learning_bp.route('/<int:plan_id>', methods=['GET'])
@jwt_required()
def get_plan(plan_id: int):
    """GET /learning-plan/{id} — Full plan detail."""
    current_user_id = int(get_jwt_identity())
    plan = db.session.get(LearningPlan, plan_id)
    if not plan:
        return jsonify({"error": "Learning plan not found"}), 404
    if current_user_id != plan.student_id:
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify({
        "learning_plan_id": plan.id,
        "recommendations": plan.recommendations,
        "estimated_hours": plan.estimated_hours,
        "created_at": plan.created_at.isoformat(),
    }), 200
