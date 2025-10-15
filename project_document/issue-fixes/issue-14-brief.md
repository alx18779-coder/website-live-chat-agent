# Issue #14 修复摘要

**Issue**: #14 - Milvus连接配置缺少数据库名称参数
**修复时间**: 2025-01-27
**修复人**: LD

## 修复内容
- 在配置类中添加 milvus_database 字段，默认值为"default"
- 修改 Milvus 连接代码，添加 db_name 参数支持
- 更新 docker-compose.yml 添加 MILVUS_DATABASE 环境变量
- 保持向后兼容性，默认使用"default"数据库

## 影响文件
- `src/core/config.py` (+1 line) - 添加 milvus_database 配置项
- `src/services/milvus_service.py` (+1 line) - 连接代码添加 db_name 参数
- `docker-compose.yml` (+1 line) - 添加 MILVUS_DATABASE 环境变量

## 测试结果
- ✅ 10/10 milvus_service 测试通过
- ✅ 8/8 config 测试通过
- ✅ Linter: 0 errors
- ✅ 向后兼容性验证通过

## PR
- 创建后于此补充链接
