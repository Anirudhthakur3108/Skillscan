import os
import re
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from extensions import db, migrate
from supabase_auth import create_supabase_auth_middleware

load_dotenv()

jwt = JWTManager()


def _parse_cors_origins() -> list[object]:
    raw_origins = os.getenv('CORS_ORIGINS', '')
    origins: list[object] = []

    for origin in [value.strip() for value in raw_origins.split(',') if value.strip()]:
        if '*' in origin:
            escaped = re.escape(origin).replace(r'\*', '.*')
            origins.append(re.compile(f'^{escaped}$'))
        else:
            origins.append(origin)

    if origins:
        return origins

    return [
        'http://localhost:5173',
        'http://localhost:4173',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:4173',
    ]

def create_app():
    app = Flask(__name__)
    # Enable CORS for the frontend origins we explicitly allow.
    CORS(
        app,
        resources={r"/*": {"origins": _parse_cors_origins()}},
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # Database config — Use SUPABASE_URL for PostgreSQL connection
    # Falls back to SQLite for local development if SUPABASE_URL not set
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'skillscan.db')
    database_url = os.getenv('SUPABASE_URL') or f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT config
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-please-change-in-prod')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # No expiry for MVP

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Initialize Supabase authentication middleware
    create_supabase_auth_middleware(app)

    # Better JSON error responses for JWT issues so frontend can act on them
    @jwt.unauthorized_loader
    def _jwt_unauthorized_callback(reason):
        return {'error': 'Authorization header missing or malformed', 'message': reason}, 401

    @jwt.invalid_token_loader
    def _jwt_invalid_token_callback(reason):
        return {'error': 'Invalid JWT', 'message': reason}, 422

    @jwt.expired_token_loader
    def _jwt_expired_token_callback(header, payload):
        return {'error': 'Token expired'}, 401

    @jwt.revoked_token_loader
    def _jwt_revoked_token_callback(header, payload):
        return {'error': 'Token revoked'}, 401

    # Register blueprints
    from routes.auth import auth_bp
    from routes.assessments import assessments_bp
    from routes.skills import skills_bp
    from routes.students import students_bp
    from routes.learning_plan import learning_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(assessments_bp, url_prefix='/assessments')
    app.register_blueprint(skills_bp, url_prefix='/students')
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(learning_bp, url_prefix='/learning-plan')

    # For local development, ensure the SQLite DB tables exist.
    # This avoids 500 errors when migrations haven't been run.
    if app.config.get('ENV') == 'development' or os.getenv('AUTO_CREATE_DB', 'true').lower() in ('1','true','yes'):
        with app.app_context():
            try:
                # Import models so SQLAlchemy knows about them
                from models import Student, SkillTaxonomy, StudentSkill, QuestionBank, Assessment, AssessmentResponse, AssessmentScoreDetail, SkillScore, LearningPlan
                db.create_all()
            except Exception as e:
                # Don't crash startup — log and continue. Errors will still appear on DB ops.
                print('Warning: failed to create DB tables automatically:', e)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'version': '1.0.0'}

    return app

# Create app instance at module level for Gunicorn/other WSGI servers
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
