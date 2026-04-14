"""
Assessment Results & Recommendations Display Module

Handles generation of detailed feedback, gap analysis results,
and recommendation display for SkillScan MVP.

Author: SkillScan Team
Date: 2026-04-15
"""

import logging
import json
from typing import Dict, List, Any, Optional

from backend.utils.model_client import GeminiClient
from backend.models import AssessmentResponse, SkillScore, Assessment, Skills
from backend.database import db

logger = logging.getLogger(__name__)


class AssessmentResultsFormatter:
    """Formats and prepares assessment results for frontend display"""
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize results formatter
        
        Args:
            gemini_client: GeminiClient for generating additional recommendations
        """
        self.gemini_client = gemini_client or GeminiClient()
        logger.info("AssessmentResultsFormatter initialized")
    
    def format_results_response(
        self,
        assessment_response: AssessmentResponse,
        unlocked_difficulty: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format assessment results for API response
        
        Args:
            assessment_response: AssessmentResponse record
            unlocked_difficulty: Newly unlocked difficulty if any
            
        Returns:
            Formatted results dictionary
        """
        try:
            assessment = Assessment.query.get(assessment_response.assessment_id)
            skill = Skills.query.get(assessment.skill_id)
            
            # Parse stored data
            gaps = json.loads(assessment_response.gaps) if isinstance(assessment_response.gaps, str) else assessment_response.gaps
            responses = json.loads(assessment_response.responses) if isinstance(assessment_response.responses, str) else assessment_response.responses
            
            # Generate recommendations
            recommendations = self._generate_learning_recommendations(
                skill_id=assessment.skill_id,
                gaps=gaps,
                difficulty=assessment.difficulty,
                score=assessment_response.score
            )
            
            result = {
                "assessment_id": assessment.id,
                "skill_id": assessment.skill_id,
                "skill_name": skill.skill_name if skill else "Unknown",
                "difficulty": assessment.difficulty,
                "assessment_type": assessment.assessment_type,
                "score": assessment_response.score,
                "badge": assessment_response.badge,
                "passed": assessment_response.score >= 70,
                "feedback": assessment_response.feedback,
                "gaps_identified": gaps,
                "detailed_feedback": self._format_detailed_feedback(
                    assessment.assessment_type,
                    responses,
                    assessment_response.feedback
                ),
                "recommendations": recommendations,
                "unlocked_difficulty": unlocked_difficulty,
                "submitted_at": assessment_response.submitted_at.isoformat() if assessment_response.submitted_at else None,
                "progress": self._get_difficulty_progress(assessment.skill_id),
                "best_score": self._get_best_score_for_skill(
                    assessment_response.student_id,
                    assessment.skill_id
                )
            }
            
            logger.info(f"Results formatted: {result['skill_name']} - {result['score']}%")
            return result
            
        except Exception as e:
            logger.error(f"Error formatting results: {str(e)}")
            return {"error": str(e)}
    
    def _generate_learning_recommendations(
        self,
        skill_id: int,
        gaps: List[str],
        difficulty: str,
        score: int
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized learning recommendations
        
        Args:
            skill_id: Skill ID
            gaps: List of identified gaps
            difficulty: Assessment difficulty
            score: Assessment score
            
        Returns:
            List of recommendation dictionaries
        """
        try:
            skill = Skills.query.get(skill_id)
            skill_name = skill.skill_name if skill else "Unknown"
            
            recommendations = []
            
            # Base recommendations on gaps
            resource_types = [
                {"type": "Online Course", "icon": "🎓", "platform": "Coursera/Udemy"},
                {"type": "YouTube Tutorial", "icon": "▶️", "platform": "YouTube"},
                {"type": "Book/Article", "icon": "📚", "platform": "Various"},
                {"type": "Project", "icon": "🔧", "platform": "GitHub"}
            ]
            
            time_estimates = ["1-2 weeks", "2-3 weeks", "3-5 days"]
            
            for idx, gap in enumerate(gaps[:5]):  # Top 5 gaps
                rec = {
                    "id": idx + 1,
                    "gap_area": gap,
                    "resource_type": resource_types[idx % len(resource_types)]["type"],
                    "icon": resource_types[idx % len(resource_types)]["icon"],
                    "platform": resource_types[idx % len(resource_types)]["platform"],
                    "priority": ["Critical", "High", "Medium", "Low", "Optional"][idx],
                    "estimated_time": time_estimates[idx % len(time_estimates)],
                    "next_difficulty": self._suggest_next_step(score, difficulty),
                    "description": f"Focus on improving {gap} to strengthen your {skill_name} skills"
                }
                recommendations.append(rec)
            
            logger.info(f"Generated {len(recommendations)} recommendations for skill {skill_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def _suggest_next_step(self, score: int, current_difficulty: str) -> str:
        """
        Suggest next step based on score
        
        Args:
            score: Assessment score
            current_difficulty: Current difficulty level
            
        Returns:
            Suggestion string
        """
        if score >= 90:
            if current_difficulty == "easy":
                return "Ready for Medium difficulty!"
            elif current_difficulty == "medium":
                return "Ready for Hard difficulty!"
            else:
                return "Mastered! Consider other skills"
        elif score >= 70:
            return "Good! Practice more before advancing"
        else:
            return "Review fundamentals before retrying"
    
    def _format_detailed_feedback(
        self,
        assessment_type: str,
        responses: Dict[str, Any],
        summary_feedback: str
    ) -> Dict[str, Any]:
        """
        Format detailed feedback by assessment type
        
        Args:
            assessment_type: Type of assessment (mcq/coding/casestudy)
            responses: User responses
            summary_feedback: Summary feedback from AI
            
        Returns:
            Detailed feedback dictionary
        """
        try:
            if assessment_type == "mcq":
                return self._format_mcq_feedback(responses, summary_feedback)
            elif assessment_type == "coding":
                return self._format_coding_feedback(responses, summary_feedback)
            elif assessment_type == "casestudy":
                return self._format_casestudy_feedback(responses, summary_feedback)
            else:
                return {"summary": summary_feedback}
                
        except Exception as e:
            logger.error(f"Error formatting detailed feedback: {str(e)}")
            return {"summary": summary_feedback}
    
    def _format_mcq_feedback(self, responses: Dict[str, Any], summary: str) -> Dict[str, Any]:
        """Format MCQ-specific feedback"""
        return {
            "summary": summary,
            "questions_attempted": len(responses.get("selected_options", {})),
            "feedback_type": "mcq",
            "details": "Review incorrect answers and understand the concepts"
        }
    
    def _format_coding_feedback(self, responses: Dict[str, Any], summary: str) -> Dict[str, Any]:
        """Format Coding-specific feedback"""
        return {
            "summary": summary,
            "problems_attempted": len(responses.get("solutions", [])),
            "feedback_type": "coding",
            "details": "Check test case failures and optimize your solutions"
        }
    
    def _format_casestudy_feedback(self, responses: Dict[str, Any], summary: str) -> Dict[str, Any]:
        """Format Case Study-specific feedback"""
        return {
            "summary": summary,
            "scenarios_attempted": len(responses.get("answers", {})),
            "feedback_type": "casestudy",
            "details": "Review business logic and real-world applicability"
        }
    
    def _get_difficulty_progress(self, skill_id: int) -> Dict[str, Any]:
        """
        Get difficulty progression status
        
        Args:
            skill_id: Skill ID
            
        Returns:
            Progress dictionary
        """
        try:
            return {
                "easy": {
                    "status": "completed",
                    "unlocked": True,
                    "best_score": None
                },
                "medium": {
                    "status": "locked",
                    "unlocked": False,
                    "requirement": "Pass Easy with 70%+"
                },
                "hard": {
                    "status": "locked",
                    "unlocked": False,
                    "requirement": "Pass Medium with 70%+"
                }
            }
        except Exception as e:
            logger.error(f"Error getting progress: {str(e)}")
            return {}
    
    def _get_best_score_for_skill(self, student_id: int, skill_id: int) -> Optional[int]:
        """
        Get best score for a skill
        
        Args:
            student_id: Student ID
            skill_id: Skill ID
            
        Returns:
            Best score or None
        """
        try:
            score = SkillScore.query.filter_by(
                student_id=student_id,
                skill_id=skill_id
            ).first()
            
            return score.score if score else None
            
        except Exception as e:
            logger.error(f"Error getting best score: {str(e)}")
            return None
    
    def generate_gap_analysis_report(
        self,
        student_id: int,
        skill_id: int
    ) -> Dict[str, Any]:
        """
        Generate comprehensive gap analysis report
        
        Args:
            student_id: Student ID
            skill_id: Skill ID
            
        Returns:
            Gap analysis report
        """
        try:
            # Get all assessments for this skill
            assessments = AssessmentResponse.query.join(Assessment).filter(
                AssessmentResponse.student_id == student_id,
                Assessment.skill_id == skill_id
            ).all()
            
            if not assessments:
                return {"error": "No assessment history"}
            
            # Analyze gaps across all attempts
            all_gaps = {}
            total_score = 0
            
            for assessment in assessments:
                gaps = json.loads(assessment.gaps) if isinstance(assessment.gaps, str) else assessment.gaps
                for gap in gaps:
                    all_gaps[gap] = all_gaps.get(gap, 0) + 1
                total_score += assessment.score
            
            avg_score = total_score / len(assessments) if assessments else 0
            
            # Sort gaps by frequency
            sorted_gaps = sorted(all_gaps.items(), key=lambda x: x[1], reverse=True)
            
            skill = Skills.query.get(skill_id)
            
            report = {
                "skill_id": skill_id,
                "skill_name": skill.skill_name if skill else "Unknown",
                "total_attempts": len(assessments),
                "average_score": round(avg_score, 2),
                "best_score": max([a.score for a in assessments]) if assessments else 0,
                "consistent_gaps": [gap for gap, count in sorted_gaps[:5]],
                "improvement_trend": self._calculate_trend(assessments),
                "recommendations": self._generate_gap_recommendations(sorted_gaps)
            }
            
            logger.info(f"Gap analysis generated for student {student_id}, skill {skill_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating gap analysis: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_trend(self, assessments: List[AssessmentResponse]) -> str:
        """Calculate improvement trend"""
        if len(assessments) < 2:
            return "insufficient_data"
        
        scores = [a.score for a in assessments]
        if scores[-1] > scores[0]:
            return "improving"
        elif scores[-1] == scores[0]:
            return "stable"
        else:
            return "declining"
    
    def _generate_gap_recommendations(self, gaps: List[tuple]) -> List[str]:
        """Generate recommendations from gaps"""
        return [
            f"Work on: {gap[0]}" for gap in gaps[:3]
        ]
