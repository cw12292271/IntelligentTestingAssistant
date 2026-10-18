"""测试混合检索。"""
from src.rag.chain import build_rag_chain

print(">>> 构建混合检索链...")
chain = build_rag_chain(k=5, fetch_k=20, use_rerank=True, use_hybrid=True)
print(">>> 构建完成\n")

# 测试精确编号检索
questions = [
    "BUG-002 的修复方案是什么？",
    "TC-USER-001 这条用例的前置条件是什么？",
    "支付成功后订单状态没更新，是哪个 Bug？",
    "P0 优先级的测试用例有哪些？",
]

for q in questions:
    print(f"\n问题: {q}")
    print("回答: ", end="", flush=True)
    chain(q)