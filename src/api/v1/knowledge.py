"""
知识库管理 API

提供知识库文档上传、检索测试等功能。
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.security import verify_api_key
from src.models.knowledge import (
    KnowledgeDocumentListResponse,
    KnowledgeSearchResponse,
    KnowledgeUpsertRequest,
    KnowledgeUpsertResponse,
    SearchResult,
)
from src.services import llm_factory
from src.core.exceptions import MilvusConnectionError
from src.services.milvus_service import milvus_service

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/knowledge/upsert", response_model=KnowledgeUpsertResponse)
async def upsert_knowledge(request: KnowledgeUpsertRequest) -> KnowledgeUpsertResponse:
    """
    批量上传知识库文档

    自动处理：
    1. 文档切片（TODO: 实现文本切片逻辑）
    2. 生成 Embedding
    3. 存入 Milvus
    """
    logger.info(f"📥 Upserting {len(request.documents)} documents to knowledge base")

    try:
        # 创建 Embeddings 实例（按模块引用，便于测试补丁生效）
        embeddings = llm_factory.create_embeddings()

        # 准备插入数据
        documents_to_insert = []

        for doc in request.documents:
            # 检查文本长度并分块
            from src.core.utils import chunk_text_for_embedding
            chunks = chunk_text_for_embedding(doc.text, max_tokens=512)

            if len(chunks) > 1:
                logger.info(f"Document split into {len(chunks)} chunks")

            for idx, chunk in enumerate(chunks):
                doc_id = str(uuid.uuid4())
                embedding = await embeddings.aembed_query(chunk)

                # 更新metadata，标记分块信息
                chunk_metadata = doc.metadata.copy() if doc.metadata else {}
                if len(chunks) > 1:
                    chunk_metadata["chunk_index"] = idx
                    chunk_metadata["total_chunks"] = len(chunks)

                documents_to_insert.append({
                    "id": doc_id,
                    "text": chunk,
                    "embedding": embedding,
                    "metadata": chunk_metadata,
                })

        # 批量插入到 Milvus（兼容不同服务实现/测试桩）
        inserted_count: int = 0
        if hasattr(milvus_service, "insert_documents"):
            result = await milvus_service.insert_documents(documents_to_insert)  # type: ignore[attr-defined]
            if isinstance(result, dict) and "inserted_count" in result:
                inserted_count = int(result["inserted_count"])
            elif isinstance(result, int):
                inserted_count = result
            else:
                inserted_count = len(documents_to_insert)
        else:
            inserted_count = await milvus_service.insert_knowledge(documents_to_insert)

        logger.info(f"✅ Successfully inserted {inserted_count} documents")

        return KnowledgeUpsertResponse(
            success=True,
            inserted_count=inserted_count,
            collection_name=request.collection_name,
            message=f"成功上传 {len(request.documents)} 个文档，共生成 {inserted_count} 个向量切片",
        )

    except Exception as e:
        logger.error(f"❌ Failed to upsert knowledge: {e}")
        return KnowledgeUpsertResponse(
            success=False,
            inserted_count=0,
            collection_name=request.collection_name,
            message=f"上传失败: {str(e)}",
        )


@router.get("/knowledge/documents", response_model=KnowledgeDocumentListResponse)
async def list_knowledge_documents(
    page: int = Query(default=1, ge=1, description="页码，从1开始"),
    page_size: int = Query(default=20, ge=1, le=200, description="每页数量"),
    keyword: str | None = Query(default=None, description="搜索关键字"),
    status: str | None = Query(default=None, description="状态过滤"),
    tags: list[str] | None = Query(default=None, description="标签过滤"),
) -> KnowledgeDocumentListResponse:
    """分页获取知识库文档概要信息"""

    try:
        documents, total = await milvus_service.list_knowledge_documents(
            page=page,
            page_size=page_size,
            keyword=keyword,
            status=status,
            tags=tags,
        )
    except MilvusConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return KnowledgeDocumentListResponse(
        documents=documents,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    query: str = Query(..., description="搜索查询"),
    top_k: int = Query(default=3, ge=1, le=10, description="返回结果数量"),
) -> KnowledgeSearchResponse:
    """
    测试知识库检索

    用于调试和验证知识库内容。
    """
    logger.info(f"🔍 Searching knowledge base: query='{query}', top_k={top_k}")

    try:
        # 生成查询向量
        embeddings = llm_factory.create_embeddings()
        # 截断查询文本到512 tokens以内
        from src.core.utils import truncate_text_to_tokens
        truncated_query = truncate_text_to_tokens(query, max_tokens=512)
        query_embedding = await embeddings.aembed_query(truncated_query)

        # 检索
        results = await milvus_service.search_knowledge(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        # 格式化结果
        formatted_results = [
            SearchResult(
                text=result["text"],
                score=result["score"],
                metadata=result.get("metadata", {}),
            )
            for result in results
        ]

        logger.info(f"✅ Found {len(formatted_results)} results")

        return KnowledgeSearchResponse(
            results=formatted_results,
            query=query,
            total_results=len(formatted_results),
        )

    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        return KnowledgeSearchResponse(
            results=[],
            query=query,
            total_results=0,
        )

