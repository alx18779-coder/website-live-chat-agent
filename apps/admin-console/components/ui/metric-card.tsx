'use client';

import { ArrowDownOutlined, ArrowUpOutlined, MinusOutlined } from '@ant-design/icons';
import { Card } from 'antd';
import type { MetricKpi } from '@/services/metrics';

function getTrendIcon(trend: MetricKpi['trend']) {
  switch (trend) {
    case 'up':
      return <ArrowUpOutlined className="text-emerald-400" />;
    case 'down':
      return <ArrowDownOutlined className="text-rose-400" />;
    default:
      return <MinusOutlined className="text-slate-400" />;
  }
}

function getDeltaColor(trend: MetricKpi['trend']) {
  switch (trend) {
    case 'up':
      return 'text-emerald-300';
    case 'down':
      return 'text-rose-300';
    default:
      return 'text-slate-300';
  }
}

interface MetricCardProps {
  metric: MetricKpi;
}

export default function MetricCard({ metric }: MetricCardProps) {
  return (
    <Card className="bg-surface-elevated/80 shadow-lg shadow-brand-primary/10 backdrop-blur" bordered={false}>
      <div className="flex flex-col gap-3">
        <div className="text-xs uppercase tracking-widest text-slate-400">{metric.title}</div>
        <div className="text-3xl font-semibold text-slate-100">
          {metric.value.toLocaleString('zh-CN', { maximumFractionDigits: 2 })}
          {metric.unit && <span className="ml-1 text-base text-slate-400">{metric.unit}</span>}
        </div>
        <div className="text-sm text-slate-400">{metric.description}</div>
        <div className={`flex items-center gap-2 text-xs ${getDeltaColor(metric.trend)}`}>
          {getTrendIcon(metric.trend)}
          <span>{metric.delta > 0 ? '+' : ''}{metric.delta.toFixed(2)}%</span>
          <span className="text-slate-500">对比上个周期</span>
        </div>
      </div>
    </Card>
  );
}
