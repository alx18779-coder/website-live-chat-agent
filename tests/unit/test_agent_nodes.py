"""
测试 Agent 节点逻辑

测试 LangGraph 节点函数的行为。
"""

from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.agent.nodes import _is_valid_user_query, call_llm_node, retrieve_node, router_node
from src.agent.state import AgentState


@pytest.mark.asyncio
async def test_call_llm_simple(mock_llm):
    """测试 LLM 调用节点"""
    state: AgentState = {
        "messages": [HumanMessage(content="你好")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    with patch("src.agent.nodes.create_llm", return_value=mock_llm):
        result = await call_llm_node(state)

        assert "messages" in result
        assert len(result["messages"]) > 0
        # 最后一条消息应该是 AI 的回复
        last_message = result["messages"][-1]
        assert isinstance(last_message, AIMessage)


@pytest.mark.asyncio
async def test_call_llm_with_context(mock_llm):
    """测试带上下文的 LLM 调用"""
    state: AgentState = {
        "messages": [
            HumanMessage(content="介绍一下产品"),
        ],
        "retrieved_docs": [
            {
                "text": "我们的产品是智能客服系统",
                "score": 0.95,
                "metadata": {"source": "product.md"},
            }
        ],
        "tool_calls": [],
        "session_id": "test-123",
    }

    with patch("src.agent.nodes.create_llm", return_value=mock_llm):
        result = await call_llm_node(state)

        assert "messages" in result
        # LLM 应该收到包含检索文档的上下文


@pytest.mark.asyncio
async def test_retrieve_knowledge(mock_embeddings):
    """测试知识库检索节点"""
    state: AgentState = {
        "messages": [HumanMessage(content="退货政策是什么？")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    # Mock search_knowledge_for_agent function return value
    mock_results = [
        {
            "text": "30天内可以无条件退货",
            "score": 0.9,
            "metadata": {"source": "policy.md", "title": "退货政策"},
        }
    ]

    with patch("src.agent.nodes.search_knowledge_for_agent", return_value=mock_results):
        result = await retrieve_node(state)

        assert "retrieved_docs" in result
        assert len(result["retrieved_docs"]) > 0
        assert result["confidence_score"] == 0.9


@pytest.mark.asyncio
async def test_retrieve_knowledge_empty_query():
    """测试空查询的检索"""
    state: AgentState = {
        "messages": [],  # 没有消息
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = await retrieve_node(state)

    # 应该返回空的检索结果
    assert result.get("retrieved_docs", []) == []


@pytest.mark.asyncio
async def test_router_node_greeting():
    """测试路由节点 - 简单打招呼"""
    state: AgentState = {
        "messages": [HumanMessage(content="你好")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = await router_node(state)

    # 路由节点应该判断是否需要检索
    assert "next_step" in result or result == {}


@pytest.mark.asyncio
async def test_router_node_product_query():
    """测试路由节点 - 产品查询（需要检索）"""
    state: AgentState = {
        "messages": [HumanMessage(content="你们的产品有哪些功能？")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = await router_node(state)

    # 对于产品查询，可能需要检索
    assert result is not None


# Issue #34 相关测试用例
def test_is_valid_user_query_valid_queries():
    """测试有效用户查询的验证"""
    valid_queries = [
        "你好",
        "你们的产品有哪些功能？",
        "退货政策是什么？",
        "价格怎么样？",
        "如何联系客服？",
        "这个产品有什么特点？"
    ]

    for query in valid_queries:
        assert _is_valid_user_query(query), f"Valid query should pass: {query}"


def test_is_valid_user_query_instruction_templates():
    """测试指令模板过滤"""
    instruction_templates = [
        "You are an AI question rephraser. Your role is to rephrase follow-up queries from a conversation into standalone queries that can be used by another LLM to retrieve information through web search.",
        "Your role is to help users with their questions",
        "You are a helpful assistant that can answer questions",
        "Please rephrase the following query",
        "Convert the following question into a search query",
        "Transform this query into a standalone question"
    ]

    for template in instruction_templates:
        assert not _is_valid_user_query(template), f"Instruction template should be filtered: {template[:50]}..."


def test_is_valid_user_query_technical_terms():
    """测试技术术语过滤"""
    technical_queries = [
        "API endpoint function method parameter response request",
        "The API function method parameter is used for response request",
        "This endpoint uses API function method parameter response request"
    ]

    for query in technical_queries:
        assert not _is_valid_user_query(query), f"Technical query should be filtered: {query}"


def test_is_valid_user_query_length_limit():
    """测试长度限制"""
    # 超长查询（超过1000字符）
    long_query = "这是一个很长的查询" * 200  # 约1800字符
    assert not _is_valid_user_query(long_query), "Long query should be filtered"

    # 正常长度查询
    normal_query = "你们的产品有哪些功能？"
    assert _is_valid_user_query(normal_query), "Normal query should pass"


def test_is_valid_user_query_starts_with_instructions():
    """测试以指令开头的查询过滤"""
    instruction_start_queries = [
        "You are a helpful assistant",
        "Your role is to answer questions",
        "Please help me with this",
        "Convert this query",
        "Transform the following"
    ]

    for query in instruction_start_queries:
        assert not _is_valid_user_query(query), f"Instruction start query should be filtered: {query}"


@patch("src.agent.nodes.search_knowledge_for_agent")
@pytest.mark.asyncio
async def test_retrieve_node_filters_instruction_templates(mock_search):
    """测试retrieve_node过滤指令模板"""
    # 模拟指令模板消息
    instruction_template = "You are an AI question rephraser. Your role is to rephrase follow-up queries from a conversation into standalone queries that can be used by another LLM to retrieve information through web search."

    state: AgentState = {
        "messages": [HumanMessage(content=instruction_template)],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = await retrieve_node(state)

    # 应该返回空结果，不调用search_knowledge_for_agent
    assert result["retrieved_docs"] == []
    assert result["confidence_score"] == 0.0
    mock_search.assert_not_called()


@patch("src.agent.nodes.search_knowledge_for_agent")
@pytest.mark.asyncio
async def test_retrieve_node_allows_valid_queries(mock_search):
    """测试retrieve_node允许有效查询"""
    # 模拟有效用户查询
    valid_query = "你们的产品有哪些功能？"

    state: AgentState = {
        "messages": [HumanMessage(content=valid_query)],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    # 模拟搜索结果
    mock_results = [
        {
            "text": "我们的产品功能包括智能客服、知识库检索等",
            "score": 0.9,
            "metadata": {"source": "product.md", "title": "产品功能"},
        }
    ]
    mock_search.return_value = mock_results

    result = await retrieve_node(state)

    # 应该调用search_knowledge_for_agent并返回结果
    mock_search.assert_called_once_with(valid_query, top_k=3)
    assert len(result["retrieved_docs"]) > 0
    assert result["confidence_score"] == 0.9


@patch("src.agent.nodes.search_knowledge_for_agent")
@pytest.mark.asyncio
async def test_retrieve_node_mixed_scenario(mock_search):
    """测试混合场景：指令模板+真实问题"""
    # 模拟包含指令模板和真实问题的混合消息
    mixed_message = """You are an AI question rephraser. Your role is to rephrase follow-up queries from a conversation into standalone queries that can be used by another LLM to retrieve information through web search.

Please rephrase the following query: 你们的产品有哪些功能？"""

    state: AgentState = {
        "messages": [HumanMessage(content=mixed_message)],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = await retrieve_node(state)

    # 应该过滤掉整个混合消息，不调用search_knowledge_for_agent
    assert result["retrieved_docs"] == []
    assert result["confidence_score"] == 0.0
    assert "messages" in result  # 应该返回过滤后的消息列表
    assert len(result["messages"]) == 0  # 异常消息被完全移除
    mock_search.assert_not_called()

    # 验证tool_calls中记录了过滤事件
    assert len(result["tool_calls"]) > 0
    filter_event = result["tool_calls"][-1]
    assert filter_event["action"] == "filter_invalid_message"
    assert filter_event["reason"] == "instruction_template_detected"


def test_is_valid_user_query_configuration():
    """测试配置化参数"""
    # 测试默认配置
    assert _is_valid_user_query("你们的产品有哪些功能？")

    # 测试长度限制
    long_query = "这是一个很长的查询" * 200
    assert not _is_valid_user_query(long_query)

    # 测试指令模板过滤
    instruction_template = "You are an AI question rephraser"
    assert not _is_valid_user_query(instruction_template)

    # 测试技术术语过滤
    technical_query = "API endpoint function method parameter response request"
    assert not _is_valid_user_query(technical_query)

