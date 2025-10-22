"""Dashboard metrics response models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MetricsRange = Literal["24h", "7d", "30d"]


class MetricKPI(BaseModel):
    """Single KPI card displayed on the dashboard."""

    key: str
    title: str
    description: str
    value: float
    delta: float = Field(description="Percentage delta compared with previous period")
    trend: Literal["up", "down", "flat"]
    unit: str | None = None


class MetricTrendSeries(BaseModel):
    """One time-series series rendered on the dashboard chart."""

    name: str
    points: list[float]


class MetricsTrend(BaseModel):
    """Aggregated time-series data."""

    timestamps: list[str]
    series: list[MetricTrendSeries]


class ComponentStatus(BaseModel):
    """Status information for an infrastructure component."""

    status: Literal["healthy", "degraded", "down", "unknown"]
    latency_ms: float | None = Field(default=None, description="Latency in milliseconds")


class DashboardMetricsResponse(BaseModel):
    """Payload returned by the metrics endpoint."""

    kpis: list[MetricKPI]
    trend: MetricsTrend
    status: dict[str, ComponentStatus]
    generated_at: datetime

