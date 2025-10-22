'use client';

import { Layout, Menu, Tooltip } from 'antd';
import type { MenuProps } from 'antd';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { DashboardOutlined, BookOutlined, MessageOutlined, DeploymentUnitOutlined, ApiOutlined, SafetyCertificateOutlined, SettingOutlined } from '@ant-design/icons';
import clsx from 'clsx';
import { useLayoutStore } from '@/features/layout/store';
import AppLogo from '@/components/layout/app-logo';

const { Sider } = Layout;

type MenuItem = Required<MenuProps>['items'][number];

const menuItems: MenuItem[] = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: <Link href="/dashboard">仪表盘</Link>,
  },
  {
    key: '/knowledge-base',
    icon: <BookOutlined />,
    label: <Link href="/knowledge-base">知识库</Link>,
  },
  {
    key: '/conversations',
    icon: <MessageOutlined />,
    label: <Link href="/conversations">会话审查</Link>,
  },
  {
    key: '/model-routing',
    icon: <DeploymentUnitOutlined />,
    label: <Link href="/model-routing">模型与路由</Link>,
  },
  {
    key: '/integrations',
    icon: <ApiOutlined />,
    label: <Link href="/integrations">接入配置</Link>,
  },
  {
    key: '/monitoring',
    icon: <SafetyCertificateOutlined />,
    label: <Link href="/monitoring">监控与审计</Link>,
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: <Link href="/settings">系统设置</Link>,
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, setSidebarCollapsed } = useLayoutStore();
  const selectedKey = menuItems.find((item) => typeof item?.key === 'string' && pathname.startsWith(item.key))?.key ?? '/dashboard';

  return (
    <Sider
      collapsible
      collapsed={sidebarCollapsed}
      onCollapse={setSidebarCollapsed}
      width={264}
      theme="dark"
      className="!bg-[#111827] !text-slate-200"
    >
      <div className={clsx('flex h-16 items-center justify-center border-b border-white/5 px-4', sidebarCollapsed && 'px-0')}>
        <Tooltip title="返回仪表盘" placement="right">
          <Link href="/dashboard">
            <AppLogo compact={sidebarCollapsed} />
          </Link>
        </Tooltip>
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[selectedKey as string]}
        items={menuItems}
        className="mt-2 border-none !bg-transparent text-sm"
      />
    </Sider>
  );
}
