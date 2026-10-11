# """命令行 RAG 问答测试。"""
# from src.rag.chain import build_rag_chain

# chain = build_rag_chain()

# while True:
#     q = input("\n问题: ")
#     if q.lower() in ["exit", "quit", "退出"]:
#         break
#     print("回答:", chain(q))

"""命令行 RAG 问答测试。"""
from src.rag.chain import build_rag_chain
from src.rag.embedder import get_embedding_model

# 1. 先测 embedding
print(">>> 测试 embedding...")
try:
    emb = get_embedding_model()
    vec = emb.embed_query("测试")
    print(f">>> embedding OK, 维度: {len(vec)}")
except Exception as e:
    print(f">>> embedding 失败: {e}")
    exit(1)

# 2. 再测检索
print(">>> 测试检索...")
try:
    from src.rag.vectorstore import get_retriever
    retriever = get_retriever(k=3)
    docs = retriever("测试")
    print(f">>> 检索 OK, 返回 {len(docs)} 个文档")
except Exception as e:
    print(f">>> 检索失败: {e}")
    exit(1)

# 3. 跑完整链
chain = build_rag_chain()
while True:
    q = input("\n问题: ")
    if q.lower() in ["exit", "quit", "退出"]:
        break
    print("回答:", chain(q))