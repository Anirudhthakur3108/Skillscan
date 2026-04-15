# 🚀 SkillScan Deployment Manual - Day 7 (MANUAL STEPS)

## ⚡ QUICK START (Zero Premium Requests)

This guide uses ONLY manual steps - no code generation needed. Follow step-by-step.

---

## STEP 1: CREATE SUPABASE POSTGRESQL DATABASE (5 minutes)

### 1.1 Create Supabase Project
1. Go to https://supabase.com
2. Click "Sign In" or "Sign Up"
3. Click "New Project"
4. Fill in:
   - **Project name:** skillscan-prod
   - **Database password:** [Generate strong password]
   - **Region:** Choose closest to you
5. Click "Create new project" (wait 2-3 minutes)

### 1.2 Get Database Credentials
1. Once project created, go to "Settings" → "Database"
2. Copy these values:
   - **Host:** `db.xxx.supabase.co`
   - **Port:** `5432`
   - **Database:** `postgres`
   - **User:** `postgres`
   - **Password:** [Your password from step 1.1]

3. Build connection string:
   ```
   postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres
   ```

### 1.3 Create Database Tables (Copy-Paste into SQL Editor)

1. In Supabase, go to "SQL Editor"
2. Click "New query"
3. Copy-paste this entire SQL block:

```sql
-- Create student table
CREATE TABLE IF NOT EXISTS student (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  user_type VARCHAR(50) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create skill table
CREATE TABLE IF NOT EXISTS skill (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) UNIQUE NOT NULL,
  category VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create student_skill table
CREATE TABLE IF NOT EXISTS student_skill (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES student(id) ON DELETE CASCADE,
  skill_id INTEGER NOT NULL REFERENCES skill(id),
  proficiency INTEGER CHECK (proficiency >= 0 AND proficiency <= 10),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create assessment table
CREATE TABLE IF NOT EXISTS assessment (
  id SERIAL PRIMARY KEY,
  skill_id INTEGER NOT NULL REFERENCES skill(id),
  type VARCHAR(50),
  difficulty VARCHAR(50),
  questions_data TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create assessment_response table
CREATE TABLE IF NOT EXISTS assessment_response (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES student(id) ON DELETE CASCADE,
  assessment_id INTEGER NOT NULL REFERENCES assessment(id),
  responses_data TEXT,
  time_taken INTEGER,
  score FLOAT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create skill_score table
CREATE TABLE IF NOT EXISTS skill_score (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES student(id) ON DELETE CASCADE,
  skill_id INTEGER NOT NULL REFERENCES skill(id),
  score FLOAT,
  assessment_type VARCHAR(50),
  assessment_id INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create gap_analysis table
CREATE TABLE IF NOT EXISTS gap_analysis (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES student(id) ON DELETE CASCADE,
  skill_id INTEGER NOT NULL REFERENCES skill(id),
  gaps TEXT,
  priority VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create learning_plan table
CREATE TABLE IF NOT EXISTS learning_plan (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES student(id) ON DELETE CASCADE,
  skill_id INTEGER NOT NULL REFERENCES skill(id),
  duration_weeks INTEGER,
  recommendations TEXT,
  progress INTEGER DEFAULT 0,
  status VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_student_email ON student(email);
CREATE INDEX IF NOT EXISTS idx_student_skill_student ON student_skill(student_id);
CREATE INDEX IF NOT EXISTS idx_assessment_response_student ON assessment_response(student_id);
CREATE INDEX IF NOT EXISTS idx_skill_score_student_skill ON skill_score(student_id, skill_id);
CREATE INDEX IF NOT EXISTS idx_learning_plan_active ON learning_plan(student_id, status);
```

4. Click "Run" and wait for success ✅

### 1.4 Seed Skill Taxonomy (Copy-Paste this SQL)

1. Click "New query" again
2. Copy-paste:

```sql
-- Insert skill taxonomy (18 skills)
INSERT INTO skill (name, category) VALUES
('Python', 'Programming'),
('Java', 'Programming'),
('C++', 'Programming'),
('JavaScript', 'Web Development'),
('React', 'Frontend'),
('Web Dev', 'Frontend'),
('SQL', 'Database'),
('Data Structures', 'Computer Science'),
('System Design', 'Architecture'),
('Excel/VBA', 'Business Tools'),
('Tableau', 'Data Visualization'),
('Power BI', 'Data Visualization'),
('Statistics', 'Analytics'),
('Data Analysis', 'Analytics'),
('R', 'Programming'),
('ML', 'Machine Learning'),
('Git', 'DevOps'),
('Docker', 'DevOps')
ON CONFLICT (name) DO NOTHING;
```

