"""
将 FAQ JSONL 数据写入 Milvus `chatagent` 数据库的 `faq` Collection。

运行示例：
    uv run python scripts/load_faq_to_milvus.py --drop-old

依赖：
    - langchain-milvus
    - 项目内的 create_embeddings 工厂
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List

from langchain_core.documents import Document
from langchain_milvus import Milvus

from src.core.config import settings
from src.services.llm_factory import create_embeddings

FAQ_JSONL_PATH = Path("evaluate/ragas/processed/faq.jsonl")
DEFAULT_COLLECTION_NAME = "faq"


def parse_args() -> argparse.Namespace:
    """CLI 参数解析。"""
    parser = argparse.ArgumentParser(
        description="将 FAQ JSONL 写入 Milvus 指定 Collection。"
    )
    parser.add_argument(
        "--faq-path",
        type=Path,
        default=FAQ_JSONL_PATH,
        help="FAQ JSONL 文件路径（默认：evaluate/ragas/processed/faq.jsonl）",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=DEFAULT_COLLECTION_NAME,
        help="Milvus Collection 名称（默认：faq）",
    )
    parser.add_argument(
        "--drop-old",
        action="store_true",
        help="写入前若 Collection 存在则先删除。",
    )
    return parser.parse_args()


def load_faq_documents(path: Path) -> List[Document]:
    """读取 JSONL 并将中英文拆分为独立文档。"""
    if not path.exists():
        raise FileNotFoundError(f"FAQ 文件不存在: {path}")

    documents: list[Document] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue

            payload = json.loads(line)
            base_metadata = {
                "section": payload.get("section", "").strip(),
                "faq_id": f"faq-{line_number:04d}",
            }

            question_zh = payload.get("question_zh", "").strip()
            answer_zh = payload.get("answer_zh", "").strip()
            if question_zh and answer_zh:
                documents.append(
                    Document(
                        page_content=f"问题：{question_zh}\n回答：{answer_zh}",
                        metadata={
                            **base_metadata,
                            "language": "zh",
                            "question": question_zh,
                            "answer": answer_zh,
                        },
                    )
                )

            question_en = payload.get("question_en", "").strip()
            answer_en = payload.get("answer_en", "").strip()
            if question_en and answer_en:
                documents.append(
                    Document(
                        page_content=f"Question: {question_en}\nAnswer: {answer_en}",
                        metadata={
                            **base_metadata,
                            "language": "en",
                            "question": question_en,
                            "answer": answer_en,
                        },
                    )
                )

    if not documents:
        raise ValueError(f"在 {path} 中未读取到任何 FAQ 文档。")

    return documents


def create_connection_args() -> dict[str, object]:
    """根据项目配置生成 Milvus 连接参数。"""
    connection_args: dict[str, object] = {
        "uri": f"http://{settings.milvus_host}:{settings.milvus_port}",
        "host": settings.milvus_host,
        "port": settings.milvus_port,
        "user": settings.milvus_user,
        "password": settings.milvus_password,
        "db_name": settings.milvus_database,
        "timeout": 10,
    }
    return connection_args


def chunked(iterable: Iterable[Document], size: int) -> Iterable[list[Document]]:
    """简单的分批迭代器，避免一次性写入过多文档。"""
    batch: list[Document] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def main() -> None:
    args = parse_args()
    documents = load_faq_documents(args.faq_path)

    embeddings = create_embeddings()
    connection_args = create_connection_args()

    vector_store = Milvus(
        embedding_function=embeddings,
        collection_name=args.collection,
        connection_args=connection_args,
        index_params={"index_type": "AUTOINDEX", "metric_type": "COSINE"},
        drop_old=args.drop_old,
        consistency_level="Strong",
    )

    inserted = 0
    for batch in chunked(documents, size=32):
        vector_store.add_documents(batch)
        inserted += len(batch)

    print(
        f"✅ 已写入 {inserted} 条 FAQ 文档到 "
        f"Milvus 数据库 '{settings.milvus_database}' / Collection '{args.collection}'."
    )


if __name__ == "__main__":
    main()
