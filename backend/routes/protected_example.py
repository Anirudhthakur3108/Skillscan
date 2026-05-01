"""
Example Protected Routes using Supabase Authentication

This file demonstrates how to use the @supabase_auth_required decorator
to protect your Flask routes with Supabase JWT authentication.

Each route shows:
- How to require authentication
- How to access current user information
- How to return proper error responses
"""

from flask import Blueprint, jsonify
from supabase_auth import supabase_auth_required
from extensions import db
from models import Student, Assessment

# Create blueprint
protected_bp = Blueprint('protected', __name__)


# ============================================================================
# Example 1: Get Current User Profile
# ============================================================================

@protected_bp.route('/api/me', methods=['GET'])
@supabase_auth_required
def get_current_user(current_user):
    """
    GET /api/me
    
    Returns current user's profile information.
    
    Headers Required:
        Authorization: Bearer <JWT_TOKEN>
    
    Returns:
        200 OK: User profile
        401 Unauthorized: Invalid/missing token
    """
    user_id = current_user['user_id']
    email = current_user['email']
    
    return jsonify({
        'status': 'success',
        'user_id': user_id,
        'email': email,
        'token_issued_at': current_user.get('iat'),
        'token_expires_at': current_user.get('exp')
    }), 200


# ============================================================================
# Example 2: Get User's Assessments
# ============================================================================

@protected_bp.route('/api/assessments', methods=['GET'])
@supabase_auth_required
def get_user_assessments(current_user):
    """
    GET /api/assessments
    
    Returns all assessments for the current user.
    
    Returns:
        200 OK: List of assessments
        401 Unauthorized: Invalid token
    """
    user_id = current_user['user_id']
    
    # In real app, you'd query from database
    # assessments = Assessment.query.filter_by(student_id=user_id).all()
    
    return jsonify({
        'status': 'success',
        'user_id': user_id,
        'assessments': [],
        'count': 0
    }), 200


# ============================================================================
# Example 3: Update User Profile
# ============================================================================

@protected_bp.route('/api/profile/update', methods=['POST'])
@supabase_auth_required
def update_profile(current_user):
    """
    POST /api/profile/update
    
    Update current user's profile information.
    
    Request Body:
    {
        "full_name": "John Doe",
        "profile_data": { "bio": "..." }
    }
    
    Returns:
        200 OK: Updated profile
        401 Unauthorized: Invalid token
        400 Bad Request: Invalid data
    """
    from flask import request
    
    user_id = current_user['user_id']
    data = request.get_json(silent=True) or {}
    
    # In real app:
    # student = Student.query.filter_by(id=user_id).first()
    # if not student:
    #     return jsonify({'error': 'User not found'}), 404
    # student.full_name = data.get('full_name')
    # db.session.commit()
    
    return jsonify({
        'status': 'success',
        'user_id': user_id,
        'message': 'Profile updated'
    }), 200


# ============================================================================
# Example 4: Get Leaderboard (Paginated)
# ============================================================================

@protected_bp.route('/api/leaderboard', methods=['GET'])
@supabase_auth_required
def get_leaderboard(current_user):
    """
    GET /api/leaderboard?page=1&limit=10
    
    Get skill leaderboard (user must be authenticated to view).
    
    Query Parameters:
        page: Page number (default 1)
        limit: Items per page (default 10)
    
    Returns:
        200 OK: Leaderboard data
        401 Unauthorized: Invalid token
    """
    from flask import request
    
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # In real app: query leaderboard from database
    
    return jsonify({
        'status': 'success',
        'user_id': current_user['user_id'],
        'page': page,
        'limit': limit,
        'leaderboard': []
    }), 200


# ============================================================================
# Example 5: Delete Account
# ============================================================================

@protected_bp.route('/api/account/delete', methods=['DELETE'])
@supabase_auth_required
def delete_account(current_user):
    """
    DELETE /api/account/delete
    
    Delete current user's account. Requires authentication.
    
    Returns:
        200 OK: Account deleted
        401 Unauthorized: Invalid token
        404 Not Found: User not found
    """
    user_id = current_user['user_id']
    
    # In real app:
    # student = Student.query.filter_by(id=user_id).first()
    # if not student:
    #     return jsonify({'error': 'User not found'}), 404
    # db.session.delete(student)
    # db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'Account {user_id} deleted successfully'
    }), 200


# ============================================================================
# REGISTRATION: How to Register with Supabase
# ============================================================================

# Note: Registration is typically handled by Supabase Auth UI or via:
# - supabase.auth.signUp() on frontend
# - Your /auth/register endpoint (already in routes/auth.py)
#
# Once registered, user gets a JWT token from Supabase
# Frontend stores this token (usually in localStorage)
# Frontend sends token in Authorization header for all authenticated requests


# ============================================================================
# Integration Example
# ============================================================================

"""
How to use in your app.py:

    from flask import Flask
    from routes.protected_example import protected_bp
    
    app = create_app()
    app.register_blueprint(protected_bp)
    
    # Now available:
    # GET  /api/me
    # GET  /api/assessments
    # POST /api/profile/update
    # GET  /api/leaderboard
    # DELETE /api/account/delete
"""


# ============================================================================
# Testing Examples
# ============================================================================

"""
Using curl to test protected routes:

1. Get a valid JWT token from Supabase
2. Store it in a variable:
   TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

3. Test endpoint:
   curl -H "Authorization: Bearer $TOKEN" \\
        http://localhost:5001/api/me

4. Test with invalid token (should return 401):
   curl -H "Authorization: Bearer invalid_token" \\
        http://localhost:5001/api/me

5. Test without token (should return 401):
   curl http://localhost:5001/api/me
"""
