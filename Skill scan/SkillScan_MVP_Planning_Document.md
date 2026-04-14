# SkillScan MVP - Complete Planning Document

**Project:** SkillScan - Skill Verification & Gap Analysis Platform  
**Target Users:** Tier 2/3 College Students in India  
**Phase:** MVP (Minimum Viable Product)  
**Status:** Planning & Documentation  
**Date Created:** 2026-04-11

---

## 1. Executive Summary

SkillScan is a data-driven skill verification platform designed to help Tier 2/3 college students assess their skills, identify gaps, and receive personalized learning recommendations. The MVP will enable students to:
- Upload/input their skills (resume/text)
- Take AI-generated assessments (MCQ, coding, case study)
- Receive skill scores and gap analysis
- Get personalized learning plans
- View results in a dashboard
- Export results and earn digital badges

**MVP Timeline:** 8-12 weeks (from architecture to deployment)  
**Target Launch:** Local testing in 4 weeks, cloud deployment in 8 weeks

---

## 2. MVP Scope & Features

### 2.1 Core Features (Priority Order)

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 1 | Student Profile & Input | Students create account, upload resume/input skills manually | MVP-1 |
| 2 | Assessment Generation | AI generates tailored assessments (MCQ, coding, case study) based on skills | MVP-1 |
| 3 | Skill Scoring & Gap Analysis | AI scores assessments (1-10 scale), identifies skill gaps, compares to industry benchmarks | MVP-1 |
| 4 | Personalized Learning Plan | AI generates custom learning recommendations based on gaps | MVP-1 |
| 5 | Dashboard & Results Display | Visual skill summary, assessment history, progress tracking | MVP-1 |
| 6 | Export Results | PDF, CSV export of assessments and learning plans | MVP-1 |
| 7 | Digital Badges | Award badges for skill verification milestones | MVP-2 (optional) |

### 2.2 Out of Scope (MVP)
- Social features (sharing, collaboration)
- Advanced analytics (trend analysis, cohort comparison)
- Mobile app (web-only initially)
- Payment/subscription system
- Employer integrations

---

## 3. Technical Architecture

### 3.1 Tech Stack

```
Frontend:
  - React (TypeScript)
  - Tailwind CSS (styling)
  - Axios (HTTP client)
  - Recharts (dashboard visualizations)

Backend:
  - Python 3.10+
  - Flask + Flask-CORS
  - SQLAlchemy (ORM)
  - Pydantic (validation)

Database:
  - Development: SQLite
  - Production: PostgreSQL

NLP & Processing:
  - spaCy (resume parsing, text processing)
  - NLTK (text analysis)

AI Model Integration:
  - Free model API (Gemini, Groq, etc.)
  - requests/httpx library

Authentication:
  - JWT (JSON Web Tokens)
  - bcrypt (password hashing)

Local Testing:
  - Flask development server
  - React dev server (npm)

Cloud Deployment:
  - Backend: Railway or Render
  - Frontend: Vercel
  - Database: PostgreSQL managed service
```

### 3.2 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    SKILLSCAN MVP ARCHITECTURE                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  FRONTEND (React + TypeScript)                               │
│  ├─ Student Dashboard                                        │
│  ├─ Profile & Input Form                                     │
│  ├─ Assessment Interface                                     │
│  ├─ Results & Gap Analysis                                   │
│  └─ Export & Badges Page                                     │
│                          ↓ (Axios HTTP)                      │
│  ┌───────────────────────────────────────────────────────┐   │
│  │      API GATEWAY / AUTHENTICATION LAYER              │   │
│  │  ├─ JWT Token Validation                             │   │
│  │  └─ CORS Policy                                      │   │
│  └───────────────────────────────────────────────────────┘   │
│                          ↓                                    │
│  BACKEND (Flask + Python)                                    │
│  ├─ /auth/register, /auth/login                              │
│  ├─ /students/{id}/profile                                   │
│  ├─ /assessments/generate                                    │
│  ├─ /assessments/{id}/submit                                 │
│  ├─ /assessments/{id}/score                                  │
│  ├─ /learning-plan/{id}                                      │
│  ├─ /results/{id}                                            │
│  └─ /export/{id}                                             │
│                          ↓                                    │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  AI MODEL INTEGRATION LAYER                          │   │
│  │  ├─ Assessment Generator (NLP + Model API)          │   │
│  │  ├─ Skill Scorer (Model API)                        │   │
│  │  └─ Learning Plan Generator (Model API)             │   │
│  └───────────────────────────────────────────────────────┘   │
│                          ↓                                    │
│  DATABASE LAYER (SQLAlchemy ORM)                             │
│  ├─ Students Table                                           │
│  ├─ Assessments Table                                        │
│  ├─ Results Table                                            │
│  ├─ Learning Plans Table                                     │
│  └─ Skills Taxonomy Table                                    │
│                          ↓                                    │
│  STORAGE (PostgreSQL / SQLite)                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. User Workflow

