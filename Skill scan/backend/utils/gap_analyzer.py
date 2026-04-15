"""
SkillScan MVP - Gap Analysis Engine
Analyzes student skill gaps, identifies weak areas, and generates prioritized recommendations.
Implements gap threshold of 60-79% per specification.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, and_
from models import (
    Student, SkillScore, AssessmentResponse, Assessment, 
    SkillsTaxonomy, db
)

logger = logging.getLogger(__name__)

# Gap Threshold Constants (per specification)
GAP_LOWER_THRESHOLD = 60  # 60-79% = gaps identified
GAP_UPPER_THRESHOLD = 79
MINOR_GAP_LOWER = 80     # 80-89% = minor gaps
MINOR_GAP_UPPER = 89
NO_GAP_THRESHOLD = 90    # 90-100% = no gaps

# Benchmark scores by user type (percentage scale)
BENCHMARK_SCORES = {
    "MBA": 75,
    "BCA": 72
}

# Priority calculation weights
FREQUENCY_WEIGHT = 0.6
IMPACT_WEIGHT = 0.4


class GapAnalyzer:
    """
    Analyzes student skill gaps and generates gap reports with prioritization.
    
    Implements gap analysis logic:
    - Gap definition: 60-79% score range
    - Priority calculation: (frequency × 0.6) + (impact × 0.4)
    - Benchmarking: Compare to industry standards
    - Percentile ranking: Compare to peer students
    """
    
    def __init__(self, gemini_client: Optional[Any] = None):
        """
        Initialize GapAnalyzer.
        
        Args:
            gemini_client (Optional[Any]): Gemini API client for enhanced analysis.
                                          If not provided, uses basic analysis.
        """
        self.gemini_client = gemini_client
        logger.info("GapAnalyzer initialized")
    
    def analyze_gaps(
        self, 
        student_id: int, 
        skill_id: int
    ) -> List[Dict[str, Any]]:
        """
        Identify and prioritize skill gaps for a student in a specific skill.
        
        Gap Definition: Scores in 60-79% range are considered gaps.
        Frequency: How often the gap appears across multiple assessments.
        Impact: Difference from benchmark score (higher difference = higher impact).
        
        Args:
            student_id (int): Student ID
            skill_id (int): Skill ID
        
        Returns:
            List[Dict]: Sorted list of gaps with structure:
                {
                    'skill_id': int,
                    'gap_id': str,
                    'name': str,
                    'frequency': int,
                    'impact': float,
                    'priority': float,
                    'score_range': List[int],
                    'assessments_count': int
                }
        """
        try:
            # Get all skill scores for student+skill
            skill_scores = SkillScore.query.filter(
                and_(
                    SkillScore.student_id == student_id,
                    SkillScore.skill_id == skill_id
                )
            ).all()
            
            if not skill_scores:
                logger.info(f"No assessment history for student {student_id}, skill {skill_id}")
                return []
            
            # Convert scores to percentage (1-10 scale → 0-100 percentage)
            percentage_scores = [int(score.score * 10) for score in skill_scores]
            
            # Identify gap scores (60-79%)
            gap_scores = [s for s in percentage_scores if GAP_LOWER_THRESHOLD <= s <= GAP_UPPER_THRESHOLD]
            
            if not gap_scores:
                logger.info(f"No gaps identified for student {student_id}, skill {skill_id}")
                return []
            
            # Calculate frequency
            frequency = len(gap_scores)
            total_assessments = len(percentage_scores)
            frequency_percentage = (frequency / total_assessments) * 100
            
            # Calculate impact (distance from benchmark)
            benchmark = self.get_industry_benchmark(skill_id)
            avg_gap_score = sum(gap_scores) / len(gap_scores)
            impact = max(0, benchmark - avg_gap_score)  # Higher gap = higher impact
            
            # Calculate priority
            priority = self.calculate_gap_priority(
                gap_name="Main Gap",
                frequency=frequency_percentage,
                impact=impact
            )
            
            gaps = [
                {
                    'skill_id': skill_id,
                    'gap_id': f'gap_{skill_id}_main',
                    'name': 'Skill Gap Identified',
                    'frequency': frequency,
                    'frequency_percentage': frequency_percentage,
                    'impact': impact,
                    'priority': priority,
                    'score_range': gap_scores,
                    'avg_score': avg_gap_score,
                    'assessments_count': total_assessments
                }
            ]
            
            # Sort by priority descending
            gaps.sort(key=lambda x: x['priority'], reverse=True)
            logger.info(f"Identified {len(gaps)} gap(s) for student {student_id}, skill {skill_id}")
            
            return gaps
        
        except Exception as e:
            logger.error(f"Error analyzing gaps for student {student_id}, skill {skill_id}: {str(e)}")
            return []
    
    def identify_weak_areas(
        self, 
        student_id: int, 
        skill_id: int, 
        gaps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Cluster gaps by theme and group related gaps together.
        
        Args:
            student_id (int): Student ID
            skill_id (int): Skill ID
            gaps (List[Dict]): List of identified gaps from analyze_gaps()
        
        Returns:
            List[Dict]: Grouped weak areas:
                {
                    'theme': str,
                    'gaps': List[str],
                    'priority': str (high/medium/low),
                    'priority_score': float,
                    'gap_count': int,
                    'avg_frequency': float
                }
        """
        try:
            if not gaps:
                logger.info(f"No gaps to identify weak areas for student {student_id}")
                return []
            
            # Get skill details for context
            skill = SkillsTaxonomy.query.get(skill_id)
            if not skill:
                logger.warning(f"Skill {skill_id} not found")
                return []
            
            # Group gaps into weak area theme
            # For MVP, we have one main gap per skill, but structure allows for multiple
            weak_areas = []
            
            for gap in gaps:
                priority_score = gap.get('priority', 0)
                
                # Determine priority level based on score (0-100 scale)
                if priority_score >= 75:
                    priority_level = 'high'
                elif priority_score >= 50:
                    priority_level = 'medium'
                else:
                    priority_level = 'low'
                
                weak_area = {
                    'theme': f"{skill.name} - {gap['name']}",
                    'skill_id': skill_id,
                    'gaps': [gap['gap_id']],
                    'priority': priority_level,
                    'priority_score': priority_score,
                    'gap_count': 1,
                    'avg_frequency': gap.get('frequency_percentage', 0),
                    'avg_impact': gap.get('impact', 0)
                }
                weak_areas.append(weak_area)
            
            logger.info(f"Identified {len(weak_areas)} weak area(s) for student {student_id}")
            return weak_areas
        
        except Exception as e:
            logger.error(f"Error identifying weak areas: {str(e)}")
            return []
    
    def calculate_gap_priority(
        self, 
        gap_name: str, 
        frequency: float, 
        impact: float
    ) -> float:
        """
        Calculate priority score for a gap using weighted formula.
        
        Formula: priority = (frequency × 0.6) + (impact × 0.4)
        - Frequency: 0-100 (percentage of assessments with gap)
        - Impact: 0-100 (difference from benchmark)
        - Result: 0-100 priority score
        
        Args:
            gap_name (str): Name of the gap (for logging)
            frequency (float): Frequency percentage (0-100)
            impact (float): Impact score (0-100)
        
        Returns:
            float: Priority score (0-100)
        """
        try:
            # Normalize inputs to 0-100 scale
            frequency_norm = min(100, max(0, frequency))
            impact_norm = min(100, max(0, impact))
            
            # Calculate weighted priority
            priority = (frequency_norm * FREQUENCY_WEIGHT) + (impact_norm * IMPACT_WEIGHT)
            
            logger.debug(f"Gap '{gap_name}': frequency={frequency_norm}%, impact={impact_norm}% → priority={priority:.2f}")
            return priority
        
        except Exception as e:
            logger.error(f"Error calculating gap priority for '{gap_name}': {str(e)}")
            return 0.0
    
    def get_industry_benchmark(self, skill_id: int) -> float:
        """
        Get industry average benchmark for a skill.
        
        Returns benchmark based on user type:
        - MBA: 75%
        - BCA: 72%
        
        Falls back to seed data if available.
        
        Args:
            skill_id (int): Skill ID
        
        Returns:
            float: Industry benchmark score (0-100 percentage)
        """
        try:
            skill = SkillsTaxonomy.query.get(skill_id)
            if not skill:
                logger.warning(f"Skill {skill_id} not found for benchmark lookup")
                return 70.0  # Default fallback
            
            # Check if skill has industry_benchmark field (1-10 scale)
            if skill.industry_benchmark:
                benchmark_percentage = skill.industry_benchmark * 10  # Convert to percentage
                logger.debug(f"Benchmark for skill {skill_id} ({skill.name}): {benchmark_percentage}%")
                return benchmark_percentage
            
            # Fallback to default based on target users
            if skill.target_users:
                if "MBA" in skill.target_users:
                    benchmark = BENCHMARK_SCORES["MBA"]
                elif "BCA" in skill.target_users:
                    benchmark = BENCHMARK_SCORES["BCA"]
                else:
                    benchmark = 70.0
            else:
                benchmark = 70.0
            
            logger.debug(f"Benchmark for skill {skill_id} ({skill.name}): {benchmark}%")
            return benchmark
        
        except Exception as e:
            logger.error(f"Error getting benchmark for skill {skill_id}: {str(e)}")
            return 70.0  # Safe default
    
    def calculate_percentile(
        self, 
        student_id: int, 
        skill_id: int, 
        score: float
    ) -> int:
        """
        Calculate student's percentile rank compared to all students.
        
        Compares student's score against all other students' scores for the skill.
        Percentile = (students_with_lower_score / total_students) × 100
        
        Args:
            student_id (int): Student ID
            skill_id (int): Skill ID
            score (float): Student's score (1-10 scale or 0-100 percentage)
        
        Returns:
            int: Percentile rank (0-100)
        """
        try:
            # Normalize score if on 1-10 scale
            score_percentage = score * 10 if score <= 10 else score
            
            # Get all scores for this skill across all students
            all_scores = db.session.query(
                SkillScore.score
            ).filter(
                SkillScore.skill_id == skill_id
            ).all()
            
            if not all_scores:
                logger.warning(f"No scores found for skill {skill_id}")
                return 50  # Default to median
            
            all_scores_list = [s.score * 10 for s in all_scores]  # Convert to percentage
            
            # Count how many scores are lower than student's score
            lower_count = sum(1 for s in all_scores_list if s < score_percentage)
            total_count = len(all_scores_list)
            
            percentile = int((lower_count / total_count) * 100) if total_count > 0 else 50
            
            logger.debug(f"Percentile for student {student_id}, skill {skill_id}: {percentile}th")
            return percentile
        
        except Exception as e:
            logger.error(f"Error calculating percentile: {str(e)}")
            return 50  # Safe default
    
    def generate_gap_report(
        self, 
        student_id: int, 
        skill_id: int
    ) -> Dict[str, Any]:
        """
        Generate comprehensive gap analysis report for a skill.
        
        Combines all gap analysis methods into one report with:
        - Current score vs benchmark
        - Percentile ranking
        - Identified gaps and weak areas
        - Improvement potential
        - Recommended focus areas
        
        Args:
            student_id (int): Student ID
            skill_id (int): Skill ID
        
        Returns:
            Dict: Comprehensive report:
                {
                    'skill_id': int,
                    'skill_name': str,
                    'current_score': float,
                    'benchmark_score': float,
                    'percentile': int,
                    'gaps_identified': List[Dict],
                    'weak_areas': List[Dict],
                    'improvement_potential': float,
                    'recommended_focus_areas': List[str],
                    'generated_at': str
                }
        """
        try:
            # Get skill info
            skill = SkillsTaxonomy.query.get(skill_id)
            if not skill:
                logger.error(f"Skill {skill_id} not found")
                return {
                    'error': f'Skill {skill_id} not found',
                    'status': 404
                }
            
            # Get current score (best score)
            best_score = db.session.query(
                func.max(SkillScore.score)
            ).filter(
                and_(
                    SkillScore.student_id == student_id,
                    SkillScore.skill_id == skill_id
                )
            ).scalar()
            
            current_score = (best_score * 10) if best_score else 0  # Convert to percentage
            
            # Get benchmark
            benchmark = self.get_industry_benchmark(skill_id)
            
            # Calculate percentile
            percentile = self.calculate_percentile(student_id, skill_id, best_score or 0)
            
            # Analyze gaps
            gaps = self.analyze_gaps(student_id, skill_id)
            
            # Identify weak areas
            weak_areas = self.identify_weak_areas(student_id, skill_id, gaps)
            
            # Calculate improvement potential
            improvement_potential = max(0, benchmark - current_score)
            
            # Generate focus areas
            focus_areas = []
            if gaps:
                focus_areas.append("Core skill development needed")
                for gap in gaps:
                    focus_areas.append(f"Address {gap['name']}: currently {gap['avg_score']:.0f}%")
            
            report = {
                'skill_id': skill_id,
                'skill_name': skill.name,
                'skill_category': skill.category,
                'current_score': current_score,
                'benchmark_score': benchmark,
                'gap_status': self._get_gap_status(current_score),
                'percentile': percentile,
                'gaps_identified': gaps,
                'weak_areas': weak_areas,
                'improvement_potential': improvement_potential,
                'recommended_focus_areas': focus_areas,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Generated gap report for student {student_id}, skill {skill_id}")
            return report
        
        except Exception as e:
            logger.error(f"Error generating gap report: {str(e)}")
            return {
                'error': str(e),
                'status': 500
            }
    
    def get_best_and_worst_assessments(
        self, 
        student_id: int, 
        skill_id: int
    ) -> Dict[str, Any]:
        """
        Find best and worst scoring assessments for a skill.
        
        Args:
            student_id (int): Student ID
            skill_id (int): Skill ID
        
        Returns:
            Dict: {
                'best': {'score': float, 'date': str, 'assessment_id': int},
                'worst': {'score': float, 'date': str, 'assessment_id': int, 'gaps': List}
            }
        """
        try:
            # Get best assessment
            best = db.session.query(
                SkillScore
            ).filter(
                and_(
                    SkillScore.student_id == student_id,
                    SkillScore.skill_id == skill_id
                )
            ).order_by(
                SkillScore.score.desc()
            ).first()
            
            # Get worst assessment
            worst = db.session.query(
                SkillScore
            ).filter(
                and_(
                    SkillScore.student_id == student_id,
                    SkillScore.skill_id == skill_id
                )
            ).order_by(
                SkillScore.score.asc()
            ).first()
            
            result = {}
            
            if best:
                result['best'] = {
                    'score': int(best.score * 10),
                    'date': best.scored_at.isoformat(),
                    'assessment_id': best.assessment_id,
                    'confidence': float(best.ai_confidence)
                }
            
            if worst:
                result['worst'] = {
                    'score': int(worst.score * 10),
                    'date': worst.scored_at.isoformat(),
                    'assessment_id': worst.assessment_id,
                    'gaps': worst.gaps_identified or [],
                    'confidence': float(worst.ai_confidence)
                }
            
            logger.debug(f"Retrieved best/worst assessments for student {student_id}, skill {skill_id}")
            return result
        
        except Exception as e:
            logger.error(f"Error getting best/worst assessments: {str(e)}")
            return {}
    
    def track_gap_progression(
        self, 
        student_id: int, 
        skill_id: int, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Track historical gap progression over time.
        
        Shows whether gaps are improving, stable, or worsening.
        
        Args:
            student_id (int): Student ID
            skill_id (int): Skill ID
            limit (int): Number of historical records to analyze (default 10)
        
        Returns:
            Dict: {
                'trend': str ('improving', 'stable', 'worsening'),
                'progression': List[{score, date}],
                'first_score': float,
                'latest_score': float,
                'change': float,
                'assessments': int
            }
        """
        try:
            # Get historical scores
            scores = db.session.query(
                SkillScore
            ).filter(
                and_(
                    SkillScore.student_id == student_id,
                    SkillScore.skill_id == skill_id
                )
            ).order_by(
                SkillScore.scored_at.asc()
            ).limit(limit).all()
            
            if len(scores) < 2:
                logger.info(f"Insufficient history for progression tracking: student {student_id}, skill {skill_id}")
                return {
                    'trend': 'insufficient_data',
                    'progression': [],
                    'assessments': len(scores)
                }
            
            # Build progression list
            progression = [
                {
                    'score': int(s.score * 10),
                    'date': s.scored_at.isoformat()
                }
                for s in scores
            ]
            
            # Calculate trend
            first_score = scores[0].score * 10
            latest_score = scores[-1].score * 10
            change = latest_score - first_score
            
            # Determine trend
            if change > 5:
                trend = 'improving'
            elif change < -5:
                trend = 'worsening'
            else:
                trend = 'stable'
            
            result = {
                'trend': trend,
                'progression': progression,
                'first_score': first_score,
                'latest_score': latest_score,
                'change': change,
                'assessments': len(scores)
            }
            
            logger.info(f"Gap progression for student {student_id}, skill {skill_id}: {trend} ({change:+.0f}%)")
            return result
        
        except Exception as e:
            logger.error(f"Error tracking gap progression: {str(e)}")
            return {
                'error': str(e),
                'trend': 'error'
            }
    
    def _get_gap_status(self, score: float) -> str:
        """
        Get human-readable gap status based on score.
        
        Args:
            score (float): Score in 0-100 percentage
        
        Returns:
            str: Gap status (expert, good, fair, fundamental)
        """
        if score >= NO_GAP_THRESHOLD:
            return 'expert'
        elif score >= MINOR_GAP_LOWER:
            return 'good'
        elif score >= GAP_LOWER_THRESHOLD:
            return 'fair'
        else:
            return 'fundamental'
