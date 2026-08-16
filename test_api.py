"""
API测试模块
使用pytest和httpx对后端API进行全面的单元测试
包含：基础功能测试、边界值测试、等价类划分测试、异常处理测试
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


@pytest.fixture(scope="module")
def second_user_id(client):
    """创建第二个测试用户，用于测试用户隔离"""
    user_data = {
        "username": "test_user_2",
        "email": "test2@example.com",
        "password": "password123"
    }
    response = client.post("/users/", json=user_data)
    if response.status_code == 201:
        return response.json()["id"]
    # 用户可能已存在，尝试获取
    return 2


@pytest.fixture
def cleanup_tasks(client, test_user_id):
    """清理测试用户的所有任务（测试前后执行）"""
    # 测试前清理
    response = client.get("/tasks/", params={"user_id": test_user_id})
    if response.status_code == 200:
        for task in response.json():
            client.delete(f"/tasks/{task['id']}")

    yield  # 执行测试

    # 测试后清理
    response = client.get("/tasks/", params={"user_id": test_user_id})
    if response.status_code == 200:
        for task in response.json():
            client.delete(f"/tasks/{task['id']}")


# ==================== 用户API单元测试 ====================

class TestUserAPI:
    """用户API单元测试类"""

    def test_create_user_success(self, client):
        """测试创建用户-正常情况"""
        user_data = {
            "username": "new_user_unit",
            "email": "new_unit@example.com",
            "password": "123456"
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "created_at" in data

    def test_create_user_duplicate_username(self, client, test_user_id):
        """测试创建用户-用户名重复"""
        user_data = {
            "username": TEST_USER["username"],
            "email": "another@example.com",
            "password": "123456"
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 400

    def test_create_user_duplicate_email(self, client, test_user_id):
        """测试创建用户-邮箱重复"""
        user_data = {
            "username": "another_user",
            "email": TEST_USER["email"],
            "password": "123456"
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 400

    def test_get_user_success(self, client, test_user_id):
        """测试获取用户信息-正常情况"""
        response = client.get(f"/users/{test_user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user_id
        assert data["username"] == TEST_USER["username"]

    def test_get_user_not_found(self, client):
        """测试获取用户信息-用户不存在"""
        response = client.get("/users/999999")
        assert response.status_code == 404


# ==================== 用户边界值测试 ====================

class TestUserBoundaryValues:
    """用户API边界值测试类"""

    def test_username_min_length_valid(self, client):
        """边界值测试：用户名长度=3（最小有效值）"""
        user_data = {
            "username": "abc",  # 正好3个字符
            "email": "boundary1@example.com",
            "password": "123456"
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 201

    def test_username_below_min_length(self, client):
        """边界值测试：用户名长度=2（小于最小值）"""
        user_data = {
            "username": "ab",  # 2个字符
            "email": "boundary2@example.com",
            "password": "123456"
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 422  # 验证失败

    def test_username_max_length_valid(self, client):
        """边界值测试：用户名长度=50（最大有效值）"""
        user_data = {
            "username": "a" * 50,  # 正好50个字符
            "email": "boundary3@example.com",
            "password": "123456"
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 201

    def test_username_above_max_length(self, client):
        """边界值测试：用户名长度=51（超过最大值）"""
        user_data = {
            "username": "a" * 51,  # 51个字符
            "email": "boundary4@example.com",
            "password": "123456"
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 422

    def test_password_min_length_valid(self, client):
        """边界值测试：密码长度=6（最小有效值）"""
        user_data = {
            "username": "pwd_boundary1",
            "email": "pwdboundary1@example.com",
            "password": "123456"  # 正好6个字符
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 201

    def test_password_below_min_length(self, client):
        """边界值测试：密码长度=5（小于最小值）"""
        user_data = {
            "username": "pwd_boundary2",
            "email": "pwdboundary2@example.com",
            "password": "12345"  # 5个字符
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 422


# ==================== 用户等价类划分测试 ====================

class TestUserEquivalenceClasses:
    """用户API等价类划分测试类"""

    def test_valid_email_format(self, client):
        """等价类测试：有效邮箱格式"""
        valid_emails = [
            "user@example.com",
            "test.user@example.com",
            "user+tag@example.co.uk"
        ]
        for i, email in enumerate(valid_emails):
            user_data = {
                "username": f"email_valid_{i}",
                "email": email,
                "password": "123456"
            }
            response = client.post("/users/", json=user_data)
            assert response.status_code == 201

    def test_invalid_email_format(self, client):
        """等价类测试：无效邮箱格式"""
        invalid_emails = [
            "not_an_email",
            "@example.com",
            "user@",
            "user@.com",
            ""
        ]
        for i, email in enumerate(invalid_emails):
            user_data = {
                "username": f"email_invalid_{i}",
                "email": email,
                "password": "123456"
            }
            response = client.post("/users/", json=user_data)
            assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """等价类测试：缺少必填字段"""
        # 缺少用户名
        response = client.post("/users/", json={
            "email": "missing_username@example.com",
            "password": "123456"
        })
        assert response.status_code == 422

        # 缺少邮箱
        response = client.post("/users/", json={
            "username": "missing_email",
            "password": "123456"
        })
        assert response.status_code == 422

        # 缺少密码
        response = client.post("/users/", json={
            "username": "missing_password",
            "email": "missing_password@example.com"
        })
        assert response.status_code == 422

    def test_empty_request_body(self, client):
        """等价类测试：空请求体"""
        response = client.post("/users/", json={})
        assert response.status_code == 422


# ==================== 任务API单元测试 ====================

class TestTaskAPI:
    """任务API单元测试类"""

    def test_create_task_success(self, client, test_user_id, cleanup_tasks):
        """测试创建任务-正常情况"""
        task_data = {**TEST_TASK, "user_id": test_user_id}
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == TEST_TASK["title"]
        assert data["user_id"] == test_user_id
        assert data["status"] == "pending"
        assert data["priority"] == "medium"

    def test_create_task_with_deadline(self, client, test_user_id, cleanup_tasks):
        """测试创建任务-带截止时间"""
        deadline = (datetime.now() + timedelta(days=7)).isoformat()
        task_data = {
            **TEST_TASK,
            "user_id": test_user_id,
            "title": "带截止时间的任务",
            "deadline": deadline
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["deadline"] is not None

    def test_create_task_nonexistent_user(self, client):
        """测试创建任务-用户不存在"""
        task_data = {**TEST_TASK, "user_id": 999999}
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 404

    def test_get_tasks_success(self, client, test_user_id, cleanup_tasks):
        """测试获取任务列表-正常情况"""
        # 先创建几个任务
        for i in range(3):
            client.post("/tasks/", json={
                **TEST_TASK,
                "user_id": test_user_id,
                "title": f"任务_{i}"
            })

        response = client.get("/tasks/", params={"user_id": test_user_id})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        for task in data:
            assert task["user_id"] == test_user_id

    def test_get_task_success(self, client, test_user_id, cleanup_tasks):
        """测试获取单个任务-正常情况"""
        create_response = client.post("/tasks/", json={
            **TEST_TASK,
            "user_id": test_user_id,
            "title": "单个任务测试"
        })
        task_id = create_response.json()["id"]

        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "单个任务测试"

    def test_get_task_not_found(self, client):
        """测试获取单个任务-任务不存在"""
        response = client.get("/tasks/999999")
        assert response.status_code == 404

    def test_update_task_success(self, client, test_user_id, cleanup_tasks):
        """测试更新任务-正常情况"""
        create_response = client.post("/tasks/", json={
            **TEST_TASK,
            "user_id": test_user_id,
            "title": "更新测试"
        })
        task_id = create_response.json()["id"]

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

    def test_update_task_partial(self, client, test_user_id, cleanup_tasks):
        """测试更新任务-部分更新"""
        create_response = client.post("/tasks/", json={
            **TEST_TASK,
            "user_id": test_user_id,
            "title": "部分更新测试",
            "priority": "low"
        })
        task_id = create_response.json()["id"]

        # 只更新状态
        update_data = {"status": "completed"}
        response = client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["priority"] == "low"  # 优先级应保持不变

    def test_update_task_not_found(self, client):
        """测试更新任务-任务不存在"""
        response = client.put("/tasks/999999", json={"title": "新标题"})
        assert response.status_code == 404

    def test_delete_task_success(self, client, test_user_id, cleanup_tasks):
        """测试删除任务-正常情况"""
        create_response = client.post("/tasks/", json={
            **TEST_TASK,
            "user_id": test_user_id,
            "title": "删除测试"
        })
        task_id = create_response.json()["id"]

        response = client.delete(f"/tasks/{task_id}")
        assert response.status_code == 204

        # 验证任务已删除
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 404

    def test_delete_task_not_found(self, client):
        """测试删除任务-任务不存在"""
        response = client.delete("/tasks/999999")
        assert response.status_code == 404


# ==================== 任务边界值测试 ====================

class TestTaskBoundaryValues:
    """任务API边界值测试类"""

    def test_title_min_length_valid(self, client, test_user_id, cleanup_tasks):
        """边界值测试：任务标题长度=1（最小有效值）"""
        task_data = {
            **TEST_TASK,
            "user_id": test_user_id,
            "title": "a"  # 1个字符
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 201

    def test_title_empty_string(self, client, test_user_id, cleanup_tasks):
        """边界值测试：任务标题为空字符串"""
        task_data = {
            **TEST_TASK,
            "user_id": test_user_id,
            "title": ""
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 422

    def test_title_whitespace_only(self, client, test_user_id, cleanup_tasks):
        """边界值测试：任务标题只有空格"""
        task_data = {
            **TEST_TASK,
            "user_id": test_user_id,
            "title": "   "
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 422

    def test_title_max_length_valid(self, client, test_user_id, cleanup_tasks):
        """边界值测试：任务标题长度=200（最大有效值）"""
        task_data = {
            **TEST_TASK,
            "user_id": test_user_id,
            "title": "a" * 200  # 正好200个字符
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 201

    def test_title_above_max_length(self, client, test_user_id, cleanup_tasks):
        """边界值测试：任务标题长度=201（超过最大值）"""
        task_data = {
            **TEST_TASK,
            "user_id": test_user_id,
            "title": "a" * 201  # 201个字符
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 422

    def test_deadline_past_date(self, client, test_user_id, cleanup_tasks):
        """边界值测试：截止时间为过去时间"""
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        task_data = {
            **TEST_TASK,
            "user_id": test_user_id,
            "title": "过去截止时间测试",
            "deadline": past_date
        }
        response = client.post("/tasks/", json=task_data)
        # 后端未限制过去时间，应创建成功
        assert response.status_code == 201

    def test_deadline_far_future(self, client, test_user_id, cleanup_tasks):
        """边界值测试：截止时间为很远的未来"""
        far_future = (datetime.now() + timedelta(days=36500)).isoformat()  # 100年后
        task_data = {
            **TEST_TASK,
            "user_id": test_user_id,
            "title": "远期截止时间测试",
            "deadline": far_future
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 201


# ==================== 任务等价类划分测试 ====================

class TestTaskEquivalenceClasses:
    """任务API等价类划分测试类"""

    def test_valid_priorities(self, client, test_user_id, cleanup_tasks):
        """等价类测试：有效优先级值"""
        valid_priorities = ["high", "medium", "low"]
        for priority in valid_priorities:
            task_data = {
                **TEST_TASK,
                "user_id": test_user_id,
                "title": f"优先级_{priority}",
                "priority": priority
            }
            response = client.post("/tasks/", json=task_data)
            assert response.status_code == 201
            assert response.json()["priority"] == priority

    def test_invalid_priority(self, client, test_user_id, cleanup_tasks):
        """等价类测试：无效优先级值"""
        invalid_priorities = ["urgent", "critical", "normal", "", "HIGH"]
        for priority in invalid_priorities:
            task_data = {
                **TEST_TASK,
                "user_id": test_user_id,
                "title": f"无效优先级_{priority}",
                "priority": priority
            }
            response = client.post("/tasks/", json=task_data)
            assert response.status_code == 422

    def test_valid_statuses(self, client, test_user_id, cleanup_tasks):
        """等价类测试：有效状态值"""
        valid_statuses = ["pending", "in_progress", "completed"]
        for status in valid_statuses:
            task_data = {
                **TEST_TASK,
                "user_id": test_user_id,
                "title": f"状态_{status}",
                "status": status
            }
            response = client.post("/tasks/", json=task_data)
            assert response.status_code == 201
            assert response.json()["status"] == status

    def test_invalid_status(self, client, test_user_id, cleanup_tasks):
        """等价类测试：无效状态值"""
        invalid_statuses = ["done", "todo", "processing", "", "PENDING"]
        for status in invalid_statuses:
            task_data = {
                **TEST_TASK,
                "user_id": test_user_id,
                "title": f"无效状态_{status}",
                "status": status
            }
            response = client.post("/tasks/", json=task_data)
            assert response.status_code == 422

    def test_task_with_null_description(self, client, test_user_id, cleanup_tasks):
        """等价类测试：描述为null"""
        task_data = {
            "user_id": test_user_id,
            "title": "空描述任务",
            "description": None,
            "priority": "medium",
            "status": "pending"
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 201

    def test_task_without_optional_fields(self, client, test_user_id, cleanup_tasks):
        """等价类测试：不提供可选字段"""
        task_data = {
            "user_id": test_user_id,
            "title": "最小字段任务"
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 201
        data = response.json()
        # 验证默认值
        assert data["status"] == "pending"
        assert data["priority"] == "medium"
        assert data["description"] is None
        assert data["deadline"] is None

    def test_missing_required_fields(self, client, test_user_id):
        """等价类测试：缺少必填字段"""
        # 缺少user_id
        response = client.post("/tasks/", json={
            "title": "缺少用户ID",
            "priority": "medium"
        })
        assert response.status_code == 422

        # 缺少title
        response = client.post("/tasks/", json={
            "user_id": test_user_id,
            "priority": "medium"
        })
        assert response.status_code == 422


# ==================== 任务统计API测试 ====================

class TestTaskStats:
    """任务统计API测试类"""

    def test_get_stats_success(self, client, test_user_id, cleanup_tasks):
        """测试获取统计信息-正常情况"""
        response = client.get(f"/tasks/stats/{test_user_id}")
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "completed_tasks" in data
        assert "in_progress_tasks" in data
        assert "pending_tasks" in data
        assert isinstance(data["total_tasks"], int)

    def test_stats_counts_correct(self, client, test_user_id, cleanup_tasks):
        """测试统计数量正确性"""
        # 创建特定状态的任务
        client.post("/tasks/", json={**TEST_TASK, "user_id": test_user_id, "title": "待办1", "status": "pending"})
        client.post("/tasks/", json={**TEST_TASK, "user_id": test_user_id, "title": "待办2", "status": "pending"})
        client.post("/tasks/", json={**TEST_TASK, "user_id": test_user_id, "title": "进行中1", "status": "in_progress"})
        client.post("/tasks/", json={**TEST_TASK, "user_id": test_user_id, "title": "已完成1", "status": "completed"})

        response = client.get(f"/tasks/stats/{test_user_id}")
        data = response.json()
        assert data["pending_tasks"] >= 2
        assert data["in_progress_tasks"] >= 1
        assert data["completed_tasks"] >= 1
        assert data["total_tasks"] >= 4

    def test_stats_empty_user(self, client):
        """测试获取统计信息-无任务用户"""
        response = client.get("/tasks/stats/999999")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 0
        assert data["completed_tasks"] == 0
        assert data["in_progress_tasks"] == 0
        assert data["pending_tasks"] == 0


# ==================== 筛选与排序测试 ====================

class TestTaskFilterAndSort:
    """任务筛选与排序测试类"""

    def test_filter_by_priority_high(self, client, test_user_id, cleanup_tasks):
        """测试按高优先级筛选"""
        for priority in ["high", "medium", "low"]:
            client.post("/tasks/", json={
                **TEST_TASK,
                "user_id": test_user_id,
                "title": f"优先级测试_{priority}",
                "priority": priority
            })

        response = client.get("/tasks/", params={"user_id": test_user_id, "priority": "high"})
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["priority"] == "high"

    def test_filter_by_priority_medium(self, client, test_user_id, cleanup_tasks):
        """测试按中优先级筛选"""
        for priority in ["high", "medium", "low"]:
            client.post("/tasks/", json={
                **TEST_TASK,
                "user_id": test_user_id,
                "title": f"筛选测试_{priority}",
                "priority": priority
            })

        response = client.get("/tasks/", params={"user_id": test_user_id, "priority": "medium"})
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["priority"] == "medium"

    def test_sort_by_created_at_desc(self, client, test_user_id, cleanup_tasks):
        """测试按创建时间降序排序"""
        for i in range(3):
            client.post("/tasks/", json={
                **TEST_TASK,
                "user_id": test_user_id,
                "title": f"排序测试_{i}"
            })

        response = client.get("/tasks/", params={
            "user_id": test_user_id,
            "sort_by": "created_at",
            "sort_order": "desc"
        })
        assert response.status_code == 200
        data = response.json()
        # 验证降序
        created_times = [task["created_at"] for task in data]
        assert created_times == sorted(created_times, reverse=True)

    def test_sort_by_created_at_asc(self, client, test_user_id, cleanup_tasks):
        """测试按创建时间升序排序"""
        for i in range(3):
            client.post("/tasks/", json={
                **TEST_TASK,
                "user_id": test_user_id,
                "title": f"升序测试_{i}"
            })

        response = client.get("/tasks/", params={
            "user_id": test_user_id,
            "sort_by": "created_at",
            "sort_order": "asc"
        })
        assert response.status_code == 200
        data = response.json()
        created_times = [task["created_at"] for task in data]
        assert created_times == sorted(created_times)

    def test_sort_by_deadline_asc(self, client, test_user_id, cleanup_tasks):
        """测试按截止时间升序排序"""
        deadlines = [
            datetime.now() + timedelta(days=3),
            datetime.now() + timedelta(days=1),
            datetime.now() + timedelta(days=2)
        ]
        for i, deadline in enumerate(deadlines):
            client.post("/tasks/", json={
                **TEST_TASK,
                "user_id": test_user_id,
                "title": f"截止排序_{i}",
                "deadline": deadline.isoformat()
            })

        response = client.get("/tasks/", params={
            "user_id": test_user_id,
            "sort_by": "deadline",
            "sort_order": "asc"
        })
        assert response.status_code == 200
        data = response.json()
        deadlines_from_response = [task["deadline"] for task in data if task["deadline"]]
        assert deadlines_from_response == sorted(deadlines_from_response)


# ==================== 用户任务隔离测试 ====================

class TestUserIsolation:
    """用户任务隔离测试类"""

    def test_user_isolation(self, client, test_user_id, second_user_id, cleanup_tasks):
        """测试用户任务隔离-不同用户任务互不干扰"""
        # 为用户1创建任务
        client.post("/tasks/", json={
            **TEST_TASK,
            "user_id": test_user_id,
            "title": "用户1的任务"
        })

        # 为用户2创建任务
        client.post("/tasks/", json={
            **TEST_TASK,
            "user_id": second_user_id,
            "title": "用户2的任务"
        })

        # 获取用户1的任务
        response1 = client.get("/tasks/", params={"user_id": test_user_id})
        assert response1.status_code == 200
        tasks1 = response1.json()
        for task in tasks1:
            assert task["user_id"] == test_user_id

        # 获取用户2的任务
        response2 = client.get("/tasks/", params={"user_id": second_user_id})
        assert response2.status_code == 200
        tasks2 = response2.json()
        for task in tasks2:
            assert task["user_id"] == second_user_id

    def test_stats_isolation(self, client, test_user_id, second_user_id, cleanup_tasks):
        """测试统计信息隔离"""
        # 为用户1创建任务
        client.post("/tasks/", json={**TEST_TASK, "user_id": test_user_id, "title": "隔离统计测试"})

        # 获取用户2的统计
        stats2 = client.get(f"/tasks/stats/{second_user_id}").json()

        # 用户2的统计不应包含用户1的任务
        response1 = client.get("/tasks/", params={"user_id": test_user_id})
        user1_tasks = response1.json()

        assert stats2["total_tasks"] != len(user1_tasks) or len(user1_tasks) == 0


# ==================== 健康检查测试 ====================

class TestHealthCheck:
    """健康检查测试类"""

    def test_health_check_success(self, client):
        """测试健康检查接口"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data


