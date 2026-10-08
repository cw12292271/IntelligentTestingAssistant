"""向量库：直接用 pymilvus 的 MilvusClient，不依赖 langchain-milvus。"""
import os
from typing import List
from dotenv import load_dotenv
from pymilvus import MilvusClient, DataType
from langchain_core.documents import Document
from src.rag.embedder import get_embedding_model

load_dotenv(override=True)

MILVUS_URI = os.getenv("MILVUS_URI", "http://localhost:19530")
DB_NAME = "rag_ita"
COLLECTION_NAME = "test_knowledge"


def _get_client():
    client = MilvusClient(MILVUS_URI)

    # 查询已有的数据库，如果不存在指定名的数据库，则进行创建
    existed_databases = client.list_databases()
    if DB_NAME not in existed_databases:
        client.create_database(db_name=DB_NAME)

    # 切换到指定的数据库
    client.use_database(db_name=DB_NAME)
    return client


def _ensure_collection(client, dim: int):
    """collection 不存在就建，存在就复用。"""
    if client.has_collection(COLLECTION_NAME):
        return
    schema = client.create_schema(auto_id=True, enable_dynamic_field=True)
    schema.add_field("id", DataType.INT64, is_primary=True)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=dim)
    schema.add_field("text", DataType.VARCHAR, max_length=65535)
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="vector",
        index_type="AUTOINDEX",
        metric_type="COSINE",
    )
    client.create_collection(
        collection_name=COLLECTION_NAME,
        schema=schema,
        index_params=index_params,
    )
    client.load_collection(COLLECTION_NAME)
    print(f"已创建 collection: {DB_NAME}.{COLLECTION_NAME}")


def add_documents(docs: List[Document]):
    """把 Document 列表向量化后写入 Milvus。"""
    embedder = get_embedding_model()
    texts = [d.page_content for d in docs]
    vectors = embedder.embed_documents(texts)
    dim = len(vectors[0])

    client = _get_client()
    _ensure_collection(client, dim)

    data = [{"vector": v, "text": t} for v, t in zip(vectors, texts)]
    client.insert(collection_name=COLLECTION_NAME, data=data)
    client.flush(COLLECTION_NAME)   # 强制刷盘
    print(f"已插入 {len(data)} 条到 {DB_NAME}.{COLLECTION_NAME}")


def get_retriever(k: int = 5):
    """返回一个函数：输入问题，返回相关 Document 列表。"""
    client = _get_client()
    embedder = get_embedding_model()

    def retrieve(question: str) -> List[Document]:
        q_vec = embedder.embed_query(question)
        results = client.search(
            collection_name=COLLECTION_NAME,
            data=[q_vec],
            limit=k,
            output_fields=["text"],
        )
        return [Document(page_content=hit["entity"]["text"]) for hit in results[0]]

    return retrieve