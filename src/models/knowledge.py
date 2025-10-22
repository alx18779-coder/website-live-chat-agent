"""
知识库数据模型
"""

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """文档切片"""

    text: str = Field(..., max_length=10000, description="文档文本内容")
    metadata: dict = Field(default_factory=dict, description="文档元数据")


class KnowledgeUpsertRequest(BaseModel):
    """知识库上传请求"""

    documents: list[DocumentChunk] = Field(..., min_length=0, max_length=100)
    collection_name: str = Field(default="knowledge_base")
    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)


class KnowledgeUpsertResponse(BaseModel):
    """知识库上传响应"""

    success: bool
    inserted_count: int
    collection_name: str
    message: str


class SearchResult(BaseModel):
    """搜索结果"""

    text: str
    score: float = Field(..., ge=0.0, le=1.0, description="相似度分数")
    metadata: dict


class KnowledgeSearchRequest(BaseModel):
    """知识库搜索请求"""

    query: str
    top_k: int = Field(default=3, ge=1, le=10)
    collection_name: str = Field(default="knowledge_base")


class KnowledgeSearchResponse(BaseModel):
    """知识库搜索响应"""

    results: list[SearchResult]
    query: str
    total_results: int


class KnowledgeDocumentSummary(BaseModel):
    """知识库文档概要信息"""

    id: str = Field(..., description="文档唯一标识")
    title: str = Field(..., description="文档标题")
    category: str | None = Field(default=None, description="所属分类")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    version: str | None = Field(default=None, description="版本信息")
    status: str = Field(default="draft", description="文档状态")
    chunk_count: int = Field(default=1, ge=1, description="向量切片数量")
    updated_at: datetime = Field(..., description="最近更新时间")
    created_by: str | None = Field(default=None, description="创建人")
    metadata: dict = Field(default_factory=dict, description="原始元数据")


class KnowledgeDocumentListResponse(BaseModel):
    """知识库文档分页响应"""

    documents: list[KnowledgeDocumentSummary]
    total: int = Field(..., ge=0, description="文档总数")
    page: int = Field(..., ge=1, description="当前页码")
    page_size: int = Field(..., ge=1, description="每页数量")

