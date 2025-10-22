'use client';

import { DatabaseOutlined } from '@ant-design/icons';
import clsx from 'clsx';

interface AppLogoProps {
  compact?: boolean;
}

export default function AppLogo({ compact = false }: AppLogoProps) {
  return (
    <div className={clsx('flex items-center gap-3 text-lg font-semibold tracking-wide text-slate-100', compact && 'gap-0 text-base')}>
      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-primary/20 text-brand-secondary shadow-glow">
        <DatabaseOutlined className="text-xl" />
      </span>
      {!compact && <span className="uppercase text-xs text-slate-300">Admin Console</span>}
    </div>
  );
}
