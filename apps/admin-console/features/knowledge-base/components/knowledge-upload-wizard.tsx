'use client';

import { useCallback, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  message,
  Radio,
  Space,
  Steps,
  Tag,
  Upload,
} from 'antd';
import type { RcFile } from 'antd/es/upload';
import { InboxOutlined } from '@ant-design/icons';
import { useMutation } from '@tanstack/react-query';
import dayjs from 'dayjs';
import {
  uploadKnowledgeDocuments,
  type KnowledgeUploadPayload,
  type KnowledgeUploadResponse,
} from '@/services/knowledge';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

interface KnowledgeUploadWizardProps {
  onUploaded?: (response: KnowledgeUploadResponse) => void;
}

interface MetadataFormValues {
  title: string;
  category?: string;
  tags?: string[];
  version?: string;
  description?: string;
}

type SourceType = 'file' | 'text';

export default function KnowledgeUploadWizard({ onUploaded }: KnowledgeUploadWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [sourceType, setSourceType] = useState<SourceType>('file');
  const [rawContent, setRawContent] = useState<string>('');
  const [fileName, setFileName] = useState<string>('');
  const [form] = Form.useForm<MetadataFormValues>();

  const uploadMutation = useMutation({
    mutationFn: (payload: KnowledgeUploadPayload) => uploadKnowledgeDocuments(payload),
    onSuccess: (response) => {
      message.success(response.message || '上传成功');
      onUploaded?.(response);
      resetWizard();
    },
    onError: (error: unknown) => {
      const err = error as { message?: string };
      message.error(err?.message ?? '上传失败，请稍后重试');
    },
  });

  const resetWizard = () => {
    setCurrentStep(0);
    setRawContent('');
    setFileName('');
    form.resetFields();
  };

  const handleFileSelect = useCallback((file: RcFile) => {
    if (file.size > MAX_FILE_SIZE) {
      message.error('文件大小超出 10MB 限制');
      return Upload.LIST_IGNORE;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result;
      if (typeof content === 'string') {
        setRawContent(content);
        setFileName(file.name);
      }
    };
    reader.readAsText(file);

    return false;
  }, []);

  const canProceedToMetadata = useMemo(() => rawContent.trim().length > 0, [rawContent]);

  const handleNext = async () => {
    if (currentStep === 0 && !canProceedToMetadata) {
      message.warning('请先上传文件或输入文本内容');
      return;
    }

    if (currentStep === 1) {
      try {
        await form.validateFields();
      } catch {
        message.error('请完善文档元信息');
        return;
      }
    }

    setCurrentStep((prev) => Math.min(prev + 1, steps.length - 1));
  };

  const handlePrevious = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  };

  const previewMetadata = form.getFieldsValue();

  const submitPayload = useMemo(() => {
    const metadata = form.getFieldsValue();
    if (!rawContent) {
      return undefined;
    }

    return {
      documents: [
        {
          text: rawContent,
          metadata: {
            ...metadata,
            source: metadata.category,
            source_filename: fileName || undefined,
            uploaded_at: dayjs().toISOString(),
          },
        },
      ],
    } satisfies KnowledgeUploadPayload;
  }, [fileName, form, rawContent]);

  const handleSubmit = () => {
    if (!submitPayload) {
      message.error('缺少需要上传的内容');
      return;
    }

    uploadMutation.mutate(submitPayload);
  };

  const steps = [
    {
      key: 'source',
      title: '选择内容',
      description: '支持 Markdown、HTML、纯文本',
    },
    {
      key: 'metadata',
      title: '补充元信息',
      description: '设置分类、标签和版本',
    },
    {
      key: 'review',
      title: '确认并上传',
      description: '预览摘要与元数据',
    },
  ];

  return (
    <Card className="bg-surface-elevated/60" bordered={false}>
      <Space direction="vertical" size={24} className="w-full">
        <Steps
          current={currentStep}
          items={steps.map((step) => ({ key: step.key, title: step.title, description: step.description }))}
        />

        {currentStep === 0 && (
          <Space direction="vertical" size={16} className="w-full">
            <Radio.Group
              value={sourceType}
              onChange={(event) => {
                const value = event.target.value as SourceType;
                setSourceType(value);
                if (value === 'text') {
                  setFileName('');
                }
              }}
            >
              <Radio.Button value="file">上传文件</Radio.Button>
              <Radio.Button value="text">粘贴文本</Radio.Button>
            </Radio.Group>

            {sourceType === 'file' ? (
              <Upload.Dragger
                maxCount={1}
                accept=".md,.markdown,.txt,.html,.htm"
                beforeUpload={handleFileSelect}
                showUploadList={false}
                className="bg-surface-elevated/80"
              >
                <p className="ant-upload-drag-icon">
                  <InboxOutlined />
                </p>
                <p className="ant-upload-text">点击或拖拽文件到此处</p>
                <p className="ant-upload-hint">最大 10MB，支持 Markdown/HTML/纯文本</p>
                {fileName && <Tag color="blue">已选择：{fileName}</Tag>}
              </Upload.Dragger>
            ) : (
              <Input.TextArea
                value={rawContent}
                onChange={(event) => setRawContent(event.target.value)}
                placeholder="直接粘贴文档内容..."
                autoSize={{ minRows: 12 }}
              />
            )}

            <Alert
              type="info"
              message="上传后系统将自动切片并生成向量，可能需要数秒时间。"
              showIcon
            />
          </Space>
        )}

        {currentStep === 1 && (
          <Form form={form} layout="vertical" initialValues={{ tags: [], version: 'v1' }}>
            <Form.Item
              label="文档标题"
              name="title"
              rules={[{ required: true, message: '请输入标题' }]}
            >
              <Input placeholder="例如：工单提交流程" />
            </Form.Item>
            <Form.Item label="分类" name="category">
              <Input placeholder="例如：客服 / 产品" />
            </Form.Item>
            <Form.Item label="标签" name="tags">
              <Select mode="tags" placeholder="输入后回车添加标签" />
            </Form.Item>
            <Form.Item label="版本" name="version">
              <Input placeholder="例如：v1.0" />
            </Form.Item>
            <Form.Item label="摘要" name="description">
              <Input.TextArea placeholder="简要说明文档内容" autoSize={{ minRows: 4 }} />
            </Form.Item>
          </Form>
        )}

        {currentStep === 2 && (
          <Space direction="vertical" size={16} className="w-full">
            <Card title="文档预览" className="bg-surface-elevated/80" size="small">
              <pre className="max-h-64 overflow-y-auto whitespace-pre-wrap text-sm text-slate-200">
                {rawContent.slice(0, 2000) || '内容为空'}
              </pre>
            </Card>
            <Card title="元信息" className="bg-surface-elevated/80" size="small">
              <dl className="grid grid-cols-1 gap-3 text-sm text-slate-300 md:grid-cols-2">
                <div>
                  <dt className="text-slate-400">标题</dt>
                  <dd className="text-slate-100">{previewMetadata.title || '未填写'}</dd>
                </div>
                <div>
                  <dt className="text-slate-400">分类</dt>
                  <dd className="text-slate-100">{previewMetadata.category || '未填写'}</dd>
                </div>
                <div>
                  <dt className="text-slate-400">标签</dt>
                  <dd className="text-slate-100">
                    {previewMetadata.tags?.length ? (
                      <Space size={[4, 4]} wrap>
                        {previewMetadata.tags.map((tag) => (
                          <Tag key={tag} color="geekblue">
                            {tag}
                          </Tag>
                        ))}
                      </Space>
                    ) : (
                      '未填写'
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-400">版本</dt>
                  <dd className="text-slate-100">{previewMetadata.version || '未填写'}</dd>
                </div>
                <div className="md:col-span-2">
                  <dt className="text-slate-400">摘要</dt>
                  <dd className="text-slate-100">{previewMetadata.description || '未填写'}</dd>
                </div>
              </dl>
            </Card>
          </Space>
        )}

        <Space className="flex justify-between" wrap>
          <div>
            {currentStep > 0 && (
              <Button onClick={handlePrevious} disabled={uploadMutation.isPending}>
                上一步
              </Button>
            )}
          </div>
          <Space>
            <Button onClick={resetWizard} disabled={uploadMutation.isPending}>
              重新开始
            </Button>
            {currentStep < steps.length - 1 && (
              <Button type="primary" onClick={handleNext}>
                下一步
              </Button>
            )}
            {currentStep === steps.length - 1 && (
              <Button type="primary" onClick={handleSubmit} loading={uploadMutation.isPending}>
                提交上传
              </Button>
            )}
          </Space>
        </Space>
      </Space>
    </Card>
  );
}
