import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from extensions import db, migrate

load_dotenv()

jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Database config — SQLite for local, swap DATABASE_URL for Supabase/Postgres in prod
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'skillscan.db')
    database_url = os.getenv('DATABASE_URL') or f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT config
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-please-change-in-prod')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # No expiry for MVP

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

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

    @app.route('/health')
    def health():
        return {'status': 'ok', 'version': '1.0.0'}

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)
