"use client";

import { Layout } from 'antd';
import Sidebar from '@/components/layout/sidebar';
import Topbar from '@/components/layout/topbar';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <Layout hasSider className="min-h-screen bg-transparent">
      <Sidebar />
      <Layout className="bg-transparent">
        <Topbar />
        <Layout.Content className="p-6 md:p-8 lg:p-10">
          <div className="mx-auto max-w-[1440px] space-y-6">{children}</div>
        </Layout.Content>
      </Layout>
    </Layout>
  );
}
