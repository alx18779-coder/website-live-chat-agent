'use client';

import { useMemo, useState } from 'react';
import {
  Alert,
  Badge,
  Button,
  Card,
  Descriptions,
  Drawer,
  Empty,
  Form,
  Input,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
} from 'antd';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import { ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { listKnowledgeDocuments, type KnowledgeDocumentSummary } from '@/services/knowledge';

const statusMeta: Record<KnowledgeDocumentSummary['status'], { label: string; color: string }> = {
  draft: { label: '草稿', color: 'orange' },
  published: { label: '已发布', color: 'blue' },
  archived: { label: '已归档', color: 'default' },
};

interface KnowledgeDocumentsTableProps {
  refreshKey: number;
}

interface FilterState {
  keyword?: string;
  status: 'all' | KnowledgeDocumentSummary['status'];
  tags: string[];
}

export default function KnowledgeDocumentsTable({ refreshKey }: KnowledgeDocumentsTableProps) {
  const [pagination, setPagination] = useState<TablePaginationConfig>({
    current: 1,
    pageSize: 10,
    showSizeChanger: true,
  });
  const [filters, setFilters] = useState<FilterState>({ status: 'all', tags: [] });
  const [selectedDocument, setSelectedDocument] = useState<KnowledgeDocumentSummary | null>(null);

  const { data, isLoading, refetch, isFetching, isError, error } = useQuery({
    queryKey: ['knowledge-documents', pagination.current, pagination.pageSize, filters, refreshKey],
    queryFn: () =>
      listKnowledgeDocuments({
        page: pagination.current,
        page_size: pagination.pageSize,
        keyword: filters.keyword,
        status: filters.status,
        tags: filters.tags,
      }),
    keepPreviousData: true,
  });

  const columns: ColumnsType<KnowledgeDocumentSummary> = useMemo(
    () => [
      {
        title: '标题',
        dataIndex: 'title',
        key: 'title',
        render: (title: string) => (
          <Tooltip title={title}>
            <span className="line-clamp-1 text-slate-200">{title}</span>
          </Tooltip>
        ),
      },
      {
        title: '分类',
        dataIndex: 'category',
        key: 'category',
        width: 160,
        render: (category?: string) => category ?? '—',
      },
      {
        title: '标签',
        dataIndex: 'tags',
        key: 'tags',
        width: 220,
        render: (tags: string[]) =>
          tags?.length ? (
            <Space size={[4, 4]} wrap>
              {tags.map((tag) => (
                <Tag key={tag} color="geekblue">
                  {tag}
                </Tag>
              ))}
            </Space>
          ) : (
            '—'
          ),
      },
      {
        title: '版本',
        dataIndex: 'version',
        key: 'version',
        width: 120,
        render: (version?: string) => version ?? '—',
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 120,
        render: (status: KnowledgeDocumentSummary['status']) => {
          const meta = statusMeta[status];
          return <Tag color={meta.color}>{meta.label}</Tag>;
        },
      },
      {
        title: '切片数',
        dataIndex: 'chunk_count',
        key: 'chunk_count',
        width: 120,
        align: 'right',
      },
      {
        title: '最近更新',
        dataIndex: 'updated_at',
        key: 'updated_at',
        width: 200,
        render: (value: string) => dayjs(value).format('YYYY-MM-DD HH:mm'),
      },
    ],
    [],
  );

  const onTableChange = (page: TablePaginationConfig) => {
    setPagination((prev) => ({
      ...prev,
      current: page.current ?? prev.current,
      pageSize: page.pageSize ?? prev.pageSize,
    }));
  };

  const handleFilterChange = (changed: Partial<FilterState>) => {
    setFilters((prev) => ({ ...prev, ...changed }));
    setPagination((prev) => ({ ...prev, current: 1 }));
  };

  const tableData = data?.documents ?? [];

  return (
    <Card
      className="bg-surface-elevated/60"
      bordered={false}
      title={
        <Space className="flex flex-wrap items-center justify-between gap-3" size={16}>
          <Form
            layout="inline"
            onFinish={(values: FilterState) => handleFilterChange(values)}
            initialValues={filters}
            className="flex flex-wrap items-center gap-3"
          >
            <Form.Item name="keyword" className="!mb-0">
              <Input
                allowClear
                prefix={<SearchOutlined className="text-slate-400" />}
                placeholder="搜索标题或描述"
                className="min-w-[240px]"
                onPressEnter={(event) => {
                  event.preventDefault();
                  const form = event.currentTarget.form;
                  form?.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                }}
              />
            </Form.Item>
            <Form.Item name="status" className="!mb-0">
              <Select
                className="w-32"
                options={[
                  { label: '全部状态', value: 'all' },
                  { label: '草稿', value: 'draft' },
                  { label: '已发布', value: 'published' },
                  { label: '已归档', value: 'archived' },
                ]}
              />
            </Form.Item>
            <Form.Item name="tags" className="!mb-0">
              <Select mode="tags" placeholder="标签过滤" className="min-w-[200px]" />
            </Form.Item>
            <Form.Item className="!mb-0">
              <Button type="primary" htmlType="submit" icon={<SearchOutlined />}>
                筛选
              </Button>
            </Form.Item>
          </Form>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={isFetching}>
            刷新
          </Button>
        </Space>
      }
      extra={
        <Badge count={data?.total ?? 0} showZero color="#2952FF" offset={[8, -2]}>
          <span className="text-sm text-slate-400">总文档</span>
        </Badge>
      }
    >
      {isError && (
        <Alert
          type="error"
          showIcon
          className="mb-4"
          message="文档列表加载失败"
          description={(error as Error)?.message ?? '请稍后重试或刷新页面。'}
        />
      )}

      <Table
        rowKey="id"
        columns={columns}
        dataSource={tableData}
        loading={isLoading}
        pagination={{
          current: pagination.current ?? 1,
          pageSize: pagination.pageSize ?? 10,
          total: data?.total ?? 0,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
        onChange={onTableChange}
        onRow={(record) => ({
          onClick: () => setSelectedDocument(record),
        })}
        locale={{
          emptyText: (
            <Empty
              description="暂无文档。完成上传后将展示知识库内容。"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              className="py-12"
            />
          ),
        }}
        rowClassName="cursor-pointer hover:bg-white/5"
      />

      <Drawer
        open={Boolean(selectedDocument)}
        width={520}
        onClose={() => setSelectedDocument(null)}
        title={selectedDocument?.title}
        styles={{ body: { background: '#0f172a' } }}
      >
        {selectedDocument && (
          <Space direction="vertical" size={24} className="w-full">
            <Descriptions bordered column={1} size="small" labelStyle={{ width: 120 }}>
              <Descriptions.Item label="状态">
                <Tag color={statusMeta[selectedDocument.status].color}>
                  {statusMeta[selectedDocument.status].label}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="分类">
                {selectedDocument.category ?? '—'}
              </Descriptions.Item>
              <Descriptions.Item label="版本">{selectedDocument.version ?? '—'}</Descriptions.Item>
              <Descriptions.Item label="标签">
                {selectedDocument.tags?.length ? (
                  <Space size={[4, 4]} wrap>
                    {selectedDocument.tags.map((tag) => (
                      <Tag key={tag} color="geekblue">
                        {tag}
                      </Tag>
                    ))}
                  </Space>
                ) : (
                  '—'
                )}
              </Descriptions.Item>
              <Descriptions.Item label="切片数">{selectedDocument.chunk_count}</Descriptions.Item>
              <Descriptions.Item label="最近更新">
                {dayjs(selectedDocument.updated_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="创建人">{selectedDocument.created_by ?? '—'}</Descriptions.Item>
            </Descriptions>

            {selectedDocument.metadata && Object.keys(selectedDocument.metadata).length > 0 && (
              <Card title="元数据" size="small" className="bg-surface-elevated/80">
                <dl className="space-y-2 text-sm text-slate-300">
                  {Object.entries(selectedDocument.metadata).map(([key, value]) => (
                    <div key={key} className="flex items-start justify-between gap-3">
                      <dt className="text-slate-400">{key}</dt>
                      <dd className="text-right text-slate-100">
                        {typeof value === 'string' ? value : JSON.stringify(value)}
                      </dd>
                    </div>
                  ))}
                </dl>
              </Card>
            )}
          </Space>
        )}
      </Drawer>
    </Card>
  );
}
