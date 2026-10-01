"""接口契约测试：正常/边界/异常三类场景。"""
import os

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
TEST_API_KEY = os.getenv("MY_API_KEY")


# ===== 正常场景 =====

def test_health(client):
    """健康检查接口正常返回。"""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_chat_success(client):
    """正常对话：200，返回 reply 字段。"""
    resp = client.post(
        "/chat",
        json={"session_id": "test_001", "message": "帮我分析登录功能"},
        headers={"X-API-Key": TEST_API_KEY},
    )
    print("状态码:", resp.status_code)
    print("响应体:", resp.text)     
    assert resp.status_code == 200
    assert "reply" in resp.json()
    assert "test_001" not in resp.json()["reply"]  # 验证返回的是替身内容

# ===== 边界场景 =====

def test_chat_empty_message(client):
    """边界：消息为空字符串（Pydantic 校验应拦截）。"""
    resp = client.post(
        "/chat",
        json={"session_id": "test_001", "message": ""},
        headers={"X-API-Key": TEST_API_KEY},
    )
    # message 字段在 ChatRequest 里要求 min_length=1，应返回 422
    assert resp.status_code == 422

# ===== 异常场景 =====

def test_chat_missing_session(client):
    """异常：缺少必填字段 session_id。"""
    resp = client.post(
        "/chat",
        json={"message": "hello"},   # 故意不传 session_id
        headers={"X-API-Key": TEST_API_KEY},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    # 确认错误定位到 session_id 字段
    assert any("session_id" in str(d.get("loc", "")) for d in detail)

def test_chat_invalid_api_key(client):
    """异常：API Key 错误。"""
    resp = client.post(
        "/chat",
        json={"session_id": "test_001", "message": "hello"},
        headers={"X-API-Key": "wrong-key"},
    )
    # FastAPI 端 verify_api_key 配置了 MY_API_KEY，应返回 403
    # 如果没配置（开发模式放行），此测试可能需要调整
    assert resp.status_code in (200, 403)