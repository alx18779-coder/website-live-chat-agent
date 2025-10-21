"""
测试向量配置环境变量（Issue #52 修复验证）

修复内容：将 validation_alias 从 RAG_* 改为 VECTOR_*
影响范围：vector_top_k, vector_score_threshold, vector_chunk_size, vector_chunk_overlap

测试目的：
1. 验证 VECTOR_* 环境变量可以正确加载
2. 验证所有 vector 配置项都能通过环境变量设置
3. 确认配置与文档一致
"""

import os
from unittest.mock import patch

import pytest

from src.core.config import Settings


def test_vector_score_threshold_env_working():
    """验证：VECTOR_SCORE_THRESHOLD 环境变量可以正确加载
    
    修复后行为：在 .env 中配置 VECTOR_SCORE_THRESHOLD=0.5 应该生效
    """
    with patch.dict(os.environ, {
        "VECTOR_SCORE_THRESHOLD": "0.5",
        "MILVUS_HOST": "localhost",
        "API_KEY": "test-key",
        "DEEPSEEK_API_KEY": "test-key"
    }, clear=True):
        settings = Settings()
        # 验证：VECTOR_SCORE_THRESHOLD 可以正确加载
        assert settings.vector_score_threshold == 0.5, \
            "VECTOR_SCORE_THRESHOLD 环境变量应该生效"


def test_backward_compatibility_rag_aliases():
    """验证：RAG_* 别名仍然可用（向后兼容）
    
    Pydantic validation_alias 特性：同时支持新旧两种环境变量名
    - 新名称：VECTOR_SCORE_THRESHOLD（推荐）
    - 旧名称：RAG_SCORE_THRESHOLD（兼容）
    """
    with patch.dict(os.environ, {
        "RAG_SCORE_THRESHOLD": "0.5",  # 旧别名，仍然可用
        "MILVUS_HOST": "localhost",
        "API_KEY": "test-key",
        "DEEPSEEK_API_KEY": "test-key"
    }, clear=True):
        settings = Settings()
        # 验证：RAG_* 别名仍然可用（向后兼容）
        assert settings.vector_score_threshold == 0.5, \
            "RAG_SCORE_THRESHOLD 别名仍然可用（向后兼容）"


def test_all_vector_configs_env_working():
    """验证：所有 VECTOR_* 配置项都可以通过环境变量设置
    
    修复范围：
    - VECTOR_TOP_K
    - VECTOR_SCORE_THRESHOLD
    - VECTOR_CHUNK_SIZE
    - VECTOR_CHUNK_OVERLAP
    """
    with patch.dict(os.environ, {
        "VECTOR_TOP_K": "5",
        "VECTOR_SCORE_THRESHOLD": "0.5",
        "VECTOR_CHUNK_SIZE": "800",
        "VECTOR_CHUNK_OVERLAP": "100",
        "MILVUS_HOST": "localhost",
        "API_KEY": "test-key",
        "DEEPSEEK_API_KEY": "test-key"
    }, clear=True):
        settings = Settings()
        
        # 所有配置都应该生效
        assert settings.vector_top_k == 5, \
            "VECTOR_TOP_K 应该生效"
        assert settings.vector_score_threshold == 0.5, \
            "VECTOR_SCORE_THRESHOLD 应该生效"
        assert settings.vector_chunk_size == 800, \
            "VECTOR_CHUNK_SIZE 应该生效"
        assert settings.vector_chunk_overlap == 100, \
            "VECTOR_CHUNK_OVERLAP 应该生效"




def test_vector_config_documentation_consistent():
    """验证：文档与实际行为一致
    
    修复后：文档中的 VECTOR_SCORE_THRESHOLD 配置示例可以正常工作
    """
    with patch.dict(os.environ, {
        "VECTOR_SCORE_THRESHOLD": "0.8",  # 按照文档中的示例
        "MILVUS_HOST": "localhost",
        "API_KEY": "test-key",
        "DEEPSEEK_API_KEY": "test-key"
    }, clear=True):
        settings = Settings()
        
        # 验证：按照文档配置可以生效
        assert settings.vector_score_threshold == 0.8, \
            "文档示例配置应该生效：VECTOR_SCORE_THRESHOLD"

