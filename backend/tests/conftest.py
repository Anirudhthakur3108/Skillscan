import pytest
from app import create_app
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    # Uses the actual Supabase database via .env file
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def student_headers(app):
    with app.app_context():
        # Using a fixed ID for testing, assuming there is a valid student ID
        # Alternatively, you can use the API to register a test user and get the ID.
        # But for now, let's use a dummy UUID since JWT only needs it to be a string
        # in some places, or a real one if Supabase constraints require.
        # Let's create a real token for a known ID. We'll use a dummy UUID that exists
        # or we'll create a student in the test setup.
        # For this test we assume 'test_student_id_123' works for API endpoints,
        # but DB constraints might fail. We will create a test user via API.
        pass

@pytest.fixture
def setup_user(client):
    # Register a temporary test user
    import uuid
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "password123"
    
    # Register
    res = client.post('/auth/register', json={
        "email": test_email,
        "password": test_password,
        "full_name": "Test User"
    })
    
    if res.status_code == 201:
        data = res.get_json()
        token = data.get('access_token')
        user_id = data.get('student', {}).get('id')
    else:
        print("Register failed:", res.get_json())
        # Fallback to login if somehow it exists
        res = client.post('/auth/login', json={
            "email": test_email,
            "password": test_password
        })
        if res.status_code == 200:
            data = res.get_json()
            token = data.get('access_token')
            user_id = data.get('student', {}).get('id')
        else:
            print("Login failed:", res.get_json())
            raise Exception(f"Failed to setup user: {res.get_json()}")

    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    return {
        "headers": headers,
        "user_id": user_id,
        "email": test_email
    }
