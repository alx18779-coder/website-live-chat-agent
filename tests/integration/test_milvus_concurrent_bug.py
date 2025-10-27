"""
测试Milvus并发查询超时问题（Issue #53）

Bug描述：并发访问时查询Milvus超时，没有召回数据
影响场景：压力测试、高并发场景
Bug表现：第一个请求正常，后续请求超时，只是没有返回数据无明确报错

测试目的：
1. 复现并发查询超时问题
2. 对比顺序查询vs并发查询的性能差异
3. 验证第一个请求成功、后续请求超时的现象
"""

import asyncio
import logging
import time
from typing import List

import pytest

from src.services.llm_factory import create_embeddings
from src.services.milvus_service import milvus_service

logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_milvus_queries_timeout():
    """
    Bug复现：并发查询Milvus时超时无数据返回

    场景：压力测试时，10个并发查询请求
    预期：第一个请求正常，后续请求超时（bug存在时）
    修复后：所有请求都应该在合理时间内返回数据
    """
    # 准备测试数据
    embeddings = create_embeddings()
    test_query = "什么是Python？"
    query_embedding = await embeddings.aembed_query(test_query)

    # 并发数量
    concurrent_count = 10
    timeout_seconds = 5  # 单个查询超时时间

    async def single_query(query_id: int) -> dict:
        """执行单个查询并记录时间"""
        start_time = time.time()
        try:
            results = await asyncio.wait_for(
                milvus_service.search_knowledge(
                    query_embedding=query_embedding,
                    top_k=3
                ),
                timeout=timeout_seconds
            )
            elapsed = time.time() - start_time
            return {
                "query_id": query_id,
                "success": True,
                "results_count": len(results),
                "elapsed_time": elapsed,
                "error": None
            }
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            return {
                "query_id": query_id,
                "success": False,
                "results_count": 0,
                "elapsed_time": elapsed,
                "error": "Timeout"
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "query_id": query_id,
                "success": False,
                "results_count": 0,
                "elapsed_time": elapsed,
                "error": str(e)
            }

    # 执行并发查询
    logger.info(f"开始并发测试：{concurrent_count} 个查询")
    start_total = time.time()

    tasks = [single_query(i) for i in range(concurrent_count)]
    results = await asyncio.gather(*tasks)

    total_elapsed = time.time() - start_total

    # 分析结果
    success_count = sum(1 for r in results if r["success"])
    timeout_count = sum(1 for r in results if r["error"] == "Timeout")
    avg_elapsed = sum(r["elapsed_time"] for r in results) / len(results)

    logger.info("并发测试完成：")
    logger.info(f"  总耗时: {total_elapsed:.2f}s")
    logger.info(f"  成功: {success_count}/{concurrent_count}")
    logger.info(f"  超时: {timeout_count}/{concurrent_count}")
    logger.info(f"  平均响应时间: {avg_elapsed:.2f}s")

    # 详细结果
    for result in results:
        logger.info(
            f"  Query {result['query_id']}: "
            f"{'✅' if result['success'] else '❌'} "
            f"({result['elapsed_time']:.2f}s, "
            f"results={result['results_count']}, "
            f"error={result['error']})"
        )

    # Bug验证：
    # 如果bug存在，预期大部分请求超时（success_count < concurrent_count / 2）
    # 修复后，预期所有或大部分请求成功（success_count >= concurrent_count * 0.8）

    # 当前测试：验证bug存在
    if success_count < concurrent_count * 0.5:
        pytest.fail(
            f"Bug确认：并发查询大量超时 ({success_count}/{concurrent_count} 成功率 "
            f"{success_count/concurrent_count*100:.1f}%)"
        )
    else:
        # Bug已修复或不存在
        assert success_count >= concurrent_count * 0.8, \
            f"并发查询成功率应 ≥80%，实际：{success_count/concurrent_count*100:.1f}%"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sequential_vs_concurrent_performance():
    """
    对比测试：顺序查询 vs 并发查询

    目的：证明并发查询存在性能问题
    预期：顺序查询总时间更长，但每个请求都成功
          并发查询总时间更短，但大部分请求超时（bug存在时）
    """
    embeddings = create_embeddings()
    test_query = "Python编程语言"
    query_embedding = await embeddings.aembed_query(test_query)

    query_count = 5

    # 1. 顺序查询
    logger.info("=== 顺序查询测试 ===")
    sequential_start = time.time()
    sequential_results = []

    for i in range(query_count):
        start = time.time()
        try:
            results = await milvus_service.search_knowledge(
                query_embedding=query_embedding,
                top_k=3
            )
            elapsed = time.time() - start
            sequential_results.append({
                "success": True,
                "elapsed": elapsed,
                "count": len(results)
            })
            logger.info(f"  Query {i}: ✅ ({elapsed:.2f}s, {len(results)} results)")
        except Exception as e:
            elapsed = time.time() - start
            sequential_results.append({
                "success": False,
                "elapsed": elapsed,
                "count": 0
            })
            logger.info(f"  Query {i}: ❌ ({elapsed:.2f}s, error: {e})")

    sequential_total = time.time() - sequential_start
    sequential_success = sum(1 for r in sequential_results if r["success"])

    # 2. 并发查询
    logger.info("=== 并发查询测试 ===")
    concurrent_start = time.time()

    async def query_task(task_id: int):
        start = time.time()
        try:
            results = await asyncio.wait_for(
                milvus_service.search_knowledge(
                    query_embedding=query_embedding,
                    top_k=3
                ),
                timeout=5.0
            )
            elapsed = time.time() - start
            return {
                "id": task_id,
                "success": True,
                "elapsed": elapsed,
                "count": len(results)
            }
        except Exception as e:
            elapsed = time.time() - start
            return {
                "id": task_id,
                "success": False,
                "elapsed": elapsed,
                "count": 0,
                "error": str(e)
            }

    tasks = [query_task(i) for i in range(query_count)]
    concurrent_results = await asyncio.gather(*tasks)

    concurrent_total = time.time() - concurrent_start
    concurrent_success = sum(1 for r in concurrent_results if r["success"])

    for result in concurrent_results:
        status = "✅" if result["success"] else "❌"
        logger.info(
            f"  Query {result['id']}: {status} "
            f"({result['elapsed']:.2f}s, {result['count']} results)"
        )

    # 对比结果
    logger.info("=== 对比结果 ===")
    logger.info(f"顺序查询：总时间 {sequential_total:.2f}s, 成功率 {sequential_success}/{query_count}")
    logger.info(f"并发查询：总时间 {concurrent_total:.2f}s, 成功率 {concurrent_success}/{query_count}")
    logger.info(f"时间差异：并发比顺序快 {sequential_total - concurrent_total:.2f}s")
    logger.info(f"成功率差异：{sequential_success - concurrent_success} 个请求失败")

    # 验证：顺序查询应该全部成功
    assert sequential_success == query_count, \
        f"顺序查询应该全部成功，实际成功 {sequential_success}/{query_count}"

    # Bug验证：并发查询成功率低于顺序查询
    if concurrent_success < sequential_success:
        logger.warning(
            f"⚠️  Bug确认：并发查询成功率 ({concurrent_success}/{query_count}) "
            f"低于顺序查询 ({sequential_success}/{query_count})"
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_first_request_success_others_timeout():
    """
    验证：第一个请求成功，后续请求超时

    这是用户反馈的具体现象 (1c, 2c, 3b)
    - 1c: 压力测试场景
    - 2c: 第一个请求正常，后续请求超时
    - 3b: 只是没有返回数据，无明确报错
    """
    embeddings = create_embeddings()
    test_query = "测试查询"
    query_embedding = await embeddings.aembed_query(test_query)

    request_count = 5
    results: List[dict] = []

    async def timed_query(query_id: int) -> dict:
        """带超时的查询"""
        start = time.time()
        try:
            data = await asyncio.wait_for(
                milvus_service.search_knowledge(
                    query_embedding=query_embedding,
                    top_k=3
                ),
                timeout=3.0  # 3秒超时
            )
            elapsed = time.time() - start
            has_data = len(data) > 0
            return {
                "id": query_id,
                "success": True,
                "has_data": has_data,
                "data_count": len(data),
                "elapsed": elapsed
            }
        except asyncio.TimeoutError:
            elapsed = time.time() - start
            return {
                "id": query_id,
                "success": False,
                "has_data": False,
                "data_count": 0,
                "elapsed": elapsed,
                "error": "Timeout - 没有返回数据"
            }
        except Exception as e:
            elapsed = time.time() - start
            return {
                "id": query_id,
                "success": False,
                "has_data": False,
                "data_count": 0,
                "elapsed": elapsed,
                "error": str(e)
            }

    # 并发启动所有请求（模拟压力测试）
    logger.info("启动并发请求（模拟压力测试）...")
    tasks = [timed_query(i) for i in range(request_count)]
    results = await asyncio.gather(*tasks)

    # 分析结果
    first_request = results[0]
    subsequent_requests = results[1:]

    first_success = first_request["success"]
    subsequent_success_count = sum(1 for r in subsequent_requests if r["success"])

    logger.info("=== 测试结果 ===")
    logger.info(
        f"第一个请求：{'✅ 成功' if first_success else '❌ 失败'} "
        f"({first_request['elapsed']:.2f}s, 数据量: {first_request['data_count']})"
    )
    logger.info(
        f"后续请求：{subsequent_success_count}/{len(subsequent_requests)} 成功"
    )

    for result in subsequent_requests:
        status = "✅" if result["success"] else "❌"
        logger.info(
            f"  Request {result['id']}: {status} "
            f"({result['elapsed']:.2f}s, "
            f"数据: {result['data_count']}, "
            f"{'有数据' if result['has_data'] else '无数据'})"
        )

    # Bug验证：符合用户描述 (2c)
    # 第一个请求正常，后续请求超时
    if first_success and subsequent_success_count < len(subsequent_requests) * 0.5:
        logger.error(
            f"⚠️  Bug确认：第一个请求成功，但后续 "
            f"{len(subsequent_requests) - subsequent_success_count}/{len(subsequent_requests)} "
            f"个请求超时/无数据"
        )
        pytest.fail(
            "Bug确认：符合用户描述的现象 - 第一个请求正常，后续请求超时无数据"
        )
    else:
        # Bug已修复
        assert subsequent_success_count >= len(subsequent_requests) * 0.8, \
            "后续请求成功率应 ≥80%"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_milvus_timeout_configuration():
    """
    验证：recall_timeout_ms配置未被使用

    根本原因：
    - config.py 中配置了 recall_timeout_ms=3000
    - 但 milvus_service.search_knowledge() 未使用此配置
    - collection.search() 调用没有timeout参数
    """
    from src.core.config import settings

    # 验证配置存在
    assert hasattr(settings, 'recall_timeout_ms'), \
        "配置中应该有 recall_timeout_ms 字段"

    timeout_ms = settings.recall_timeout_ms
    logger.info(f"配置的召回超时时间：{timeout_ms}ms")

    # 验证：search方法是否使用了这个超时配置
    # 当前实现：collection.search() 没有timeout参数

    embeddings = create_embeddings()
    query_embedding = await embeddings.aembed_query("测试")

    start = time.time()
    try:
        # 尝试在配置的超时时间内完成查询
        await asyncio.wait_for(
            milvus_service.search_knowledge(
                query_embedding=query_embedding,
                top_k=3
            ),
            timeout=timeout_ms / 1000.0  # 转换为秒
        )
        elapsed_ms = (time.time() - start) * 1000
        logger.info(f"查询完成：{elapsed_ms:.0f}ms (配置超时: {timeout_ms}ms)")

        # 如果查询时间接近或超过配置的超时时间，说明配置未生效
        if elapsed_ms > timeout_ms * 0.9:
            logger.warning(
                f"⚠️  查询时间 ({elapsed_ms:.0f}ms) 接近配置超时 ({timeout_ms}ms)，"
                f"说明内部没有使用配置的超时时间"
            )
    except asyncio.TimeoutError:
        elapsed_ms = (time.time() - start) * 1000
        logger.info(
            f"查询超时：{elapsed_ms:.0f}ms "
            f"(由asyncio.wait_for强制超时，而非Milvus内部超时)"
        )
        pytest.fail(
            "Bug确认：recall_timeout_ms配置未在Milvus查询中生效，"
            "需要手动使用asyncio.wait_for强制超时"
        )

