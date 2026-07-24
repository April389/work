"""
Pydantic数据模式模块
用于API请求和响应的数据验证与格式约束
"""

from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional
from models import TaskStatus, TaskPriority


class UserCreate(BaseModel):
    """用户创建请求模式"""
    username: str
    email: EmailStr  # 自动验证邮箱格式
    password: str

    @field_validator('username')
    def validate_username(cls, v):
        """验证用户名长度"""
        if len(v) < 3 or len(v) > 50:
            raise ValueError('用户名长度必须在3-50个字符之间')
        return v

    @field_validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 6:
            raise ValueError('密码长度至少6个字符')
        return v


class UserResponse(BaseModel):
    """用户响应模式"""
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True  # 支持从ORM模型转换


class TaskCreate(BaseModel):
    """任务创建请求模式"""
    user_id: int
    title: str
    description: Optional[str] = None
    status: Optional[TaskStatus] = TaskStatus.PENDING
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM
    deadline: Optional[datetime] = None

    @field_validator('title')
    def validate_title(cls, v):
        """验证任务标题"""
        if not v or len(v.strip()) == 0:
            raise ValueError('任务标题不能为空')
        if len(v) > 200:
            raise ValueError('任务标题长度不能超过200个字符')
        return v


class TaskUpdate(BaseModel):
    """任务更新请求模式"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    deadline: Optional[datetime] = None


class TaskResponse(BaseModel):
    """任务响应模式"""
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    deadline: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # 支持从ORM模型转换


class TaskStatsResponse(BaseModel):
    """任务统计响应模式"""
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    pending_tasks: int


class TaskFilter(BaseModel):
    """任务筛选参数模式"""
    priority: Optional[TaskPriority] = None
    sort_by: Optional[str] = 'created_at'  # created_at, deadline, priority
    sort_order: Optional[str] = 'desc'  # asc, desc
