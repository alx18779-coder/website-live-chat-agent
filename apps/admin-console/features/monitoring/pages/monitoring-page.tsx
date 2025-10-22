'use client';

import { Card, Col, Empty, Row, Segmented, Table, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';

interface AuditRow {
  id: string;
  actor: string;
  action: string;
  target: string;
  createdAt: string;
}

const columns: ColumnsType<AuditRow> = [
  { title: '操作时间', dataIndex: 'createdAt', key: 'createdAt', width: 180 },
  { title: '操作者', dataIndex: 'actor', key: 'actor' },
  { title: '操作类型', dataIndex: 'action', key: 'action' },
  { title: '目标资源', dataIndex: 'target', key: 'target' },
];

const metricOptions = ['对话量', '知识命中率', '响应时间'] as const;

export default function MonitoringPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Typography.Title level={3} className="!text-slate-100">
            监控与审计
          </Typography.Title>
          <Typography.Paragraph className="!mb-0 text-slate-400">
            聚合对话指标、系统健康状态和审计日志，支持快速定位问题。
          </Typography.Paragraph>
        </div>
        <Segmented options={metricOptions} defaultValue={metricOptions[0]} />
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="实时指标" className="bg-surface-elevated/60" bordered={false}>
            <Empty description="等待指标服务上线后接入图表" className="py-10" />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="系统状态" className="bg-surface-elevated/60" bordered={false}>
            <Empty description="将展示 Milvus、Redis、LLM Provider 的健康检查" className="py-10" />
          </Card>
        </Col>
      </Row>

      <Card title="审计日志" className="bg-surface-elevated/60" bordered={false}>
        <Table
          columns={columns}
          dataSource={[]}
          rowKey="id"
          pagination={false}
          locale={{ emptyText: <Empty description="待接入 `/api/v1/audit-logs` 接口后显示审计数据" /> }}
        />
      </Card>
    </div>
  );
}
