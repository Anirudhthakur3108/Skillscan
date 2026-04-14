# SkillScan MVP - Agentic Development Roadmap

**Purpose:** Break down MVP development into agentified tasks that can be delegated, coordinated, and integrated.  
**Approach:** Use agent-based workflow to scaffold, document, and prepare implementation for VS Code.  
**Status:** Planning Phase

---

## 1. Development Phases & Agent Tasks

### Phase 1: Architecture & Environment Setup (Week 1-2)

#### Task 1.1: Database & ORM Layer
- **What:** Finalize SQLAlchemy models for all 8 core tables
- **Deliverables:**
  - `models.py` - All SQLAlchemy table definitions
  - `schema.sql` - SQL schema dump
  - `migrations/` - Alembic migration setup
- **Agent:** Backend Architect
- **Dependencies:** None
- **Acceptance:** Models compile without errors, all relationships defined

#### Task 1.2: Flask Project Scaffolding
- **What:** Create Flask app structure with blueprints
- **Deliverables:**
  - `app.py` - Flask app factory
  - `config.py` - Config for dev/prod
  - `routes/auth.py`, `routes/students.py`, etc.
  - `requirements.txt` - All dependencies
  - `.env.example` - Environment variables template
- **Agent:** Backend Infrastructure
- **Dependencies:** None
- **Acceptance:** Flask runs without errors, blueprints registered

#### Task 1.3: React Project Scaffolding
- **What:** Create React TypeScript app with folder structure
- **Deliverables:**
  - `src/components/` - Reusable components
  - `src/pages/` - Page components
  - `src/api/` - API client setup
  - `package.json` - Dependencies
  - Tailwind CSS configured
  - `.env.example`
- **Agent:** Frontend Infrastructure
- **Dependencies:** None
- **Acceptance:** React app runs, compiles without errors

#### Task 1.4: Local Development Environment Setup
- **What:** Docker Compose or local DB setup for SQLite/PostgreSQL
- **Deliverables:**
  - `docker-compose.yml` (optional)
  - Local database initialization script
  - Setup instructions (README)
- **Agent:** DevOps & Environment
- **Dependencies:** Tasks 1.2, 1.3
- **Acceptance:** Database initialized, both backend and frontend start locally

---

### Phase 2: Authentication & Student Management (Week 3-4)

#### Task 2.1: Authentication Backend
- **What:** JWT-based registration, login, logout
- **Deliverables:**
  - `/auth/register` endpoint
  - `/auth/login` endpoint
  - `/auth/logout` endpoint
  - `utils/auth.py` - JWT helpers, password hashing
  - Authentication middleware
- **Agent:** Backend - Auth Module
- **Dependencies:** Task 1.2
- **Acceptance:** All endpoints tested, tokens issued correctly

#### Task 2.2: Student Profile Management
- **What:** CRUD operations for student profiles
- **Deliverables:**
  - `GET /students/{id}/profile`
  - `PUT /students/{id}/profile`
  - Profile serialization logic
- **Agent:** Backend - Student Module
- **Dependencies:** Task 2.1
- **Acceptance:** Profile endpoints working, data persisted

#### Task 2.3: Resume Parsing & Skill Extraction
- **What:** Integration with spaCy for resume parsing
- **Deliverables:**
  - `utils/resume_parser.py` - spaCy + NLP logic
  - `/students/{id}/skills/upload` endpoint
  - `/students/{id}/skills/add-manual` endpoint
  - Skill taxonomy database population
- **Agent:** Backend - NLP Module
- **Dependencies:** Task 1.2
- **Acceptance:** Resume parsing works, skills extracted, stored correctly

#### Task 2.4: Frontend - Auth & Profile Pages
- **What:** Registration, login, profile editing UI
- **Deliverables:**
  - `pages/Register.tsx`
  - `pages/Login.tsx`
  - `pages/Profile.tsx`
  - `components/SkillInput.tsx` (manual skill input)
  - API integration (axios)
- **Agent:** Frontend - Auth & Profile UI
- **Dependencies:** Tasks 1.3, 2.1
- **Acceptance:** Auth flow works end-to-end, UI responsive

---

### Phase 3: Assessment Generation & Scoring (Week 5-6)

#### Task 3.1: AI Model Integration Layer
- **What:** Wrapper for free model API (Gemini/Groq)
- **Deliverables:**
  - `utils/model_client.py` - API wrapper
  - Prompt templates for assessments
  - Error handling & retry logic
  - Model configuration (temp, tokens, etc.)
- **Agent:** Backend - AI Integration
- **Dependencies:** Task 1.2
- **Acceptance:** Model API calls working, responses parsed

