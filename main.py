"""
FastAPI主应用模块
实现RESTful API路由，处理任务和用户的CRUD操作
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from passlib.context import CryptContext
from datetime import datetime
import models
import schemas
from database import engine, get_db

# 创建数据库表（如果不存在）
models.Base.metadata.create_all(bind=engine)

# 初始化FastAPI应用
app = FastAPI(
    title="任务管理系统API",
    description="支持用户任务隔离、任务全生命周期管理的RESTful API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI文档地址
    redoc_url="/redoc"  # ReDoc文档地址
)

# CORS配置：允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（生产环境应限制特定域名）
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """对密码进行哈希加密"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否正确"""
    return pwd_context.verify(plain_password, hashed_password)


# ==================== 用户相关路由 ====================

@app.post("/api/users/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    创建新用户
    - user_id由系统自动生成
    - 用户名和邮箱必须唯一
    - 密码会进行哈希加密存储
    """
    # 检查用户名是否已存在
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被注册"
        )

    # 检查邮箱是否已存在
    db_email = db.query(models.User).filter(models.User.email == user.email).first()
    if db_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 创建新用户
    hashed_password = hash_password(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/api/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取指定用户的信息"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


# ==================== 任务相关路由 ====================

@app.post("/api/tasks/", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    """
    创建新任务
    - user_id: 任务所属用户ID（实现用户任务隔离）
    - title: 任务标题（必填）
    - description: 任务描述（可选）
    - status: 任务状态，默认为待办(pending)
    - priority: 任务优先级，默认为中(medium)
    - deadline: 截止时间（可选）
    """
    # 检查用户是否存在
    db_user = db.query(models.User).filter(models.User.id == task.user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 创建新任务
    new_task = models.Task(**task.dict())
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@app.get("/api/tasks/", response_model=list[schemas.TaskResponse])
def get_tasks(
    user_id: int = Query(..., description="用户ID，用于筛选该用户的任务"),
    priority: str = Query(None, description="按优先级筛选：high/medium/low"),
    sort_by: str = Query("created_at", description="排序字段：created_at/deadline"),
    sort_order: str = Query("desc", description="排序顺序：asc/desc"),
    db: Session = Depends(get_db)
):
    """
    获取用户的任务列表（支持筛选和排序）
    - user_id: 必须指定，实现用户任务隔离
    - priority: 可选，按优先级筛选
    - sort_by: 排序字段，默认为创建时间
    - sort_order: 排序顺序，默认为降序
    """
    # 构建查询：只查询指定用户的任务
    query = db.query(models.Task).filter(models.Task.user_id == user_id)

    # 按优先级筛选
    if priority and priority in ["high", "medium", "low"]:
        query = query.filter(models.Task.priority == priority)

    # 排序处理
    sort_field = getattr(models.Task, sort_by, models.Task.created_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(asc(sort_field))

    return query.all()


@app.get("/api/tasks/{task_id}", response_model=schemas.TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """获取单个任务的详细信息"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    return task


@app.put("/api/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db)):
    """
    更新任务信息
    - 支持修改标题、描述、状态、优先级、截止时间
    - 只更新提供的字段，未提供的字段保持不变
    """
    # 查找任务
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 更新任务字段
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除指定任务"""
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    db.delete(db_task)
    db.commit()
    return {"detail": "任务删除成功"}


@app.get("/api/tasks/stats/{user_id}", response_model=schemas.TaskStatsResponse)
def get_task_stats(user_id: int, db: Session = Depends(get_db)):
    """
    获取用户任务统计信息
    - total_tasks: 总任务数
    - completed_tasks: 已完成任务数
    - in_progress_tasks: 进行中任务数
    - pending_tasks: 待办任务数
    """
    # 统计总任务数
    total_tasks = db.query(models.Task).filter(models.Task.user_id == user_id).count()

    # 统计各状态任务数
    completed_tasks = db.query(models.Task).filter(
        models.Task.user_id == user_id,
        models.Task.status == models.TaskStatus.COMPLETED
    ).count()

    in_progress_tasks = db.query(models.Task).filter(
        models.Task.user_id == user_id,
        models.Task.status == models.TaskStatus.IN_PROGRESS
    ).count()

    pending_tasks = db.query(models.Task).filter(
        models.Task.user_id == user_id,
        models.Task.status == models.TaskStatus.PENDING
    ).count()

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "pending_tasks": pending_tasks
    }


# 健康检查接口
@app.get("/health")
def health_check():
    """健康检查接口，用于验证服务是否正常运行"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
