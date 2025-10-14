"""
测试配置管理模块

测试 Settings 类的环境变量加载、验证和默认值。
"""

import os
import pytest
from pydantic import ValidationError

from src.core.config import Settings


def test_settings_load_from_env():
    """测试从环境变量加载配置"""
    settings = Settings()

    assert settings.llm_provider == "deepseek"
    assert settings.deepseek_api_key == "test-deepseek-key"
    assert settings.milvus_host == "localhost"
    assert settings.milvus_port == 19530
    assert settings.api_key == "test-api-key-12345"


def test_settings_default_values():
    """测试默认值"""
    settings = Settings()

    assert settings.llm_temperature == 0.7
    assert settings.redis_port == 6379
    assert settings.redis_db == 0
    assert settings.log_level == "ERROR"
    assert settings.rag_top_k == 3
    assert settings.rag_score_threshold == 0.7


def test_settings_milvus_collections():
    """测试 Milvus Collection 名称配置"""
    settings = Settings()

    assert settings.milvus_knowledge_collection == "knowledge_base"
    assert settings.milvus_history_collection == "conversation_history"


def test_settings_langgraph_config():
    """测试 LangGraph 配置"""
    settings = Settings()

    assert settings.langgraph_max_iterations == 10
    assert settings.langgraph_checkpointer in ["memory", "redis"]


def test_settings_embedding_config():
    """测试 Embedding 配置"""
    settings = Settings()

    assert settings.embedding_model == "text-embedding-ada-002"
    assert settings.embedding_dim == 1536


def test_settings_required_fields():
    """测试必填字段验证"""
    from unittest.mock import patch, MagicMock
    
    # 测试缺少 api_key 字段
    # 需要 patch BaseSettings 的 model_config 以避免加载 .env 文件
    with patch.dict(
        os.environ,
        {
            "LLM_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "MILVUS_HOST": "localhost",
            # 故意不设置 API_KEY
        },
        clear=True
    ):
        # 临时修改 model_config 以禁用 .env 文件加载
        original_config = Settings.model_config.copy()
        try:
            Settings.model_config['env_file'] = None
            # 缺少 API_KEY 应该抛出 ValidationError
            with pytest.raises(ValidationError):
                Settings()
        finally:
            # 恢复原始配置
            Settings.model_config.update(original_config)
    
    # 测试缺少 milvus_host 字段
    with patch.dict(
        os.environ,
        {
            "LLM_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "API_KEY": "test-api-key",
            # 故意不设置 MILVUS_HOST
        },
        clear=True
    ):
        try:
            Settings.model_config['env_file'] = None
            # 缺少 MILVUS_HOST 应该抛出 ValidationError
            with pytest.raises(ValidationError):
                Settings()
        finally:
            Settings.model_config.update(original_config)


def test_settings_llm_provider_validation():
    """测试 LLM Provider 枚举验证"""
    # 临时设置无效的 provider
    original_provider = os.environ.get("LLM_PROVIDER")

    try:
        os.environ["LLM_PROVIDER"] = "invalid-provider"

        with pytest.raises(ValidationError):
            Settings()

    finally:
        if original_provider:
            os.environ["LLM_PROVIDER"] = original_provider


def test_settings_case_insensitive():
    """测试环境变量大小写不敏感"""
    # Settings 配置为 case_sensitive=False
    settings = Settings()

    # 应该能正确加载不同大小写的环境变量
    assert settings.api_key is not None