3. Click "Run" ✅

---

## STEP 2: PREPARE BACKEND FOR RENDER (5 minutes)

### 2.1 Verify Procfile exists
- Check: `C:\Users\thaku\Projects\Skill scan\Skill scan\Procfile`
- Content should be:
  ```
  web: gunicorn "app:create_app()" --workers 3 --worker-class sync --timeout 120 --bind 0.0.0.0:$PORT
  ```

### 2.2 Verify requirements.txt
- Check: `C:\Users\thaku\Projects\Skill scan\backend\requirements.txt`
- Should contain all dependencies including:
  - `gunicorn>=20.1.0`
  - `flask`
  - `sqlalchemy`
  - `psycopg2-binary`
  - `google-generativeai`
  - All others listed

### 2.3 Final Git Commit
```bash
cd "C:\Users\thaku\Projects\Skill scan"
git add -A
git commit -m "Day 7: Deployment Configuration - Procfile and Environment Files"
git push origin main
```

---

## STEP 3: DEPLOY BACKEND TO RENDER (15 minutes)

### 3.1 Create Render Account
1. Go to https://render.com
2. Sign up with GitHub account (easier!)
3. Verify email

### 3.2 Create Web Service on Render

1. Click "New +"
2. Select "Web Service"
3. Connect GitHub:
   - Select your repo: `Anirudhthakur3108/Skillscan`
   - Select branch: `main`
   - Root directory: `Skill scan` (leave blank if folder not needed)

4. Configure Service:
   - **Name:** skillscan-backend
   - **Environment:** Python 3
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `gunicorn "app:create_app()" --workers 3 --timeout 120`

5. Add Environment Variables (click "Advanced"):
   - **FLASK_ENV:** production
   - **DATABASE_URL:** `postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres`
     (Replace with your Supabase credentials from Step 1)
   - **GEMINI_API_KEY:** `AIzaSyB9P_6sQDLh4bZYoFy_Fm3rSySaXdU7grw`
   - **JWT_SECRET:** Generate 32 random characters (use: `abcdefghijklmnopqrstuvwxyz123456`)
   - **CORS_ORIGINS:** `https://skillscan.vercel.app`
   - **LOG_LEVEL:** INFO

6. Select Plan: **Free** tier (or Pro if needed)

7. Click "Create Web Service"
   - **WAIT: 5-10 minutes for build & deployment** ⏳

### 3.3 Verify Backend Deployment

Once deployed, you'll get a URL like: `https://skillscan-backend.onrender.com`

Test it:
```bash
# In PowerShell:
Invoke-WebRequest -Uri "https://skillscan-backend.onrender.com/api/health" -Headers @{"Authorization"="Bearer test"}
```

Should return: `{"status": "healthy"}` ✅

---

## STEP 4: PREPARE FRONTEND FOR VERCEL (5 minutes)

### 4.1 Create .env.local in frontend
- File: `C:\Users\thaku\Projects\Skill scan\frontend\.env.local`
- Content:
  ```
  VITE_API_URL=https://skillscan-backend.onrender.com/api
  VITE_APP_NAME=SkillScan
  VITE_ENVIRONMENT=production
  ```

### 4.2 Build Frontend Bundle
```bash
cd "C:\Users\thaku\Projects\Skill scan\frontend"
npm install
npm run build
```
- Should complete in <1 minute
- Creates `dist/` folder (~300-500KB)

### 4.3 Test Build Locally
```bash
npm run preview
```
- Visit http://localhost:4173
- Verify page loads ✅

---

## STEP 5: DEPLOY FRONTEND TO VERCEL (10 minutes)

### 5.1 Create Vercel Account
1. Go to https://vercel.com
2. Sign up with GitHub
3. Verify email

### 5.2 Create Frontend Project on Vercel

1. Click "Add New..." → "Project"
2. Import Git Repository:
   - Select: `Anirudhthakur3108/Skillscan`
3. Configure Project:
   - **Project Name:** skillscan
   - **Framework:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`

4. Add Environment Variables:
   - **VITE_API_URL:** `https://skillscan-backend.onrender.com/api`
   - **VITE_ENVIRONMENT:** `production`

5. Click "Deploy"
   - **WAIT: 2-5 minutes for build & deployment** ⏳

### 5.3 Verify Frontend Deployment

