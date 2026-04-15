"""
Authentication routes blueprint.
Handles user registration, login, logout, and JWT token management.
"""

import logging
import re
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from models import Student
from database import DatabaseManager
from utils.auth import (
    hash_password,
    verify_password,
    generate_jwt_token,
    decode_jwt_token,
    get_token_from_request,
    token_required
)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__)


def validate_email_format(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email (str): Email address to validate
    
    Returns:
        bool: True if valid format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple:
    """
    Validate password requirements (minimum 6 characters).
    
    Args:
        password (str): Password to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    return True, ""


def validate_user_type(user_type: str) -> bool:
    """
    Validate user type.
    
    Args:
        user_type (str): User type to validate
    
    Returns:
        bool: True if valid
    """
    valid_types = ['MBA_Analytics', 'BCA']
    return user_type in valid_types


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint.
    
    Expected JSON:
    {
        "email": "user@example.com",
        "password": "password123",
        "confirm_password": "password123",
        "full_name": "John Doe",
        "user_type": "MBA_Analytics" or "BCA"
    }
    
    Returns:
        JSON: {token, user_id, full_name, user_type, message}
    """
    session = DatabaseManager.get_session()
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'confirm_password', 'full_name', 'user_type']
        if not all(field in data for field in required_fields):
            logger.warning("Registration: Missing required fields")
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': 'Missing required fields: email, password, confirm_password, full_name, user_type'
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        full_name = data.get('full_name', '').strip()
        user_type = data.get('user_type', '').strip()
        
        # Validate email format
        if not validate_email_format(email):
            logger.warning(f"Registration: Invalid email format - {email}")
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': 'Invalid email format'
            }), 400
        
        # Validate password
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            logger.warning(f"Registration: {error_msg}")
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': error_msg
            }), 400
        
        # Verify password confirmation
        if password != confirm_password:
            logger.warning(f"Registration: Password mismatch for {email}")
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': 'Passwords do not match'
            }), 400
        
        # Validate user type
        if not validate_user_type(user_type):
            logger.warning(f"Registration: Invalid user_type - {user_type}")
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': 'Invalid user_type. Must be MBA_Analytics or BCA'
            }), 400
        
        # Validate full name
        if not full_name or len(full_name) < 2:
            logger.warning("Registration: Invalid full_name")
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': 'Full name must be at least 2 characters'
            }), 400
        
        # Check if email already exists
        existing_user = session.query(Student).filter_by(email=email).first()
        if existing_user:
            logger.warning(f"Registration: Email already exists - {email}")
            return jsonify({
                'status': 'error',
                'code': 409,
                'message': 'Email already registered'
            }), 409
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create new user
        new_user = Student(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            user_type=user_type
        )
        
        session.add(new_user)
        session.commit()
        
        # Generate token
        token = generate_jwt_token(new_user.id, new_user.email)
        
        logger.info(f"User registered successfully: {email} (ID: {new_user.id})")
        
        return jsonify({
            'status': 'success',
            'code': 201,
            'message': 'User registered successfully',
            'token': token,
            'user_id': new_user.id,
            'full_name': new_user.full_name,
            'email': new_user.email,
            'user_type': new_user.user_type
        }), 201
    except IntegrityError as e:
        session.rollback()
        logger.error(f"Database integrity error during registration: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 409,
            'message': 'Email already registered'
        }), 409
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error during registration: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error'
        }), 500
    finally:
        session.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint.
    
    Expected JSON:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    
    Returns:
        JSON: {token, user_id, email, full_name, user_type, message}
    """
    session = DatabaseManager.get_session()
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'email' not in data or 'password' not in data:
            logger.warning("Login: Missing email or password")
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': 'Missing email or password'
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validate email format
        if not validate_email_format(email):
            logger.warning(f"Login: Invalid email format - {email}")
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': 'Invalid email format'
            }), 400
        
        # Find user by email
        user = session.query(Student).filter_by(email=email).first()
        
        if not user:
            logger.warning(f"Login: User not found - {email}")
            return jsonify({
                'status': 'error',
                'code': 401,
                'message': 'Invalid email or password'
            }), 401
        
        # Verify password
        if not verify_password(password, user.password_hash):
            logger.warning(f"Login: Invalid password for {email}")
            return jsonify({
                'status': 'error',
                'code': 401,
                'message': 'Invalid email or password'
            }), 401
        
        # Generate token
        token = generate_jwt_token(user.id, user.email)
        
        logger.info(f"User logged in successfully: {email} (ID: {user.id})")
        
        return jsonify({
            'status': 'success',
            'code': 200,
            'message': 'Login successful',
            'token': token,
            'user_id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'user_type': user.user_type
        }), 200
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error'
        }), 500
    finally:
        session.close()


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    """
    User logout endpoint.
    
    Requires: Authorization header with Bearer token
    
    Returns:
        JSON: {message}
    """
    try:
        user_id = current_user.get('user_id')
        logger.info(f"User logged out: ID {user_id}")
        
        return jsonify({
            'status': 'success',
            'code': 200,
            'message': 'Logged out successfully'
        }), 200
    except Exception as e:
        logger.error(f"Unexpected error during logout: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error'
        }), 500


@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify(current_user):
    """
    Token verification endpoint.
    
    Requires: Authorization header with Bearer token
    
    Returns:
        JSON: {user_id, email, valid}
    """
    session = DatabaseManager.get_session()
    try:
        user_id = current_user.get('user_id')
        email = current_user.get('username')  # username field contains email
        
        # Verify user still exists in database
        user = session.get(Student, user_id)
        if not user:
            logger.warning(f"Token verification: User not found - ID {user_id}")
            return jsonify({
                'status': 'error',
                'code': 401,
                'message': 'User not found'
            }), 401
        
        logger.info(f"Token verified for user: {email}")
        
        return jsonify({
            'status': 'success',
            'code': 200,
            'user_id': user_id,
            'email': email,
            'valid': True
        }), 200
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error'
        }), 500
    finally:
        session.close()
