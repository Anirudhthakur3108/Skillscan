"""
PDF Report Generator Module

Generates comprehensive PDF reports for assessments, gap analysis, and student profiles
using ReportLab library.

Author: SkillScan Team
Date: 2026-04-15
"""

import logging
import io
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.platypus import KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generates professional PDF reports for assessments and student data"""
    
    def __init__(self):
        """Initialize PDF generator"""
        self.page_width, self.page_height = letter
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        logger.info("PDFReportGenerator initialized")
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a365d'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Normal text
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=6
        ))
    
    def generate_assessment_pdf(
        self,
        assessment_data: Dict
    ) -> Optional[bytes]:
        """
        Generate PDF report for assessment results
        
        Args:
            assessment_data: Assessment export data dict
            
        Returns:
            PDF bytes
        """
        try:
            logger.info(f"Generating assessment PDF for assessment {assessment_data.get('assessment_id')}")
            
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=letter,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            story = []
            
            # Title
            title = Paragraph(
                f"Assessment Report: {assessment_data.get('skill_name', 'Unknown')}",
                self.styles['CustomTitle']
            )
            story.append(title)
            story.append(Spacer(1, 0.3*inch))
            
            # Basic Info
            story.append(self._create_info_section(assessment_data))
            story.append(Spacer(1, 0.2*inch))
            
            # Score Display
            score_table = self._create_score_display(assessment_data)
            story.append(score_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Questions and Answers
            story.append(Paragraph("Questions and Answers", self.styles['SectionHeading']))
            story.append(self._create_qa_section(assessment_data))
            story.append(Spacer(1, 0.2*inch))
            
            # Gaps Identified
            if assessment_data.get('gaps_identified'):
                story.append(Paragraph("Identified Gaps", self.styles['SectionHeading']))
                story.append(self._create_gaps_section(assessment_data.get('gaps_identified', [])))
                story.append(Spacer(1, 0.2*inch))
            
            # Recommendations
            if assessment_data.get('recommendations'):
                story.append(Paragraph("Recommendations", self.styles['SectionHeading']))
                story.append(self._create_recommendations_section(assessment_data.get('recommendations', [])))
            
            # Footer with timestamp
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph(
                f"<i>Report generated on {assessment_data.get('export_timestamp', datetime.utcnow().isoformat())}</i>",
                self.styles['Normal']
            ))
            
            # Build PDF
            doc.build(story)
            pdf_buffer.seek(0)
            pdf_bytes = pdf_buffer.getvalue()
            logger.info(f"Assessment PDF generated: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating assessment PDF: {str(e)}")
            return None
    
    def generate_gap_report_pdf(
        self,
        gap_data: Dict
    ) -> Optional[bytes]:
        """
        Generate PDF report for gap analysis with benchmarks
        
        Args:
            gap_data: Gap analysis export data dict
            
        Returns:
            PDF bytes
        """
        try:
            logger.info(f"Generating gap report PDF for skill {gap_data.get('skill_id')}")
            
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=letter,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            story = []
            
            # Title
            title = Paragraph(
                f"Gap Analysis Report: {gap_data.get('skill_name', 'Unknown')}",
                self.styles['CustomTitle']
            )
            story.append(title)
            story.append(Spacer(1, 0.3*inch))
            
            # Score Summary
            score_table = self._create_gap_score_summary(gap_data)
            story.append(score_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Benchmarking
            story.append(Paragraph("Industry Benchmarking", self.styles['SectionHeading']))
            bench_table = self._create_benchmark_section(gap_data)
            story.append(bench_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Gaps Table
            if gap_data.get('gaps'):
                story.append(Paragraph("Identified Gaps", self.styles['SectionHeading']))
                story.append(self._create_gap_table(gap_data.get('gaps', [])))
                story.append(Spacer(1, 0.2*inch))
            
            # Recommendations
            if gap_data.get('recommendations'):
                story.append(Paragraph("Recommendations", self.styles['SectionHeading']))
                story.append(self._create_recommendations_section(gap_data.get('recommendations', [])))
                story.append(Spacer(1, 0.2*inch))
            
            # Learning Plans
            if gap_data.get('learning_plans'):
                story.append(Paragraph("Active Learning Plans", self.styles['SectionHeading']))
                story.append(self._create_learning_plans_section(gap_data.get('learning_plans', [])))
            
            # Footer
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph(
                f"<i>Report generated on {gap_data.get('export_timestamp', datetime.utcnow().isoformat())}</i>",
                self.styles['Normal']
            ))
            
            doc.build(story)
            pdf_buffer.seek(0)
            pdf_bytes = pdf_buffer.getvalue()
            logger.info(f"Gap report PDF generated: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating gap report PDF: {str(e)}")
            return None
    
    def generate_profile_pdf(
        self,
        profile_data: Dict
    ) -> Optional[bytes]:
        """
        Generate comprehensive PDF report of complete student profile
        
        Args:
            profile_data: Complete profile export data dict
            
        Returns:
            PDF bytes
        """
        try:
            logger.info(f"Generating profile PDF for student")
            
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=letter,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            story = []
            
            # Title
            title = Paragraph(
                "Complete Student Profile Report",
                self.styles['CustomTitle']
            )
            story.append(title)
            story.append(Spacer(1, 0.2*inch))
            
            # Student Info
            story.append(Paragraph("Student Information", self.styles['SectionHeading']))
            story.append(self._create_profile_info(profile_data))
            story.append(Spacer(1, 0.3*inch))
            
            # Overall Stats
            story.append(Paragraph("Overall Statistics", self.styles['SectionHeading']))
            story.append(self._create_profile_stats(profile_data))
            story.append(Spacer(1, 0.3*inch))
            
            # Skills
            if profile_data.get('skills'):
                story.append(PageBreak())
                story.append(Paragraph("Skill Scores", self.styles['SectionHeading']))
                story.append(self._create_profile_skills_table(profile_data.get('skills', [])))
                story.append(Spacer(1, 0.3*inch))
            
            # Assessment History
            if profile_data.get('assessments'):
                story.append(Paragraph("Assessment History", self.styles['SectionHeading']))
                story.append(self._create_profile_assessments_table(profile_data.get('assessments', [])))
                story.append(Spacer(1, 0.3*inch))
            
            # Gaps
            if profile_data.get('gaps'):
                story.append(PageBreak())
                story.append(Paragraph("Gap Analysis Summary", self.styles['SectionHeading']))
                story.append(self._create_profile_gaps_table(profile_data.get('gaps', [])))
                story.append(Spacer(1, 0.3*inch))
            
            # Learning Plans
            if profile_data.get('learning_plans'):
                story.append(Paragraph("Learning Plans", self.styles['SectionHeading']))
                story.append(self._create_profile_plans_table(profile_data.get('learning_plans', [])))
            
            # Footer
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph(
                f"<i>Report generated on {profile_data.get('export_timestamp', datetime.utcnow().isoformat())}</i>",
                self.styles['Normal']
            ))
            
            doc.build(story)
            pdf_buffer.seek(0)
            pdf_bytes = pdf_buffer.getvalue()
            logger.info(f"Profile PDF generated: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating profile PDF: {str(e)}")
            return None
    
    # Helper methods for creating table sections
    
    def _create_info_section(self, data: Dict) -> Table:
        """Create assessment info section"""
        info_data = [
            ['Assessment Type', data.get('assessment_type', 'N/A')],
            ['Difficulty Level', data.get('difficulty', 'N/A')],
            ['Date Taken', data.get('created_at', 'N/A')],
            ['Time Spent', f"{data.get('time_spent_minutes', 0)} minutes"]
        ]
        
        table = Table(info_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def _create_score_display(self, data: Dict) -> Table:
        """Create score display table"""
        score_data = [
            ['Score', f"{data.get('score', 0)}/100"],
            ['Performance', data.get('badge', 'N/A')]
        ]
        
        table = Table(score_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#c6f6d5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#22543d')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('GRID', (0, 0), (-1, -1), 2, colors.black)
        ]))
        
        return table
    
    def _create_qa_section(self, data: Dict) -> Table:
        """Create Q&A section"""
        qa_data = [['Question', 'Your Answer', 'Correct Answer', 'Feedback']]
        
        questions = data.get('questions', [])
        user_responses = data.get('user_responses', [])
        correct_answers = data.get('correct_answers', [])
        feedback = data.get('feedback', {})
        
        for i, q in enumerate(questions[:5]):  # Limit to first 5
            q_text = q.get('text', 'N/A') if isinstance(q, dict) else str(q)
            user_ans = user_responses[i] if i < len(user_responses) else 'N/A'
            correct_ans = correct_answers[i] if i < len(correct_answers) else 'N/A'
            fb = feedback.get(f'question_{i}', 'N/A') if feedback else 'N/A'
            
            qa_data.append([q_text[:50], str(user_ans)[:30], str(correct_ans)[:30], str(fb)[:30]])
        
        table = Table(qa_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        return table
    
    def _create_gaps_section(self, gaps: List[Dict]) -> Table:
        """Create gaps table"""
        gaps_data = [['Gap Name', 'Priority', 'Impact']]
        
        for gap in gaps[:10]:
            gaps_data.append([
                gap.get('name', 'N/A'),
                gap.get('priority', 'N/A'),
                f"{gap.get('impact', 0)}/10"
            ])
        
        table = Table(gaps_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fed7d7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#742a2a')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        return table
    
    def _create_recommendations_section(self, recommendations: List[str]) -> Table:
        """Create recommendations section"""
        rec_data = [['Recommendation']]
        
        for rec in recommendations[:5]:
            rec_data.append([rec])
        
        table = Table(rec_data, colWidths=[6*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#bee3f8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        return table
    
    def _create_gap_score_summary(self, data: Dict) -> Table:
        """Create gap score summary"""
        summary_data = [
            ['Current Score', f"{data.get('current_score', 0)}/100"],
            ['Industry Benchmark', f"{data.get('benchmark_score', 75)}/100"],
            ['Percentile Rank', f"{data.get('percentile', 50)}%"],
            ['Gaps Identified', str(data.get('gaps_identified', 0))]
        ]
        
        table = Table(summary_data, colWidths=[2.5*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e6fffa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        return table
    
    def _create_benchmark_section(self, data: Dict) -> Table:
        """Create benchmark comparison"""
        bench_data = [
            ['Metric', 'Your Score', 'Industry Average', 'Status'],
            ['Overall Skill Level', f"{data.get('current_score', 0)}/100", f"{data.get('benchmark_score', 75)}/100", 
             'Above' if data.get('current_score', 0) >= data.get('benchmark_score', 75) else 'Below']
        ]
        
        table = Table(bench_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fbd38d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        return table
    
    def _create_gap_table(self, gaps: List[Dict]) -> Table:
        """Create gaps details table"""
        gap_data = [['Gap Name', 'Frequency', 'Priority', 'Impact']]
        
        for gap in gaps[:8]:
            gap_data.append([
                gap.get('name', 'N/A')[:20],
                str(gap.get('frequency', 0)),
                gap.get('priority', 'N/A'),
                f"{gap.get('impact', 0)}/10"
            ])
        
        table = Table(gap_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.6*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fc8181')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        return table
    
    def _create_learning_plans_section(self, plans: List[Dict]) -> Table:
        """Create learning plans table"""
        plan_data = [['Duration', 'Progress', 'Status', 'End Date']]
        
        for plan in plans[:5]:
            plan_data.append([
                f"{plan.get('duration_weeks', 0)} weeks",
                f"{plan.get('progress', 0)}%",
                plan.get('created_at', 'N/A'),
                plan.get('end_date', 'N/A')
            ])
        
        table = Table(plan_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9ae6b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        return table
    
    def _create_profile_info(self, data: Dict) -> Table:
        """Create profile info section"""
        info_data = [
            ['Name', data.get('student_name', 'N/A')],
            ['Email', data.get('email', 'N/A')],
            ['User Type', data.get('user_type', 'N/A')]
        ]
        
        table = Table(info_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        return table
    
    def _create_profile_stats(self, data: Dict) -> Table:
        """Create profile statistics"""
        stats_data = [
            ['Total Skills', str(data.get('total_skills', 0))],
            ['Average Score', f"{data.get('average_score', 0)}/100"],
            ['Assessments Taken', str(data.get('assessments_taken', 0))],
            ['Active Learning Plans', str(data.get('active_learning_plans', 0))],
            ['Total Gaps', str(data.get('total_gaps', 0))]
        ]
        
        table = Table(stats_data, colWidths=[2.5*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        return table
    
    def _create_profile_skills_table(self, skills: List[Dict]) -> Table:
        """Create profile skills table"""
        skill_data = [['Skill', 'Score', 'Proficiency', 'Last Assessed']]
        
        for skill in skills[:15]:
            skill_data.append([
                skill.get('skill_name', 'N/A')[:20],
                f"{skill.get('score', 0)}/100",
                skill.get('proficiency', 'N/A'),
                skill.get('last_assessed', 'N/A')
            ])
        
        table = Table(skill_data, colWidths=[1.8*inch, 1*inch, 1.2*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4299e1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        return table
    
    def _create_profile_assessments_table(self, assessments: List[Dict]) -> Table:
        """Create profile assessments table"""
        assess_data = [['Assessment Type', 'Skill', 'Score', 'Date']]
        
        for assess in assessments[:10]:
            assess_data.append([
                assess.get('type', 'N/A'),
                f"Skill {assess.get('skill_id', 'N/A')}",
                f"{assess.get('score', 0)}/100",
                assess.get('date', 'N/A')
            ])
        
        table = Table(assess_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#48bb78')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        return table
    
    def _create_profile_gaps_table(self, gaps: List[Dict]) -> Table:
        """Create profile gaps table"""
        gap_data = [['Skill', 'Gap Name', 'Priority']]
        
        for gap in gaps[:10]:
            gap_data.append([
                f"Skill {gap.get('skill_id', 'N/A')}",
                gap.get('gap_name', 'N/A')[:20],
                gap.get('priority', 'N/A')
            ])
        
        table = Table(gap_data, colWidths=[2*inch, 2.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f6ad55')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        return table
    
    def _create_profile_plans_table(self, plans: List[Dict]) -> Table:
        """Create profile learning plans table"""
        plan_data = [['Skill', 'Duration', 'Progress', 'Status']]
        
        for plan in plans[:10]:
            plan_data.append([
                f"Skill {plan.get('skill_id', 'N/A')}",
                f"{plan.get('duration', 0)} weeks",
                f"{plan.get('progress', 0)}%",
                plan.get('status', 'N/A')
            ])
        
        table = Table(plan_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9f7aea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        return table
