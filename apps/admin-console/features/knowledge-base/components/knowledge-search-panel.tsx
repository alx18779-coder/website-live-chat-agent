'use client';

import { useMemo } from 'react';
import {
  Alert,
  Button,
  Card,
  Empty,
  Form,
  Input,
  List,
  Skeleton,
  Slider,
  Space,
  Statistic,
  Tag,
  Tooltip,
} from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useMutation } from '@tanstack/react-query';
import { searchKnowledge, type KnowledgeSearchResponse } from '@/services/knowledge';

interface KnowledgeSearchPanelProps {
  onResult?: (response: KnowledgeSearchResponse) => void;
}

function escapeRegExp(input: string) {
  return input.replace(/[.*+?^${}()|[\]\]/g, '\$&');
}

function highlight(text: string, keyword: string) {
  if (!keyword.trim()) {
    return text;
  }

  try {
    const regex = new RegExp(`(${escapeRegExp(keyword)})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, index) =>
      part.toLowerCase() === keyword.toLowerCase() ? (
        <mark key={`${index}-${part}`} className="rounded bg-brand-primary/30 px-1 py-0.5 text-brand-secondary">
          {part}
        </mark>
      ) : (
        <span key={`${index}-${part}`}>{part}</span>
      ),
    );
  } catch {
    return text;
  }
}

export default function KnowledgeSearchPanel({ onResult }: KnowledgeSearchPanelProps) {
  const [form] = Form.useForm<{ query: string; top_k: number }>();
  const searchMutation = useMutation({
    mutationFn: searchKnowledge,
    onSuccess: (response) => {
      onResult?.(response);
    },
  });

  const results = searchMutation.data?.results ?? [];
  const topScore = useMemo(() => (results.length ? results[0].score : 0), [results]);

  const handleSubmit = (values: { query: string; top_k: number }) => {
    searchMutation.mutate({ query: values.query, top_k: values.top_k });
  };

  return (
    <Card className="bg-surface-elevated/60" bordered={false}>
      <Space direction="vertical" size={24} className="w-full">
        <Form
          layout="vertical"
          form={form}
          initialValues={{ query: '', top_k: 3 }}
          onFinish={handleSubmit}
          className="space-y-4"
        >
          <Form.Item
            name="query"
            label="检索查询"
            rules={[{ required: true, message: '请输入查询内容' }]}
          >
            <Input.TextArea
              placeholder="输入想要验证的用户问题，例如：如何重置管理员密码？"
              autoSize={{ minRows: 3, maxRows: 6 }}
            />
          </Form.Item>
          <Form.Item name="top_k" label="返回结果数量">
            <Slider min={1} max={10} marks={{ 1: '1', 5: '5', 10: '10' }} />
          </Form.Item>
          <Button type="primary" htmlType="submit" icon={<SearchOutlined />} loading={searchMutation.isPending}>
            执行检索
          </Button>
        </Form>

        <Alert
          type="info"
          message="系统会调用后端的 /knowledge/search 接口，展示命中的片段、相似度以及元数据，便于运营人员验证知识库覆盖情况。"
          showIcon
        />

        {searchMutation.isPending && <Skeleton active paragraph={{ rows: 4 }} />}

        {!searchMutation.isPending && results.length === 0 && (
          <Empty description="暂未执行检索或没有命中结果" className="py-16" />
        )}

        {results.length > 0 && (
          <Space direction="vertical" size={16} className="w-full">
            <Statistic
              title="共返回结果"
              value={searchMutation.data?.total_results ?? 0}
              suffix="条"
              valueStyle={{ color: '#E0E7FF' }}
            />
            <List
              itemLayout="vertical"
              dataSource={results}
              renderItem={(item, index) => (
                <List.Item className="rounded-lg border border-white/5 bg-surface-elevated/70 p-6">
                  <Space direction="vertical" size={12} className="w-full">
                    <Space className="flex items-center justify-between">
                      <Space size={8}>
                        <Tag color={index === 0 ? 'blue' : 'default'}>Top {index + 1}</Tag>
                        <Tooltip title="越接近 1 表示相关性越高">
                          <Tag color="purple">相似度 {item.score.toFixed(3)}</Tag>
                        </Tooltip>
                      </Space>
                      {item.metadata?.source && <Tag>{String(item.metadata.source)}</Tag>}
                    </Space>
                    <div className="whitespace-pre-wrap text-sm leading-relaxed text-slate-100">
                      {highlight(item.text, form.getFieldValue('query') ?? '')}
                    </div>
                    {item.metadata && Object.keys(item.metadata).length > 0 && (
                      <div className="rounded border border-white/10 bg-white/5 p-4 text-xs text-slate-300">
                        <div className="mb-2 text-slate-400">元数据</div>
                        <dl className="grid grid-cols-1 gap-2 md:grid-cols-2">
                          {Object.entries(item.metadata).map(([key, value]) => (
                            <div key={key} className="flex gap-2">
                              <dt className="w-24 text-slate-400">{key}</dt>
                              <dd className="flex-1 break-words text-slate-200">
                                {typeof value === 'string' || typeof value === 'number'
                                  ? value
                                  : JSON.stringify(value)}
                              </dd>
                            </div>
                          ))}
                        </dl>
                      </div>
                    )}
                  </Space>
                </List.Item>
              )}
            />
          </Space>
        )}

        {results.length > 0 && topScore < 0.6 && (
          <Alert
            type="warning"
            showIcon
            message="相似度较低"
            description="检索结果的最高相似度低于 0.6，建议补充文档或优化提示词。"
          />
        )}
      </Space>
    </Card>
  );
}
