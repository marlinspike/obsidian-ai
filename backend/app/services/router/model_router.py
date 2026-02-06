"""Model router for directing queries to appropriate LLM."""

from app.config import Settings
from app.models.llm import LLMProvider
from app.models.query import QueryComplexity
from app.services.llm.base import BaseLLMProvider
from app.services.llm.factory import LLMProviderFactory
from app.services.router.complexity import ComplexityAnalyzer


class ModelRouter:
    """Routes queries to appropriate LLM based on complexity."""

    def __init__(self, settings: Settings, factory: LLMProviderFactory):
        """Initialize router.

        Args:
            settings: Application settings
            factory: LLM provider factory
        """
        self.settings = settings
        self.factory = factory
        self.analyzer = ComplexityAnalyzer()

    def route(
        self,
        query: str,
        complexity_override: QueryComplexity | None = None,
    ) -> tuple[BaseLLMProvider, QueryComplexity]:
        """Route a query to the appropriate model.

        Args:
            query: User query string
            complexity_override: Optional override for complexity

        Returns:
            Tuple of (provider, complexity_used)
        """
        # Determine complexity
        if complexity_override and complexity_override != QueryComplexity.AUTO:
            complexity = complexity_override
        else:
            complexity = self.analyzer.analyze(query)

        # Get appropriate provider
        if complexity == QueryComplexity.SIMPLE:
            provider = self.factory.get_simple_query_provider()
        else:
            provider = self.factory.get_complex_query_provider()

        return provider, complexity

    def get_model_info(
        self, complexity: QueryComplexity
    ) -> tuple[LLMProvider, str]:
        """Get model info for a complexity level.

        Args:
            complexity: Query complexity

        Returns:
            Tuple of (provider, model_name)
        """
        if complexity == QueryComplexity.SIMPLE:
            return (
                LLMProvider(self.settings.simple_query_provider),
                self.settings.simple_query_model,
            )
        else:
            return (
                LLMProvider(self.settings.complex_query_provider),
                self.settings.complex_query_model,
            )

    def analyze_complexity(self, query: str) -> dict[str, object]:
        """Get detailed complexity analysis.

        Args:
            query: User query string

        Returns:
            Detailed analysis dictionary
        """
        return self.analyzer.get_explanation(query)
