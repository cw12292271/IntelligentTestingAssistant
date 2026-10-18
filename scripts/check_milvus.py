"""验证 Milvus 数据状态：库、collection、条数、样例。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pymilvus import MilvusClient

MILVUS_URI = "http://localhost:19530"
DB_NAME = "rag_ita"
COLLECTION_NAME = "test_knowledge"



def main():
    print("=" * 60)
    print("Milvus 数据状态验证")
    print("=" * 60)

    # 1. 连接 Milvus
    try:
        client_root = MilvusClient(uri=MILVUS_URI)
        databases = client_root.list_databases()
        print(f"\n✅ Milvus 连接成功")
        print(f"   所有数据库: {databases}")
    except Exception as e:
        print(f"\n❌ Milvus 连接失败: {e}")
        return

    # 2. 检查 rag_ita 库
    if DB_NAME not in databases:
        print(f"\n❌ 数据库 {DB_NAME} 不存在")
        print(f"   请先执行: python -c \"from pymilvus import MilvusClient; MilvusClient(uri='{MILVUS_URI}').create_database('{DB_NAME}')\"")
        return
    print(f"\n✅ 数据库 {DB_NAME} 存在")

    # 3. 连接 rag_ita 库
    client = MilvusClient(uri=MILVUS_URI, db_name=DB_NAME)

    # 4. 检查 collection
    collections = client.list_collections()
    print(f"\n   {DB_NAME} 库的 collection: {collections}")

    if COLLECTION_NAME not in collections:
        print(f"\n❌ collection {COLLECTION_NAME} 不存在")
        print(f"   请先执行: python -m scripts.build_knowledge_base")
        return
    print(f"✅ collection {COLLECTION_NAME} 存在")

    # 5. 统计条数
    stats = client.get_collection_stats(COLLECTION_NAME)
    row_count = stats.get("row_count", 0)
    print(f"\n✅ {COLLECTION_NAME} 共有 {row_count} 条数据")

    if row_count == 0:
        print(f"\n⚠️  数据为空，请重新入库: python -m scripts.build_knowledge_base")
        return

    # 6. 抽样查看前 3 条
    print(f"\n{'=' * 60}")
    print("数据样例（前 3 条）")
    print(f"{'=' * 60}")

    try:
        results = client.query(
            collection_name=COLLECTION_NAME,
            filter="",
            output_fields=["text"],
            limit=3,
        )
        for i, r in enumerate(results, 1):
            text = r.get("text", "")[:200]
            print(f"\n[第 {i} 条]")
            print(f"  {text}...")
    except Exception as e:
        print(f"\n⚠️  抽样查询失败: {e}")

    # 7. 验证 collection schema
    print(f"\n{'=' * 60}")
    print("Collection Schema")
    print(f"{'=' * 60}")
    try:
        desc = client.describe_collection(COLLECTION_NAME)
        for field in desc.get("fields", []):
            name = field.get("name")
            dtype = field.get("type")
            params = field.get("params", {})
            print(f"  {name}: {dtype} {params}")
    except Exception as e:
        print(f"⚠️  获取 schema 失败: {e}")

    # 8. 总结
    print(f"\n{'=' * 60}")
    print("✅ 验证完成")
    print(f"{'=' * 60}")
    print(f"  数据库: {DB_NAME}")
    print(f"  Collection: {COLLECTION_NAME}")
    print(f"  数据条数: {row_count}")
    print(f"\n  下一步: python -m scripts.rag_demo")


if __name__ == "__main__":
    main()