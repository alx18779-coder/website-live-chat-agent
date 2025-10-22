'use client';

import { Card, Col, Empty, Row, Skeleton, Tabs, Typography } from 'antd';
import dynamic from 'next/dynamic';
import { useState } from 'react';
import MetricCard from '@/components/ui/metric-card';
import StatusCard from '@/components/ui/status-card';
import { useDashboardMetrics } from '@/features/dashboard/hooks/use-dashboard-metrics';

const ReactECharts = dynamic(() => import('echarts-for-react'), { ssr: false });

const metricRanges = [
  { label: '24 小时', value: '24h' },
  { label: '7 天', value: '7d' },
  { label: '30 天', value: '30d' },
] as const;

type RangeValue = (typeof metricRanges)[number]['value'];

export default function DashboardOverview() {
  const [range, setRange] = useState<RangeValue>('24h');
  const { data, isLoading, isError } = useDashboardMetrics(range);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {isLoading &&
          Array.from({ length: 4 }).map((_, index) => (
            <Card key={index} className="bg-surface-elevated/60">
              <Skeleton active paragraph={{ rows: 1 }} title={false} />
            </Card>
          ))}
        {!isLoading && data &&
          data.kpis.map((item) => (
            <MetricCard key={item.key} metric={item} />
          ))}
      </div>

      <Card
        className="bg-surface-elevated/60"
        title={
          <div className="flex items-center justify-between">
            <Typography.Title level={4} className="!mb-0 text-slate-100">
              核心指标趋势
            </Typography.Title>
            <Tabs
              size="small"
              activeKey={range}
              onChange={(value) => setRange(value as RangeValue)}
              items={metricRanges.map(({ label, value }) => ({ key: value, label }))}
            />
          </div>
        }
        bordered={false}
      >
        {isError && <Empty description="指标服务暂不可用" className="py-12 text-slate-300" />}
        {!isError && (
          <ReactECharts
            option={{
              darkMode: true,
              backgroundColor: 'transparent',
              textStyle: { color: '#CBD5F5' },
              tooltip: { trigger: 'axis' },
              legend: { data: data?.trend.series.map((s) => s.name) ?? [], textStyle: { color: '#94A3B8' } },
              xAxis: { type: 'category', data: data?.trend.timestamps ?? [], boundaryGap: false, axisLine: { lineStyle: { color: '#334155' } } },
              yAxis: { type: 'value', axisLine: { lineStyle: { color: '#334155' } }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.25)' } } },
              grid: { left: 24, right: 24, top: 32, bottom: 16 },
              series:
                data?.trend.series.map((series) => ({
                  type: 'line',
                  name: series.name,
                  smooth: true,
                  showSymbol: false,
                  emphasis: { focus: 'series' },
                  areaStyle: {
                    opacity: 0.1,
                  },
                  lineStyle: {
                    width: 3,
                  },
                  data: series.points,
                })) ?? [],
            }}
            style={{ height: 320 }}
          />
        )}
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={12}>
          <StatusCard
            title="Milvus 状态"
            status={data?.status.milvus.status ?? 'unknown'}
            latency={data?.status.milvus.latency_ms}
            lastCheckedAt={data?.generated_at}
          />
        </Col>
        <Col xs={24} xl={12}>
          <StatusCard
            title="Redis 状态"
            status={data?.status.redis.status ?? 'unknown'}
            latency={data?.status.redis.latency_ms}
            lastCheckedAt={data?.generated_at}
          />
        </Col>
      </Row>
    </div>
  );
}
