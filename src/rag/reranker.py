"""Rerank：用 bge-reranker-base 对候选文档精细打分（GPU 优化版）。"""
import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from functools import lru_cache
from typing import List, Tuple
from langchain_core.documents import Document
from FlagEmbedding import FlagReranker
import torch


# 全局缓存模型，避免每次调用都重新加载
_reranker = None

# 直接用本地 snapshots 路径，不走 HF 缓存
# _MODEL_PATH = r"D:/hf_cache/hub/models--BAAI--bge-reranker-v2-m3/snapshots/953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"


def get_reranker():
    """懒加载 Reranker 模型。"""
    global _reranker
    if _reranker is None:
        use_cuda = torch.cuda.is_available()
        print(f">>> 加载 bge-reranker-base, 设备: {'cuda' if use_cuda else 'cpu'}...")
        _reranker = FlagReranker(
            "BAAI/bge-reranker-base",          # 小模型，2GB 显存够用
            use_fp16=use_cuda,                  # GPU 用 fp16
            devices="cuda" if use_cuda else "cpu",
            # "BAAI/bge-reranker-v2-m3",
            # _MODEL_PATH,
            # use_fp16=True,          # 加速推理
        )
        print(">>> 加载完成")
    return _reranker

# 用 lru_cache 缓存打分结果：同样的 (query, doc_texts) 第二次调用直接返回缓存，不重复计算
# maxsize=128 表示最多缓存 128 组不同的输入
@lru_cache(maxsize=128)
def _rerank_scores(query: str, doc_texts: Tuple[str, ...]) -> Tuple[float, ...]:
    """
    对 (query, 每个文档) 逐对打分，返回分数元组。

    为什么用 Tuple 而不是 List：
        lru_cache 要求参数可哈希（hashable）。
        List 不可哈希，Tuple 可以，所以 doc_texts 和返回值都用 Tuple。

    Args:
        query: 用户问题（字符串）
        doc_texts: 候选文档的文本内容元组（每个元素是一个 chunk 的文本）

    Returns:
        每个文档对应的相关性分数元组，顺序和 doc_texts 一一对应
    """
    # 懒加载 Reranker 模型（进程内只加载一次）
    reranker = get_reranker()

    # 构造 (query, doc) 对：Rerank 模型需要对「问题 + 文档」一起编码打分
    # 例如 pairs = [["问题A", "文档1内容"], ["问题A", "文档2内容"], ...]
    pairs = [[query, text] for text in doc_texts]

    # 调用 Cross-Encoder 打分，返回每个 pair 的相关性分数
    # 分数越高 → 文档和问题越相关
    scores = reranker.compute_score(pairs)

    # 转成 Tuple 返回，保证 lru_cache 能缓存
    return tuple(scores)


def rerank(query: str, docs: List[Document], top_k: int = 5) -> List[Document]:
    """
    对候选文档重排序，返回最相关的 TopK 个。

    流程：
        1. 从 docs 里提取文本，转成 Tuple（方便缓存）
        2. 调 _rerank_scores 拿到每个文档的分数
        3. 按分数降序排列，取前 top_k 个

    Args:
        query: 用户问题
        docs: 候选文档列表（一般是从向量检索召回的 Top20）
        top_k: 最终返回几个文档（一般给 LLM 送 5 个）

    Returns:
        按相关性降序排列的 TopK 文档
    """
    # 边界情况：没有候选文档，直接返回空列表
    if not docs:
        return []

    # 提取每个文档的文本，转成 Tuple（Tuple 可哈希，才能被 lru_cache 缓存）
    doc_texts = tuple(doc.page_content for doc in docs)

    # 打分（内部带缓存，同样的 query + docs 第二次调用直接命中缓存）
    scores = _rerank_scores(query, doc_texts)

    # 把分数和文档配对：[(score1, doc1), (score2, doc2), ...]
    scored_pairs = list(zip(scores, docs))

    # 按分数降序排序（reverse=True 表示从大到小）
    # key=lambda x: x[0] 表示按每个 tuple 的第一个元素（分数）排序
    scored_pairs.sort(key=lambda x: x[0], reverse=True)

    # 取前 top_k 个，只返回文档本身（不带分数）
    return [doc for _, doc in scored_pairs[:top_k]]


def rerank(query: str, docs: List[Document], top_k: int = 5) -> List[Document]:
    """对候选文档重排序，返回 TopK。

    Args:
        query: 用户问题
        docs: 候选文档列表（从向量检索拿到的 TopK=20）
        top_k: 最终返回的文档数

    Returns:
        按相关性降序排列的 TopK 文档
    """
    if not docs:
        return []

    reranker = get_reranker()

    # 构造 (query, doc) 对
    pairs = [[query, doc.page_content] for doc in docs]

    # 打分
    scores = reranker.compute_score(pairs)

    # 按分数降序排序，取 TopK
    scored_docs = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored_docs[:top_k]]

