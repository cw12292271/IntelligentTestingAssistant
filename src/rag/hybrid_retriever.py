"""混合检索：BM25（关键词）+ 向量（语义），用 RRF 融合。"""
from typing import List
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_community.retrievers import BM25Retriever
from pydantic import Field

try:
    from langchain_classic.retrievers import EnsembleRetriever
except ImportError:
    from langchain.retrievers import EnsembleRetriever

from src.rag.vectorstore import get_milvus_client, COLLECTION_NAME, DB_NAME

class CustomVectorRetriever(BaseRetriever):
    """把自封装的检索函数包装成 LangChain 标准 Retriever"""
    k: int = Field(default=20)

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
        from src.rag.vectorstore import get_retriever
        retriever_fn = get_retriever(k=self.k)
        return retriever_fn(query)


def _load_all_docs() -> List[Document]:
    client = get_milvus_client()
    results = client.query(
        collection_name=COLLECTION_NAME,
        filter="",
        output_fields=["text", "metadata"],   # ← 加上 metadata
        limit=10000,
    )
    # docs = [Document(page_content=r["text"]) for r in results if r.get("text")]
    docs = []
    for r in results:
        text = r.get("text", "")
        if not text:
            continue
        meta = r.get("metadata", {})
        docs.append(Document(page_content=text, metadata=meta))   # ← 带上 metadata
    # print(f">>> 从 {DB_NAME}.{COLLECTION_NAME} 加载了 {len(docs)} 条文档作为 BM25 语料")
    return docs


def build_hybrid_retriever(k: int = 5, fetch_k: int = 20, weights: tuple = (0.5, 0.5)):
    all_docs = _load_all_docs()
    
    # 1. BM25
    bm25_retriever = BM25Retriever.from_documents(all_docs)
    bm25_retriever.k = fetch_k

    # 2. 向量检索（用包装类）
    vector_retriever = CustomVectorRetriever(k=fetch_k)  # ← 关键：用包装类，不用函数

    # 3. 融合
    ensemble = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=list(weights),
    )
    return ensemble