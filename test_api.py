"""
API测试模块
使用pytest和httpx对后端API进行单元测试
"""

import pytest
import httpx
from datetime import datetime, timedelta

# API基础URL
BASE_URL = "http://localhost:8000/api"

# 测试用户数据
TEST_USER = {
    "username": "test_user",
    "email": "test@example.com",
    "password": "123456"
}

# 测试任务数据
TEST_TASK = {
    "title": "测试任务",
    "description": "这是一个测试任务",
    "priority": "medium",
    "status": "pending"
}


@pytest.fixture(scope="module")
def client():
    """创建HTTP客户端"""
    return httpx.Client(base_url=BASE_URL)


@pytest.fixture(scope="module")
def test_user_id(client):
    """创建测试用户并返回用户ID"""
    # 尝试删除已存在的测试用户
    try:
        response = client.get("/users/", params={"username": TEST_USER["username"]})
        if response.status_code == 200:
            client.delete(f"/users/{response.json()[0]['id']}")
    except Exception:
        pass

    # 创建测试用户
    response = client.post("/users/", json=TEST_USER)
    assert response.status_code == 201
    return response.json()["id"]


class TestUserAPI:
    """用户API测试类"""

    def test_create_user(self, client):
        """测试创建用户"""
        user_data = {
            "username": "new_user",
            "email": "new@example.com",
            "password": "123456"
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data

    def test_create_user_duplicate_username(self, client, test_user_id):
        """测试创建重复用户名"""
        user_data = {
            "username": TEST_USER["username"],
            "email": "another@example.com",
            "password": "123456"
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 400

    def test_get_user(self, client, test_user_id):
        """测试获取用户信息"""
        response = client.get(f"/users/{test_user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user_id
        assert data["username"] == TEST_USER["username"]


class TestTaskAPI:
    """任务API测试类"""

    def test_create_task(self, client, test_user_id):
        """测试创建任务"""
        task_data = {**TEST_TASK, "user_id": test_user_id}
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == TEST_TASK["title"]
        assert data["user_id"] == test_user_id
        assert data["status"] == "pending"
        assert data["priority"] == "medium"

    def test_get_tasks(self, client, test_user_id):
        """测试获取任务列表"""
        response = client.get("/tasks/", params={"user_id": test_user_id})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 确保只返回该用户的任务
        for task in data:
            assert task["user_id"] == test_user_id

    def test_get_task(self, client, test_user_id):
        """测试获取单个任务"""
        # 先创建一个任务
        task_data = {**TEST_TASK, "user_id": test_user_id, "title": "单个任务测试"}
        create_response = client.post("/tasks/", json=task_data)
        task_id = create_response.json()["id"]

        # 获取任务
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "单个任务测试"

    def test_update_task(self, client, test_user_id):
        """测试更新任务"""
        # 先创建一个任务
        task_data = {**TEST_TASK, "user_id": test_user_id, "title": "更新测试"}
        create_response = client.post("/tasks/", json=task_data)
        task_id = create_response.json()["id"]

        # 更新任务
        update_data = {
            "title": "更新后的标题",
            "status": "in_progress",
            "priority": "high"
        }
        response = client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后的标题"
        assert data["status"] == "in_progress"
        assert data["priority"] == "high"

    def test_delete_task(self, client, test_user_id):
        """测试删除任务"""
        # 先创建一个任务
        task_data = {**TEST_TASK, "user_id": test_user_id, "title": "删除测试"}
        create_response = client.post("/tasks/", json=task_data)
        task_id = create_response.json()["id"]

        # 删除任务
        response = client.delete(f"/tasks/{task_id}")
        assert response.status_code == 204

        # 验证任务已删除
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 404

    def test_get_task_stats(self, client, test_user_id):
        """测试获取任务统计"""
        response = client.get(f"/tasks/stats/{test_user_id}")
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "completed_tasks" in data
        assert "in_progress_tasks" in data
        assert "pending_tasks" in data
        assert isinstance(data["total_tasks"], int)

    def test_task_filter_by_priority(self, client, test_user_id):
        """测试按优先级筛选任务"""
        # 创建不同优先级的任务
        for priority in ["high", "medium", "low"]:
            client.post("/tasks/", json={
                **TEST_TASK,
                "user_id": test_user_id,
                "title": f"优先级测试_{priority}",
                "priority": priority
            })

        # 按高优先级筛选
        response = client.get("/tasks/", params={"user_id": test_user_id, "priority": "high"})
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["priority"] == "high"

    def test_task_sort_by_deadline(self, client, test_user_id):
        """测试按截止时间排序"""
        # 创建带截止时间的任务
        deadlines = [
            datetime.now() + timedelta(days=3),
            datetime.now() + timedelta(days=1),
            datetime.now() + timedelta(days=2)
        ]
        for i, deadline in enumerate(deadlines):
            client.post("/tasks/", json={
                **TEST_TASK,
                "user_id": test_user_id,
                "title": f"排序测试_{i}",
                "deadline": deadline.isoformat()
            })

        # 按截止时间升序排序
        response = client.get("/tasks/", params={
            "user_id": test_user_id,
            "sort_by": "deadline",
            "sort_order": "asc"
        })
        assert response.status_code == 200
        data = response.json()

        # 验证排序
        deadlines_from_response = [task["deadline"] for task in data if task["deadline"]]
        assert deadlines_from_response == sorted(deadlines_from_response)


class TestHealthCheck:
    """健康检查测试类"""

    def test_health_check(self, client):
        """测试健康检查接口"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data


if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v"])