### 4.1 Student Journey (Happy Path)

```
1. REGISTRATION
   ├─ Student signs up with email/password
   ├─ Profile created in database
   └─ JWT token issued

2. SKILL INPUT
   ├─ Upload resume (PDF/TXT) OR manually enter skills
   ├─ Backend parses resume (spaCy) or accepts manual input
   ├─ Skills extracted and stored
   └─ Show "Skills identified: Java, Python, React, etc."

3. ASSESSMENT GENERATION
   ├─ AI generates 3 assessments (MCQ, Coding, Case Study)
   ├─ Assessments tailored to identified skills
   ├─ Display assessments on frontend
   └─ Student can review before starting

4. ASSESSMENT COMPLETION
   ├─ Student takes all 3 assessments
   ├─ Answers submitted to backend
   ├─ Backend stores responses
   └─ Show "Assessment submitted for scoring"

5. SKILL SCORING & GAP ANALYSIS
   ├─ AI scores each assessment (1-10 scale per skill)
   ├─ Identifies skill gaps (areas < 5/10)
   ├─ Compares to industry benchmarks
   ├─ Generate gap report
   └─ Results saved to database

6. LEARNING PLAN GENERATION
   ├─ AI generates personalized learning recommendations
   ├─ Includes courses, projects, resources for each gap
   ├─ Estimated time to upskill
   └─ Save to database

7. DASHBOARD & RESULTS
   ├─ Student views skill dashboard (visualized scores)
   ├─ See identified gaps
   ├─ View learning plan
   ├─ Track progress
   └─ Option to export or badge

8. EXPORT & BADGES
   ├─ Export assessment results (PDF/CSV)
   ├─ Receive digital badges for verified skills
   ├─ Download badge certificate
   └─ Share results (optional)
```

---

## 5. Data Models & Database Schema

### 5.1 Core Tables

```
STUDENTS
├─ id (PK)
├─ email (UNIQUE)
├─ password_hash
├─ full_name
├─ created_at
├─ updated_at
└─ profile_data (JSON)

SKILLS_TAXONOMY
├─ id (PK)
├─ skill_name
├─ category (Backend, Frontend, etc.)
├─ industry_benchmark (1-10)
└─ subcategories (JSON)

STUDENT_SKILLS (Join Table)
├─ id (PK)
├─ student_id (FK)
├─ skill_id (FK)
├─ proficiency_claimed (1-10, from resume)
├─ source (resume, manual, etc.)
└─ created_at

ASSESSMENTS
├─ id (PK)
├─ student_id (FK)
├─ assessment_type (MCQ, Coding, CaseStudy)
├─ skill_id (FK)
├─ questions (JSON - array of Q&A)
├─ status (generated, in_progress, completed)
├─ created_at
└─ updated_at

ASSESSMENT_RESPONSES
├─ id (PK)
├─ assessment_id (FK)
├─ student_response (JSON - answers)
├─ submitted_at
└─ ai_feedback (JSON)

SKILL_SCORES
├─ id (PK)
├─ student_id (FK)
├─ skill_id (FK)
├─ assessment_id (FK)
├─ score (1-10)
├─ ai_reasoning (TEXT)
├─ gap_identified (BOOLEAN)
└─ scored_at

LEARNING_PLANS
├─ id (PK)
├─ student_id (FK)
├─ skill_gap_id (FK)
├─ recommendations (JSON - array of courses/resources)
├─ estimated_hours (INT)
├─ priority (1-5)
└─ created_at

DIGITAL_BADGES
├─ id (PK)
├─ student_id (FK)
├─ badge_type (skill_verified, milestone, etc.)
├─ skill_id (FK)
├─ awarded_at
└─ certificate_url
```