Once deployed, you'll get a URL like: `https://skillscan.vercel.app`

Test it:
1. Open https://skillscan.vercel.app in browser
2. Page should load within 3 seconds ✅
3. Try login/register (will fail if backend not ready, but page loads) ✅

---

## STEP 6: PRODUCTION VERIFICATION (30 minutes)

### 6.1 Test New User Registration

1. Open https://skillscan.vercel.app
2. Click "Sign Up"
3. Fill in:
   - Email: `test@skillscan.com`
   - Password: `TestPassword123`
   - User Type: `BCA`
4. Click "Register"
5. Should redirect to profile page ✅

### 6.2 Test Skill Management

1. On profile page, click "Add Skill"
2. Search for "Python"
3. Set proficiency to 8
4. Click "Add"
5. Verify skill appears in list ✅

### 6.3 Test Assessment

1. Click "Start Assessment"
2. Select skill: Python
3. Select difficulty: Easy
4. Select type: MCQ
5. Click "Generate"
6. Answer 5-6 questions
7. Click "Submit"
8. Verify score displays ✅

### 6.4 Test Error Scenarios

**Test Timeout:**
1. DevTools → Network → Slow 3G
2. Try any API call
3. Should show error + retry button ✅

**Test Validation:**
1. Try login with email "invalid"
2. Should show error message ✅

### 6.5 Test Export

1. Go to Export page
2. Select format: PDF
3. Click "Export Profile"
4. File should download ✅

---

## STEP 7: FINAL CHECKLIST & GO-LIVE ✅

### 7.1 Production Verification Checklist

```
Backend (Render):
[ ] Service deployed and running (green status)
[ ] API responds to health check
[ ] Database connected (check logs)
[ ] No critical errors in logs
[ ] Response time <500ms

Frontend (Vercel):
[ ] Site deployed and live
[ ] Page loads in <3s
[ ] API calls work
[ ] No console errors
[ ] Mobile responsive

Database (Supabase):
[ ] All 8 tables created
[ ] Indexes created
[ ] Skills populated (18 items)
[ ] Can connect from backend

User Journey:
[ ] Register → Login → Profile works
[ ] Add skill works
[ ] Assessment works
[ ] Export works
[ ] Error handling works
```

### 7.2 Share Deployment URLs

Share these with stakeholders:
- **Frontend (Public):** https://skillscan.vercel.app
- **Backend API (Internal):** https://skillscan-backend.onrender.com/api
- **Database (Internal):** Supabase PostgreSQL

### 7.3 Create Demo Account

For testing/demo purposes:
- Email: `demo@skillscan.com`
- Password: `Demo@123456`
- User Type: `BCA`

### 7.4 Setup Monitoring

**Render:**
1. Go to service settings
2. Enable auto-redeploy on git push
3. Set up Slack alerts (optional)

**Vercel:**
1. Project settings
2. Enable automatic deployments from main branch

---

## 🎉 DEPLOYMENT COMPLETE!

**Timeline:**
- Supabase setup: 5 min
- Backend prep: 5 min
- Render deployment: 15 min (mostly waiting)
- Frontend prep: 5 min
- Vercel deployment: 10 min (mostly waiting)
- Verification: 30 min
- **TOTAL: ~70 minutes (1 hour 10 min)**

**Status:** 🟢 LIVE IN PRODUCTION

---

## 📝 TROUBLESHOOTING

### Backend won't start
- Check Procfile syntax
- Verify DATABASE_URL is correct
- Check Render logs for errors
- Verify all env vars are set

### Frontend can't connect to backend
- Check VITE_API_URL is correct
- Verify backend is running
- Check CORS settings in backend
- Check browser console for errors

### Database connection fails
- Verify connection string format
- Check Supabase firewall settings
- Verify password doesn't have special chars
- Test connection from SQL Editor first

### Tests failing in production
- Check env variables match
- Verify database tables exist
- Check JWT secret is set correctly
- Look at Render logs for details

---

## ✅ POST-LAUNCH CHECKLIST

- [ ] Monitor error logs for 24 hours
- [ ] Check uptime (should be 99.9%+)
- [ ] Monitor API response times
- [ ] Check database query performance
- [ ] Collect user feedback
- [ ] Plan Phase 2 improvements

---

**Deployment Date:** 2026-04-16  
**Status:** 🟢 READY FOR MANUAL DEPLOYMENT  
**Timeline:** 70 minutes total  
**Premium Requests Used:** 0 (All manual steps)

