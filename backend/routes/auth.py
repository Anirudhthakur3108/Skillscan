from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from pydantic import ValidationError
from extensions import db
from models import Student
from schemas import UserRegisterRequest, UserLoginRequest

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """POST /auth/register — Create a new student account."""
    try:
        data = UserRegisterRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Validation failed", "details": e.errors()}), 400

    # Check email uniqueness
    if Student.query.filter_by(email=data.email).first():
        return jsonify({"error": "Email already registered"}), 409

    student = Student(
        email=data.email,
        password_hash=generate_password_hash(data.password, method='pbkdf2:sha256'),
        full_name=data.full_name,
    )
    db.session.add(student)
    db.session.commit()

    token = create_access_token(identity=str(student.id))
    return jsonify({
        "status": "success",
        "message": "Account created successfully",
        "access_token": token,
        "student": {
            "id": student.id,
            "email": student.email,
            "full_name": student.full_name,
        }
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """POST /auth/login — Authenticate and return JWT."""
    try:
        data = UserLoginRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Validation failed", "details": e.errors()}), 400

    student = Student.query.filter_by(email=data.email).first()

    if not student or not check_password_hash(student.password_hash, data.password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(student.id))
    return jsonify({
        "status": "success",
        "access_token": token,
        "student": {
            "id": student.id,
            "email": student.email,
            "full_name": student.full_name,
        }
    }), 200
