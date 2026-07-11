"""
智能化健康管理系统 — 后端入口

启动：uvicorn main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from app.database import init_db
from app.routers import user, health, chat, ocr, classify


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库"""
    init_db()
    print(f"  {settings.APP_NAME} v{settings.APP_VERSION} 启动成功")
    print(f"  数据库: {settings.DATABASE_URL}")
    print(f"  API 文档: http://localhost:8000/docs")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI 驱动的个人健康管理平台 — 后端 API",
    lifespan=lifespan,
)

# CORS — 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(user.router)
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(ocr.router)
app.include_router(classify.router)


@app.get("/api/health")
def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
