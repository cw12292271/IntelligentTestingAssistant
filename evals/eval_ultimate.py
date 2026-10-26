import os
import re
import json
import warnings
import time
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from langchain.rate_limiters import InMemoryRateLimiter
from langchain_openai import ChatOpenAI

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.rag.vectorstore import get_retriever
from src.rag.reranker import rerank
from src.rag.hybrid_retriever import build_hybrid_retriever
from src.rag.chain import RAG_PROMPT
from src.llm import get_llm

warnings.filterwarnings("ignore")
_ = load_dotenv(find_dotenv(), override=True)

# ==========================================
# 限流器（防止打分时触发 429 报错）
# ==========================================
rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.5, 
    check_every_n_seconds=0.1, 
    max_bucket_size=2,
)


# ==========================================
# 业务答题模型：用大参数模型（如 Qwen 72B）
# ==========================================
business_llm = ChatOpenAI(
    model="Qwen/Qwen2.5-72B-Instruct",  # 答题目建议选大参数模型，思考更深入
    api_key=os.getenv("SILICONFLOW_API_KEY"),
    base_url=os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"),
    temperature=0.7,
    max_tokens=512
)


judge_llm = ChatOpenAI(
    model="Qwen/Qwen2.5-7B-Instruct",
    api_key=os.getenv("SILICONFLOW_API_KEY"),
    base_url=os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"),
    temperature=0,
    max_tokens=500,
    timeout=30 
)

def run_rag(question, use_hybrid=True):
    if use_hybrid:
        hybrid_retriever = build_hybrid_retriever(k=8, fetch_k=20)
        docs = hybrid_retriever.invoke(question)
    else:
        pure_retriever = get_retriever(k=5)
        docs = pure_retriever(question)
        
    contexts = [d.page_content for d in docs]
    context_str = "\n\n".join(contexts)
    prompt = RAG_PROMPT.format_messages(context=context_str, question=question)
    # answer = get_llm().invoke(prompt).content
    answer = business_llm.invoke(prompt).content 
    return answer, context_str, contexts

# ================= 4 个指标的裁判逻辑 =================

def judge_faithfulness(context, answer):
    """忠实度：打分 0.0 ~ 1.0"""
    prompt = f"""请评估【回答】是否完全基于【上下文】得出。
评分标准：
- 1.0分：回答的每一句都能在上下文中找到依据。
- 0.5分：回答部分基于上下文，但有少许推测或遗漏。
- 0.0分：回答完全是胡编乱造，或上下文未提供相关信息。
请只输出一个 0.0 到 1.0 之间的浮点数数字，不要输出任何其他文字。
【上下文】：{context[:2000]}
【回答】：{answer}"""
    try:
        res = judge_llm.invoke(prompt).content.strip()
        # 用正则提取数字
        match = re.search(r'(\d+(\.\d+)?)', res)
        return float(match.group(1)) if match else 0.0
    except:
        return 0.0

def judge_answer_relevancy(question, answer):
    """答案相关性：打分 0.0 ~ 1.0"""
    prompt = f"""请评估【回答】是否直接切中了【问题】的核心。
评分标准：
- 1.0分：完全切题，直接回答了问题。
- 0.5分：部分切题，但有偏题或冗余。
- 0.0分：答非所问。
请只输出一个 0.0 到 1.0 之间的浮点数数字，不要输出任何其他文字。
【问题】：{question}
【回答】：{answer}"""
    try:
        res = judge_llm.invoke(prompt).content.strip()
        match = re.search(r'(\d+(\.\d+)?)', res)
        return float(match.group(1)) if match else 0.0
    except:
        return 0.0

def judge_context_recall(context, ground_truth):
    """上下文召回率：打分 0.0 ~ 1.0"""
    prompt = f"""请判断【上下文】中是否包含了【标准答案】所表达的核心业务事实（比如相同的功能、相同的异常场景、相同的修复手段）。
注意：如果上下文中使用了同义词、中文解释或不同的表达方式，只要语义等同于标准答案，也算作“包含”。
请只输出一个 0.0 到 1.0 之间的浮点数数字。
【标准答案】：{ground_truth}
【上下文】：{context[:2000]}"""
    try:
        res = judge_llm.invoke(prompt).content.strip()
        match = re.search(r'(\d+(\.\d+)?)', res)
        return float(match.group(1)) if match else 0.0
    except:
        return 0.0

def judge_context_precision(question, contexts):
    """上下文精度：打分 0.0 ~ 1.0"""
    context_str = "\n".join(contexts[:3])
    prompt = f"""请评估前3段【上下文】内容与【问题】的相关程度。
评分标准：
- 1.0分：3段内容高度相关，没有废话。
- 0.5分：有部分相关内容，但也夹杂了无关信息。
- 0.0分：全是无关废话。
请只输出一个 0.0 到 1.0 之间的浮点数数字，不要输出任何其他文字。
【问题】：{question}
【上下文】：{context_str[:2000]}"""
    try:
        res = judge_llm.invoke(prompt).content.strip()
        match = re.search(r'(\d+(\.\d+)?)', res)
        return float(match.group(1)) if match else 0.0
    except:
        return 0.0

def main():
    eval_file = Path(__file__).parent / "eval_set.json"
    with open(eval_file, "r", encoding="utf-8") as f:
        data = json.load(f)  # 20 题

    modes = {"纯向量": False, "混合检索": True}
    final_results = {}

    for mode_name, use_hybrid in modes.items():
        print(f"\n▶ 开始测试模式: {mode_name} ...")
        metrics = {"faithfulness": [], "answer_relevancy": [], "context_recall": [], "context_precision": []}
        
        for i, item in enumerate(data):
            q = item["question"]
            gt = item["ground_truth"]
            print(f"  [{i+1}/{len(data)}] 题目: {q[:15]}...", end="", flush=True)
            
            try:
                ans, ctx, ctx_list = run_rag(q, use_hybrid=use_hybrid)
                
                f_score = judge_faithfulness(ctx, ans)
                ar_score = judge_answer_relevancy(q, ans)
                r_score = judge_context_recall(ctx, gt)
                p_score = judge_context_precision(q, ctx_list)
                
                metrics["faithfulness"].append(f_score)
                metrics["answer_relevancy"].append(ar_score)
                metrics["context_recall"].append(r_score)
                metrics["context_precision"].append(p_score)
                
                print(f" => F:{f_score} AR:{ar_score} R:{r_score} P:{p_score}")
                
            except Exception as e:
                print(f" => ❌ 失败: {e}")
                for k in metrics: metrics[k].append(0.0)
            
            time.sleep(1)

        final_results[mode_name] = {
            k: sum(v) / len(v) if v else 0 for k, v in metrics.items()
        }

    print("\n" + "="*70)
    print("🏆 RAG 系统全量 4 指标评测对比报告 (20 题)")
    print("="*70)
    print(f"| {'指标':<20} | {'纯向量':<10} | {'混合检索+Rerank':<15} |")
    print(f"|{'-'*22}|{'-'*12}|{'-'*17}|")
    
    for m in ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]:
        print(f"| {m:<20} | {final_results['纯向量'][m]:.4f}     | {final_results['混合检索'][m]:.4f}          |")

if __name__ == "__main__":
    main()