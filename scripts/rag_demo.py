"""命令行 RAG 问答测试。"""
from src.rag.chain import build_rag_chain

chain = build_rag_chain()

while True:
    q = input("\n问题: ")
    if q.lower() in ["exit", "quit", "退出"]:
        break
    print("回答:", chain(q))