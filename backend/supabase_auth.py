"""
Supabase Authentication Module

Provides JWT token verification and authentication decorator using Supabase.
Extracts Bearer token from Authorization header and verifies it.
"""

import os
import jwt
from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional, Dict, Any
from datetime import datetime
import requests

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET')


class SupabaseAuthError(Exception):
    """Raised when Supabase authentication fails."""
    pass


def extract_token(request_obj) -> Optional[str]:
    """
    Extract Bearer token from Authorization header.
    
    Args:
        request_obj: Flask request object
        
    Returns:
        Token string or None if not found
    """
    auth_header = request_obj.headers.get('Authorization', '')
    
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


def verify_supabase_token(token: str) -> Dict[str, Any]:
    """
    Verify Supabase JWT token and extract user info.
    
    Decodes the JWT using the Supabase JWT secret and validates:
    - Token signature
    - Token expiration
    - Token structure
    
    Args:
        token: JWT token string
        
    Returns:
        Dict with decoded token data including 'sub' (user_id)
        
    Raises:
        SupabaseAuthError: If token is invalid or expired
    """
    if not token:
        raise SupabaseAuthError('Token is missing')
    
    try:
        # Decode JWT using Supabase secret
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=['HS256'],
            options={'verify_exp': True}  # Verify expiration
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise SupabaseAuthError('Token has expired')
    except jwt.InvalidTokenError as e:
        raise SupabaseAuthError(f'Invalid token: {str(e)}')
    except Exception as e:
        raise SupabaseAuthError(f'Token verification failed: {str(e)}')


def get_user_from_token(token: str) -> Dict[str, Any]:
    """
    Get user information from valid Supabase token.
    
    Args:
        token: JWT token string
        
    Returns:
        User data from token payload
    """
    payload = verify_supabase_token(token)
    
    return {
        'user_id': payload.get('sub'),  # Supabase stores user ID in 'sub' claim
        'email': payload.get('email'),
        'aud': payload.get('aud'),  # Audience claim
        'iss': payload.get('iss'),  # Issuer claim
        'iat': payload.get('iat'),  # Issued at
        'exp': payload.get('exp'),  # Expiration time
        'raw_payload': payload
    }


def supabase_auth_required(f):
    """
    Decorator for Flask routes that require Supabase authentication.
    
    Extracts Bearer token from Authorization header, verifies it,
    and passes user info to the route handler.
    
    Usage:
        @app.route('/protected')
        @supabase_auth_required
        def protected_route(current_user):
            return jsonify({'user': current_user})
    
    Returns:
        401 Unauthorized if token missing, invalid, or expired
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = extract_token(request)
        
        if not token:
            return jsonify({
                'error': 'Authorization header missing',
                'message': 'Bearer token is required in Authorization header'
            }), 401
        
        try:
            current_user = get_user_from_token(token)
            return f(current_user, *args, **kwargs)
        
        except SupabaseAuthError as e:
            return jsonify({
                'error': 'Invalid token',
                'message': str(e)
            }), 401
        
        except Exception as e:
            return jsonify({
                'error': 'Authentication failed',
                'message': str(e)
            }), 401
    
    return decorated_function


def create_supabase_auth_middleware(app):
    """
    Create and attach Supabase authentication middleware to Flask app.
    
    Middleware:
    - Validates Supabase JWT tokens
    - Extracts user context
    - Makes user info available in g.current_user
    
    Args:
        app: Flask application instance
    """
    from flask import g
    
    @app.before_request
    def before_request():
        """Check token before each request if route requires it."""
        # Skip token validation for public routes
        public_routes = ['/health', '/auth/register', '/auth/login']
        
        if request.path in public_routes or request.path.startswith('/auth/'):
            return
        
        token = extract_token(request)
        
        if token:
            try:
                g.current_user = get_user_from_token(token)
            except SupabaseAuthError:
                # Token exists but is invalid - will be caught by decorator if needed
                g.current_user = None
        else:
            g.current_user = None


# Example usage documentation
"""
Example 1: Using the decorator on a route

    from flask import Blueprint, jsonify
    from supabase_auth import supabase_auth_required
    
    api_bp = Blueprint('api', __name__)
    
    @api_bp.route('/me', methods=['GET'])
    @supabase_auth_required
    def get_current_user(current_user):
        return jsonify({
            'user_id': current_user['user_id'],
            'email': current_user['email']
        }), 200

Example 2: Manual token verification in route

    from flask import Blueprint, request, jsonify
    from supabase_auth import extract_token, get_user_from_token, SupabaseAuthError
    
    api_bp = Blueprint('api', __name__)
    
    @api_bp.route('/me', methods=['GET'])
    def get_current_user():
        token = extract_token(request)
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        try:
            current_user = get_user_from_token(token)
            return jsonify({'user_id': current_user['user_id']}), 200
        except SupabaseAuthError as e:
            return jsonify({'error': str(e)}), 401

Example 3: Adding middleware to app

    app = create_app()
    create_supabase_auth_middleware(app)
"""
