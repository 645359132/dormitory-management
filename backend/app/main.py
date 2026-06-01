"""
学生宿舍管理系统 - FastAPI 应用工厂模块
===============================
负责创建和配置 FastAPI 应用实例，包括 CORS 中间件、全局异常处理和路由注册。
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .db import DatabaseUnavailable
from .routes import router


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例，设置 CORS、异常处理器和路由。"""
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    # 配置 CORS 跨域中间件，允许前端开发服务器访问后端 API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 全局异常处理器：数据库不可用时返回 503 状态码
    @app.exception_handler(DatabaseUnavailable)
    async def database_unavailable_handler(
        _: Request,
        exc: DatabaseUnavailable,
    ) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    # 注册所有 API 路由
    app.include_router(router)
    return app


# 创建全局应用实例，供 uvicorn 启动使用
app = create_app()
