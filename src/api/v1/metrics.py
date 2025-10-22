"""Dashboard metrics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from src.models.metrics import DashboardMetricsResponse, MetricsRange
from src.services.metrics_service import metrics_service

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    range_: MetricsRange = Query(  # type: ignore[assignment]
        default="24h",
        alias="range",
        description="Metrics aggregation range (24h, 7d, 30d)",
    ),
) -> DashboardMetricsResponse:
    """Return aggregated dashboard metrics for the requested time range."""

    try:
        return await metrics_service.get_dashboard_metrics(range_)
    except Exception as exc:  # noqa: BLE001 - convert unexpected errors to 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dashboard metrics",
        ) from exc

