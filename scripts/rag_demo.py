"""命令行 RAG 问答测试（流式）。"""
import time
from src.rag.chain import build_rag_chain

print(">>> 预加载 Rerank 模型...")
from src.rag.reranker import get_reranker
get_reranker()
print(">>> Rerank OK")

# chain = build_rag_chain()
# 改成开启混合检索：
print(">>> 构建混合检索链...")
chain = build_rag_chain(k=5, fetch_k=20, use_rerank=True, use_hybrid=True)

while True:
    q = input("\n问题: ")
    if q.lower() in ["exit", "quit", "退出"]:
        break

    t0 = time.time()
    print("回答: ", end="", flush=True)
    chain(q)
    t1 = time.time()
    print(f"[总耗时 {t1-t0:.2f}s]")