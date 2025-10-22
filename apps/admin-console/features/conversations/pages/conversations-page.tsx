'use client';

import { Button, Card, Empty, Space, Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { DownloadOutlined } from '@ant-design/icons';

interface ConversationRow {
  id: string;
  user: string;
  summary: string;
  hasFeedback: boolean;
  knowledgeHit: boolean;
  updatedAt: string;
}

const columns: ColumnsType<ConversationRow> = [
  { title: '会话 ID', dataIndex: 'id', key: 'id', width: 180 },
  { title: '用户标签', dataIndex: 'user', key: 'user' },
  { title: '对话摘要', dataIndex: 'summary', key: 'summary' },
  {
    title: '知识命中',
    dataIndex: 'knowledgeHit',
    key: 'knowledgeHit',
    render: (value: boolean) => (value ? <Tag color="blue">命中</Tag> : <Tag>未命中</Tag>),
  },
  {
    title: '收到反馈',
    dataIndex: 'hasFeedback',
    key: 'hasFeedback',
    render: (value: boolean) => (value ? <Tag color="green">有反馈</Tag> : <Tag>—</Tag>),
  },
  { title: '最近更新时间', dataIndex: 'updatedAt', key: 'updatedAt' },
];

export default function ConversationsPage() {
  return (
    <Space direction="vertical" size={24} className="w-full">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Typography.Title level={3} className="!text-slate-100">
            会话监控与人工介入
          </Typography.Title>
          <Typography.Paragraph className="!mb-0 text-slate-400">
            浏览会话列表、追踪命中率，并在需要时追加人工回复。
          </Typography.Paragraph>
        </div>
        <Button type="default" icon={<DownloadOutlined />} ghost>
          导出报表
        </Button>
      </div>
      <Card className="bg-surface-elevated/60" bordered={false}>
        <Table
          columns={columns}
          dataSource={[]}
          rowKey="id"
          pagination={false}
          locale={{ emptyText: <Empty description="待接入后端接口后显示会话数据" /> }}
        />
      </Card>
    </Space>
  );
}
