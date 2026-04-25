"""
Skill extraction service.
Extracts skill keywords from plain text (resume copy-paste or manual input).
Uses a curated keyword list + simple regex — no spaCy model download required for MVP.
"""
import re
from typing import List

# Master skill taxonomy — maps keywords to canonical skill names and categories
SKILL_TAXONOMY = {
    # Frontend
    "react": ("React", "Frontend"),
    "reactjs": ("React", "Frontend"),
    "react.js": ("React", "Frontend"),
    "vue": ("Vue.js", "Frontend"),
    "angular": ("Angular", "Frontend"),
    "javascript": ("JavaScript", "Frontend"),
    "typescript": ("TypeScript", "Frontend"),
    "html": ("HTML", "Frontend"),
    "css": ("CSS", "Frontend"),
    "tailwind": ("Tailwind CSS", "Frontend"),
    "next.js": ("Next.js", "Frontend"),
    "nextjs": ("Next.js", "Frontend"),
    "redux": ("Redux", "Frontend"),

    # Backend
    "python": ("Python", "Backend"),
    "flask": ("Flask", "Backend"),
    "django": ("Django", "Backend"),
    "fastapi": ("FastAPI", "Backend"),
    "node": ("Node.js", "Backend"),
    "node.js": ("Node.js", "Backend"),
    "express": ("Express.js", "Backend"),
    "java": ("Java", "Backend"),
    "spring": ("Spring Boot", "Backend"),
    "golang": ("Go", "Backend"),
    "go": ("Go", "Backend"),
    "rust": ("Rust", "Backend"),
    "php": ("PHP", "Backend"),
    "laravel": ("Laravel", "Backend"),
    "ruby": ("Ruby", "Backend"),
    "rails": ("Ruby on Rails", "Backend"),
    "c#": ("C#", "Backend"),
    "dotnet": (".NET", "Backend"),
    ".net": (".NET", "Backend"),

    # Database
    "sql": ("SQL", "Database"),
    "postgresql": ("PostgreSQL", "Database"),
    "postgres": ("PostgreSQL", "Database"),
    "mysql": ("MySQL", "Database"),
    "mongodb": ("MongoDB", "Database"),
    "redis": ("Redis", "Database"),
    "sqlite": ("SQLite", "Database"),
    "firebase": ("Firebase", "Database"),
    "supabase": ("Supabase", "Database"),

    # Cloud / DevOps
    "aws": ("AWS", "Cloud"),
    "azure": ("Azure", "Cloud"),
    "gcp": ("GCP", "Cloud"),
    "docker": ("Docker", "DevOps"),
    "kubernetes": ("Kubernetes", "DevOps"),
    "git": ("Git", "DevOps"),
    "github": ("GitHub", "DevOps"),
    "ci/cd": ("CI/CD", "DevOps"),
    "linux": ("Linux", "DevOps"),

    # Data / ML
    "machine learning": ("Machine Learning", "Data Science"),
    "ml": ("Machine Learning", "Data Science"),
    "deep learning": ("Deep Learning", "Data Science"),
    "pandas": ("Pandas", "Data Science"),
    "numpy": ("NumPy", "Data Science"),
    "tensorflow": ("TensorFlow", "Data Science"),
    "pytorch": ("PyTorch", "Data Science"),
    "scikit-learn": ("Scikit-learn", "Data Science"),
    "data science": ("Data Science", "Data Science"),

    # Soft Skills
    "communication": ("Communication", "Soft Skill"),
    "leadership": ("Leadership", "Soft Skill"),
    "problem solving": ("Problem Solving", "Soft Skill"),
    "teamwork": ("Teamwork", "Soft Skill"),
    "collaboration": ("Teamwork", "Soft Skill"),
    "time management": ("Time Management", "Soft Skill"),
    "adaptability": ("Adaptability", "Soft Skill"),
    "creativity": ("Creativity", "Soft Skill"),
    "critical thinking": ("Critical Thinking", "Soft Skill"),
    "emotional intelligence": ("Emotional Intelligence", "Soft Skill"),

    # Domain Knowledge
    "fintech": ("FinTech", "Domain"),
    "healthcare": ("Healthcare", "Domain"),
    "e-commerce": ("E-commerce", "Domain"),
    "ecommerce": ("E-commerce", "Domain"),
    "cybersecurity": ("Cybersecurity", "Domain"),
    "blockchain": ("Blockchain", "Domain"),
    "cloud computing": ("Cloud Computing", "Domain"),
    "edtech": ("EdTech", "Domain"),
    "logistics": ("Logistics", "Domain"),

    # Tools
    "jira": ("Jira", "Tool"),
    "confluence": ("Confluence", "Tool"),
    "slack": ("Slack", "Tool"),
    "trello": ("Trello", "Tool"),
    "asana": ("Asana", "Tool"),
    "figma": ("Figma", "Tool"),
    "adobe xd": ("Adobe XD", "Tool"),
    "notion": ("Notion", "Tool"),
    "zoom": ("Zoom", "Tool"),
    "microsoft teams": ("Microsoft Teams", "Tool"),
}


def extract_skills_from_text(text: str) -> List[dict]:
    """
    Given free-form text (resume body, pasted skills), return a list of
    { skill_name, category, confidence } dicts.
    """
    text_lower = text.lower()
    found = {}

    # Multi-word skills first (longest match wins)
    sorted_keywords = sorted(SKILL_TAXONOMY.keys(), key=len, reverse=True)

    for keyword in sorted_keywords:
        # Use word boundary matching
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_lower):
            skill_name, category = SKILL_TAXONOMY[keyword]
            if skill_name not in found:
                found[skill_name] = {
                    "skill_name": skill_name,
                    "category": category,
                    "source": "resume",
                    "confidence": 0.9,
                }

    return list(found.values())
