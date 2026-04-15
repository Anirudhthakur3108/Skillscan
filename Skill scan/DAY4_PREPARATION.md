# SkillScan MVP - Day 4 Pre-Start Preparation

**Date:** 2026-04-15 Evening Prep  
**Status:** Ready for Day 4 (2026-04-16)  
**Focus:** Gap Analysis + Learning Plans + Dashboard Prep

---

## 📋 PRE-DAY 4 CHECKLIST

### ✅ Code Review & Integration Points

**Existing Code to Reference:**
- ✅ Day 3: Assessment generation, scoring, results (3,663 lines)
- ✅ Models: Assessment, AssessmentResponse, SkillScore (already in models.py)
- ✅ Gemini Client: score_assessment, generate_learning_plan methods ready
- ✅ Frontend: Results page receives score + gaps (AssessmentResults.tsx)

**Integration Needed:**
- Gap Analysis data → Learning Plan generation
- Learning Plan → Dashboard visualization
- Best scores → Progression tracking

---

## 🎯 DAY 4 TASKS BREAKDOWN

### **TASK 4.1: Gap Analysis Backend (3-4 hours)**

**Deliverables:**
- [ ] `utils/gap_analyzer.py` (~300-400 lines)
  - GapAnalyzer class with methods:
    - analyze_gaps() - Compare user scores vs benchmarks
    - identify_weak_areas() - Cluster gaps by skill cluster
    - prioritize_gaps() - Rank gaps by importance
    - calculate_competency_score() - Overall assessment
    - generate_gap_report() - Comprehensive report

- [ ] `routes/gap_analysis.py` (~200-300 lines)
  - GET /gap-analysis/{skill_id} - Get gaps for skill
  - GET /gap-analysis/report - Full report
  - GET /gap-analysis/benchmarks - Industry benchmarks

**Endpoints to Create:**
```python
GET /gap-analysis/{skill_id}
  → Returns: gaps[], benchmark_score, current_score, percentile

GET /gap-analysis/report
  → Returns: summary, by_skill[], trends, recommendations

GET /gap-analysis/benchmarks
  → Returns: industry_avg, expert_level, beginner_level
```

**Features:**
- Compare to industry benchmarks
- Identify trending gaps (appearing across multiple assessments)
- Priority scoring (critical/high/medium/low)
- Competency percentile calculation
- Skill cluster analysis

---

### **TASK 4.2: Learning Plan Generation (3-4 hours)**

**Deliverables:**
- [ ] `utils/learning_plan_generator.py` (~400-500 lines)
  - LearningPlanGenerator class with methods:
    - generate_plan() - Create personalized plan
    - recommend_resources() - Find courses/books/projects
    - prioritize_learning() - Order by impact
    - estimate_duration() - Time to upskill
    - create_milestones() - Weekly/monthly targets

- [ ] `routes/learning_plans.py` (~250-350 lines)
  - POST /learning-plans/generate - Create plan
  - GET /learning-plans/{plan_id} - Get plan details
  - PUT /learning-plans/{plan_id}/progress - Update progress
  - GET /learning-plans/active - Get current plans

**Endpoints to Create:**
```python
POST /learning-plans/generate
  Input: skill_id, gaps[]
  → Returns: plan_id, duration_weeks, milestones[], resources[]

GET /learning-plans/{plan_id}
  → Returns: full plan with weekly breakdown

PUT /learning-plans/{plan_id}/progress
  Input: completed_milestones
  → Returns: updated progress, next_steps

GET /learning-plans/active
  → Returns: list of active plans
```

**Features:**
- AI-generated learning paths using Gemini
- Resource recommendations (courses, YouTube, books, projects, GitHub repos)
- Milestone-based progress tracking
- Weekly commitment estimates
- Difficulty progression suggestions
- Success criteria for each milestone

---

### **TASK 4.3: Frontend Learning Plan UI (3-4 hours)**

**Deliverables:**
- [ ] `pages/LearningPlan.tsx` (~300 lines)
  - Display personalized learning plan
  - Weekly breakdown with milestones
  - Resource links
  - Progress tracking

- [ ] `pages/GapAnalysis.tsx` (~250 lines)
  - Visualize gaps
  - Show benchmarks
  - Rank by priority
  - Links to learning plans

- [ ] Components:
  - [ ] `GapCard.tsx` - Display individual gap
  - [ ] `MilestoneCard.tsx` - Weekly milestone
  - [ ] `ResourceCard.tsx` - Learning resource link
  - [ ] `ProgressTracker.tsx` - Plan progress

- [ ] `api/learningPlan.ts` - API integration (~150 lines)

**Pages to Create:**
```typescript
/gap-analysis → GapAnalysis.tsx
/learning-plan → LearningPlan.tsx
/learning-plan/:planId → LearningPlanDetail.tsx
```

---

### **TASK 4.4: Dashboard Preparation (2 hours)**

**Deliverables:**
- [ ] `pages/Dashboard.tsx` (~400-500 lines)
  - Overview cards (skills, assessments, gaps)
  - 3 main charts (Bar, Table, Roadmap)
  - Quick stats
  - Call-to-action buttons

- [ ] Components:
  - [ ] `SkillScoreChart.tsx` - Bar chart of scores
  - [ ] `GapAnalysisTable.tsx` - Gap priorities
  - [ ] `LearningRoadmap.tsx` - Timeline
  - [ ] `StatsCard.tsx` - Key metrics

- [ ] `api/dashboard.ts` - Aggregate data (~100 lines)