---

## 6. API Endpoints Reference

### 6.1 Authentication

```
POST /auth/register
  Body: { email, password, full_name }
  Response: { token, student_id }

POST /auth/login
  Body: { email, password }
  Response: { token, student_id }

POST /auth/logout
  Response: { status: "logged_out" }
```

### 6.2 Student Profile

```
GET /students/{id}/profile
  Response: { id, email, name, skills, assessments_count }

PUT /students/{id}/profile
  Body: { full_name, bio, etc. }
  Response: { updated_profile }
```

### 6.3 Skills & Input

```
POST /students/{id}/skills/upload
  Body: { resume_file or skills_text }
  Response: { extracted_skills: [...], confidence: [...] }

GET /students/{id}/skills
  Response: [{ skill_name, proficiency_claimed, source }]

POST /students/{id}/skills/add-manual
  Body: { skill_name, proficiency_claimed }
  Response: { skill_id, added_at }
```

### 6.4 Assessments

```
POST /assessments/generate
  Body: { student_id }
  Response: { assessment_ids: [...], assessments: [...] }

GET /assessments/{id}
  Response: { id, type, questions: [...], status }

POST /assessments/{id}/submit
  Body: { student_id, responses: {...} }
  Response: { submitted_at, status: "scoring" }

GET /assessments/{id}/status
  Response: { status, score, feedback (if ready) }
```

### 6.5 Scoring & Results

```
POST /assessments/{id}/score
  (Internal endpoint - triggered after submission)
  Response: { score, reasoning, gaps_identified }

GET /students/{id}/results
  Response: { overall_scores, gaps, benchmarks }

GET /students/{id}/gap-analysis
  Response: { identified_gaps: [...], priority_order: [...] }
```

### 6.6 Learning Plans

```
POST /learning-plan/generate
  Body: { student_id }
  Response: { learning_plan_id, recommendations: [...] }

GET /learning-plan/{id}
  Response: { skill_gaps, courses, projects, resources, timeline }

PUT /learning-plan/{id}/update
  Body: { status: "in_progress" / "completed" }
  Response: { updated_at }
```

### 6.7 Export & Badges

```
GET /students/{id}/export/pdf
  Response: PDF file (binary)

GET /students/{id}/export/csv
  Response: CSV file (binary)

GET /students/{id}/badges
  Response: [{ badge_type, awarded_at, certificate_url }]

POST /students/{id}/badges/award
  (Internal - triggered on verification)
  Response: { badge_id, certificate_url }
```

---

## 7. AI Model Integration Points

### 7.1 Where Models Are Used

| Feature | Model Task | Input | Output |
|---------|-----------|-------|--------|
| **Assessment Generation** | Generate MCQ, coding, case study questions tailored to skills | Skill name, proficiency level | Question set with 5-10 questions per type |
| **Skill Scoring** | Evaluate student responses against rubric (1-10 scale) | Assessment type, student answers, rubric | Score, reasoning, confidence level |
| **Gap Analysis** | Compare scores to industry benchmarks, identify gaps | Skill scores, benchmarks | Gap report, priority ranking |
| **Learning Plan** | Generate personalized recommendations based on gaps | Identified gaps, skill level, available time | Courses, projects, resources, timeline |
| **Resume Parsing** | Extract skills from resume text | Resume text/PDF | List of skills, proficiency hints |

### 7.2 Free Model Options

