"""对话记录的读写操作。"""
from typing import List
from sqlalchemy.orm import Session
from src.db_models import DialogueTurn

def save_turn(db: Session, session_id: str, role: str, content: str) -> None:
    """保存一轮对话（用户或助手）"""
    turn = DialogueTurn(session_id=session_id, role=role, content=content)
    db.add(turn)
    db.commit()

def get_history(db: Session, session_id: str, limit: int = 50) -> List[DialogueTurn]:
    """按时间顺序查询某个会话的历史记录"""
    return (
        db.query(DialogueTurn)
        .filter(DialogueTurn.session_id == session_id)
        .order_by(DialogueTurn.created_at.asc())
        .limit(limit)
        .all()
    )