#### Task 3.2: Assessment Generation Engine
- **What:** Generate MCQ, coding, case study assessments
- **Deliverables:**
  - `services/assessment_generator.py` - Core logic
  - `/assessments/generate` endpoint
  - Assessment templates (JSON structure)
  - Quality assurance checks
- **Agent:** Backend - Assessment Module
- **Dependencies:** Tasks 3.1, 2.3
- **Acceptance:** Generates 3 assessments per skill, questions are relevant

#### Task 3.3: Assessment Scoring & Rubric Engine
- **What:** AI-based assessment scoring with 1-10 scale
- **Deliverables:**
  - `services/assessment_scorer.py` - Scoring logic
  - `/assessments/{id}/submit` endpoint
  - `/assessments/{id}/score` endpoint (internal)
  - Scoring rubric templates
  - Gap identification logic
- **Agent:** Backend - Scoring Module
- **Dependencies:** Tasks 3.1, 3.2
- **Acceptance:** Scores generated, gaps identified, reasoning provided

#### Task 3.4: Frontend - Assessment Interface
- **What:** UI for displaying and completing assessments
- **Deliverables:**
  - `pages/Assessments.tsx`
  - `components/MCQQuestion.tsx`
  - `components/CodingChallenge.tsx` (Monaco Editor integration)
  - `components/CaseStudyQuestion.tsx`
  - Real-time progress tracking
- **Agent:** Frontend - Assessment UI
- **Dependencies:** Tasks 1.3, 3.2
- **Acceptance:** Assessments display correctly, submission works

---

### Phase 4: Learning Plans & Dashboard (Week 7)

#### Task 4.1: Learning Plan Generation
- **What:** Generate personalized recommendations based on gaps
- **Deliverables:**
  - `services/learning_plan_generator.py`
  - `/learning-plan/generate` endpoint
  - Recommendation templates
  - Resource database (courses, projects)
- **Agent:** Backend - Learning Plan Module
- **Dependencies:** Tasks 3.3, 3.1
- **Acceptance:** Learning plans generated with ≥3 recommendations

#### Task 4.2: Export Functionality (PDF/CSV)
- **What:** Generate exportable reports
- **Deliverables:**
  - `utils/export_pdf.py` - PDF generation
  - `utils/export_csv.py` - CSV export
  - `/students/{id}/export/pdf` endpoint
  - `/students/{id}/export/csv` endpoint
- **Agent:** Backend - Export Module
- **Dependencies:** Task 3.3
- **Acceptance:** PDF and CSV exports created, data complete

#### Task 4.3: Frontend - Dashboard & Results
- **What:** Visual dashboard displaying scores, gaps, learning plan
- **Deliverables:**
  - `pages/Dashboard.tsx`
  - `components/SkillChart.tsx` (Recharts)
  - `components/GapAnalysis.tsx`
  - `components/LearningPlanDisplay.tsx`
  - Export buttons (PDF/CSV)
- **Agent:** Frontend - Dashboard UI
- **Dependencies:** Tasks 1.3, 4.1, 4.2
- **Acceptance:** Dashboard displays all data correctly, charts render

---

### Phase 5: Digital Badges & Polish (Week 8)

#### Task 5.1: Digital Badge System
- **What:** Award badges for skill verification milestones
- **Deliverables:**
  - `services/badge_service.py` - Badge logic
  - `/students/{id}/badges` endpoint
  - Badge award triggers
  - Certificate generation (PNG/PDF)
- **Agent:** Backend - Badge Module
- **Dependencies:** Task 1.2
- **Acceptance:** Badges awarded correctly, certificates generated

#### Task 5.2: Frontend - Badge Display
- **What:** Display awarded badges to user
- **Deliverables:**
  - `components/BadgeDisplay.tsx`
  - `pages/Badges.tsx`
  - Badge animations
- **Agent:** Frontend - Badge UI
- **Dependencies:** Tasks 1.3, 5.1
- **Acceptance:** Badges display with animations

#### Task 5.3: Error Handling & Validation
- **What:** Comprehensive error handling across all endpoints
- **Deliverables:**
  - Error middleware
  - Input validation schemas
  - User-friendly error messages
  - Logging setup
- **Agent:** Backend & Frontend - QA
- **Dependencies:** All tasks
- **Acceptance:** No unhandled errors, validation working

---

### Phase 6: Testing & Optimization (Week 9-10)

#### Task 6.1: Backend Testing
- **What:** Unit and integration tests for all endpoints
- **Deliverables:**
  - `tests/` directory with pytest tests
  - Test coverage ≥80%
  - API endpoint documentation (Swagger/OpenAPI)
- **Agent:** Backend - QA & Testing
- **Dependencies:** All backend tasks
- **Acceptance:** All tests passing, coverage ≥80%

