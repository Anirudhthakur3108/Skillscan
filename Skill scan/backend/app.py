"""
SkillScan Flask Application Factory.
Main entry point for the Flask backend API.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from config import get_config

# Initialize extensions
db = SQLAlchemy()

# Configure logging
def setup_logging():
    """Configure application logging."""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, 'skillscan.log')
    
    # Rotating file handler (max 10MB, keep 10 backups)
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    
    return handler


def create_app(config_name='development'):
    """
    Flask Application Factory.
    Creates and configures Flask app with blueprints, CORS, and error handlers.
    
    Args:
        config_name (str): Configuration environment ('development', 'production', 'testing').
        
    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Setup logging
    log_handler = setup_logging()
    app.logger.addHandler(log_handler)
    app.logger.setLevel(logging.INFO)
    
    app.logger.info(f'Creating SkillScan app with config: {config_name}')
    
    # Initialize extensions
    db.init_app(app)
    
    # Enable CORS for React frontend
    cors_config = {
        'origins': app.config.get('CORS_ORIGINS', ['http://localhost:3000']),
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        'allow_headers': ['Content-Type', 'Authorization'],
        'supports_credentials': True
    }
    CORS(app, resources={r'/api/*': cors_config})
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register health check endpoint
    register_health_check(app)
    
    app.logger.info('SkillScan app initialized successfully')
    
    return app


def register_blueprints(app):
    """
    Register all route blueprints.
    
    Args:
        app (Flask): Flask application instance.
    """
    # Import blueprints
    from routes.auth import auth_bp
    from routes.students import students_bp
    from routes.skills import skills_bp
    from routes.assessments import assessments_bp
    from routes.results import results_bp
    from routes.learning_plans import learning_plans_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(students_bp, url_prefix='/api/students')
    app.register_blueprint(skills_bp, url_prefix='/api/skills')
    app.register_blueprint(assessments_bp, url_prefix='/api/assessments')
    app.register_blueprint(results_bp, url_prefix='/api/results')
    app.register_blueprint(learning_plans_bp, url_prefix='/api/learning-plans')
    
    app.logger.info('All blueprints registered')


def register_error_handlers(app):
    """
    Register global error handlers.
    
    Args:
        app (Flask): Flask application instance.
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            'status': 'error',
            'code': 400,
            'message': 'Bad request',
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors."""
        return jsonify({
            'status': 'error',
            'code': 401,
            'message': 'Unauthorized - authentication required',
            'timestamp': datetime.utcnow().isoformat()
        }), 401
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            'status': 'error',
            'code': 404,
            'message': 'Resource not found',
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        app.logger.error(f'Internal server error: {str(error)}')
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


def register_health_check(app):
    """
    Register health check endpoint.
    
    Args:
        app (Flask): Flask application instance.
    """
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for monitoring."""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'SkillScan Backend',
            'version': '1.0.0'
        }), 200


if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config.get('DEBUG', False)
    )
