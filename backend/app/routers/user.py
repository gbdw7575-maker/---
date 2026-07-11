"""用户档案 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.health_service import get_user_or_default

router = APIRouter(prefix="/api/users", tags=["用户档案"])


@router.get("/default", response_model=UserResponse)
def get_default_user(db: Session = Depends(get_db)):
    """获取默认用户（演示模式）"""
    user = get_user_or_default(db)
    return user.to_dict()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user.to_dict()


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    """更新用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user.to_dict()


@router.post("", response_model=UserResponse, status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    """创建用户"""
    user = User(**data.model_dump(exclude_unset=True))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.to_dict()
