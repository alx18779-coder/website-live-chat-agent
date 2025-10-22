'use client';

import { useState } from 'react';
import { ConfigProvider, theme as antdTheme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';

dayjs.locale('zh-cn');

const themeToken = {
  colorPrimary: '#2952FF',
  colorInfo: '#3BA3FF',
  colorBgBase: '#0F172A',
  colorTextBase: '#E2E8F0',
};

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: 2,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
      <ConfigProvider
        locale={zhCN}
        theme={{
          algorithm: antdTheme.darkAlgorithm,
          token: themeToken,
          components: {
            Layout: {
              bodyBg: '#0F172A',
              siderBg: '#111827',
              headerBg: '#0B1120',
            },
          },
        }}
      >
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      </ConfigProvider>
    </ThemeProvider>
  );
}
