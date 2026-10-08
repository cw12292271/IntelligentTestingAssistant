# 智能测试助手 v2

![CI](https://github.com/cw12292271/IntelligentTestingAssistant/actions/workflows/ci.yml/badge.svg)
[![ModelScope](https://img.shields.io/badge/🤖-魔搭创空间-blue)](https://cw12292271-intelligenttestingassistant.ms.show/docs)
[![GitHub](https://img.shields.io/badge/GitHub-源码-black)](https://github.com/cw12292271/IntelligentTestingAssistant)

> 基于 LangChain 1.x + FastAPI 的 AI 测试助手，支持多轮对话、结构化用例生成、RAG 评测。
## RAG 功能
- 支持本地文档加载、切分、向量化、检索、生成全链路
- 向量库：Milvus（自封装 MilvusClient，绕开 langchain-milvus 兼容问题）
- Embedding：豆包 doubao-embedding
- 检索质量：5/5 测试问题准确回答
- 实验记录见 `docs/rag_experiment_log.md`