```
Candidates:
  - Google Gemini (free tier)
  - Groq (free tier, fast)
  - OpenRouter (free tier with limits)
  - HuggingFace (free inference)

Recommendation: Start with Google Gemini or Groq
  - Both have generous free tiers
  - Fast response times
  - Good for MVP testing
  - Easy to upgrade later
```

---

## 8. Development Timeline (MVP)

```
WEEK 1-2: Architecture & Setup
  ├─ [ ] Database schema finalized
  ├─ [ ] Project repo initialized (GitHub)
  ├─ [ ] Backend scaffold (Flask, SQLAlchemy)
  ├─ [ ] Frontend scaffold (React, TypeScript)
  └─ [ ] Local dev environment setup

WEEK 3-4: Authentication & Core Backend
  ├─ [ ] User registration/login system
  ├─ [ ] JWT token implementation
  ├─ [ ] Student profile endpoints
  ├─ [ ] Resume parsing (spaCy integration)
  └─ [ ] Skills extraction & storage

WEEK 5-6: Assessment Generation & Scoring
  ├─ [ ] Model API integration (Gemini/Groq)
  ├─ [ ] Assessment generation endpoint
  ├─ [ ] Assessment submission endpoint
  ├─ [ ] AI scoring logic
  ├─ [ ] Gap analysis calculation
  └─ [ ] Results storage

WEEK 7: Learning Plan & Dashboard
  ├─ [ ] Learning plan generation endpoint
  ├─ [ ] Dashboard frontend components
  ├─ [ ] Results visualization (Recharts)
  ├─ [ ] Progress tracking
  └─ [ ] Export (PDF/CSV) functionality

WEEK 8: Digital Badges & Polish
  ├─ [ ] Badge system backend
  ├─ [ ] Badge award logic
  ├─ [ ] Badge display frontend
  ├─ [ ] UI/UX refinements
  ├─ [ ] Error handling & validation
  └─ [ ] Local testing & bug fixes

WEEK 9-10: Testing & Optimization
  ├─ [ ] End-to-end testing
  ├─ [ ] Performance optimization
  ├─ [ ] Security audit
  ├─ [ ] Load testing
  └─ [ ] Documentation finalization

WEEK 11-12: Cloud Deployment
  ├─ [ ] PostgreSQL setup (Railway/Render)
  ├─ [ ] Backend deployment
  ├─ [ ] Frontend deployment (Vercel)
  ├─ [ ] Domain setup (if needed)
  ├─ [ ] Monitoring & logging
  └─ [ ] Launch & feedback collection
```

---

## 9. Success Metrics (MVP)

- [ ] User can register and create profile
- [ ] User can upload resume or input skills manually
- [ ] AI generates 3 assessments (MCQ, Coding, Case Study)
- [ ] User can complete assessments
- [ ] AI scores assessments with 1-10 scale
- [ ] Gap analysis identifies ≥2 skill gaps
- [ ] Learning plan generated with ≥3 recommendations
- [ ] Dashboard displays all results
- [ ] Export to PDF/CSV working
- [ ] Digital badges awarded on completion
- [ ] All endpoints documented
- [ ] Local testing successful
- [ ] Cloud deployment successful
- [ ] App loads in <3 seconds
- [ ] No critical bugs

---

## 10. Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Model API rate limiting | Medium | High | Use free tier strategically, implement caching |
| Resume parsing errors | High | Medium | Manual skill input as fallback |
| Assessment quality issues | Medium | High | Implement feedback loop, continuous refinement |
| Database performance | Low | Medium | Optimize queries, add indexing |
| User authentication issues | Low | High | Use proven JWT libraries, thorough testing |
| Deployment challenges | Medium | Medium | Use PaaS (Railway/Render), follow best practices |

---

## 11. Next Steps

1. ✅ Finalize tech stack decision → **DONE**
2. → Create detailed architecture docs (API, database, model integration)
3. → Create agentic development roadmap (task breakdown for VS Code)
4. → Set up boilerplate code (Flask + React scaffolds)
5. → Begin Phase 1: Authentication & Backend setup
6. → Move to VS Code for implementation

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-11  
**Status:** Ready for Implementation Phase
