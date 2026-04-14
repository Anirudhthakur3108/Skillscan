"""
Authentication utilities module.
Provides JWT token handling, password hashing, and authentication helpers.
"""

import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
import bcrypt
from typing import Dict, Optional, Tuple


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.
    
    Args:
        password (str): Plain text password to hash.
        
    Returns:
        str: Bcrypt hashed password.
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify password against bcrypt hash.
    
    Args:
        password (str): Plain text password to verify.
        hashed_password (str): Bcrypt hashed password.
        
    Returns:
        bool: True if password matches, False otherwise.
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def generate_jwt_token(user_id: int, username: str) -> str:
    """
    Generate JWT authentication token.
    
    Args:
        user_id (int): User ID to include in token.
        username (str): Username to include in token.
        
    Returns:
        str: Encoded JWT token.
    """
    payload = {
        'user_id': user_id,
        'username': username,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(
            hours=current_app.config.get('JWT_EXPIRATION_HOURS', 24)
        )
    }
    
    token = jwt.encode(
        payload,
        current_app.config.get('JWT_SECRET_KEY'),
        algorithm=current_app.config.get('JWT_ALGORITHM', 'HS256')
    )
    
    return token


def decode_jwt_token(token: str) -> Optional[Dict]:
    """
    Decode and verify JWT token.
    
    Args:
        token (str): JWT token to decode.
        
    Returns:
        Optional[Dict]: Decoded token payload or None if invalid.
    """
    try:
        payload = jwt.decode(
            token,
            current_app.config.get('JWT_SECRET_KEY'),
            algorithms=[current_app.config.get('JWT_ALGORITHM', 'HS256')]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_token_from_request() -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    
    Returns:
        Optional[str]: JWT token or None if not found.
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None
    
    try:
        # Expected format: "Bearer <token>"
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            return parts[1]
    except Exception:
        pass
    
    return None


def token_required(f):
    """
    Decorator to require valid JWT token for endpoint.
    
    Args:
        f: Function to decorate.
        
    Returns:
        Wrapped function that checks JWT token.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({
                'status': 'error',
                'code': 401,
                'message': 'Missing authentication token'
            }), 401
        
        payload = decode_jwt_token(token)
        
        if not payload:
            return jsonify({
                'status': 'error',
                'code': 401,
                'message': 'Invalid or expired token'
            }), 401
        
        return f(payload, *args, **kwargs)
    
    return decorated
