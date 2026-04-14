# SkillScan MVP - Day 2 Setup & Testing Guide

## 🚀 Quick Start (Local Testing)

### Prerequisites
- Python 3.9+
- Node.js 16+
- Git
- Virtual environment

---

## 📦 BACKEND SETUP

### 1. Create Python Virtual Environment
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install PyPDF2 pdfplumber
```

### 3. Setup Environment
```bash
cp .env.example .env
```

**Update .env with:**
```
FLASK_ENV=development
SQLALCHEMY_DATABASE_URI=sqlite:///skillscan.db
JWT_SECRET_KEY=dev-secret-key-change-in-production
GEMINI_API_KEY=AIzaSyB9P_6sQDLh4bZYoFy_Fm3rSySaXdU7grw
LOG_LEVEL=INFO
```

### 4. Initialize Database
```bash
python
>>> from database import init_db
>>> init_db()
>>> exit()
```

### 5. Seed Data (Optional)
```bash
python seed_data.py
```

### 6. Run Tests (Resume Parser)
```bash
python -m pytest utils/test_resume_parser.py -v
python -m pytest utils/test_model_integration.py -v
```

### 7. Start Flask Server
```bash
python app.py
```

**Server runs on:** http://localhost:5000

---

## 🎨 FRONTEND SETUP

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Setup Environment
```bash
cp .env.example .env.local
```

**Update .env.local:**
```
VITE_API_BASE_URL=http://localhost:5000/api
VITE_APP_NAME=SkillScan
```

### 3. Start Development Server
```bash
npm run dev
```

**App runs on:** http://localhost:3000

---

## 🧪 LOCAL TESTING CHECKLIST

### Auth Flow Testing

**Test 1: User Registration**
```
1. Go to http://localhost:3000/register
2. Fill form:
   - Full Name: John Doe
   - Email: john@example.com
   - User Type: BCA
   - Password: password123
   - Confirm: password123
3. Click "Create Account"
4. Expected: Redirect to /profile, token in localStorage
```

**Test 2: User Login**
```
1. Go to http://localhost:3000/login
2. Fill form:
   - Email: john@example.com
   - Password: password123
3. Click "Sign In"
4. Expected: Redirect to /profile, token in localStorage
```

**Test 3: Protected Routes**
```
1. Clear localStorage (DevTools Console)
2. Try to access http://localhost:3000/profile
3. Expected: Redirect to /login
```

### Skills Flow Testing

**Test 4: Resume Upload (with sample)**
```
1. Go to /profile (after login)
2. Click resume upload area
3. Select test_resumes/resume_mba_analytics.txt (convert to PDF first)
4. Expected: Shows extracted skills with confidence scores
5. Click "Confirm & Add Skills"
6. Expected: Skills added to profile
```

**Test 5: Manual Skill Addition**
```
1. On /profile, scroll to "Add Skills Manually"
2. Type "Pyt" in skill search
3. Expected: Shows "Python" suggestion
4. Click "Python"
5. Drag proficiency slider to 8
6. Click "Add Skill"
7. Expected: Skill appears in "Your Skills" section
```

**Test 6: Custom Skill Addition**
```
1. On manual skill form, click "Or add a custom skill →"
2. Type: "Custom Skill Name"
3. Set proficiency to 5
4. Click "Add Skill"
5. Expected: Shows warning about custom skill, still adds it
```

**Test 7: Remove Skill**
```
1. In "Your Skills" section, click "Remove" on any skill
2. Confirm deletion
3. Expected: Skill removed immediately
```

---

## 🔍 API TESTING (POSTMAN/CURL)

### Register User
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "confirm_password": "password123",
    "full_name": "Test User",
    "user_type": "MBA_Analytics"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "code": 201,
  "token": "eyJ0eXAi...",
  "user_id": 1,
  "email": "test@example.com",
  "full_name": "Test User",
  "user_type": "MBA_Analytics"
}
```

### Login User
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### Upload Resume
```bash
curl -X POST http://localhost:5000/students/1/skills/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@resume.pdf"
```

**Expected Response:**
```json
{
  "status": "success",
  "extracted_skills": [
    {
      "skill_name": "Python",
      "confidence": 1.0
    },
    {
      "skill_name": "SQL",
      "confidence": 0.95
    }
  ],
  "stats": {
    "total_matches": 2,
    "exact_matches": 2,
    "fuzzy_matches": 0,
    "average_confidence": 0.975
  }
}
```

### Add Manual Skill
```bash
curl -X POST http://localhost:5000/students/1/skills/add-manual \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "skill_name": "Python",
    "proficiency_claimed": 8
  }'
```

### Get Skills
```bash
curl -X GET http://localhost:5000/students/1/skills \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🐛 Troubleshooting

### Backend Issues

**Error: "No module named 'PyPDF2'"**
```bash
pip install PyPDF2 pdfplumber
```

**Error: "Database not found"**
```bash
python
>>> from database import init_db
>>> init_db()
```

**Error: "JWT token invalid"**
- Make sure JWT_SECRET_KEY is set in .env
- Token should be in Authorization header as "Bearer <token>"

### Frontend Issues

**Error: "Cannot GET /profile"**
- Make sure backend is running on http://localhost:5000
- Check VITE_API_BASE_URL in .env.local

**Error: "CORS error"**
- Backend needs CORS enabled (configured in app.py)
- Verify frontend URL matches CORS_ORIGINS

**Error: "Blank page"**
- Check browser console for errors (F12)
- Make sure npm packages are installed (npm install)
- Restart dev server (npm run dev)

---

## 📊 Success Indicators

✅ All tests pass locally  
✅ Register → Login → Profile flow works  
✅ Resume upload extracts skills  
✅ Manual skill addition works  
✅ Skill removal works  
✅ Token persists in localStorage  
✅ Protected routes redirect to login  
✅ API returns proper JSON responses  
✅ No console errors in browser  
✅ No CORS errors  

---

## 🎯 Next Steps (Day 3+)

1. **Assessment Generation** - AI generates MCQ/Coding/Case Study
2. **Assessment UI** - Frontend forms for answering assessments
3. **Assessment Scoring** - AI scores responses, identifies gaps
4. **Dashboard** - Bar charts for scores, gap analysis
5. **Learning Plans** - AI generates personalized recommendations

---

## 📞 Support

For issues or questions:
1. Check logs (backend: console output, frontend: browser DevTools)
2. Verify .env configuration
3. Ensure all dependencies installed (pip install -r requirements.txt, npm install)
4. Clear cache (npm cache clean --force, pip cache purge)
