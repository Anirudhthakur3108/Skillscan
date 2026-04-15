"""
CSV Export Module

Generates CSV exports of assessments, skills, and student profile data.

Author: SkillScan Team
Date: 2026-04-15
"""

import logging
import csv
import io
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class CSVExporter:
    """Generates CSV exports of assessment and student data"""
    
    def __init__(self):
        """Initialize CSV exporter"""
        logger.info("CSVExporter initialized")
    
    @staticmethod
    def export_assessments_csv(
        assessments_data: List[Dict]
    ) -> Optional[str]:
        """
        Export assessments to CSV format
        
        Args:
            assessments_data: List of assessment export dicts
            
        Returns:
            CSV string
        """
        try:
            logger.info(f"Exporting {len(assessments_data)} assessments to CSV")
            
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    'Assessment ID',
                    'Skill Name',
                    'Assessment Type',
                    'Difficulty',
                    'Score',
                    'Performance Badge',
                    'Total Questions',
                    'Gaps Identified',
                    'Time Spent (minutes)',
                    'Date Taken',
                    'Timestamp'
                ]
            )
            
            writer.writeheader()
            
            for assessment in assessments_data:
                writer.writerow({
                    'Assessment ID': assessment.get('assessment_id', ''),
                    'Skill Name': assessment.get('skill_name', 'Unknown'),
                    'Assessment Type': assessment.get('assessment_type', ''),
                    'Difficulty': assessment.get('difficulty', ''),
                    'Score': assessment.get('score', 0),
                    'Performance Badge': assessment.get('badge', 'N/A'),
                    'Total Questions': assessment.get('total_questions', 0),
                    'Gaps Identified': len(assessment.get('gaps_identified', [])),
                    'Time Spent (minutes)': assessment.get('time_spent_minutes', 0),
                    'Date Taken': assessment.get('created_at', ''),
                    'Timestamp': assessment.get('export_timestamp', '')
                })
            
            csv_string = output.getvalue()
            logger.info(f"Assessments CSV generated: {len(csv_string)} bytes")
            return csv_string
            
        except Exception as e:
            logger.error(f"Error exporting assessments to CSV: {str(e)}")
            return None
    
    @staticmethod
    def export_skills_csv(
        skills_data: List[Dict],
        overall_stats: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Export skills to CSV format
        
        Args:
            skills_data: List of skill export dicts
            overall_stats: Optional overall student stats
            
        Returns:
            CSV string
        """
        try:
            logger.info(f"Exporting {len(skills_data)} skills to CSV")
            
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    'Skill Name',
                    'Current Score',
                    'Proficiency Level',
                    'Last Assessed',
                    'Assessments Taken',
                    'Best Score',
                    'Average Score',
                    'Status'
                ]
            )
            
            writer.writeheader()
            
            for skill in skills_data:
                writer.writerow({
                    'Skill Name': skill.get('skill_name', 'Unknown'),
                    'Current Score': skill.get('score', 0),
                    'Proficiency Level': skill.get('proficiency', 'Beginner'),
                    'Last Assessed': skill.get('last_assessed', ''),
                    'Assessments Taken': skill.get('assessments_taken', 0),
                    'Best Score': skill.get('best_score', 0),
                    'Average Score': skill.get('average_score', 0),
                    'Status': skill.get('status', 'Unlocked')
                })
            
            csv_string = output.getvalue()
            logger.info(f"Skills CSV generated: {len(csv_string)} bytes")
            return csv_string
            
        except Exception as e:
            logger.error(f"Error exporting skills to CSV: {str(e)}")
            return None
    
    @staticmethod
    def export_gap_analysis_csv(
        gap_data: Dict
    ) -> Optional[str]:
        """
        Export gap analysis to CSV format
        
        Args:
            gap_data: Gap analysis export dict
            
        Returns:
            CSV string
        """
        try:
            logger.info(f"Exporting gap analysis for skill {gap_data.get('skill_id')} to CSV")
            
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    'Skill Name',
                    'Current Score',
                    'Benchmark Score',
                    'Percentile',
                    'Gap Name',
                    'Frequency',
                    'Priority',
                    'Impact Score',
                    'Recommendation'
                ]
            )
            
            writer.writeheader()
            
            gaps = gap_data.get('gaps', [])
            recommendations = gap_data.get('recommendations', [])
            
            for idx, gap in enumerate(gaps):
                writer.writerow({
                    'Skill Name': gap_data.get('skill_name', 'Unknown'),
                    'Current Score': gap_data.get('current_score', 0),
                    'Benchmark Score': gap_data.get('benchmark_score', 75),
                    'Percentile': gap_data.get('percentile', 50),
                    'Gap Name': gap.get('name', 'N/A'),
                    'Frequency': gap.get('frequency', 0),
                    'Priority': gap.get('priority', 'Medium'),
                    'Impact Score': gap.get('impact', 0),
                    'Recommendation': recommendations[idx] if idx < len(recommendations) else ''
                })
            
            csv_string = output.getvalue()
            logger.info(f"Gap analysis CSV generated: {len(csv_string)} bytes")
            return csv_string
            
        except Exception as e:
            logger.error(f"Error exporting gap analysis to CSV: {str(e)}")
            return None
    
    @staticmethod
    def export_learning_plans_csv(
        plans_data: List[Dict]
    ) -> Optional[str]:
        """
        Export learning plans to CSV format
        
        Args:
            plans_data: List of learning plan export dicts
            
        Returns:
            CSV string
        """
        try:
            logger.info(f"Exporting {len(plans_data)} learning plans to CSV")
            
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    'Plan ID',
                    'Skill ID',
                    'Duration (weeks)',
                    'Progress (%)',
                    'Status',
                    'Created Date',
                    'End Date'
                ]
            )
            
            writer.writeheader()
            
            for plan in plans_data:
                writer.writerow({
                    'Plan ID': plan.get('id', ''),
                    'Skill ID': plan.get('skill_id', ''),
                    'Duration (weeks)': plan.get('duration_weeks', 0),
                    'Progress (%)': plan.get('progress', 0),
                    'Status': plan.get('status', 'Active'),
                    'Created Date': plan.get('created_at', ''),
                    'End Date': plan.get('end_date', '')
                })
            
            csv_string = output.getvalue()
            logger.info(f"Learning plans CSV generated: {len(csv_string)} bytes")
            return csv_string
            
        except Exception as e:
            logger.error(f"Error exporting learning plans to CSV: {str(e)}")
            return None
    
    @staticmethod
    def export_complete_profile_csv(
        profile_data: Dict
    ) -> Optional[str]:
        """
        Export complete profile to CSV format (summary)
        
        Args:
            profile_data: Complete profile export dict
            
        Returns:
            CSV string
        """
        try:
            logger.info(f"Exporting complete profile to CSV")
            
            output = io.StringIO()
            
            # Summary section
            output.write("=== STUDENT PROFILE SUMMARY ===\n")
            output.write(f"Name,{profile_data.get('student_name', 'Unknown')}\n")
            output.write(f"Email,{profile_data.get('email', '')}\n")
            output.write(f"User Type,{profile_data.get('user_type', '')}\n")
            output.write(f"Total Skills,{profile_data.get('total_skills', 0)}\n")
            output.write(f"Average Score,{profile_data.get('average_score', 0)}\n")
            output.write(f"Assessments Taken,{profile_data.get('assessments_taken', 0)}\n")
            output.write(f"Active Learning Plans,{profile_data.get('active_learning_plans', 0)}\n")
            output.write(f"Total Gaps,{profile_data.get('total_gaps', 0)}\n\n")
            
            # Skills section
            output.write("=== SKILLS ===\n")
            skills = profile_data.get('skills', [])
            if skills:
                writer = csv.DictWriter(
                    output,
                    fieldnames=['Skill Name', 'Score', 'Proficiency', 'Last Assessed']
                )
                writer.writeheader()
                for skill in skills:
                    writer.writerow({
                        'Skill Name': skill.get('skill_name', ''),
                        'Score': skill.get('score', 0),
                        'Proficiency': skill.get('proficiency', ''),
                        'Last Assessed': skill.get('last_assessed', '')
                    })
                output.write("\n")
            
            # Assessments section
            output.write("=== ASSESSMENT HISTORY ===\n")
            assessments = profile_data.get('assessments', [])
            if assessments:
                writer = csv.DictWriter(
                    output,
                    fieldnames=['Assessment Type', 'Skill ID', 'Score', 'Date']
                )
                writer.writeheader()
                for assess in assessments:
                    writer.writerow({
                        'Assessment Type': assess.get('type', ''),
                        'Skill ID': assess.get('skill_id', ''),
                        'Score': assess.get('score', 0),
                        'Date': assess.get('date', '')
                    })
                output.write("\n")
            
            # Gaps section
            output.write("=== IDENTIFIED GAPS ===\n")
            gaps = profile_data.get('gaps', [])
            if gaps:
                writer = csv.DictWriter(
                    output,
                    fieldnames=['Skill ID', 'Gap Name', 'Priority']
                )
                writer.writeheader()
                for gap in gaps:
                    writer.writerow({
                        'Skill ID': gap.get('skill_id', ''),
                        'Gap Name': gap.get('gap_name', ''),
                        'Priority': gap.get('priority', '')
                    })
                output.write("\n")
            
            # Learning Plans section
            output.write("=== LEARNING PLANS ===\n")
            plans = profile_data.get('learning_plans', [])
            if plans:
                writer = csv.DictWriter(
                    output,
                    fieldnames=['Skill ID', 'Duration', 'Progress', 'Status']
                )
                writer.writeheader()
                for plan in plans:
                    writer.writerow({
                        'Skill ID': plan.get('skill_id', ''),
                        'Duration': plan.get('duration', 0),
                        'Progress': plan.get('progress', 0),
                        'Status': plan.get('status', '')
                    })
            
            csv_string = output.getvalue()
            logger.info(f"Complete profile CSV generated: {len(csv_string)} bytes")
            return csv_string
            
        except Exception as e:
            logger.error(f"Error exporting complete profile to CSV: {str(e)}")
            return None
    
    @staticmethod
    def escape_csv_value(value: str) -> str:
        """
        Escape special characters in CSV values
        
        Args:
            value: Value to escape
            
        Returns:
            Escaped value
        """
        if not value:
            return ''
        
        value = str(value)
        if '"' in value or ',' in value or '\n' in value:
            value = '"' + value.replace('"', '""') + '"'
        
        return value
