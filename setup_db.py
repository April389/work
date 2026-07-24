"""
数据库初始化脚本
用于创建数据库和表结构
"""

import pymysql

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'charset': 'utf8mb4'
}

# 数据库名称
DATABASE_NAME = 'task_db'


def create_database():
    """创建数据库"""
    try:
        # 连接MySQL服务器（不指定数据库）
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"数据库 '{DATABASE_NAME}' 创建成功（如果不存在）")

        cursor.close()
        connection.close()
    except Exception as e:
        print(f"创建数据库失败: {e}")
        raise


def main():
    """主函数"""
    print("开始初始化数据库...")
    create_database()
    print("数据库初始化完成！")
    print("\n接下来运行以下命令启动应用：")
    print("1. 安装依赖: pip install -r requirements.txt")
    print("2. 启动后端: python main.py")
    print("3. 打开前端: 浏览器访问 frontend/index.html")


if __name__ == "__main__":
    main()
