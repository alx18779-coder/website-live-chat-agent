import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: '登录 - 管理控制台',
};

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#0f172a] to-[#1e293b] p-6">
      {children}
    </div>
  );
}
