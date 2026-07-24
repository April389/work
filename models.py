"""
SQLAlchemy数据模型模块
定义任务和用户相关的数据库表结构
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.sql import func
from database import Base


# 任务状态枚举
class TaskStatus(str, Enum):
    """任务状态枚举类"""
    PENDING = "pending"      # 待办
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成


# 任务优先级枚举
class TaskPriority(str, Enum):
    """任务优先级枚举类"""
    HIGH = "high"    # 高优先级
    MEDIUM = "medium"  # 中优先级
    LOW = "low"      # 低优先级


class User(Base):
    """
    用户模型类
    每个用户拥有独立的任务列表，实现用户任务隔离
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Task(Base):
    """
    任务模型类
    支持任务全生命周期管理
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)  # 关联用户，实现任务隔离
    title = Column(String(200), nullable=False)  # 任务标题
    description = Column(Text, nullable=True)  # 任务描述
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)  # 任务状态
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)  # 优先级
    deadline = Column(DateTime(timezone=True), nullable=True)  # 截止时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 更新时间

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"
