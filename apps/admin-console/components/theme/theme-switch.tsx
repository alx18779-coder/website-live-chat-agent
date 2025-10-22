'use client';

import { Switch, Tooltip } from 'antd';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

export function ThemeSwitch() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="h-6 w-12 rounded-full bg-white/10" />;
  }

  return (
    <Tooltip title={theme === 'dark' ? '切换为亮色模式' : '切换为暗色模式'}>
      <Switch
        checked={theme === 'dark'}
        onChange={(checked) => setTheme(checked ? 'dark' : 'light')}
        checkedChildren={<Moon size={14} />}
        unCheckedChildren={<Sun size={14} />}
        className="bg-white/10"
      />
    </Tooltip>
  );
}
