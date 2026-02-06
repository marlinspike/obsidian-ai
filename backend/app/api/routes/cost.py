"""Cost tracking endpoints."""

from typing import Any

from fastapi import APIRouter

from app.api.deps import ApiKeyDep
from app.api.routes.query import CostTrackerDep
from app.models.cost import CostSummary, ModelPricing, QueryCost

router = APIRouter()


@router.get("/summary", response_model=CostSummary)
async def get_cost_summary(
    _: ApiKeyDep,
    tracker: CostTrackerDep,
) -> CostSummary:
    """Get cost summary for the current session.

    Returns:
        Summary with total costs and breakdowns by model/provider
    """
    return tracker.get_summary()


@router.get("/history", response_model=list[QueryCost])
async def get_cost_history(
    _: ApiKeyDep,
    tracker: CostTrackerDep,
    limit: int = 50,
) -> list[QueryCost]:
    """Get query-by-query cost history.

    Args:
        limit: Maximum queries to return (default 50)

    Returns:
        List of recent query costs
    """
    return tracker.get_query_history(limit)


@router.get("/pricing", response_model=list[ModelPricing])
async def get_pricing_table(
    _: ApiKeyDep,
    tracker: CostTrackerDep,
) -> list[ModelPricing]:
    """Get the current pricing table for all models.

    Returns:
        List of model pricing information
    """
    return tracker.get_pricing_table()


@router.post("/reset")
async def reset_session(
    _: ApiKeyDep,
    tracker: CostTrackerDep,
) -> dict[str, str]:
    """Reset the cost tracking session.

    Clears current session costs but keeps historical data.
    Historical data is saved before reset.

    Returns:
        Confirmation message
    """
    tracker.reset_session()
    return {"message": "Session reset", "new_session_id": tracker.session_id}


@router.get("/all-time")
async def get_all_time_summary(
    _: ApiKeyDep,
    tracker: CostTrackerDep,
) -> dict[str, Any]:
    """Get all-time cost summary including historical data.

    Returns:
        Summary with all-time totals across all sessions
    """
    return tracker.get_all_time_summary()


@router.post("/save")
async def save_costs(
    _: ApiKeyDep,
    tracker: CostTrackerDep,
) -> dict[str, Any]:
    """Manually save costs to file.

    Costs are automatically saved after each query, but this
    endpoint allows explicit manual saving.

    Returns:
        Success status and summary
    """
    success = tracker.save()
    summary = tracker.get_all_time_summary()
    return {
        "success": success,
        "message": "Costs saved successfully" if success else "Failed to save costs",
        "total_queries": summary["total_queries"],
        "total_cost": summary["total_cost"],
    }


@router.post("/reset-all")
async def reset_all_costs(
    _: ApiKeyDep,
    tracker: CostTrackerDep,
) -> dict[str, str]:
    """Reset all costs including historical data.

    WARNING: This permanently deletes all cost history.

    Returns:
        Confirmation message
    """
    tracker.reset_all()
    return {"message": "All costs reset", "new_session_id": tracker.session_id}
