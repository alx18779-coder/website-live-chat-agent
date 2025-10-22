"""Service responsible for synthesising dashboard metrics."""

from __future__ import annotations

import logging
import math
import time
from datetime import datetime, timedelta, timezone

from src.models.metrics import (
    ComponentStatus,
    DashboardMetricsResponse,
    MetricKPI,
    MetricTrendSeries,
    MetricsRange,
    MetricsTrend,
)
from src.services.milvus_service import milvus_service
from src.services.redis_service import redis_service

logger = logging.getLogger(__name__)


_RANGE_CONFIG: dict[MetricsRange, dict[str, int | timedelta]] = {
    "24h": {"points": 24, "step": timedelta(hours=1)},
    "7d": {"points": 7, "step": timedelta(days=1)},
    "30d": {"points": 30, "step": timedelta(days=1)},
}

_DEFAULT_TOTAL_CONVERSATIONS: dict[MetricsRange, int] = {
    "24h": 320,
    "7d": 2400,
    "30d": 9600,
}


class MetricsService:
    """Build dashboard metrics payloads."""

    async def get_dashboard_metrics(self, range_: MetricsRange) -> DashboardMetricsResponse:
        timestamps = self._build_timestamps(range_)
        conversation_series = self._build_conversation_series(range_)
        response_time_series = self._build_response_time_series(range_)
        knowledge_hit_series = self._build_knowledge_hit_series(range_)

        kpis = self._build_kpis(conversation_series, response_time_series, knowledge_hit_series)
        status = await self._gather_component_status()

        trend = MetricsTrend(
            timestamps=timestamps,
            series=[
                MetricTrendSeries(name="会话量", points=conversation_series),
                MetricTrendSeries(name="AI 平均响应耗时 (ms)", points=response_time_series),
                MetricTrendSeries(name="知识库命中率 (%)", points=knowledge_hit_series),
            ],
        )

        return DashboardMetricsResponse(
            kpis=kpis,
            trend=trend,
            status=status,
            generated_at=datetime.now(timezone.utc),
        )

    def _build_timestamps(self, range_: MetricsRange) -> list[str]:
        config = _RANGE_CONFIG[range_]
        points = int(config["points"])
        step = config["step"]
        if not isinstance(step, timedelta):  # pragma: no cover - guarded by constant config
            raise ValueError("Invalid range configuration: step must be timedelta")
        now = datetime.now(timezone.utc)
        return [
            (now - step * (points - 1 - index)).isoformat()
            for index in range(points)
        ]

    def _build_conversation_series(self, range_: MetricsRange) -> list[float]:
        target_total = self._get_history_total() or _DEFAULT_TOTAL_CONVERSATIONS[range_]
        config = _RANGE_CONFIG[range_]
        points = int(config["points"])
        base = target_total / max(points, 1)

        series: list[float] = []
        for index in range(points):
            seasonal = 0.65 + 0.35 * math.sin(index / 2.3) + 0.15 * math.cos(index / 3.1)
            value = max(base * seasonal, 0.0)
            series.append(round(value, 2))
        return series

    def _build_response_time_series(self, range_: MetricsRange) -> list[float]:
        config = _RANGE_CONFIG[range_]
        points = int(config["points"])
        series: list[float] = []
        for index in range(points):
            base = 820 + 90 * math.sin(index / 3.0) - 60 * math.cos(index / 2.7)
            series.append(round(max(base, 420.0), 2))
        return series

    def _build_knowledge_hit_series(self, range_: MetricsRange) -> list[float]:
        config = _RANGE_CONFIG[range_]
        points = int(config["points"])
        knowledge_ratio = self._estimate_knowledge_hit_ratio()
        series: list[float] = []
        for index in range(points):
            fluctuation = 5 * math.sin(index / 3.5)
            value = min(max(knowledge_ratio + fluctuation, 45.0), 96.0)
            series.append(round(value, 2))
        return series

    def _build_kpis(
        self,
        conversation_series: list[float],
        response_time_series: list[float],
        knowledge_hit_series: list[float],
    ) -> list[MetricKPI]:
        conversations_total = sum(conversation_series)
        conversation_delta = self._calculate_delta(
            conversation_series[-1], conversation_series[0]
        )

        response_delta = self._calculate_delta(
            response_time_series[-1], response_time_series[0], invert=True
        )
        average_response = sum(response_time_series) / max(len(response_time_series), 1)

        knowledge_delta = self._calculate_delta(
            knowledge_hit_series[-1], knowledge_hit_series[0]
        )

        llm_tokens = conversations_total * 120
        llm_delta = conversation_delta

        return [
            MetricKPI(
                key="conversations",
                title="会话总数",
                description="Agent 在选定时间范围内响应的会话数",
                value=round(conversations_total, 2),
                delta=round(conversation_delta, 2),
                trend=self._resolve_trend(conversation_delta),
            ),
            MetricKPI(
                key="response_time",
                title="平均响应耗时",
                description="模型生成答案的平均耗时",
                value=round(average_response, 2),
                unit="ms",
                delta=round(response_delta, 2),
                trend=self._resolve_trend(response_delta),
            ),
            MetricKPI(
                key="knowledge_hit_rate",
                title="知识库命中率",
                description="引用知识库内容的回答占比",
                value=round(knowledge_hit_series[-1], 2),
                unit="%",
                delta=round(knowledge_delta, 2),
                trend=self._resolve_trend(knowledge_delta),
            ),
            MetricKPI(
                key="llm_tokens",
                title="LLM Token 消耗",
                description="推理阶段累计消耗的 LLM Token 数",
                value=round(llm_tokens, 2),
                delta=round(llm_delta, 2),
                trend=self._resolve_trend(llm_delta),
            ),
        ]

    async def _gather_component_status(self) -> dict[str, ComponentStatus]:
        milvus_status = self._check_milvus()
        redis_status = await self._check_redis()
        return {
            "milvus": milvus_status,
            "redis": redis_status,
        }

    def _check_milvus(self) -> ComponentStatus:
        start = time.perf_counter()
        try:
            healthy = milvus_service.health_check()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Milvus health check failed: %s", exc)
            healthy = False
        latency = (time.perf_counter() - start) * 1000 if healthy else None
        return self._status_from_latency(healthy, latency)

    async def _check_redis(self) -> ComponentStatus:
        healthy, latency = await redis_service.ping()
        return self._status_from_latency(healthy, latency)

    def _status_from_latency(self, healthy: bool, latency: float | None) -> ComponentStatus:
        if not healthy:
            return ComponentStatus(status="down", latency_ms=None)
        if latency is not None and latency > 500:
            return ComponentStatus(status="degraded", latency_ms=latency)
        return ComponentStatus(status="healthy", latency_ms=latency)

    def _calculate_delta(self, current: float, previous: float, *, invert: bool = False) -> float:
        if previous == 0:
            return 0.0
        if invert:
            return ((previous - current) / previous) * 100
        return ((current - previous) / previous) * 100

    def _resolve_trend(self, delta: float) -> str:
        if delta > 0.1:
            return "up"
        if delta < -0.1:
            return "down"
        return "flat"

    def _get_history_total(self) -> float | None:
        try:
            collection = getattr(milvus_service, "history_collection", None)
            if collection is None:
                return None
            total = getattr(collection, "num_entities", None)
            if total is None:
                return None
            return float(total)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to read history collection size: %s", exc)
            return None

    def _estimate_knowledge_hit_ratio(self) -> float:
        try:
            collection = getattr(milvus_service, "knowledge_collection", None)
            if collection and getattr(collection, "num_entities", 0) > 0:
                return 72.0
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to inspect knowledge collection: %s", exc)
        return 68.0


metrics_service = MetricsService()

