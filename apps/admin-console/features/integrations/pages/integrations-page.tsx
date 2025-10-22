'use client';

import { Button, Card, Descriptions, Form, Input, Typography } from 'antd';
import { CopyOutlined, ReloadOutlined } from '@ant-design/icons';

export default function IntegrationsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Typography.Title level={3} className="!text-slate-100">
            多渠道接入
          </Typography.Title>
          <Typography.Paragraph className="!mb-0 text-slate-400">
            管理 API Key、生成 WordPress 插件配置，验证调用链路。
          </Typography.Paragraph>
        </div>
        <div className="flex gap-2">
          <Button icon={<CopyOutlined />} ghost>
            复制嵌入代码
          </Button>
          <Button type="primary" icon={<ReloadOutlined />} className="shadow-glow">
            自检连接
          </Button>
        </div>
      </div>

      <Card title="API Key 管理" className="bg-surface-elevated/60" bordered={false}>
        <Form layout="vertical" className="grid gap-4 md:grid-cols-2">
          <Form.Item label="Key 名称" required>
            <Input placeholder="如：WordPress 生产环境" />
          </Form.Item>
          <Form.Item label="权限范围">
            <Input placeholder="chat:read, knowledge:write" />
          </Form.Item>
          <Form.Item label="有效期 (天)">
            <Input type="number" min={1} max={365} />
          </Form.Item>
          <Form.Item label="IP 白名单">
            <Input placeholder="可选，逗号分隔" />
          </Form.Item>
          <div className="md:col-span-2">
            <Button type="primary">生成 API Key</Button>
          </div>
        </Form>
      </Card>

      <Card title="WordPress 接入指引" className="bg-surface-elevated/60" bordered={false}>
        <Descriptions column={1} labelStyle={{ color: '#A5B4FC' }} contentStyle={{ color: '#E2E8F0' }}>
          <Descriptions.Item label="步骤一">
            安装聊天插件并在“API 设置”中填写上方生成的 Base URL 与 Key。
          </Descriptions.Item>
          <Descriptions.Item label="步骤二">
            在 WordPress 页面嵌入脚本：
            <pre className="mt-2 overflow-auto rounded bg-black/40 p-4 text-xs text-slate-100">
{`<script>
  window.chatbot = { baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL, apiKey: '***' };
</script>`}
            </pre>
          </Descriptions.Item>
          <Descriptions.Item label="步骤三">
            点击“自检连接”验证 `/v1/chat/completions` 响应是否正常。
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
}
