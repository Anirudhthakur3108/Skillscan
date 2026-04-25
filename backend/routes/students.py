from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Student, SkillTaxonomy

students_bp = Blueprint('students', __name__)


@students_bp.route('/<int:student_id>/profile', methods=['GET'])
@jwt_required()
def get_profile(student_id: int):
    """GET /students/{id}/profile"""
    current_user_id = int(get_jwt_identity())
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


@students_bp.route('/<int:student_id>/profile', methods=['PUT'])
@jwt_required()
def update_profile(student_id: int):
    """PUT /students/{id}/profile"""
    current_user_id = int(get_jwt_identity())
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
