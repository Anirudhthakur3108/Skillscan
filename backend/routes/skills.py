from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError
from datetime import datetime
from extensions import db
from models import Student, StudentSkill, SkillTaxonomy, Assessment, AssessmentResponse, AssessmentScoreDetail, SkillScore, LearningPlan
from schemas import ManualSkillRequest
from skill_extractor import extract_skills_from_text

skills_bp = Blueprint('skills', __name__)


def _get_or_create_taxonomy(skill_name: str, category: str) -> SkillTaxonomy:
    """Get existing taxonomy entry or create a new one."""
    clean_name = skill_name.strip()
    entry = SkillTaxonomy.query.filter(SkillTaxonomy.skill_name.ilike(clean_name)).first()
    if not entry:
        entry = SkillTaxonomy(
            skill_name=clean_name,
            category=category,
            industry_benchmark=7,  # Default benchmark
        )
        db.session.add(entry)
        db.session.flush()  # Get ID without full commit
    return entry


@skills_bp.route('/<string:student_id>/skills/upload', methods=['POST'])
@jwt_required()
def upload_resume(student_id: str):
    """
    POST /students/{id}/skills/upload
    Accepts raw resume text or a 'skills_text' field.
    The text is processed immediately and discarded — never stored.
    """
    current_user_id = str(get_jwt_identity())
    if current_user_id != student_id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request must be JSON with a 'resume_text' field"}), 400

    resume_text = (data.get('resume_text') or data.get('skills_text', '') or '').strip()

    if not resume_text:
        return jsonify({"error": "No text provided"}), 400

    # Extract skills — text is used here and never persisted
    extracted = extract_skills_from_text(resume_text)
    del resume_text  # Explicitly discard from memory

    if not extracted:
        return jsonify({
            "status": "no_skills_found",
            "message": "No recognizable skills found. Try adding them manually.",
            "extracted_skills": []
        }), 200

    # Save extracted skills to DB
    saved = []
    for skill_data in extracted:
        taxonomy = _get_or_create_taxonomy(skill_data['skill_name'], skill_data['category'])

        # Skip duplicates
        exists = StudentSkill.query.filter_by(
            student_id=student_id, skill_id=taxonomy.id
        ).first()
        if exists:
            continue

        student_skill = StudentSkill(
            student_id=student_id,
            skill_id=taxonomy.id,
            proficiency_claimed=None,  # Will be assessed
            source='resume',
        )
        db.session.add(student_skill)
        saved.append({
            "skill_name": skill_data['skill_name'],
            "category": skill_data['category'],
            "confidence": skill_data['confidence'],
        })

    db.session.commit()

    return jsonify({
        "status": "success",
        "extracted_skills": saved,
        "total_found": len(saved),
    }), 200


@skills_bp.route('/<string:student_id>/skills', methods=['GET'])
@jwt_required()
def get_skills(student_id: str):
    """GET /students/{id}/skills — List all skills for a student."""
    current_user_id = str(get_jwt_identity())
    if current_user_id != student_id:
        return jsonify({"error": "Unauthorized"}), 403

    student = db.session.get(Student, student_id)
    profile_data = student.profile_data if student and isinstance(student.profile_data, dict) else {}
    skill_settings = profile_data.get('skill_settings', {}) if isinstance(profile_data, dict) else {}

    student_skills = (
        db.session.query(StudentSkill, SkillTaxonomy)
        .join(SkillTaxonomy, StudentSkill.skill_id == SkillTaxonomy.id)
        .filter(StudentSkill.student_id == student_id)
        .all()
    )

    skills_list = [
        {
            "id": ss.id,
            "skill_id": tax.id,
            "skill_name": tax.skill_name,
            "category": tax.category,
            "proficiency_claimed": ss.proficiency_claimed,
            "difficulty_configured": (skill_settings.get(str(tax.id), {}) or {}).get('difficulty') if isinstance(skill_settings, dict) else None,
            "source": ss.source,
            "industry_benchmark": tax.industry_benchmark,
        }
        for ss, tax in student_skills
    ]

    return jsonify({"skills": skills_list}), 200


