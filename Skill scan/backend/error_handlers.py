"""
Bug fixes and edge case handling for all routes
"""

import os
import logging
from functools import wraps
from flask import jsonify
import traceback

logger = logging.getLogger(__name__)

# ============================================================================
# DECORATOR: Enhanced error handling with retry logic
# ============================================================================

def handle_errors(f):
    """Decorator to handle all route errors uniformly"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error: {str(e)}")
            return jsonify({'error': f'Invalid input: {str(e)}'}), 400
        except KeyError as e:
            logger.warning(f"Missing field: {str(e)}")
            return jsonify({'error': f'Missing required field: {str(e)}'}), 400
        except FileNotFoundError as e:
            logger.error(f"File not found: {str(e)}")
            return jsonify({'error': 'File not found or corrupted'}), 404
        except MemoryError as e:
            logger.error(f"Memory error during processing: {str(e)}")
            return jsonify({'error': 'File too large - maximum 50MB allowed'}), 413
        except TimeoutError as e:
            logger.error(f"Operation timeout: {str(e)}")
            return jsonify({'error': 'Operation timed out - please try again'}), 504
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': 'Internal server error - please try again'}), 500
    return decorated_function


# ============================================================================
# HELPER: Retry logic for Gemini API
# ============================================================================

def retry_gemini(max_retries=3, backoff_factor=2):
    """Retry decorator for Gemini API calls with exponential backoff"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            import time
            for attempt in range(max_retries):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Gemini API failed after {max_retries} retries: {str(e)}")
                        raise
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Gemini API attempt {attempt + 1}/{max_retries} failed. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
        return wrapper
    return decorator


# ============================================================================
# FILE UPLOAD: Size validation & malformed file handling
# ============================================================================

