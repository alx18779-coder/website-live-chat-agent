# Issue #34 修复摘要

**Issue**: #34 - 外部指令模板被错误传递导致Agent检索失败
**修复时间**: 2025-01-17
**修复人**: LD

## 问题描述
外部AI工具的指令模板（"AI question rephraser"）被错误地传递给了Agent的消息流，导致`search_knowledge_for_agent`函数接收到超长文本，触发413错误，阻塞Agent检索功能。

## 修复内容
- 在`retrieve_node`中添加消息验证机制
- 过滤外部指令模板，只处理用户查询
- 添加消息长度和内容验证
- 完善异常处理机制

## 影响文件
- `src/agent/nodes.py` (添加消息验证逻辑)
- `tests/unit/test_agent_nodes.py` (新增测试用例)

## 测试结果
- ✅ 177/177 tests passed
- ✅ Coverage: 保持原有水平
- ✅ 新增7个测试用例验证消息过滤功能

## 相关PR
- PR #35: https://github.com/alx18779-coder/website-live-chat-agent/pull/35