@skills_bp.route('/<string:student_id>/skills/add-manual', methods=['POST'])
@jwt_required()
def add_manual_skill(student_id: str):
    """POST /students/{id}/skills/add-manual — Manually add a skill."""
    current_user_id = str(get_jwt_identity())
    if current_user_id != student_id:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        data = ManualSkillRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Validation failed", "details": e.errors()}), 400

    taxonomy = _get_or_create_taxonomy(data.skill_name, "General")

    # Check for duplicate
    exists = StudentSkill.query.filter_by(
        student_id=student_id, skill_id=taxonomy.id
    ).first()
    if exists:
        return jsonify({"error": f"'{data.skill_name}' is already in your profile"}), 409

    student_skill = StudentSkill(
        student_id=student_id,
        skill_id=taxonomy.id,
        proficiency_claimed=data.proficiency_claimed,
        source='manual',
    )
    db.session.add(student_skill)
    db.session.commit()

    return jsonify({
        "status": "success",
        "skill_id": student_skill.id,
        "skill_name": data.skill_name,
        "proficiency_claimed": data.proficiency_claimed,
    }), 201


@skills_bp.route('/<string:student_id>/skills/bulk-add', methods=['POST'])
@jwt_required()
def bulk_add_skills(student_id: str):
    """POST /students/{id}/skills/bulk-add — Manually add multiple skills."""
    current_user_id = str(get_jwt_identity())
    if current_user_id != student_id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    skills = data.get('skills', [])

    if not skills:
        return jsonify({"error": "No skills provided"}), 400

    saved = []
    for skill_item in skills:
        name = skill_item.get('name')
        category = skill_item.get('category', 'General')
        proficiency = skill_item.get('proficiency', 3)

        if not name:
            continue

        taxonomy = _get_or_create_taxonomy(name, category)

        # Check for duplicate
        exists = StudentSkill.query.filter_by(
            student_id=student_id, skill_id=taxonomy.id
        ).first()
        if exists:
            continue

        student_skill = StudentSkill(
            student_id=student_id,
            skill_id=taxonomy.id,
            proficiency_claimed=proficiency,
            source='manual',
        )
        db.session.add(student_skill)
        saved.append(name)

    db.session.commit()

    return jsonify({
        "status": "success",
        "added_skills": saved,
        "total_added": len(saved)
    }), 201


@skills_bp.route('/<string:student_id>/skills/configure', methods=['POST'])
@jwt_required()
def configure_skill_levels(student_id: str):
    """POST /students/{id}/skills/configure — Persist per-skill difficulty and proficiency selections."""
    current_user_id = str(get_jwt_identity())
    if current_user_id != student_id:
        return jsonify({"error": "Unauthorized"}), 403

    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    data = request.get_json(silent=True) or {}
    skills = data.get('skills', [])
    if not isinstance(skills, list) or not skills:
        return jsonify({"error": "skills list is required"}), 400

    profile_data = student.profile_data if isinstance(student.profile_data, dict) else {}
    skill_settings = profile_data.get('skill_settings', {}) if isinstance(profile_data, dict) else {}
    if not isinstance(skill_settings, dict):
        skill_settings = {}

    updated = []
    for item in skills:
        skill_id = item.get('skill_id')
        difficulty = item.get('difficulty')
        proficiency = item.get('proficiency_claimed')

        try:
            skill_id = int(skill_id)
            difficulty = int(difficulty)
            proficiency = int(proficiency)
        except (TypeError, ValueError):
            return jsonify({"error": "skill_id, difficulty and proficiency_claimed must be integers"}), 400

        if not (1 <= difficulty <= 10):
            return jsonify({"error": f"difficulty for skill_id={skill_id} must be between 1 and 10"}), 400
        if not (1 <= proficiency <= 10):
            return jsonify({"error": f"proficiency_claimed for skill_id={skill_id} must be between 1 and 10"}), 400

        student_skill = StudentSkill.query.filter_by(student_id=student_id, skill_id=skill_id).first()
        if not student_skill:
            return jsonify({"error": f"skill_id={skill_id} does not belong to the student"}), 404

        student_skill.proficiency_claimed = proficiency
        skill_settings[str(skill_id)] = {
            "difficulty": difficulty,
            "proficiency_claimed": proficiency,
            "configured_at": datetime.utcnow().isoformat(),
        }
        updated.append(skill_id)

    from sqlalchemy.orm.attributes import flag_modified

    profile_data['skill_settings'] = skill_settings
    student.profile_data = profile_data
    flag_modified(student, "profile_data")
    db.session.commit()

    return jsonify({
        "status": "success",
        "configured_skills": updated,
        "total_configured": len(updated),
    }), 200