#### Task 6.2: Frontend Testing
- **What:** Component tests and E2E tests
- **Deliverables:**
  - Jest/React Testing Library tests
  - Cypress E2E tests
  - Test coverage ≥75%
- **Agent:** Frontend - QA & Testing
- **Dependencies:** All frontend tasks
- **Acceptance:** All tests passing, user flows work

#### Task 6.3: Performance & Security
- **What:** Optimize and secure the application
- **Deliverables:**
  - Performance profiling results
  - Security audit checklist
  - Optimized queries, caching
  - HTTPS/CORS configured
- **Agent:** DevOps & Security
- **Dependencies:** All tasks
- **Acceptance:** App loads <3sec, no security vulnerabilities

---

### Phase 7: Cloud Deployment (Week 11-12)

#### Task 7.1: Cloud Infrastructure Setup
- **What:** Set up PostgreSQL, backend hosting, frontend hosting
- **Deliverables:**
  - Railway/Render account setup
  - PostgreSQL database provisioned
  - Environment variables configured
  - CI/CD pipeline (GitHub Actions)
- **Agent:** DevOps - Cloud Setup
- **Dependencies:** All tasks
- **Acceptance:** Services provisioned, connected

#### Task 7.2: Backend Deployment
- **What:** Deploy Flask app to Railway or Render
- **Deliverables:**
  - Dockerfile
  - Deployment scripts
  - Database migrations applied
  - Monitoring configured
- **Agent:** DevOps - Backend Deploy
- **Dependencies:** Task 7.1
- **Acceptance:** Backend accessible via URL, working

#### Task 7.3: Frontend Deployment
- **What:** Deploy React app to Vercel
- **Deliverables:**
  - Vercel project setup
  - Env vars configured
  - API endpoint pointing to cloud backend
- **Agent:** DevOps - Frontend Deploy
- **Dependencies:** Tasks 7.1, 7.2
- **Acceptance:** Frontend accessible, all features working

#### Task 7.4: Launch & Monitoring
- **What:** Final testing, launch, and ongoing monitoring
- **Deliverables:**
  - Smoke tests passed
  - Logging/monitoring dashboard
  - Backup strategy
  - Documentation finalized
- **Agent:** DevOps & Product
- **Dependencies:** All tasks
- **Acceptance:** App live, monitoring active

---

## 2. Task Dependency Graph

```
Phase 1: Setup
├─ Task 1.1 (Database) ─────┐
├─ Task 1.2 (Flask) ────────┼─→ Task 1.4 (Dev Env)
├─ Task 1.3 (React) ────────┘
└─ Task 1.4 (Dev Env)

Phase 2: Auth & Student
├─ Task 2.1 (Auth) ─────→ Task 2.2 (Profile)
├─ Task 2.3 (Resume) ───→ Task 2.4 (Profile UI)
└─ Task 2.4 requires Tasks 1.3 & 2.1

Phase 3: Assessments
├─ Task 3.1 (AI Wrapper) ┐
├─ Task 2.3 (Resume) ────┼─→ Task 3.2 (Gen) ─→ Task 3.3 (Score)
└─ Task 3.3 ────────────────→ Task 3.4 (UI)

Phase 4: Plans & Dashboard
├─ Task 3.3 ──→ Task 4.1 (Learning Plan)
├─ Task 3.3 ──→ Task 4.2 (Export)
└─ All ────→ Task 4.3 (Dashboard)

Phase 5: Badges
├─ Task 1.2 ──→ Task 5.1 (Badge Backend)
├─ Task 1.3 ──→ Task 5.2 (Badge UI)
└─ All ────→ Task 5.3 (Error Handling)

Phase 6: Testing
├─ All Backend ──→ Task 6.1 (Backend Tests)
├─ All Frontend ──→ Task 6.2 (Frontend Tests)
└─ All ──→ Task 6.3 (Performance & Security)

Phase 7: Deployment
├─ All ──→ Task 7.1 (Cloud Infra)
├─ 7.1 ──→ Task 7.2 (Backend Deploy)
├─ 7.1 & 7.2 ──→ Task 7.3 (Frontend Deploy)
└─ 7.2 & 7.3 ──→ Task 7.4 (Launch)
```

---

## 3. Agent Coordination & Work Partitioning

### Agents & Their Responsibilities

