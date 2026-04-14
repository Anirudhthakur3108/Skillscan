"""
Skill Matching & Extraction Logic
Hybrid approach: Exact match + Fuzzy matching with confidence scoring
"""

import re
from difflib import SequenceMatcher
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SkillMatcher:
    """
    Intelligent skill matcher using hybrid approach (exact + fuzzy matching)
    """

    # Synonym mappings for fuzzy matching - maps to canonical skill names
    SYNONYMS = {
        "python": ["py", "python3", "python 3", "python3.x", "python3.10", "python3.11"],
        "sql": ["mysql", "postgresql", "postgres", "sql server", "mariadb", "nosql", "mongo"],
        "r": ["r programming", "rstudio"],
        "java": ["java8", "j2ee", "springframework"],
        "c++": ["cpp", "c plus plus", "cplusplus", "c++ 11"],
        "javascript": ["js", "node", "node.js", "nodejs", "node.js", "ts", "typescript"],
        "react": ["react.js", "reactjs", "jsx"],
        "web development": ["web dev", "frontend", "backend", "fullstack", "full stack"],
        "data structures": ["dsa", "data structures & algorithms", "algorithms", "ds"],
        "system design": ["architecture", "low level design", "high level design"],
        "excel/vba": ["excel", "vba", "spreadsheet", "microsoft excel"],
        "tableau": ["tableau public"],
        "power bi": ["powerbi", "power bi desktop"],
        "statistics": ["stats", "statistical analysis"],
        "data analysis": ["analytics", "business intelligence"],
        "machine learning (intro)": ["machine learning", "ml", "artificial intelligence", "ai"],
        "sql/databases": ["databases", "database design", "relational databases"],
    }

    # Reverse mapping: synonym → canonical skill
    SYNONYM_TO_SKILL = {}

    def __init__(self, skill_list: Optional[List[str]] = None):
        """
        Initialize SkillMatcher

        Args:
            skill_list: List of canonical skill names
        """
        self.skill_list = skill_list or self._get_default_skills()
        self._build_synonym_map()
        logger.info(f"SkillMatcher initialized with {len(self.skill_list)} skills")

    @staticmethod
    def _get_default_skills() -> List[str]:
        """Get default skill taxonomy"""
        return [
            "Python",
            "SQL",
            "Excel/VBA",
            "Tableau",
            "Power BI",
            "Statistics",
            "Data Analysis",
            "R",
            "Machine Learning (Intro)",
            "Java",
            "C++",
            "JavaScript",
            "React",
            "Web Development",
            "SQL/Databases",
            "Data Structures",
            "System Design",
        ]

    def _build_synonym_map(self):
        """Build reverse mapping from synonyms to canonical skills"""
        self.SYNONYM_TO_SKILL = {}
        for canonical, synonyms in self.SYNONYMS.items():
            canonical_lower = canonical.lower()
            # Map canonical to itself (for exact matching)
            self.SYNONYM_TO_SKILL[canonical_lower] = canonical_lower

            # Map all synonyms to canonical
            for synonym in synonyms:
                self.SYNONYM_TO_SKILL[synonym.lower()] = canonical_lower

    def match_exact(self, text: str, skill_list: Optional[List[str]] = None) -> List[Dict]:
        """
        Exact string matching - case insensitive

        Args:
            text: Resume text to search in
            skill_list: List of skills to match against (uses self.skill_list if None)

        Returns:
            List of exact matches with confidence 1.0
        """
        if skill_list is None:
            skill_list = self.skill_list

        matches = []
        text_lower = text.lower()
        matched_skills = set()

        # Word boundaries to avoid partial matches
        for skill in skill_list:
            # Create regex pattern with word boundaries
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(pattern, text_lower):
                if skill.lower() not in matched_skills:
                    matches.append(
                        {"skill": skill, "confidence": 1.0, "match_type": "exact"}
                    )
                    matched_skills.add(skill.lower())
                    logger.debug(f"Exact match found: {skill}")

        return matches

    def match_fuzzy(
        self, text: str, skill_list: Optional[List[str]] = None, threshold: float = 0.8
    ) -> List[Dict]:
        """
        Fuzzy matching using SequenceMatcher for similar variations

        Args:
            text: Resume text to search in
            skill_list: List of skills to match against
            threshold: Similarity threshold (0.8 default)

        Returns:
            List of fuzzy matches with confidence scores
        """
        if skill_list is None:
            skill_list = self.skill_list

        matches = []
        # Extract all words from text
        words = re.findall(r"\b\w+(?:\s+\w+)?\b", text.lower())
        matched_skills = set()

        for word in words:
            word_clean = word.strip().lower()

            # Check if word is a known synonym
            if word_clean in self.SYNONYM_TO_SKILL:
                canonical = self.SYNONYM_TO_SKILL[word_clean]
                # Find the actual skill object that matches this canonical
                for skill in skill_list:
                    if skill.lower() == canonical:
                        if skill.lower() not in matched_skills:
                            confidence = 0.9  # High confidence for synonym matches
                            matches.append(
                                {
                                    "skill": skill,
                                    "confidence": confidence,
                                    "match_type": "fuzzy",
                                }
                            )
                            matched_skills.add(skill.lower())
                            logger.debug(
                                f"Fuzzy match (synonym) found: {word} → {skill} ({confidence})"
                            )
                        break

            # Also try SequenceMatcher for other variations
            else:
                for skill in skill_list:
                    if skill.lower() in matched_skills:
                        continue

                    # Compare word with skill name
                    ratio = SequenceMatcher(None, word_clean, skill.lower()).ratio()

                    # For longer strings, require higher threshold
                    if len(skill) > 6:
                        effective_threshold = threshold
                    else:
                        effective_threshold = max(threshold - 0.05, 0.75)

                    # Exclude exact matches (ratio = 1.0)
                    if effective_threshold <= ratio < 1.0:
                        confidence = max(0.6, ratio)  # Minimum 0.6 confidence
                        matches.append(
                            {
                                "skill": skill,
                                "confidence": confidence,
                                "match_type": "fuzzy",
                            }
                        )
                        matched_skills.add(skill.lower())
                        logger.debug(
                            f"Fuzzy match (sequence) found: {word} → {skill} ({confidence:.2f})"
                        )
                        break

        return matches

    def hybrid_match(
        self, text: str, skill_list: Optional[List[str]] = None, confidence_threshold: float = 0.6
    ) -> List[Dict]:
        """
        Hybrid matching: exact first, then fuzzy, deduplication

        Args:
            text: Resume text to search in
            skill_list: List of skills to match against
            confidence_threshold: Minimum confidence to include (default 0.6)

        Returns:
            Deduplicated list of matches sorted by confidence (descending)
        """
        if skill_list is None:
            skill_list = self.skill_list

        logger.info(f"Starting hybrid match for {len(skill_list)} skills")

        # Get exact matches first
        exact_matches = self.match_exact(text, skill_list)
        exact_skills = {m["skill"].lower() for m in exact_matches}

        # Get fuzzy matches (excluding already matched exact)
        fuzzy_matches = self.match_fuzzy(text, skill_list, threshold=0.8)

        # Filter fuzzy to exclude exact matches and low confidence
        fuzzy_filtered = [
            m for m in fuzzy_matches if m["skill"].lower() not in exact_skills
        ]

        # Combine and deduplicate
        all_matches = exact_matches + fuzzy_filtered
        seen = set()
        deduplicated = []

        for match in all_matches:
            skill_key = match["skill"].lower()
            if skill_key not in seen:
                deduplicated.append(match)
                seen.add(skill_key)

        # Filter by confidence threshold
        final_matches = [m for m in deduplicated if m["confidence"] >= confidence_threshold]

        # Sort by confidence (descending)
        final_matches.sort(key=lambda x: x["confidence"], reverse=True)

        logger.info(
            f"Hybrid match complete: {len(exact_matches)} exact, "
            f"{len(fuzzy_filtered)} fuzzy, "
            f"{len(final_matches)} final matches (threshold: {confidence_threshold})"
        )

        return final_matches

    @staticmethod
    def calculate_confidence(match_type: str, score: float) -> float:
        """
        Calculate final confidence score

        Args:
            match_type: "exact" or "fuzzy"
            score: Raw similarity score (0-1)

        Returns:
            Final confidence score (0-1)
        """
        if match_type == "exact":
            return 1.0
        elif match_type == "fuzzy":
            # Fuzzy matches: 0.6-0.99 range
            return max(0.6, min(0.99, score))
        else:
            return 0.5

    def extract_skills_with_context(self, text: str, skill_list: Optional[List[str]] = None) -> Dict:
        """
        Extract skills with additional context information

        Args:
            text: Resume text
            skill_list: List of skills to match

        Returns:
            Dictionary with extracted skills, statistics, and metadata
        """
        matches = self.hybrid_match(text, skill_list)

        exact_count = sum(1 for m in matches if m["match_type"] == "exact")
        fuzzy_count = sum(1 for m in matches if m["match_type"] == "fuzzy")
        avg_confidence = (
            sum(m["confidence"] for m in matches) / len(matches) if matches else 0
        )

        return {
            "extracted_skills": matches,
            "stats": {
                "total_matches": len(matches),
                "exact_matches": exact_count,
                "fuzzy_matches": fuzzy_count,
                "average_confidence": round(avg_confidence, 2),
            },
        }
