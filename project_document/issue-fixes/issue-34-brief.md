# Issue #34 修复摘要

**Issue**: #34 - 外部指令模板被错误传递导致Agent检索失败
**修复时间**: 2025-01-17
**修复人**: LD

## 问题描述
外部AI工具的指令模板（"AI question rephraser"）被错误地传递给了Agent的消息流，导致`search_knowledge_for_agent`函数接收到超长文本，触发413错误，阻塞Agent检索功能。

## 修复内容
- 在`retrieve_node`中添加消息验证机制，完全移除异常消息
- 过滤外部指令模板，只处理用户查询
- 配置化过滤参数，支持环境变量配置
- 添加过滤记录和日志，提供可观测性
- 完善异常处理机制

## 影响文件
- `src/agent/nodes.py` (添加消息验证逻辑)
- `src/core/config.py` (添加消息过滤配置)
- `tests/unit/test_agent_nodes.py` (新增测试用例)
- `docker-compose.yml` (添加消息过滤配置)

## 测试结果
- ✅ 179/179 tests passed
- ✅ Coverage: 保持原有水平
- ✅ 新增9个测试用例验证消息过滤功能
- ✅ 代码风格检查通过

## 相关PR
- PR #35: https://github.com/alx18779-coder/website-live-chat-agent/pull/35