| Agent | Tasks | Focus |
|-------|-------|-------|
| **Backend Architect** | 1.1 | Database schema, data models, relationships |
| **Backend Infrastructure** | 1.2 | Flask setup, project structure, config |
| **Frontend Infrastructure** | 1.3 | React setup, folder structure, tooling |
| **DevOps & Environment** | 1.4, 7.1, 7.2, 7.3, 7.4 | Deployment, cloud, infrastructure |
| **Backend - Auth Module** | 2.1 | JWT, registration, login, security |
| **Backend - Student Module** | 2.2 | Student CRUD, profile management |
| **Backend - NLP Module** | 2.3 | Resume parsing, spaCy, skill extraction |
| **Frontend - Auth & Profile UI** | 2.4 | Registration, login, profile pages |
| **Backend - AI Integration** | 3.1 | Model API wrapper, prompt engineering |
| **Backend - Assessment Module** | 3.2 | Assessment generation, quality checks |
| **Backend - Scoring Module** | 3.3 | Scoring, rubrics, gap analysis |
| **Frontend - Assessment UI** | 3.4 | Assessment display, submission UI |
| **Backend - Learning Plan Module** | 4.1 | Learning plan generation, recommendations |
| **Backend - Export Module** | 4.2 | PDF/CSV export functionality |
| **Frontend - Dashboard UI** | 4.3 | Dashboard, charts, visualization |
| **Backend - Badge Module** | 5.1 | Badge logic, certificate generation |
| **Frontend - Badge UI** | 5.2 | Badge display, animations |
| **Backend & Frontend - QA** | 5.3 | Error handling, validation, logging |
| **Backend - QA & Testing** | 6.1 | Unit tests, integration tests, coverage |
| **Frontend - QA & Testing** | 6.2 | Component tests, E2E tests, coverage |
| **DevOps & Security** | 6.3 | Performance, security audit, optimization |

---

## 4. Communication & Handoff Protocol

### Before Each Phase:
1. **Agent Review:** Each agent reviews task requirements and dependencies
2. **Clarification:** Ask questions if inputs unclear
3. **Timeline Confirmation:** Agree on estimated completion time
4. **Acceptance Criteria:** Agent confirms understanding of "done"

### During Implementation:
1. **Daily Standup:** (If multi-day task) Async status updates
2. **Blockers:** Flag any dependency issues immediately
3. **Code Review:** Code reviewed before merging to main

### After Completion:
1. **Deliverable Handoff:** Code/docs delivered to main repo
2. **Testing:** Next-phase agent validates inputs
3. **Documentation:** Update progress tracking
4. **Lessons Learned:** Note any blockers or improvements

---

## 5. Progress Tracking

```
[✅] Phase 1: Architecture & Environment Setup
  [✅] Task 1.1: Database & ORM Layer
  [✅] Task 1.2: Flask Project Scaffolding
  [✅] Task 1.3: React Project Scaffolding
  [✅] Task 1.4: Local Development Environment
  
[ ] Phase 2: Authentication & Student Management
  [ ] Task 2.1: Authentication Backend
  [ ] Task 2.2: Student Profile Management
  [ ] Task 2.3: Resume Parsing & Skill Extraction
  [ ] Task 2.4: Frontend - Auth & Profile Pages
  
[ ] Phase 3: Assessment Generation & Scoring
  [ ] Task 3.1: AI Model Integration Layer
  [ ] Task 3.2: Assessment Generation Engine
  [ ] Task 3.3: Assessment Scoring & Rubric Engine
  [ ] Task 3.4: Frontend - Assessment Interface
  
[ ] Phase 4: Learning Plans & Dashboard
  [ ] Task 4.1: Learning Plan Generation
  [ ] Task 4.2: Export Functionality (PDF/CSV)
  [ ] Task 4.3: Frontend - Dashboard & Results
  
[ ] Phase 5: Digital Badges & Polish
  [ ] Task 5.1: Digital Badge System
  [ ] Task 5.2: Frontend - Badge Display
  [ ] Task 5.3: Error Handling & Validation
  
[ ] Phase 6: Testing & Optimization
  [ ] Task 6.1: Backend Testing
  [ ] Task 6.2: Frontend Testing
  [ ] Task 6.3: Performance & Security
  
[ ] Phase 7: Cloud Deployment
  [ ] Task 7.1: Cloud Infrastructure Setup
  [ ] Task 7.2: Backend Deployment
  [ ] Task 7.3: Frontend Deployment
  [ ] Task 7.4: Launch & Monitoring
```

---

## 6. Notes for VS Code Implementation

- **Repo Setup:** Initialize GitHub repo with branching strategy (main, develop, feature branches)
- **Code Standards:** Use ESLint, Prettier for frontend; Black, isort for backend
- **Commit Messages:** Follow conventional commits format
- **Pull Requests:** Require review before merge to develop/main
- **Local Testing:** Run all tests before pushing
- **Documentation:** Inline comments for complex logic, README for each module

---

**Roadmap Version:** 1.0  
**Status:** Ready for Phase 1 Execution  
**Next:** Begin VS Code implementation following this roadmap
