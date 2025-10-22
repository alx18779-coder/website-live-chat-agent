'use client';

import { Alert, Card, Tag } from 'antd';
import type { ComponentStatus } from '@/services/metrics';
import dayjs from 'dayjs';

interface StatusCardProps {
  title: string;
  status: ComponentStatus['status'];
  latency?: number;
  lastCheckedAt?: string;
}

function getStatusTag(status: ComponentStatus['status']) {
  switch (status) {
    case 'healthy':
      return <Tag color="green">正常</Tag>;
    case 'degraded':
      return <Tag color="orange">性能下降</Tag>;
    case 'down':
      return <Tag color="red">故障</Tag>;
    default:
      return <Tag color="default">未知</Tag>;
  }
}

export default function StatusCard({ title, status, latency, lastCheckedAt }: StatusCardProps) {
  const showAlert = status === 'down' || status === 'degraded';

  return (
    <Card title={<div className="flex items-center justify-between text-slate-100"><span>{title}</span>{getStatusTag(status)}</div>} className="h-full bg-surface-elevated/70" bordered={false}>
      <div className="space-y-3 text-sm text-slate-300">
        <div className="flex items-center justify-between">
          <span>最近检查</span>
          <span>{lastCheckedAt ? dayjs(lastCheckedAt).format('YYYY-MM-DD HH:mm:ss') : '暂未上报'}</span>
        </div>
        <div className="flex items-center justify-between">
          <span>响应耗时</span>
          <span>{latency ? `${latency.toFixed(0)} ms` : '—'}</span>
        </div>
        {showAlert && <Alert type={status === 'down' ? 'error' : 'warning'} message="系统已自动触发重试，请关注告警渠道" showIcon />}
      </div>
    </Card>
  );
}
