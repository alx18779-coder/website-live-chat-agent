import { request } from '@/services/http';

export type MetricsRange = '24h' | '7d' | '30d';

export interface MetricKpi {
  key: string;
  title: string;
  description: string;
  value: number;
  delta: number;
  trend: 'up' | 'down' | 'flat';
  unit?: string;
}

export interface MetricTrendSeries {
  name: string;
  points: number[];
}

export interface MetricsTrend {
  timestamps: string[];
  series: MetricTrendSeries[];
}

export interface ComponentStatus {
  status: 'healthy' | 'degraded' | 'down' | 'unknown';
  latency_ms?: number;
}

export interface DashboardMetricsResponse {
  kpis: MetricKpi[];
  trend: MetricsTrend;
  status: {
    milvus: ComponentStatus;
    redis: ComponentStatus;
  };
  generated_at: string;
}

export async function getMetricsSummary(range: MetricsRange): Promise<DashboardMetricsResponse> {
  return request<DashboardMetricsResponse>(`/api/v1/metrics?range=${range}`);
}
