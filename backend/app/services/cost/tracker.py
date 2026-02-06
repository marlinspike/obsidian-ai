"""Cost tracking service with file persistence."""

import json
import threading
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.logging import logger
from app.models.cost import (
    DEFAULT_PRICING,
    CostSummary,
    ModelCostBreakdown,
    ModelPricing,
    QueryCost,
)
from app.models.llm import LLMProvider


class CostTracker:
    """Tracks and calculates LLM costs with file-based persistence."""

    def __init__(
        self,
        pricing: dict[str, ModelPricing] | None = None,
        persist_path: Path | None = None,
        auto_save: bool = True,
    ):
        """Initialize cost tracker.

        Args:
            pricing: Optional custom pricing table, uses defaults if not provided
            persist_path: Path to save costs JSON file (optional)
            auto_save: If True, automatically save after each new cost is recorded
        """
        self.pricing = pricing or DEFAULT_PRICING
        self.persist_path = persist_path
        self.auto_save = auto_save
        self._save_lock = threading.Lock()

        # Initialize with empty state
        self.queries: list[QueryCost] = []
        self.session_id = str(uuid4())
        self.session_start = datetime.utcnow()

        # Track cumulative totals across all sessions
        self.all_time_queries: list[QueryCost] = []
        self.all_time_cost = Decimal("0")
        self.first_tracked = datetime.utcnow()

        # Load existing data if persist_path is set
        if persist_path:
            self._load()

    def _load(self) -> None:
        """Load costs from file if it exists."""
        if not self.persist_path or not self.persist_path.exists():
            logger.info("No existing costs file found, starting fresh")
            return

        try:
            with open(self.persist_path, "r") as f:
                data = json.load(f)

            # Load all-time data
            self.first_tracked = datetime.fromisoformat(data.get("first_tracked", datetime.utcnow().isoformat()))
            self.all_time_cost = Decimal(data.get("all_time_cost", "0"))

            # Load query history
            query_list = data.get("queries", [])
            for q in query_list:
                try:
                    query = QueryCost(
                        query_id=q["query_id"],
                        timestamp=datetime.fromisoformat(q["timestamp"]),
                        model=q["model"],
                        provider=LLMProvider(q["provider"]),
                        input_tokens=q["input_tokens"],
                        output_tokens=q["output_tokens"],
                        input_cost=Decimal(q["input_cost"]),
                        output_cost=Decimal(q["output_cost"]),
                        total_cost=Decimal(q["total_cost"]),
                        embedding_tokens=q.get("embedding_tokens"),
                        embedding_cost=Decimal(q["embedding_cost"]) if q.get("embedding_cost") else None,
                    )
                    self.all_time_queries.append(query)
                except Exception as e:
                    logger.warning(f"Failed to load query: {e}")

            logger.info(
                f"Loaded {len(self.all_time_queries)} historical queries, "
                f"all-time cost: ${self.all_time_cost}"
            )
        except Exception as e:
            logger.error(f"Failed to load costs file: {e}")

    def save(self) -> bool:
        """Save costs to file.

        Returns:
            True if save was successful, False otherwise
        """
        if not self.persist_path:
            logger.warning("No persist path configured, cannot save")
            return False

        with self._save_lock:
            try:
                # Combine session queries with historical
                all_queries = self.all_time_queries + self.queries

                # Calculate all-time cost
                total = self.all_time_cost + sum(q.total_cost for q in self.queries)

                data: dict[str, Any] = {
                    "first_tracked": self.first_tracked.isoformat(),
                    "last_saved": datetime.utcnow().isoformat(),
                    "all_time_cost": str(total),
                    "total_queries": len(all_queries),
                    "queries": [
                        {
                            "query_id": q.query_id,
                            "timestamp": q.timestamp.isoformat(),
                            "model": q.model,
                            "provider": q.provider.value,
                            "input_tokens": q.input_tokens,
                            "output_tokens": q.output_tokens,
                            "input_cost": str(q.input_cost),
                            "output_cost": str(q.output_cost),
                            "total_cost": str(q.total_cost),
                            "embedding_tokens": q.embedding_tokens,
                            "embedding_cost": str(q.embedding_cost) if q.embedding_cost else None,
                        }
                        for q in all_queries
                    ],
                }

                # Write atomically using temp file
                temp_path = self.persist_path.with_suffix(".tmp")
                with open(temp_path, "w") as f:
                    json.dump(data, f, indent=2)
                temp_path.replace(self.persist_path)

                logger.debug(f"Saved {len(all_queries)} queries to {self.persist_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to save costs: {e}")
                return False

    def calculate_cost(
        self,
        model: str,
        provider: LLMProvider,
        input_tokens: int,
        output_tokens: int,
        embedding_tokens: int | None = None,
    ) -> QueryCost:
        """Calculate cost for a query and record it.

        Args:
            model: Model name used
            provider: Provider used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            embedding_tokens: Optional embedding tokens used

        Returns:
            QueryCost object with calculated costs
        """
        pricing = self.pricing.get(model)
        if not pricing:
            # Fallback pricing (zero cost for unknown models)
            pricing = ModelPricing(
                model=model,
                provider=provider,
                display_name=model,
                input_price_per_million=Decimal("0"),
                output_price_per_million=Decimal("0"),
            )

        # Calculate costs
        input_cost = (
            Decimal(input_tokens) / Decimal("1000000")
        ) * pricing.input_price_per_million
        output_cost = (
            Decimal(output_tokens) / Decimal("1000000")
        ) * pricing.output_price_per_million

        embedding_cost = None
        if embedding_tokens and pricing.embedding_price_per_million:
            embedding_cost = (
                Decimal(embedding_tokens) / Decimal("1000000")
            ) * pricing.embedding_price_per_million

        total = input_cost + output_cost + (embedding_cost or Decimal("0"))

        query_cost = QueryCost(
            query_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost.quantize(Decimal("0.000001")),
            output_cost=output_cost.quantize(Decimal("0.000001")),
            total_cost=total.quantize(Decimal("0.000001")),
            embedding_tokens=embedding_tokens,
            embedding_cost=(
                embedding_cost.quantize(Decimal("0.000001"))
                if embedding_cost
                else None
            ),
        )

        self.queries.append(query_cost)

        # Auto-save if enabled
        if self.auto_save and self.persist_path:
            self.save()

        return query_cost

    def get_summary(self) -> CostSummary:
        """Get cumulative cost summary (current session).

        Returns:
            CostSummary with detailed breakdowns
        """
        cost_by_model: dict[str, ModelCostBreakdown] = {}
        cost_by_provider: dict[str, Decimal] = {}

        for q in self.queries:
            # By model
            if q.model not in cost_by_model:
                cost_by_model[q.model] = ModelCostBreakdown(
                    model=q.model,
                    provider=q.provider,
                    query_count=0,
                    input_tokens=0,
                    output_tokens=0,
                    total_cost=Decimal("0"),
                )

            breakdown = cost_by_model[q.model]
            cost_by_model[q.model] = ModelCostBreakdown(
                model=breakdown.model,
                provider=breakdown.provider,
                query_count=breakdown.query_count + 1,
                input_tokens=breakdown.input_tokens + q.input_tokens,
                output_tokens=breakdown.output_tokens + q.output_tokens,
                total_cost=breakdown.total_cost + q.total_cost,
            )

            # By provider
            provider_name = q.provider.value
            cost_by_provider[provider_name] = cost_by_provider.get(
                provider_name, Decimal("0")
            ) + q.total_cost

        total_cost = sum((q.total_cost for q in self.queries), Decimal("0"))

        return CostSummary(
            session_id=self.session_id,
            session_start=self.session_start,
            total_queries=len(self.queries),
            total_cost=total_cost.quantize(Decimal("0.000001")),
            cost_by_model=cost_by_model,
            cost_by_provider={k: v.quantize(Decimal("0.000001")) for k, v in cost_by_provider.items()},
            total_input_tokens=sum(q.input_tokens for q in self.queries),
            total_output_tokens=sum(q.output_tokens for q in self.queries),
            total_embedding_tokens=sum(q.embedding_tokens or 0 for q in self.queries),
        )

    def get_all_time_summary(self) -> dict[str, Any]:
        """Get all-time cost summary including historical data.

        Returns:
            Dictionary with all-time statistics
        """
        all_queries = self.all_time_queries + self.queries
        total_cost = self.all_time_cost + sum(q.total_cost for q in self.queries)

        # Aggregate by model
        cost_by_model: dict[str, dict[str, Any]] = {}
        for q in all_queries:
            if q.model not in cost_by_model:
                cost_by_model[q.model] = {
                    "model": q.model,
                    "provider": q.provider.value,
                    "query_count": 0,
                    "total_cost": Decimal("0"),
                }
            cost_by_model[q.model]["query_count"] += 1
            cost_by_model[q.model]["total_cost"] += q.total_cost

        return {
            "first_tracked": self.first_tracked.isoformat(),
            "total_queries": len(all_queries),
            "total_cost": str(total_cost.quantize(Decimal("0.000001"))),
            "cost_by_model": {
                k: {
                    **v,
                    "total_cost": str(v["total_cost"].quantize(Decimal("0.000001"))),
                }
                for k, v in cost_by_model.items()
            },
            "is_saved": self.persist_path is not None and self.persist_path.exists(),
        }

    def get_query_history(self, limit: int = 50, include_historical: bool = False) -> list[QueryCost]:
        """Get recent query cost history.

        Args:
            limit: Maximum queries to return
            include_historical: If True, include queries from previous sessions

        Returns:
            List of recent QueryCost objects
        """
        if include_historical:
            all_queries = self.all_time_queries + self.queries
            return all_queries[-limit:]
        return self.queries[-limit:]

    def get_pricing_table(self) -> list[ModelPricing]:
        """Get the current pricing table.

        Returns:
            List of all model pricing
        """
        return list(self.pricing.values())

    def reset_session(self) -> None:
        """Reset the current session, clearing session costs but keeping historical data."""
        # First, merge current session into historical
        if self.queries:
            self.all_time_queries.extend(self.queries)
            self.all_time_cost += sum(q.total_cost for q in self.queries)

            # Save before reset
            if self.persist_path:
                self.save()

        # Reset session
        self.queries = []
        self.session_id = str(uuid4())
        self.session_start = datetime.utcnow()

    def reset_all(self) -> None:
        """Reset everything including historical data."""
        self.queries = []
        self.all_time_queries = []
        self.all_time_cost = Decimal("0")
        self.session_id = str(uuid4())
        self.session_start = datetime.utcnow()
        self.first_tracked = datetime.utcnow()

        # Delete the persist file
        if self.persist_path and self.persist_path.exists():
            self.persist_path.unlink()
            logger.info(f"Deleted costs file: {self.persist_path}")
