"""Query complexity analyzer for model routing."""

import re

from app.models.query import QueryComplexity


class ComplexityAnalyzer:
    """Analyzes query complexity to route to appropriate model."""

    # Patterns that indicate simple queries
    SIMPLE_PATTERNS = [
        r"^what is\b",
        r"^who is\b",
        r"^when did\b",
        r"^where is\b",
        r"^find\b",
        r"^list\b",
        r"^show me\b",
        r"^what's the\b",
        r"^which\b",
        r"^did i\b",
        r"^do i have\b",
        r"^is there\b",
    ]

    # Patterns that indicate complex queries
    COMPLEX_PATTERNS = [
        r"\banalyze\b",
        r"\bcompare\b",
        r"\bsynthesize\b",
        r"\bexplain why\b",
        r"\bwhat patterns\b",
        r"\bhow does\b",
        r"\bsummarize all\b",
        r"\bacross\b",
        r"\brelationship between\b",
        r"\bconnections?\b",
        r"\btrends?\b",
        r"\binsights?\b",
        r"\boverall\b",
        r"\bcomprehensive\b",
        r"\bdetailed analysis\b",
        r"\bwhat can you tell me about\b",
        r"\bwhat do my notes say about\b",
        r"\bwhat have i learned\b",
        r"\bwhat are the key\b",
    ]

    # Complexity multipliers based on query characteristics
    WORD_COUNT_THRESHOLD = 15  # Longer queries tend to be more complex
    QUESTION_MARK_BONUS = 2  # Multiple questions increase complexity

    def __init__(self):
        """Initialize the analyzer with compiled patterns."""
        self.simple_patterns = [re.compile(p, re.IGNORECASE) for p in self.SIMPLE_PATTERNS]
        self.complex_patterns = [re.compile(p, re.IGNORECASE) for p in self.COMPLEX_PATTERNS]

    def analyze(self, query: str) -> QueryComplexity:
        """Determine query complexity.

        Uses a scoring system:
        - Start at 0
        - Simple patterns: -1 each
        - Complex patterns: +2 each
        - Long queries: +1
        - Multiple questions: +1

        Final score:
        - < 0: SIMPLE
        - >= 0: COMPLEX

        Args:
            query: User query string

        Returns:
            QueryComplexity enum value
        """
        score = 0
        query_lower = query.lower().strip()

        # Check simple patterns
        for pattern in self.simple_patterns:
            if pattern.search(query_lower):
                score -= 1

        # Check complex patterns
        for pattern in self.complex_patterns:
            if pattern.search(query_lower):
                score += 2

        # Long queries tend to be more complex
        word_count = len(query.split())
        if word_count > self.WORD_COUNT_THRESHOLD:
            score += 1

        # Multiple question marks suggest multiple questions
        question_count = query.count("?")
        if question_count > 1:
            score += question_count - 1

        return QueryComplexity.COMPLEX if score >= 0 else QueryComplexity.SIMPLE

    def get_explanation(self, query: str) -> dict[str, object]:
        """Get detailed explanation of complexity analysis.

        Useful for debugging and understanding routing decisions.

        Args:
            query: User query string

        Returns:
            Dictionary with analysis details
        """
        query_lower = query.lower().strip()

        matched_simple = [
            p.pattern
            for p in self.simple_patterns
            if p.search(query_lower)
        ]
        matched_complex = [
            p.pattern
            for p in self.complex_patterns
            if p.search(query_lower)
        ]

        word_count = len(query.split())
        question_count = query.count("?")

        # Calculate score
        score = 0
        score -= len(matched_simple)
        score += len(matched_complex) * 2
        if word_count > self.WORD_COUNT_THRESHOLD:
            score += 1
        if question_count > 1:
            score += question_count - 1

        return {
            "query": query,
            "complexity": "complex" if score >= 0 else "simple",
            "score": score,
            "factors": {
                "simple_patterns_matched": matched_simple,
                "complex_patterns_matched": matched_complex,
                "word_count": word_count,
                "question_count": question_count,
                "is_long_query": word_count > self.WORD_COUNT_THRESHOLD,
            },
        }