# ==================== 异常处理测试 ====================

class TestErrorHandling:
    """异常处理测试类"""

    def test_invalid_json_body(self, client, test_user_id):
        """测试无效JSON请求体"""
        response = client.post(
            "/tasks/",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_user_id_param(self, client):
        """测试缺少必填查询参数"""
        response = client.get("/tasks/")
        assert response.status_code == 422

    def test_invalid_user_id_type(self, client):
        """测试无效的用户ID类型"""
        response = client.get("/tasks/", params={"user_id": "not_a_number"})
        assert response.status_code == 422

    def test_task_id_nonexistent(self, client):
        """测试访问不存在的任务ID"""
        response = client.get("/tasks/0")
        assert response.status_code == 404

    def test_user_id_nonexistent(self, client):
        """测试访问不存在的用户ID"""
        response = client.get("/users/0")
        assert response.status_code == 404


# ==================== 任务状态流转测试 ====================

class TestTaskStatusTransition:
    """任务状态流转测试类"""

    def test_full_lifecycle(self, client, test_user_id, cleanup_tasks):
        """测试任务完整生命周期：创建→待办→进行中→已完成"""
        # 创建任务
        create_response = client.post("/tasks/", json={
            **TEST_TASK,
            "user_id": test_user_id,
            "title": "生命周期测试",
            "status": "pending"
        })
        task_id = create_response.json()["id"]
        assert create_response.json()["status"] == "pending"

        # 更新为进行中
        response = client.put(f"/tasks/{task_id}", json={"status": "in_progress"})
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"

        # 更新为已完成
        response = client.put(f"/tasks/{task_id}", json={"status": "completed"})
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_status_revert(self, client, test_user_id, cleanup_tasks):
        """测试任务状态回退：已完成→待办"""
        # 创建已完成任务
        create_response = client.post("/tasks/", json={
            **TEST_TASK,
            "user_id": test_user_id,
            "title": "状态回退测试",
            "status": "completed"
        })
        task_id = create_response.json()["id"]

        # 回退为待办
        response = client.put(f"/tasks/{task_id}", json={"status": "pending"})
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_update_all_fields(self, client, test_user_id, cleanup_tasks):
        """测试更新任务所有字段"""
        create_response = client.post("/tasks/", json={
            **TEST_TASK,
            "user_id": test_user_id,
            "title": "全字段更新测试"
        })
        task_id = create_response.json()["id"]

        new_deadline = (datetime.now() + timedelta(days=5)).isoformat()
        update_data = {
            "title": "全新标题",
            "description": "全新描述",
            "status": "in_progress",
            "priority": "high",
            "deadline": new_deadline
        }
        response = client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "全新标题"
        assert data["description"] == "全新描述"
        assert data["status"] == "in_progress"
        assert data["priority"] == "high"


if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v", "--tb=short"])
