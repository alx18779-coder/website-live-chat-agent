'use client';

import { Button, Card, Form, Input, Typography } from 'antd';
import Link from 'next/link';

export default function LoginPage() {
  return (
    <Card className="w-full max-w-md bg-surface-elevated/80 shadow-xl shadow-brand-primary/20">
      <div className="space-y-6 text-center">
        <div className="space-y-2">
          <Typography.Title level={2} className="!text-slate-100">
            管理员登录
          </Typography.Title>
          <Typography.Paragraph className="!text-slate-400">
            使用内部账号或 API Key 登录以继续管理知识库与模型配置。
          </Typography.Paragraph>
        </div>
        <Form layout="vertical" requiredMark="optional" className="text-left">
          <Form.Item label="邮箱" name="email" rules={[{ required: true, message: '请输入邮箱' }]}> 
            <Input placeholder="admin@example.com" size="large" autoComplete="email" />
          </Form.Item>
          <Form.Item label="密码" name="password" rules={[{ required: true, message: '请输入密码' }]}> 
            <Input.Password placeholder="••••••" size="large" autoComplete="current-password" />
          </Form.Item>
          <Button type="primary" htmlType="submit" size="large" className="mt-2 w-full shadow-glow">
            登录
          </Button>
        </Form>
        <div className="text-sm text-slate-400">
          使用 API Key? <Link href="#" className="text-brand-secondary">切换为 API Key 登录</Link>
        </div>
      </div>
    </Card>
  );
}
