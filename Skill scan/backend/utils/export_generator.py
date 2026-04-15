"""
Export Generator Module

Generates comprehensive exports of assessments, gap analysis, and student profiles
in multiple formats (PDF, CSV, ZIP).

Author: SkillScan Team
Date: 2026-04-15
"""

import logging
import json
import csv
import io
import zipfile
from typing import Dict, List, Optional, Tuple, BinaryIO
from datetime import datetime
from dataclasses import dataclass

from backend.models import (
    Student, Skills, Assessment, AssessmentResponse, 
    SkillScore, LearningPlan, GapAnalysis
)
from backend.database import db

logger = logging.getLogger(__name__)


@dataclass
class ExportData:
    """Container for export data"""
    student_id: int
    export_type: str  # 'assessment', 'gap', 'profile', 'all'
    format_type: str  # 'pdf', 'csv', 'zip'
    timestamp: str
    content: Dict


class ExportGenerator:
    """Generates comprehensive exports of assessment and student data"""
    
    def __init__(self):
        """Initialize export generator"""
        logger.info("ExportGenerator initialized")
    
    def generate_assessment_export(
        self,
        student_id: int,
        assessment_id: Optional[int] = None,
        skill_id: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Generate full assessment export data
        
        Args:
            student_id: Student ID
            assessment_id: Specific assessment ID (optional)
            skill_id: Specific skill ID (optional, get latest assessment)
            
        Returns:
            Assessment data dict with full details
        """
        try:
            logger.info(f"Generating assessment export for student {student_id}")
            
            if assessment_id:
                response = AssessmentResponse.query.filter_by(
                    id=assessment_id,
                    student_id=student_id
                ).first()
            elif skill_id:
                # Get latest assessment for skill
                response = AssessmentResponse.query.join(Assessment).filter(
                    AssessmentResponse.student_id == student_id,
                    Assessment.skill_id == skill_id
                ).order_by(AssessmentResponse.created_at.desc()).first()
            else:
                return None
            
            if not response:
                return None
            
            assessment = response.assessment
            skill = Skills.query.get(assessment.skill_id)
            
            export_data = {
                'assessment_id': response.id,
                'skill_name': skill.skill_name if skill else 'Unknown',
                'skill_id': assessment.skill_id,
                'assessment_type': assessment.assessment_type,
                'difficulty': assessment.difficulty,
                'score': response.score,
                'badge': self._get_badge(response.score),
                'total_questions': len(json.loads(assessment.questions)) if assessment.questions else 0,
                'questions': json.loads(assessment.questions) if assessment.questions else [],
                'user_responses': json.loads(response.responses) if response.responses else [],
                'correct_answers': json.loads(response.correct_answers) if response.correct_answers else [],
                'feedback': json.loads(response.feedback) if response.feedback else {},
                'gaps_identified': json.loads(response.gaps) if response.gaps else [],
                'recommendations': json.loads(response.recommendations) if response.recommendations else [],
                'time_spent_minutes': response.time_spent_minutes,
                'created_at': response.created_at.isoformat() if response.created_at else None,
                'export_timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Assessment export generated: {assessment_id}")
            return export_data
            
        except Exception as e:
            logger.error(f"Error generating assessment export: {str(e)}")
            return None
    
    def generate_gap_export(
        self,
        student_id: int,
        skill_id: int
    ) -> Optional[Dict]:
        """
        Generate gap analysis export with full details and benchmarks
        
        Args:
            student_id: Student ID
            skill_id: Skill ID
            
        Returns:
            Gap analysis data dict with benchmarks and recommendations
        """
        try:
            logger.info(f"Generating gap export for student {student_id}, skill {skill_id}")
            
            skill = Skills.query.get(skill_id)
            if not skill:
                return None
            
            # Get skill score
            skill_score = SkillScore.query.filter_by(
                student_id=student_id,
                skill_id=skill_id
            ).first()
            
            current_score = skill_score.score if skill_score else 0
            
            # Get all gaps
            gaps = GapAnalysis.query.filter_by(
                student_id=student_id,
                skill_id=skill_id
            ).all()
            
            gap_data = []
            for gap in gaps:
                gap_data.append({
                    'name': gap.gap_name,
                    'frequency': gap.frequency,
                    'impact': gap.impact_score,
                    'priority': gap.priority,
                    'recommendations': json.loads(gap.recommendations) if gap.recommendations else []
                })
            
            # Get learning plans
            learning_plans = LearningPlan.query.filter_by(
                student_id=student_id,
                skill_id=skill_id,
                status='active'
            ).all()
            
            plans_data = []
            for plan in learning_plans:
                plans_data.append({
                    'id': plan.id,
                    'duration_weeks': plan.duration_weeks,
                    'progress': plan.progress,
                    'created_at': plan.created_at.isoformat() if plan.created_at else None,
                    'end_date': plan.end_date.isoformat() if plan.end_date else None
                })
            
            export_data = {
                'skill_name': skill.skill_name,
                'skill_id': skill_id,
                'current_score': current_score,
                'benchmark_score': 75,  # Example: adjust based on skill
                'percentile': self._calculate_percentile(skill_id, current_score),
                'gaps_identified': len(gap_data),
                'gaps': gap_data,
                'learning_plans_active': len(plans_data),
                'learning_plans': plans_data,
                'recommendations': self._generate_gap_recommendations(gap_data),
                'timeline_weeks': self._estimate_upskill_time(gap_data),
                'export_timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Gap export generated: {len(gap_data)} gaps identified")
            return export_data
            
        except Exception as e:
            logger.error(f"Error generating gap export: {str(e)}")
            return None
    
    def generate_profile_export(
        self,
        student_id: int
    ) -> Optional[Dict]:
        """
        Generate complete profile export with all data
        
        Args:
            student_id: Student ID
            
        Returns:
            Complete profile data dict
        """
        try:
            logger.info(f"Generating profile export for student {student_id}")
            
            student = Student.query.get(student_id)
            if not student:
                return None
            
            # Get all skills
            skill_scores = SkillScore.query.filter_by(student_id=student_id).all()
            
            skills_data = []
            total_score = 0
            for ss in skill_scores:
                skill = Skills.query.get(ss.skill_id)
                skills_data.append({
                    'skill_name': skill.skill_name if skill else 'Unknown',
                    'skill_id': ss.skill_id,
                    'score': ss.score,
                    'proficiency': ss.proficiency_level,
                    'last_assessed': ss.last_assessed_date.isoformat() if ss.last_assessed_date else None
                })
                total_score += ss.score
            
            avg_score = total_score / len(skill_scores) if skill_scores else 0
            
            # Get all assessments
            assessments = AssessmentResponse.query.filter_by(student_id=student_id).all()
            
            assessments_data = []
            for assessment in assessments:
                assessments_data.append({
                    'id': assessment.id,
                    'skill_id': assessment.assessment.skill_id,
                    'score': assessment.score,
                    'date': assessment.created_at.isoformat() if assessment.created_at else None,
                    'type': assessment.assessment.assessment_type
                })
            
            # Get learning plans
            learning_plans = LearningPlan.query.filter_by(student_id=student_id).all()
            
            plans_data = []
            for plan in learning_plans:
                plans_data.append({
                    'skill_id': plan.skill_id,
                    'duration': plan.duration_weeks,
                    'progress': plan.progress,
                    'status': plan.status
                })
            
            # Get gaps
            gaps = GapAnalysis.query.filter_by(student_id=student_id).all()
            
            gaps_data = []
            for gap in gaps:
                gaps_data.append({
                    'skill_id': gap.skill_id,
                    'gap_name': gap.gap_name,
                    'priority': gap.priority
                })
            
            export_data = {
                'student_name': student.full_name,
                'email': student.email,
                'user_type': student.user_type,
                'total_skills': len(skill_scores),
                'average_score': round(avg_score, 2),
                'assessments_taken': len(assessments),
                'active_learning_plans': len([p for p in learning_plans if p.status == 'active']),
                'total_gaps': len(gaps),
                'skills': skills_data,
                'assessments': assessments_data,
                'learning_plans': plans_data,
                'gaps': gaps_data,
                'export_timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Profile export generated: {len(skill_scores)} skills, {len(assessments)} assessments")
            return export_data
            
        except Exception as e:
            logger.error(f"Error generating profile export: {str(e)}")
            return None
    
    def generate_all_assessments_csv(
        self,
        student_id: int,
        skill_id: Optional[int] = None
    ) -> Optional[str]:
        """
        Generate CSV of all assessments
        
        Args:
            student_id: Student ID
            skill_id: Optional skill filter
            
        Returns:
            CSV string
        """
        try:
            query = AssessmentResponse.query.filter_by(student_id=student_id)
            
            if skill_id:
                query = query.join(Assessment).filter(Assessment.skill_id == skill_id)
            
            assessments = query.all()
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                'Assessment ID',
                'Skill Name',
                'Assessment Type',
                'Difficulty',
                'Score',
                'Badge',
                'Gaps Identified',
                'Date Taken',
                'Duration (minutes)'
            ])
            
            # Data rows
            for assessment in assessments:
                skill = Skills.query.get(assessment.assessment.skill_id)
                gaps = json.loads(assessment.gaps) if assessment.gaps else []
                
                writer.writerow([
                    assessment.id,
                    skill.skill_name if skill else 'Unknown',
                    assessment.assessment.assessment_type,
                    assessment.assessment.difficulty,
                    assessment.score,
                    self._get_badge(assessment.score),
                    len(gaps),
                    assessment.created_at.strftime('%Y-%m-%d %H:%M:%S') if assessment.created_at else '',
                    assessment.time_spent_minutes or 0
                ])
            
            csv_string = output.getvalue()
            logger.info(f"Generated CSV for {len(assessments)} assessments")
            return csv_string
            
        except Exception as e:
            logger.error(f"Error generating assessments CSV: {str(e)}")
            return None
    
    def generate_skills_csv(self, student_id: int) -> Optional[str]:
        """
        Generate CSV of all skills
        
        Args:
            student_id: Student ID
            
        Returns:
            CSV string
        """
        try:
            skill_scores = SkillScore.query.filter_by(student_id=student_id).all()
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                'Skill Name',
                'Current Score',
                'Proficiency Level',
                'Assessments Taken',
                'Best Score',
                'Average Score',
                'Last Assessed'
            ])
            
            # Data rows
            for ss in skill_scores:
                skill = Skills.query.get(ss.skill_id)
                
                # Calculate stats
                assessments = AssessmentResponse.query.join(Assessment).filter(
                    AssessmentResponse.student_id == student_id,
                    Assessment.skill_id == ss.skill_id
                ).all()
                
                best_score = max([a.score for a in assessments]) if assessments else ss.score
                avg_score = sum([a.score for a in assessments]) / len(assessments) if assessments else ss.score
                
                writer.writerow([
                    skill.skill_name if skill else 'Unknown',
                    ss.score,
                    ss.proficiency_level,
                    len(assessments),
                    best_score,
                    round(avg_score, 2),
                    ss.last_assessed_date.strftime('%Y-%m-%d') if ss.last_assessed_date else ''
                ])
            
            csv_string = output.getvalue()
            logger.info(f"Generated CSV for {len(skill_scores)} skills")
            return csv_string
            
        except Exception as e:
            logger.error(f"Error generating skills CSV: {str(e)}")
            return None
    
    def generate_zip_export(
        self,
        student_id: int,
        pdf_files: Dict[str, bytes],
        csv_files: Dict[str, str]
    ) -> Optional[bytes]:
        """
        Generate ZIP file with all exports
        
        Args:
            student_id: Student ID
            pdf_files: Dict of {filename: pdf_bytes}
            csv_files: Dict of {filename: csv_string}
            
        Returns:
            ZIP file bytes
        """
        try:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add PDFs
                for filename, content in pdf_files.items():
                    zip_file.writestr(filename, content)
                
                # Add CSVs
                for filename, content in csv_files.items():
                    zip_file.writestr(filename, content)
            
            zip_buffer.seek(0)
            logger.info(f"Generated ZIP export with {len(pdf_files)} PDFs and {len(csv_files)} CSVs")
            return zip_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating ZIP export: {str(e)}")
            return None
    
    def _get_badge(self, score: int) -> str:
        """Get performance badge based on score"""
        if score >= 90:
            return 'Excellent'
        elif score >= 80:
            return 'Good'
        elif score >= 70:
            return 'Fair'
        else:
            return 'Needs Work'
    
    def _calculate_percentile(self, skill_id: int, score: int) -> int:
        """Calculate percentile ranking for score"""
        try:
            all_scores = db.session.query(SkillScore.score).filter_by(skill_id=skill_id).all()
            if not all_scores:
                return 50
            
            scores = [s[0] for s in all_scores]
            better_count = sum(1 for s in scores if s < score)
            percentile = int((better_count / len(scores)) * 100)
            return percentile
        except:
            return 50
    
    def _generate_gap_recommendations(self, gaps: List[Dict]) -> List[str]:
        """Generate recommendations based on gaps"""
        recommendations = []
        
        for gap in gaps[:3]:  # Top 3 gaps
            if gap['priority'] == 'high':
                recommendations.append(f"Focus on improving {gap['name']} - it's critical for this skill")
            elif gap['priority'] == 'medium':
                recommendations.append(f"Consider strengthening {gap['name']} to improve overall proficiency")
        
        return recommendations
    
    def _estimate_upskill_time(self, gaps: List[Dict]) -> int:
        """Estimate time to upskill based on gaps"""
        if len(gaps) == 0:
            return 0
        elif len(gaps) <= 2:
            return 2
        elif len(gaps) <= 4:
            return 4
        else:
            return 6
