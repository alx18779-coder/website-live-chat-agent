'use client';

import { Card, Form, Input, Select, Switch, Typography } from 'antd';

const languageOptions = [
  { label: '简体中文', value: 'zh-CN' },
  { label: 'English', value: 'en-US' },
];

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <Typography.Title level={3} className="!text-slate-100">
          系统设置
        </Typography.Title>
        <Typography.Paragraph className="!mb-0 text-slate-400">
          管理账号权限、国际化、个性化配置等内容，确保后台符合组织规范。
        </Typography.Paragraph>
      </div>

      <Card title="账号与角色" className="bg-surface-elevated/60" bordered={false}>
        <Form layout="vertical" className="grid gap-4 md:grid-cols-2">
          <Form.Item label="管理员邮箱">
            <Input placeholder="ops@example.com" />
          </Form.Item>
          <Form.Item label="默认角色" tooltip="用于批量邀请时的初始权限">
            <Select options={[{ label: 'Operator', value: 'operator' }, { label: 'Auditor', value: 'auditor' }]} />
          </Form.Item>
          <Form.Item label="启用双因素认证">
            <Switch defaultChecked />
          </Form.Item>
          <Form.Item label="审计日志保留天数">
            <Input type="number" min={30} max={365} />
          </Form.Item>
        </Form>
      </Card>

      <Card title="个性化设置" className="bg-surface-elevated/60" bordered={false}>
        <Form layout="vertical" className="grid gap-4 md:grid-cols-2">
          <Form.Item label="默认语言">
            <Select options={languageOptions} defaultValue={languageOptions[0].value} />
          </Form.Item>
          <Form.Item label="邮件通知">
            <Switch defaultChecked />
          </Form.Item>
          <Form.Item label="时间格式">
            <Select options={[{ label: '24 小时制', value: '24h' }, { label: '12 小时制', value: '12h' }]} defaultValue="24h" />
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
