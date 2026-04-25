from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError
from extensions import db
from models import Student, StudentSkill, SkillTaxonomy
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


@skills_bp.route('/<int:student_id>/skills/upload', methods=['POST'])
@jwt_required()
def upload_resume(student_id: int):
    """
    POST /students/{id}/skills/upload
    Accepts raw resume text or a 'skills_text' field.
    The text is processed immediately and discarded — never stored.
    """
    current_user_id = int(get_jwt_identity())
    if current_user_id != student_id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    resume_text = data.get('resume_text') or data.get('skills_text', '')

    if not resume_text.strip():
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


@skills_bp.route('/<int:student_id>/skills', methods=['GET'])
@jwt_required()
def get_skills(student_id: int):
    """GET /students/{id}/skills — List all skills for a student."""
    current_user_id = int(get_jwt_identity())
    if current_user_id != student_id:
        return jsonify({"error": "Unauthorized"}), 403

    student_skills = (
        db.session.query(StudentSkill, SkillTaxonomy)
        .join(SkillTaxonomy, StudentSkill.skill_id == SkillTaxonomy.id)
        .filter(StudentSkill.student_id == student_id)
        .all()
    )

    skills_list = [
        {
            "id": ss.id,
            "skill_name": tax.skill_name,
            "category": tax.category,
            "proficiency_claimed": ss.proficiency_claimed,
            "source": ss.source,
            "industry_benchmark": tax.industry_benchmark,
        }
        for ss, tax in student_skills
    ]

    return jsonify({"skills": skills_list}), 200


@skills_bp.route('/<int:student_id>/skills/add-manual', methods=['POST'])
@jwt_required()
def add_manual_skill(student_id: int):
    """POST /students/{id}/skills/add-manual — Manually add a skill."""
    current_user_id = int(get_jwt_identity())
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


@skills_bp.route('/<int:student_id>/skills/bulk-add', methods=['POST'])
@jwt_required()
def bulk_add_skills(student_id: int):
    """POST /students/{id}/skills/bulk-add — Manually add multiple skills."""
    current_user_id = int(get_jwt_identity())
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
