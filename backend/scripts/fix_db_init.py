import re

with open('db_init.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the create_minimal_app function
content = content.replace(
    '''def create_minimal_app():
    \"\"\"Create Flask app without loading routes that depend on mistralai.\"\"\"
    app = Flask(__name__)
    db.init_app(app)
    return app''',
    '''def create_minimal_app():
    \"\"\"Create Flask app without loading routes that depend on mistralai.\"\"\"
    app = Flask(__name__)
    # Don't initialize db here - do it after config is set
    return app'''
)

# Also need to add db.init_app(app) after the config is set in main()
content = content.replace(
    '''        # Create missing tables
    try:
        print('\\n' + '-'*60)
        app = create_minimal_app()
        
        # Configure database
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False''',
    '''        # Create missing tables
    try:
        print('\\n' + '-'*60)
        app = create_minimal_app()
        
        # Configure database
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize db with configured app
        db.init_app(app)'''
)

with open('db_init.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Success')
