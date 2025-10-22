# Admin Console

基于 Next.js 14、Ant Design、React Query 与 Zustand 的管理后台前端工程，实现知识库维护、模型配置、会话监控等运营功能的界面层。

## 开发

```bash
cd apps/admin-console
pnpm install
pnpm dev
```

开发阶段默认从 `.env.local` 中读取 `NEXT_PUBLIC_API_BASE_URL` 指向 FastAPI 服务。

## 目录结构

- `app/`：Next.js App Router 路由与布局。
- `components/`：通用 UI 组件（布局、主题、指标卡片等）。
- `features/`：按业务模块拆分的页面与逻辑。
- `services/`：与后端接口的通信封装（React Query）。
- `i18n/`：多语言文案资源。
- `public/`：静态资源与 manifest。
- `tests/`：预留 Playwright/Vitest 测试目录。

## 下一步

- 接入实际后端接口与鉴权流程。
- 为关键交互补充组件测试与端到端流程测试。
- 结合 Sentry 与指标上报完善观测。
