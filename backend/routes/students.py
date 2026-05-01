from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Student, SkillTaxonomy, StudentSkill

students_bp = Blueprint('students', __name__)


@students_bp.route('/<student_id>/profile', methods=['GET'])
@jwt_required()
def get_profile(student_id: str):
    """GET /students/{id}/profile"""
    current_user_id = get_jwt_identity()
    if current_user_id != student_id:
        return jsonify({"error": "Unauthorized"}), 403

    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    return jsonify({
        "id": student.id,
        "email": student.email,
        "full_name": student.full_name,
        "profile_data": student.profile_data or {},
        "created_at": student.created_at.isoformat(),
    }), 200


@students_bp.route('/<student_id>/profile', methods=['PUT'])
@jwt_required()
def update_profile(student_id: str):
    """PUT /students/{id}/profile"""
    current_user_id = get_jwt_identity()
    if current_user_id != student_id:
        return jsonify({"error": "Unauthorized"}), 403

    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    data = request.get_json() or {}
    if 'full_name' in data:
        student.full_name = data['full_name']
    if 'profile_data' in data:
        student.profile_data = data['profile_data']

    db.session.commit()
    return jsonify({"status": "success", "message": "Profile updated"}), 200


@students_bp.route('/<student_id>/skills', methods=['GET'])
@jwt_required()
def get_student_skills(student_id: str):
    """GET /students/{id}/skills — Get all skills for a student."""
    current_user_id = get_jwt_identity()
    if current_user_id != student_id:
        return jsonify({"error": "Unauthorized"}), 403

    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    profile_data = student.profile_data if isinstance(student.profile_data, dict) else {}
    skill_settings = profile_data.get('skill_settings', {}) if isinstance(profile_data, dict) else {}

    # Get student's skills
    student_skills = (
        db.session.query(StudentSkill, SkillTaxonomy)
        .join(SkillTaxonomy, StudentSkill.skill_id == SkillTaxonomy.id)
        .filter(StudentSkill.student_id == student_id)
        .all()
    )

    skills_list = [
        {
            "skill_id": skill.id,
            "skill_name": skill_taxo.skill_name,
            "category": skill_taxo.category,
            "proficiency_claimed": skill.proficiency_claimed,
            "difficulty_configured": (skill_settings.get(str(skill.id), {}) or {}).get('difficulty') if isinstance(skill_settings, dict) else None,
            "source": skill.source,
            "created_at": skill.created_at.isoformat() if skill.created_at else None
        }
        for skill, skill_taxo in student_skills
    ]

    return jsonify({"skills": skills_list}), 200
