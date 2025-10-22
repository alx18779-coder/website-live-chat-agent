'use client';

import { Button, Card, Form, Input, Switch, Table, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { EditOutlined, PlusOutlined } from '@ant-design/icons';

interface AliasRow {
  key: string;
  model: string;
  temperature: number;
  ragEnabled: boolean;
  updatedAt: string;
}

const columns: ColumnsType<AliasRow> = [
  { title: '别名', dataIndex: 'key', key: 'key' },
  { title: '真实模型', dataIndex: 'model', key: 'model' },
  { title: '温度', dataIndex: 'temperature', key: 'temperature' },
  {
    title: 'RAG',
    dataIndex: 'ragEnabled',
    key: 'ragEnabled',
    render: (value: boolean) => (value ? '开启' : '关闭'),
  },
  { title: '更新时间', dataIndex: 'updatedAt', key: 'updatedAt' },
  {
    title: '操作',
    key: 'actions',
    render: () => (
      <Button type="link" icon={<EditOutlined />}>
        编辑
      </Button>
    ),
  },
];

export default function ModelRoutingPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Typography.Title level={3} className="!text-slate-100">
            模型别名与路由策略
          </Typography.Title>
          <Typography.Paragraph className="!mb-0 text-slate-400">
            管理模型别名、温度参数以及 RAG 开关，保证配置与后端一致。
          </Typography.Paragraph>
        </div>
        <Button type="primary" icon={<PlusOutlined />} className="shadow-glow">
          新增别名
        </Button>
      </div>

      <Card className="bg-surface-elevated/60" bordered={false}>
        <Table
          columns={columns}
          dataSource={[]}
          rowKey="key"
          pagination={false}
        />
      </Card>

      <Card title="系统提示词" className="bg-surface-elevated/60" bordered={false}>
        <Form layout="vertical">
          <Form.Item label="提示词内容">
            <Input.TextArea rows={6} placeholder="在此粘贴系统提示词，未来将提供版本对比与回滚。" />
          </Form.Item>
          <Form.Item label="启用缓存">
            <Switch defaultChecked />
          </Form.Item>
          <Button type="primary">保存草稿</Button>
        </Form>
      </Card>
    </div>
  );
}