@skills_bp.route('/<string:student_id>/skills/<int:skill_id>', methods=['DELETE'])
@jwt_required()
def delete_skill(student_id: str, skill_id: int):
    """DELETE /students/{student_id}/skills/{skill_id} — Remove a skill and ALL related data from the student's profile."""
    current_user_id = str(get_jwt_identity())
    if current_user_id != student_id:
        return jsonify({"error": "Unauthorized"}), 403

    # Find the student_skill record
    student_skill = StudentSkill.query.filter_by(
        student_id=student_id, skill_id=skill_id
    ).first()

    if not student_skill:
        return jsonify({"error": "Skill not found in your profile"}), 404

    # Get the skill name for the response
    taxonomy = db.session.get(SkillTaxonomy, skill_id)
    skill_name = taxonomy.skill_name if taxonomy else "Unknown"

    # --- Cascade delete all related data ---

    # 1. Find all assessments for this student + skill
    assessments = Assessment.query.filter_by(
        student_id=student_id, skill_id=skill_id
    ).all()
    assessment_ids = [a.id for a in assessments]

    if assessment_ids:
        # 2. Delete assessment responses for these assessments
        AssessmentResponse.query.filter(
            AssessmentResponse.assessment_id.in_(assessment_ids)
        ).delete(synchronize_session=False)

        # 3. Delete assessment score details for these assessments
        AssessmentScoreDetail.query.filter(
            AssessmentScoreDetail.assessment_id.in_(assessment_ids)
        ).delete(synchronize_session=False)

    # 4. Find all skill scores for this student + skill
    skill_scores = SkillScore.query.filter_by(
        student_id=student_id, skill_id=skill_id
    ).all()
    skill_score_ids = [ss.id for ss in skill_scores]

    if skill_score_ids:
        # 5. Delete learning plans linked to these skill scores
        LearningPlan.query.filter(
            LearningPlan.skill_gap_id.in_(skill_score_ids)
        ).delete(synchronize_session=False)

    # 6. Delete skill scores
    SkillScore.query.filter_by(
        student_id=student_id, skill_id=skill_id
    ).delete(synchronize_session=False)

    # 7. Delete assessments
    Assessment.query.filter_by(
        student_id=student_id, skill_id=skill_id
    ).delete(synchronize_session=False)

    # 8. Delete the student skill record itself
    db.session.delete(student_skill)

    # 9. Clean up skill_settings in profile_data
    student = db.session.get(Student, student_id)
    if student and isinstance(student.profile_data, dict):
        skill_settings = student.profile_data.get('skill_settings', {})
        if isinstance(skill_settings, dict) and str(skill_id) in skill_settings:
            del skill_settings[str(skill_id)]
            student.profile_data['skill_settings'] = skill_settings
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(student, "profile_data")

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"'{skill_name}' and all related data have been removed from your profile",
        "deleted_skill_id": skill_id,
        "deleted_assessments": len(assessment_ids),
        "deleted_skill_scores": len(skill_score_ids),
    }), 200