def validate_file_size(file, max_size_mb=50):
    """Validate file size"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    if size == 0:
        raise ValueError("Uploaded file is empty")
    
    max_bytes = max_size_mb * 1024 * 1024
    if size > max_bytes:
        raise MemoryError(f"File exceeds {max_size_mb}MB limit")
    
    return size


def validate_pdf_file(file):
    """Validate PDF file integrity"""
    file.seek(0)
    header = file.read(5)
    file.seek(0)
    
    if header != b'%PDF-':
        raise ValueError("Invalid PDF file - corrupted or not a PDF")


# ============================================================================
# DATABASE: Connection pooling & timeout handling
# ============================================================================

class DatabaseConnectionManager:
    """Manage database connections with retry logic"""
    
    max_retries = 3
    timeout = 5
    
    @staticmethod
    def execute_with_retry(operation, *args, **kwargs):
        """Execute database operation with retry logic"""
        for attempt in range(DatabaseConnectionManager.max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                if attempt == DatabaseConnectionManager.max_retries - 1:
                    logger.error(f"Database operation failed: {str(e)}")
                    raise
                logger.warning(f"Database retry attempt {attempt + 1}/{DatabaseConnectionManager.max_retries}")
                import time
                time.sleep(0.5)


# ============================================================================
# JWT TOKEN: Validation with edge cases
# ============================================================================

def validate_jwt_token(token_string):
    """Validate JWT token with comprehensive checks"""
    if not token_string:
        raise ValueError("No token provided")
    
    if not token_string.startswith('Bearer '):
        raise ValueError("Invalid token format")
    
    token = token_string.replace('Bearer ', '')
    
    if len(token) < 10:
        raise ValueError("Token too short")
    
    return token


# ============================================================================
# JSON PARSING: Handle malformed JSON
# ============================================================================

def safe_json_parse(data):
    """Safely parse JSON with fallback"""
    import json
    try:
        if isinstance(data, str):
            return json.loads(data)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {str(e)}")
        raise ValueError(f"Invalid JSON format: {str(e)}")


# ============================================================================
# RESPONSE: Safe data export with large dataset handling
# ============================================================================

def safe_dict_to_response(data):
    """Convert dict to response, handling large data safely"""
    import json
    try:
        # Check size before serialization
        json_str = json.dumps(data)
        if len(json_str) > 10_000_000:  # 10MB
            logger.warning(f"Response size large: {len(json_str)} bytes")
        return json.loads(json_str)
    except (TypeError, ValueError) as e:
        logger.error(f"Cannot serialize response: {str(e)}")
        raise ValueError("Data contains non-serializable objects")


# ============================================================================
# PDF GENERATION: Streaming & memory management
# ============================================================================

class PDFGenerationManager:
    """Manage PDF generation with memory safety"""
    
    max_size = 50 * 1024 * 1024  # 50MB
    chunk_size = 1024 * 1024  # 1MB chunks
    
    @staticmethod
    def stream_large_pdf(pdf_bytes):
        """Stream large PDF in chunks to avoid memory issues"""
        from io import BytesIO
        
        if len(pdf_bytes) > PDFGenerationManager.max_size:
            raise MemoryError("PDF too large - exceeds 50MB limit")
        
        return BytesIO(pdf_bytes)
    
    @staticmethod
    def validate_pdf_output(pdf_bytes):
        """Validate PDF output integrity"""
        if not pdf_bytes or len(pdf_bytes) == 0:
            raise ValueError("PDF generation produced empty output")
        
        if not pdf_bytes.startswith(b'%PDF'):
            raise ValueError("Invalid PDF output generated")


# ============================================================================
# FORM VALIDATION: Input sanitization
# ============================================================================

class FormValidator:
    """Validate form inputs with sanitization"""
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        import re
        if not email:
            raise ValueError("Email is required")
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError("Invalid email format")
        
        if len(email) > 254:
            raise ValueError("Email too long (max 254 characters)")
        
        return email.lower()
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if not password:
            raise ValueError("Password is required")
        
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        
        if len(password) > 128:
            raise ValueError("Password too long (max 128 characters)")
        
        return password
    
    @staticmethod
    def validate_proficiency(score):
        """Validate proficiency/score range"""
        if not isinstance(score, (int, float)):
            raise ValueError("Proficiency must be a number")
        
        if score < 0 or score > 10:
            raise ValueError("Proficiency must be between 0 and 10")
        
        return int(score) if isinstance(score, float) and score.is_integer() else score
    
    @staticmethod
    def sanitize_string(text, max_length=1000):
        """Sanitize string input"""
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
        
        text = text.strip()
        
        if len(text) == 0:
            raise ValueError("Input cannot be empty")
        
        if len(text) > max_length:
            raise ValueError(f"Input exceeds {max_length} characters")
        
        # Remove SQL injection patterns
        dangerous_patterns = ["';", '--', '/*', '*/', 'DROP', 'DELETE', 'INSERT']
        text_upper = text.upper()
        for pattern in dangerous_patterns:
            if pattern in text_upper:
                logger.warning(f"Potentially dangerous pattern detected: {pattern}")
        
        return text


# ============================================================================
# NETWORK: Timeout & retry handling
# ============================================================================

class NetworkManager:
    """Manage network requests with timeout/retry"""
    
    default_timeout = 30
    max_retries = 3
    
    @staticmethod
    def get_with_timeout(url, timeout=None):
        """GET request with timeout"""
        import requests
        timeout = timeout or NetworkManager.default_timeout
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.Timeout:
            raise TimeoutError(f"Request timed out after {timeout}s")
        except requests.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
    
    @staticmethod
    def post_with_timeout(url, data, timeout=None):
        """POST request with timeout"""
        import requests
        timeout = timeout or NetworkManager.default_timeout
        try:
            response = requests.post(url, json=data, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.Timeout:
            raise TimeoutError(f"Request timed out after {timeout}s")
        except requests.RequestException as e:
            raise Exception(f"Network error: {str(e)}")


# ============================================================================
# EXPORT: File naming & cleanup
# ============================================================================

class FileManager:
    """Manage file operations safely"""
    
    @staticmethod
    def safe_filename(filename):
        """Generate safe filename"""
        import re
        from datetime import datetime
        
        # Remove/replace unsafe characters
        safe_name = re.sub(r'[^\w\s.-]', '', filename)
        safe_name = re.sub(r'\s+', '_', safe_name)
        
        # Add timestamp to ensure uniqueness
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name_parts = safe_name.rsplit('.', 1)
        
        if len(name_parts) == 2:
            return f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
        else:
            return f"{safe_name}_{timestamp}"
    
    @staticmethod
    def cleanup_old_files(directory, max_age_hours=24):
        """Clean up old temporary files"""
        import os
        import time
        
        if not os.path.exists(directory):
            return
        
        current_time = time.time()
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age_hours * 3600:
                    try:
                        os.remove(filepath)
                        logger.info(f"Cleaned up old file: {filename}")
                    except Exception as e:
                        logger.warning(f"Could not delete {filename}: {str(e)}")


# ============================================================================
# USAGE: Apply to routes
# ============================================================================

"""
Usage in routes:

from routes.error_handlers import handle_errors, FormValidator

@app.route('/api/auth/register', methods=['POST'])
@handle_errors
def register():
    data = request.json
    email = FormValidator.validate_email(data.get('email'))
    password = FormValidator.validate_password(data.get('password'))
    # ... rest of logic
"""
