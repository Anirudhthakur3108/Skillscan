"""
Learning Plan Generation Module

Generates personalized learning plans with weekly milestones,
resource recommendations, and progress tracking for SkillScan MVP.

Author: SkillScan Team
Date: 2026-04-15
"""

import logging
import json
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from backend.utils.model_client import GeminiClient
from backend.models import (
    Student, Skills, LearningPlan, LearningMilestone,
    AssessmentResponse, Assessment
)
from backend.database import db

logger = logging.getLogger(__name__)


@dataclass
class ResourceRecommendation:
    """Data class for learning resource"""
    type: str  # 'course', 'project', 'video', 'documentation'
    title: str
    platform: str
    duration: str  # "2 weeks", "10 hours", etc.
    difficulty: str  # 'easy', 'medium', 'hard'
    link: str
    priority: str  # 'high', 'medium', 'low'


class LearningPlanGenerator:
    """Generates personalized learning plans based on assessment gaps"""
    
    # Score-based duration recommendations (in weeks)
    DURATION_RECOMMENDATIONS = {
        (90, 100): 2,      # Excellent: quick polish
        (80, 89): 3,       # Good: standard upskill
        (60, 79): 4,       # Fair: intensive focus
        (0, 59): 6         # Needs work: fundamental learning
    }
    
    # Resource distribution (percentage, no books)
    RESOURCE_DISTRIBUTION = {
        'course': 0.40,           # 40% Online Courses
        'project': 0.35,          # 35% Projects
        'video': 0.15,            # 15% YouTube Tutorials
        'documentation': 0.10     # 10% Documentation/Articles
    }
    
    # Resource types and platforms
    RESOURCES_DB = {
        'course': [
            {'title': 'Python for Data Analysis', 'platform': 'Coursera', 'duration': '4 weeks'},
            {'title': 'Advanced Python Programming', 'platform': 'Udemy', 'duration': '8 hours'},
            {'title': 'Java Basics to Advanced', 'platform': 'Pluralsight', 'duration': '6 weeks'},
            {'title': 'React Advanced Concepts', 'platform': 'Coursera', 'duration': '5 weeks'},
            {'title': 'SQL Mastery', 'platform': 'Udemy', 'duration': '12 hours'},
            {'title': 'System Design Fundamentals', 'platform': 'Educative', 'duration': '4 weeks'},
        ],
        'project': [
            {'title': 'Build a REST API with Python', 'platform': 'GitHub', 'duration': '2 weeks'},
            {'title': 'Create a Data Dashboard', 'platform': 'Kaggle', 'duration': '3 weeks'},
            {'title': 'Implement LeetCode Problems', 'platform': 'LeetCode', 'duration': '4 weeks'},
            {'title': 'Build Todo App in React', 'platform': 'GitHub', 'duration': '1 week'},
            {'title': 'Machine Learning Project', 'platform': 'Kaggle', 'duration': '4 weeks'},
        ],
        'video': [
            {'title': 'Python Tutorial Series', 'platform': 'YouTube', 'duration': '20 hours'},
            {'title': 'Web Development Crash Course', 'platform': 'YouTube', 'duration': '4 hours'},
            {'title': 'Data Structures Explained', 'platform': 'YouTube', 'duration': '8 hours'},
            {'title': 'React Hooks Deep Dive', 'platform': 'YouTube', 'duration': '3 hours'},
            {'title': 'SQL Query Optimization', 'platform': 'YouTube', 'duration': '2 hours'},
        ],
        'documentation': [
            {'title': 'Python Official Docs', 'platform': 'python.org', 'duration': '2 weeks'},
            {'title': 'React Documentation', 'platform': 'react.dev', 'duration': '3 weeks'},
            {'title': 'SQL Reference Guide', 'platform': 'W3Schools', 'duration': '1 week'},
            {'title': 'Java API Documentation', 'platform': 'oracle.com', 'duration': '2 weeks'},
            {'title': 'MDN Web Docs', 'platform': 'mdn.org', 'duration': '3 weeks'},
        ]
    }
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize learning plan generator
        
        Args:
            gemini_client: GeminiClient for AI-powered recommendations
        """
        self.gemini_client = gemini_client or GeminiClient()
        logger.info("LearningPlanGenerator initialized")
    
    def recommend_duration(self, score: int) -> Tuple[int, str]:
        """
        Recommend learning plan duration based on score
        
        Args:
            score: Assessment score (0-100)
            
        Returns:
            Tuple of (recommended_weeks, reason_message)
        """
        try:
            for (min_score, max_score), weeks in self.DURATION_RECOMMENDATIONS.items():
                if min_score <= score <= max_score:
                    if score >= 90:
                        reason = "You're doing great! Quick polish recommended"
                        return weeks, reason
                    elif score >= 80:
                        reason = "Good progress! Plan to excel in this area"
                        return weeks, reason
                    elif score >= 60:
                        reason = "Time to focus - intensive learning recommended"
                        return weeks, reason
                    else:
                        reason = "Let's rebuild foundations - comprehensive learning needed"
                        return weeks, reason
            
            # Default: 4 weeks for unknown scores
            return 4, "Standard learning plan recommended"
            
        except Exception as e:
            logger.error(f"Error recommending duration: {str(e)}")
            return 4, "Default 4-week plan"
    
    def generate_learning_plan(
        self,
        student_id: int,
        skill_id: int,
        gaps: List[str],
        assessment_score: int,
        user_duration_weeks: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate personalized learning plan
        
        Args:
            student_id: Student ID
            skill_id: Skill ID
            gaps: List of identified gaps
            assessment_score: Latest assessment score
            user_duration_weeks: User-selected duration (optional, system recommends)
            
        Returns:
            Complete learning plan dict
        """
        try:
            logger.info(f"Generating learning plan for student {student_id}, skill {skill_id}")
            
            # Get skill name
            skill = Skills.query.get(skill_id)
            skill_name = skill.skill_name if skill else "Unknown Skill"
            
            # Recommend duration based on score
            recommended_weeks, recommendation_reason = self.recommend_duration(assessment_score)
            
            # Use user duration or recommended
            duration_weeks = user_duration_weeks or recommended_weeks
            
            logger.info(f"Duration: {duration_weeks} weeks (recommended: {recommended_weeks})")
            
            # Generate weekly milestones
            milestones = self._generate_milestones(
                skill_name=skill_name,
                gaps=gaps,
                duration_weeks=duration_weeks,
                assessment_score=assessment_score
            )
            
            # Generate resource recommendations (balanced distribution, no books)
            resources = self._recommend_resources(
                gaps=gaps,
                duration_weeks=duration_weeks,
                assessment_score=assessment_score
            )
            
            # Create plan object
            plan = {
                'skill_id': skill_id,
                'skill_name': skill_name,
                'duration_weeks': duration_weeks,
                'recommended_duration': recommended_weeks,
                'recommendation_reason': recommendation_reason,
                'assessment_score': assessment_score,
                'gaps_addressed': gaps,
                'milestones': milestones,
                'resources': resources,
                'progress': 0,
                'created_at': datetime.utcnow().isoformat(),
                'start_date': datetime.utcnow().isoformat(),
                'end_date': (datetime.utcnow() + timedelta(weeks=duration_weeks)).isoformat()
            }
            
            logger.info(f"Learning plan generated: {duration_weeks} weeks with {len(milestones)} milestones")
            return plan
            
        except Exception as e:
            logger.error(f"Error generating learning plan: {str(e)}")
            return {}
    
    def _generate_milestones(
        self,
        skill_name: str,
        gaps: List[str],
        duration_weeks: int,
        assessment_score: int
    ) -> List[Dict[str, Any]]:
        """
        Generate weekly milestones
        
        Args:
            skill_name: Skill being learned
            gaps: Gaps to address
            duration_weeks: Plan duration
            assessment_score: Current score for difficulty calibration
            
        Returns:
            List of milestone dicts
        """
        try:
            milestones = []
            hours_per_week = 15 if duration_weeks <= 3 else 10  # Intensive or moderate
            
            # Week 1-2: Foundation
            foundation_weeks = min(2, duration_weeks)
            for week in range(1, foundation_weeks + 1):
                milestone = {
                    'week': week,
                    'title': f'Week {week}: Learn Fundamentals',
                    'description': f'Build foundation in {skill_name}',
                    'success_criteria': [
                        'Complete foundation course module',
                        'Understand core concepts',
                        'Pass quiz with 70%+'
                    ],
                    'estimated_hours': hours_per_week,
                    'resources': 2,  # Number of resources for this week
                    'completed': False
                }
                milestones.append(milestone)
            
            # Middle weeks: Deep dive into gaps
            middle_start = foundation_weeks + 1
            middle_weeks = max(1, duration_weeks - foundation_weeks - 1)
            for week in range(middle_start, middle_start + middle_weeks):
                gap_focus = gaps[(week - middle_start) % len(gaps)] if gaps else 'Advanced Topics'
                milestone = {
                    'week': week,
                    'title': f'Week {week}: Master {gap_focus}',
                    'description': f'Deep dive into: {gap_focus}',
                    'success_criteria': [
                        f'Complete {gap_focus} tutorial',
                        'Build practice project',
                        'Score 80%+ on practice test'
                    ],
                    'estimated_hours': hours_per_week,
                    'resources': 2,
                    'completed': False
                }
                milestones.append(milestone)
            
            # Final week: Review & Practice
            if duration_weeks > middle_start + middle_weeks - 1:
                final_week = duration_weeks
                milestone = {
                    'week': final_week,
                    'title': f'Week {final_week}: Review & Assess',
                    'description': 'Review all concepts and take practice assessment',
                    'success_criteria': [
                        'Complete review of all topics',
                        'Score 80%+ on final practice test',
                        'Take official assessment'
                    ],
                    'estimated_hours': hours_per_week,
                    'resources': 2,
                    'completed': False
                }
                milestones.append(milestone)
            
            logger.info(f"Generated {len(milestones)} milestones")
            return milestones
            
        except Exception as e:
            logger.error(f"Error generating milestones: {str(e)}")
            return []
    
    def _recommend_resources(
        self,
        gaps: List[str],
        duration_weeks: int,
        assessment_score: int
    ) -> List[Dict[str, Any]]:
        """
        Recommend learning resources (balanced distribution, no books)
        
        Resource Distribution:
        - 40% Online Courses
        - 35% Projects
        - 15% YouTube Tutorials
        - 10% Documentation/Articles
        
        Args:
            gaps: Gaps to address
            duration_weeks: Plan duration
            assessment_score: Score for difficulty calibration
            
        Returns:
            List of recommended resources
        """
        try:
            resources = []
            total_resources = max(8, duration_weeks * 2)  # At least 8 resources
            
            # Calculate distribution counts
            course_count = int(total_resources * 0.40)
            project_count = int(total_resources * 0.35)
            video_count = int(total_resources * 0.15)
            doc_count = int(total_resources * 0.10)
            
            # Adjust for rounding
            remaining = total_resources - (course_count + project_count + video_count + doc_count)
            course_count += remaining
            
            logger.info(f"Resource distribution: {course_count} courses, {project_count} projects, "
                       f"{video_count} videos, {doc_count} docs")
            
            # Add resources maintaining distribution
            resource_id = 1
            
            # Add courses (40%)
            for i in range(course_count):
                if i < len(self.RESOURCES_DB['course']):
                    res = self.RESOURCES_DB['course'][i].copy()
                    res['id'] = resource_id
                    res['type'] = 'course'
                    res['priority'] = 'high' if i < course_count // 2 else 'medium'
                    res['difficulty'] = self._difficulty_from_score(assessment_score)
                    res['link'] = f"https://example.com/course/{resource_id}"
                    resources.append(res)
                    resource_id += 1
            
            # Add projects (35%)
            for i in range(project_count):
                if i < len(self.RESOURCES_DB['project']):
                    res = self.RESOURCES_DB['project'][i].copy()
                    res['id'] = resource_id
                    res['type'] = 'project'
                    res['priority'] = 'high' if i < project_count // 2 else 'medium'
                    res['difficulty'] = self._difficulty_from_score(assessment_score)
                    res['link'] = f"https://github.com/projects/{resource_id}"
                    resources.append(res)
                    resource_id += 1
            
            # Add videos (15%)
            for i in range(video_count):
                if i < len(self.RESOURCES_DB['video']):
                    res = self.RESOURCES_DB['video'][i].copy()
                    res['id'] = resource_id
                    res['type'] = 'video'
                    res['priority'] = 'medium'
                    res['difficulty'] = self._difficulty_from_score(assessment_score)
                    res['link'] = f"https://youtube.com/watch?v={resource_id}"
                    resources.append(res)
                    resource_id += 1
            
            # Add documentation (10%)
            for i in range(doc_count):
                if i < len(self.RESOURCES_DB['documentation']):
                    res = self.RESOURCES_DB['documentation'][i].copy()
                    res['id'] = resource_id
                    res['type'] = 'documentation'
                    res['priority'] = 'low'
                    res['difficulty'] = self._difficulty_from_score(assessment_score)
                    res['link'] = f"https://docs.example.com/{resource_id}"
                    resources.append(res)
                    resource_id += 1
            
            logger.info(f"Recommended {len(resources)} resources")
            return resources
            
        except Exception as e:
            logger.error(f"Error recommending resources: {str(e)}")
            return []
    
    def _difficulty_from_score(self, score: int) -> str:
        """Convert score to difficulty level"""
        if score >= 80:
            return 'medium'
        elif score >= 60:
            return 'medium'
        else:
            return 'easy'
    
    def save_learning_plan(
        self,
        student_id: int,
        plan_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Save learning plan to database
        
        Args:
            student_id: Student ID
            plan_data: Complete plan dictionary
            
        Returns:
            Saved plan with ID or None if failed
        """
        try:
            # Create learning plan record
            plan = LearningPlan(
                student_id=student_id,
                skill_id=plan_data['skill_id'],
                duration_weeks=plan_data['duration_weeks'],
                recommended_duration=plan_data['recommended_duration'],
                recommendation_reason=plan_data['recommendation_reason'],
                gaps_addressed=json.dumps(plan_data['gaps_addressed']),
                milestones=json.dumps(plan_data['milestones']),
                resources=json.dumps(plan_data['resources']),
                progress=0,
                created_at=datetime.utcnow(),
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(weeks=plan_data['duration_weeks']),
                status='active'
            )
            
            db.session.add(plan)
            db.session.commit()
            
            plan_data['id'] = plan.id
            logger.info(f"Learning plan saved: {plan.id}")
            return plan_data
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving learning plan: {str(e)}")
            return None
    
    def get_active_plans(self, student_id: int) -> List[Dict[str, Any]]:
        """
        Get all active learning plans for student
        
        Args:
            student_id: Student ID
            
        Returns:
            List of active plans
        """
        try:
            plans = LearningPlan.query.filter_by(
                student_id=student_id,
                status='active'
            ).all()
            
            result = []
            for plan in plans:
                result.append({
                    'id': plan.id,
                    'skill_id': plan.skill_id,
                    'skill_name': Skills.query.get(plan.skill_id).skill_name if plan.skill_id else 'Unknown',
                    'duration_weeks': plan.duration_weeks,
                    'progress': plan.progress,
                    'created_at': plan.created_at.isoformat(),
                    'end_date': plan.end_date.isoformat()
                })
            
            logger.info(f"Retrieved {len(plans)} active plans for student {student_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving active plans: {str(e)}")
            return []
    
    def update_plan_progress(
        self,
        plan_id: int,
        completed_milestones: int
    ) -> Optional[int]:
        """
        Update learning plan progress
        
        Args:
            plan_id: Plan ID
            completed_milestones: Number of milestones completed
            
        Returns:
            Updated progress percentage or None if failed
        """
        try:
            plan = LearningPlan.query.get(plan_id)
            if not plan:
                return None
            
            milestones = json.loads(plan.milestones) if isinstance(plan.milestones, str) else plan.milestones
            total_milestones = len(milestones)
            
            progress = int((completed_milestones / total_milestones) * 100) if total_milestones > 0 else 0
            plan.progress = min(progress, 100)
            
            db.session.commit()
            logger.info(f"Updated plan {plan_id} progress to {progress}%")
            return progress
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating progress: {str(e)}")
            return None
