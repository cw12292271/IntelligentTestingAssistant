"""pytest 共享 fixture：覆盖外部依赖。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api import app, get_db
from src.db_models import Base

# ---- 关键：StaticPool + 同一个连接，让内存库跨会话可见 ----
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,          # 所有会话复用同一个连接
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# 建表（在唯一的那条连接上）
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class FakeConversation:
    def invoke(self, inputs, config=None):
        msg = inputs.get("input", "")
        class Resp:
            content = f"[测试回复] 收到：{msg}"
        return Resp()


@pytest.fixture
def client():
    import src.api as api_module
    api_module.conversation = FakeConversation()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()