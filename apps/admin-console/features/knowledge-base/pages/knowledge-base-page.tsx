'use client';

import { Button, Card, Col, Empty, Row, Tabs, Typography } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';

const tabItems = [
  { key: 'documents', label: '文档列表' },
  { key: 'upload', label: '文档上传' },
  { key: 'debug', label: '检索调试' },
];

export default function KnowledgeBasePage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Typography.Title level={3} className="!text-slate-100">
            知识库维护
          </Typography.Title>
          <Typography.Paragraph className="!mb-0 text-slate-400">
            上传站点文档、管理版本，并实时验证检索效果。
          </Typography.Paragraph>
        </div>
        <div className="flex gap-2">
          <Button type="default" icon={<SearchOutlined />} ghost>
            检索调试
          </Button>
          <Button type="primary" icon={<PlusOutlined />} className="shadow-glow">
            新建文档
          </Button>
        </div>
      </div>

      <Tabs
        defaultActiveKey="documents"
        items={tabItems.map((tab) => ({
          key: tab.key,
          label: tab.label,
          children: <KnowledgeBaseTab tabKey={tab.key} />,
        }))}
      />
    </div>
  );
}

function KnowledgeBaseTab({ tabKey }: { tabKey: string }) {
  if (tabKey === 'documents') {
    return (
      <Card className="bg-surface-elevated/60" bordered={false}>
        <Empty description="暂未加载文档。完成后端接口接入后将在此展示文档列表。" className="py-12" />
      </Card>
    );
  }

  if (tabKey === 'upload') {
    return (
      <Row gutter={[16, 16]}>
        <Col xs={24} xl={16}>
          <Card className="bg-surface-elevated/60" bordered={false}>
            <Empty description="上传向导即将上线，支持 Markdown/HTML/纯文本。" className="py-12" />
          </Card>
        </Col>
        <Col xs={24} xl={8}>
          <Card className="bg-surface-elevated/50" bordered={false} title="上传检查表">
            <ul className="space-y-2 text-sm text-slate-300">
              <li>· 文件大小不超过 10MB</li>
              <li>· 支持 Markdown、HTML、纯文本</li>
              <li>· 填写分类、标签、版本号</li>
              <li>· 自动生成切片统计与审计日志</li>
            </ul>
          </Card>
        </Col>
      </Row>
    );
  }

  return (
    <Card className="bg-surface-elevated/60" bordered={false}>
      <Empty description="检索调试工具将展示相似度排序、命中片段与高亮。" className="py-12" />
    </Card>
  );
}
