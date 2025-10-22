'use client';

import { Layout, Breadcrumb, Button } from 'antd';
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons';
import { usePathname } from 'next/navigation';
import { useMemo } from 'react';
import { ThemeSwitch } from '@/components/theme/theme-switch';
import { useLayoutStore } from '@/features/layout/store';

const { Header } = Layout;

function buildBreadcrumb(pathname: string) {
  const segments = pathname.split('/').filter(Boolean);
  const mapping: Record<string, string> = {
    dashboard: '仪表盘',
    'knowledge-base': '知识库',
    conversations: '会话审查',
    'model-routing': '模型与路由',
    integrations: '接入配置',
    monitoring: '监控与审计',
    settings: '系统设置',
    login: '登录',
  };
  return segments.map((segment, index) => ({
    key: `${segment}-${index}`,
    title: mapping[segment] ?? segment,
  }));
}

export default function Topbar() {
  const pathname = usePathname();
  const breadcrumbItems = useMemo(() => buildBreadcrumb(pathname), [pathname]);
  const { sidebarCollapsed, toggleSidebar } = useLayoutStore();

  return (
    <Header className="sticky top-0 z-20 flex items-center justify-between border-b border-white/5 bg-[#0B1120]/95 px-6 backdrop-blur">
      <div className="flex items-center gap-3">
        <Button
          type="text"
          icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={toggleSidebar}
          className="text-slate-200 hover:text-brand-secondary"
        />
        <Breadcrumb items={breadcrumbItems} className="text-slate-300" />
      </div>
      <div className="flex items-center gap-4">
        <ThemeSwitch />
        <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
          <span className="h-2 w-2 rounded-full bg-green-400" />
          <span>online</span>
        </div>
      </div>
    </Header>
  );
}
