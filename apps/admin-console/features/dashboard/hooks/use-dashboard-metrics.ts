import { useQuery } from '@tanstack/react-query';
import { getMetricsSummary } from '@/services/metrics';
import type { MetricsRange } from '@/services/metrics';

export function useDashboardMetrics(range: MetricsRange) {
  return useQuery({
    queryKey: ['metrics', range],
    queryFn: () => getMetricsSummary(range),
    staleTime: range === '24h' ? 5000 : 30_000,
  });
}
