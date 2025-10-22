'use client';

import { useState } from 'react';
import { Button, Col, Row, Space, Tabs, Typography } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import KnowledgeDocumentsTable from '@/features/knowledge-base/components/knowledge-documents-table';
import KnowledgeUploadWizard from '@/features/knowledge-base/components/knowledge-upload-wizard';
import KnowledgeSearchPanel from '@/features/knowledge-base/components/knowledge-search-panel';
import type { KnowledgeUploadResponse } from '@/services/knowledge';

const tabItems = [
  { key: 'documents', label: '文档列表' },
  { key: 'upload', label: '文档上传' },
  { key: 'debug', label: '检索调试' },
] as const;

type TabKey = (typeof tabItems)[number]['key'];

export default function KnowledgeBasePage() {
  const [activeTab, setActiveTab] = useState<TabKey>('documents');
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploaded = (_response: KnowledgeUploadResponse) => {
    setRefreshKey((value) => value + 1);
    setActiveTab('documents');
  };

  return (
    <Space direction="vertical" size={24} className="w-full">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Typography.Title level={3} className="!text-slate-100">
            知识库维护
          </Typography.Title>
          <Typography.Paragraph className="!mb-0 text-slate-400">
            上传站点文档、管理版本，并实时验证检索效果。
          </Typography.Paragraph>
        </div>
        <Space>
          <Button
            type={activeTab === 'debug' ? 'primary' : 'default'}
            icon={<SearchOutlined />}
            ghost={activeTab !== 'debug'}
            onClick={() => setActiveTab('debug')}
          >
            检索调试
          </Button>
          <Button type="primary" icon={<PlusOutlined />} className="shadow-glow" onClick={() => setActiveTab('upload')}>
            新建文档
          </Button>
        </Space>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={(key) => setActiveTab(key as TabKey)}
        destroyInactiveTabPane
        items={tabItems.map((tab) => ({
          key: tab.key,
          label: tab.label,
          children: (
            <TabPanel
              tabKey={tab.key}
              refreshKey={refreshKey}
              onUploaded={handleUploaded}
            />
          ),
        }))}
      />
    </Space>
  );
}

interface TabPanelProps {
  tabKey: TabKey;
  refreshKey: number;
  onUploaded: (response: KnowledgeUploadResponse) => void;
}

function TabPanel({ tabKey, refreshKey, onUploaded }: TabPanelProps) {
  if (tabKey === 'documents') {
    return <KnowledgeDocumentsTable refreshKey={refreshKey} />;
  }

  if (tabKey === 'upload') {
    return (
      <Row gutter={[24, 24]}>
        <Col xs={24} xl={16}>
          <KnowledgeUploadWizard onUploaded={onUploaded} />
        </Col>
        <Col xs={24} xl={8}>
          <KnowledgeSearchPanel />
        </Col>
      </Row>
    );
  }

  return (
    <Row gutter={[24, 24]}>
      <Col xs={24} xl={16}>
        <KnowledgeSearchPanel />
      </Col>
      <Col xs={24} xl={8}>
        <KnowledgeUploadWizard onUploaded={onUploaded} />
      </Col>
    </Row>
  );
}