**Charts/Visualizations:**
```
1. Bar Chart: Skill scores (1-10 scale, color-coded)
2. Gap Analysis Table: Gaps with priority, importance, time
3. Learning Roadmap: Timeline to upskill per gap (4-week view)
```

---

## 🔧 TECHNICAL SETUP

### Database Models (Already Exist - Verify):
```python
✅ Assessment (id, skill_id, difficulty, questions, type)
✅ AssessmentResponse (id, student_id, assessment_id, score, gaps)
✅ SkillScore (student_id, skill_id, score, proficiency, last_assessed)
✅ Need to verify: LearningPlan, LearningMilestone, GapAnalysis tables
```

### Gemini Integration Points:
```python
✅ GeminiClient.score_assessment() - Already integrated
⏳ GeminiClient.generate_learning_plan() - Will use in Task 4.2
⏳ GeminiClient.generate_recommendations() - Use for resources
```

### Frontend Routing:
```typescript
⏳ /gap-analysis → GapAnalysis page
⏳ /learning-plan → LearningPlan page  
⏳ /dashboard → Dashboard page
✅ /assessment → Already done
✅ /profile → Already done
```

---

## 📊 DECISION REQUIREMENTS FROM USER

Before starting Day 4, need 3 clarifications:

### **DECISION 1: Gap Analysis Threshold**
What score indicates a "gap"?
```
A) 50-69% = Gap (anything below good)
B) 60-79% = Gap (anything below excellent)
C) Custom threshold (specify %)
```

### **DECISION 2: Learning Plan Duration**
How long for user to upskill?
```
A) 2 weeks (intensive)
B) 4 weeks (moderate)
C) 6 weeks (leisurely)
D) Custom (specify weeks)
```

### **DECISION 3: Recommendation Weighting**
How to prioritize learning resources?
```
A) Balanced: 40% Courses, 30% Projects, 20% Books, 10% YouTube
B) Course-Heavy: 60% Courses, 25% Projects, 10% Books, 5% YouTube
C) Project-Heavy: 50% Projects, 30% Courses, 15% Books, 5% YouTube
D) Custom weights (specify %)
```

---

## 📋 EXECUTION PLAN FOR DAY 4

### Timeline (estimated 8 hours total):

```
09:00 - 09:30: User provides 3 decisions
09:30 - 12:00: Delegate Task 4.1 (Gap Analysis Backend) + 4.3 (Frontend UI)
12:00 - 13:00: Lunch break
13:00 - 16:00: Manual implementation of Task 4.2 (Learning Plan Generation)
16:00 - 17:00: Integration testing + bug fixes
17:00 - 18:00: Documentation + GitHub commit
18:00+: Buffer for issues/refinements
```

### Parallel Execution:
- Subagent 1: Task 4.1 (Gap Analysis Backend)
- Subagent 2: Task 4.3 (Frontend UI)
- Manual: Task 4.2 (Learning Plan Generation)
- Result: All 4 tasks complete by evening

---

## 🎯 SUCCESS CRITERIA FOR DAY 4

✅ All 4 tasks complete (1,200-1,500 lines)  
✅ Gap analysis working with benchmarks  
✅ Learning plans generated with milestones  
✅ Frontend pages rendering correctly  
✅ API endpoints tested  
✅ All code committed to GitHub  
✅ Zero critical bugs  
✅ Type hints & documentation complete  

---

## 📊 CODE ESTIMATES

| Task | Backend | Frontend | Tests | Total |
|------|---------|----------|-------|-------|
| 4.1 Gap Analysis | 500 | - | 100 | 600 |
| 4.2 Learning Plans | 450 | - | 100 | 550 |
| 4.3 Frontend | - | 1,000 | - | 1,000 |
| 4.4 Dashboard Prep | - | 500 | - | 500 |
| **DAY 4 TOTAL** | **950** | **1,500** | **200** | **2,650** |

---

## 🚀 WHAT'S BLOCKED UNTIL USER INPUT

- ✅ Backend models verification
- ✅ Gemini prompt templates ready
- ✅ Frontend component architecture planned
- ⏳ **WAITING:** 3 user decisions (threshold, duration, weighting)

---

## 📝 NOTES FOR DAY 4

### Important Considerations:

1. **Benchmark Data:**
   - Need baseline scores for MBA/BCA skills
   - Option: Generate synthetic benchmarks from seed data
   - Option: User provides real benchmark data

2. **Learning Resource Database:**
   - Can use pre-populated list of courses/books/projects
   - Can fetch from Gemini AI (slower but more accurate)
   - Recommendation: Use pre-populated + Gemini enhancement

3. **Dashboard Data Aggregation:**
   - Pull from multiple tables (AssessmentResponse, SkillScore, LearningPlan)
   - Cache results for performance
   - Real-time updates not critical for MVP

4. **Frontend Routing:**
   - Ensure all new pages protected by token
   - Add to App.tsx routing
   - Update navigation menu/sidebar

---

## ✅ READY FOR DAY 4

**Status:** All preparation complete, awaiting user decisions

**What's needed to start:**
1. User answers 3 questions (5 minutes)
2. I delegate 2 subagents + start manual work (30 minutes)
3. Full execution (4 hours)
4. Integration + testing (1 hour)
5. GitHub push (15 minutes)

**Total Day 4 Time:** ~6-7 hours of work, completing by evening

---

**Prepared:** 2026-04-15 Evening  
**Status:** Ready for Day 4 Execution  
**Next Step:** User provides 3 decisions tomorrow morning
