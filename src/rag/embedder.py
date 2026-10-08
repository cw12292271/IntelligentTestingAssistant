"""向量化：豆包 embedding（必须关掉 check_embedding_ctx_length）。"""
import os
from dotenv import load_dotenv
from langchain.embeddings import Embeddings, init_embeddings
# from langchain_openai import OpenAIEmbeddings

load_dotenv(override=True)

def get_embedding_model() -> Embeddings :
    return init_embeddings (
        model= f"openai:{os.getenv('ARK_EMBEDDING_MODEL')}",   # ep- 接入点 ID
        api_key=os.getenv("ARK_API_KEY"),
        base_url=os.getenv("ARK_BASE_URL"),
        check_embedding_ctx_length=False,          # 关键
    )