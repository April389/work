"""
数据库配置模块
负责建立SQLAlchemy数据库连接和会话管理
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# MySQL数据库连接URL
# 格式: mysql+pymysql://用户名:密码@主机:端口/数据库名
# 注意：确保MySQL服务已启动，且已创建task_db数据库
DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/task_db"

# 创建数据库引擎
# connect_args={"check_same_thread": False} 用于SQLite，MySQL不需要
engine = create_engine(
    DATABASE_URL,
    # MySQL连接池配置
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False  # 设置为True可打印SQL语句，便于调试
)

# 创建数据库会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建模型基类
Base = declarative_base()


def get_db():
    """
    依赖注入函数：获取数据库会话
    使用yield实现上下文管理，确保会话正确关闭
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
