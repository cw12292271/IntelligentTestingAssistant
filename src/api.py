"""FastAPI 路由：把 W6 的对话链包成 HTTP 接口。"""
from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session
from src.chain import conversation
from src.crud import save_turn, get_history
from src.db_models import Base
from src.database import SessionLocal, engine
from src.models import ChatRequest, ChatResponse



from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
import os


# 建表
Base.metadata.create_all(bind=engine)

# 定义从请求头哪个字段读取 Key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# 验证函数
async def verify_api_key(api_key: str = Security(api_key_header)):
    # 从环境变量读取你预设的密钥（不要硬编码在代码里！）
    expected_key = os.getenv("MY_API_KEY")
    if not expected_key:
        # 如果没配，开发模式直接放行（方便调试）
        return
    if api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="智能测试助手 API", version="0.1.0")

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest, 
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)):
    """对话接口，按 session_id 隔离记忆。"""
    try:
        resp = conversation.invoke(
            {"input": req.message},
            config={"configurable": {"session_id": req.session_id}},
        )
         # 落库：用户消息 + 助手回复
        save_turn(db, req.session_id, "user", req.message)
        save_turn(db, req.session_id, "assistant", resp.content)
        return ChatResponse(reply=resp.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from fastapi.responses import StreamingResponse

@app.get("/history/{session_id}")
async def history(
    session_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    turns = get_history(db, session_id)
    return {
        "session_id": session_id,
        "turns": [
            {"role": t.role, "content": t.content, "created_at": t.created_at.isoformat()}
            for t in turns
        ],
    }

async def token_stream(prompt: str, session_id: str):
    async for chunk in conversation.astream(
        {"input": prompt},
        config={"configurable": {"session_id": session_id}},
    ):
        if chunk.content:
            yield f"data: {chunk.content}\n\n"
    yield "data: [DONE]\n\n"

@app.post("/chat/stream")
async def stream_endpoint(req: ChatRequest):
    return StreamingResponse(
        token_stream(req.message, req.session_id),
        media_type="text/event-stream",
    )