# W12: RAG 系统自动化评测报告

## 一、 测试背景
- **被测系统**：测试知识库 RAG 系统（405 个 chunks）
- **评测基准**：20 道 Golden Set（覆盖精确编号、语义查询、跨文档、防幻觉）
- **评测方案**：纯手写 LLM-as-a-Judge（异构裁判架构）
  - **业务答题模型**：SiliconFlow - Qwen2.5-72B-Instruct
  - **裁判打分模型**：SiliconFlow - Qwen2.5-7B-Instruct（Temperature=0）

## 二、 评测结果对比

| 核心指标 | 纯向量检索 | 混合检索+Rerank | 变化趋势 |
| :--- | :--- | :--- | :--- |
| **Faithfulness（忠实度）** | 0.7000 | 0.7250 | 🔺 提升 |
| **Answer Relevancy（相关性）** | 0.8500 | 0.9500 | 🔺 显著提升 |
| **Context Recall（召回率）** | 0.4975 | 0.5950 | 🔺 显著提升 |
| **Context Precision（精度）** | 0.4550 | 0.3700 | 🔻 下降 |

## 三、 结果分析与排障复盘

1. **精确编号召回痛点被解决**
   - 在纯向量模式下，面对 `BUG-002` 等精确编号，Context Recall 为 0。
   - 引入混合检索（BM25）后，精确编号题目的 Recall 提升至 0.8 以上，Answer Relevancy 总分提升至 0.95。
2. **精度下降的原因（Trade-off）**
   - 混合检索通过 `fetch_k=20` 召回大量候选，导致部分噪音被引入 Context 中，使得 Context Precision 下降了 8.5%。
   - **优化方向**：后续将引入元数据过滤，或采用父子文档索引策略来降低噪音。
3. **裁判机制的严谨性**
   - 评测中发现，大模型在生成时会对术语进行“通俗化总结”（如把 `login_password_wrong` 归纳为“密码错误场景”），导致字面匹配出现误杀。
   - **优化方向**：调整裁判 Prompt，允许语义匹配；同时在 RAG 的 System Prompt 中强制要求“保留原始术语和编号”。