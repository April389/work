/**
 * 任务管理系统前端交互逻辑
 * 使用原生JavaScript实现，通过fetch API与后端进行数据交互
 */

// API基础配置
const API_BASE_URL = 'http://localhost:8000/api';

/**
 * API请求封装函数
 * @param {string} url - 请求URL
 * @param {string} method - HTTP方法
 * @param {Object} data - 请求数据
 * @returns {Promise} - 返回响应数据
 */
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${url}`, options);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || '请求失败');
        }

        return result;
    } catch (error) {
        console.error('API请求错误:', error);
        throw error;
    }
}

// 当前用户ID（用于任务隔离）
let currentUserId = 1;

/**
 * 初始化函数
 * 页面加载完成后执行
 */
document.addEventListener('DOMContentLoaded', function() {
    // 绑定事件
    bindEvents();

    // 加载任务列表
    loadTasks();

    // 加载统计信息
    loadStats();

    // 初始化测试数据（如果需要）
    initTestData();
});

/**
 * 绑定所有事件
 */
function bindEvents() {
    // 用户切换事件
    document.getElementById('current-user').addEventListener('change', function(e) {
        currentUserId = parseInt(e.target.value);
        loadTasks();
        loadStats();
    });

    // 添加用户按钮
    document.getElementById('add-user-btn').addEventListener('click', openUserModal);

    // 添加任务按钮
    document.getElementById('add-task-btn').addEventListener('click', openAddTaskModal);

    // 筛选和排序事件
    document.getElementById('priority-filter').addEventListener('change', loadTasks);
    document.getElementById('sort-by').addEventListener('change', loadTasks);
    document.getElementById('sort-order').addEventListener('change', loadTasks);

    // 任务表单提交
    document.getElementById('task-form').addEventListener('submit', handleTaskSubmit);

    // 用户表单提交
    document.getElementById('user-form').addEventListener('submit', handleUserSubmit);
}

/**
 * 加载任务列表
 */
async function loadTasks() {
    try {
        const priority = document.getElementById('priority-filter').value;
        const sortBy = document.getElementById('sort-by').value;
        const sortOrder = document.getElementById('sort-order').value;

        // 构建查询参数
        let url = `/tasks/?user_id=${currentUserId}`;
        if (priority !== 'all') {
            url += `&priority=${priority}`;
        }
        url += `&sort_by=${sortBy}&sort_order=${sortOrder}`;

        const tasks = await apiRequest(url);
        renderKanban(tasks);
    } catch (error) {
        showToast('加载任务失败', 'error');
    }
}

/**
 * 加载统计信息
 */
async function loadStats() {
    try {
        const stats = await apiRequest(`/tasks/stats/${currentUserId}`);
        updateStatsDisplay(stats);
    } catch (error) {
        console.error('加载统计信息失败:', error);
    }
}

/**
 * 更新统计信息显示
 * @param {Object} stats - 统计数据
 */
function updateStatsDisplay(stats) {
    document.getElementById('total-count').textContent = stats.total_tasks;
    document.getElementById('pending-count').textContent = stats.pending_tasks;
    document.getElementById('progress-count').textContent = stats.in_progress_tasks;
    document.getElementById('completed-count').textContent = stats.completed_tasks;

    // 更新各列的计数
    document.getElementById('count-pending').textContent = stats.pending_tasks;
    document.getElementById('count-in_progress').textContent = stats.in_progress_tasks;
    document.getElementById('count-completed').textContent = stats.completed_tasks;
}

/**
 * 渲染看板
 * @param {Array} tasks - 任务列表
 */
function renderKanban(tasks) {
    // 清空各列内容
    document.getElementById('content-pending').innerHTML = '';
    document.getElementById('content-in_progress').innerHTML = '';
    document.getElementById('content-completed').innerHTML = '';

    // 按状态分组任务
    const pendingTasks = tasks.filter(t => t.status === 'pending');
    const inProgressTasks = tasks.filter(t => t.status === 'in_progress');
    const completedTasks = tasks.filter(t => t.status === 'completed');

    // 渲染各列
    renderColumn('content-pending', pendingTasks);
    renderColumn('content-in_progress', inProgressTasks);
    renderColumn('content-completed', completedTasks);
}

/**
 * 渲染单个列
 * @param {string} containerId - 容器ID
 * @param {Array} tasks - 任务列表
 */
function renderColumn(containerId, tasks) {
    const container = document.getElementById(containerId);

    if (tasks.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无任务</div>';
        return;
    }

    tasks.forEach(task => {
        const taskCard = createTaskCard(task);
        container.appendChild(taskCard);
    });
}

/**
 * 创建任务卡片元素
 * @param {Object} task - 任务对象
 * @returns {HTMLElement} - 任务卡片元素
 */
function createTaskCard(task) {
    const card = document.createElement('div');
    card.className = 'task-card';
    card.dataset.taskId = task.id;

    // 格式化截止时间
    const deadlineStr = task.deadline ? formatDateTime(task.deadline) : '';

    // 获取优先级样式类
    const priorityClass = `priority-${task.priority}`;
    const priorityText = {
        high: '高',
        medium: '中',
        low: '低'
    }[task.priority];

    // 获取状态按钮文本
    const statusActions = getStatusActions(task.status);

    card.innerHTML = `
        <h4 class="task-title">${escapeHtml(task.title)}</h4>
        ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ''}
        <div class="task-meta">
            <span class="priority-badge ${priorityClass}">${priorityText}优先级</span>
            ${deadlineStr ? `<span class="deadline-info"><span>📅</span>${deadlineStr}</span>` : ''}
        </div>
        <div class="task-actions">
            ${statusActions.map(action => `
                <button class="btn btn-sm ${action.class}" onclick="${action.onclick}">${action.text}</button>
            `).join('')}
            <button class="btn btn-sm btn-danger" onclick="editTask(${task.id})">编辑</button>
            <button class="btn btn-sm btn-danger" onclick="deleteTask(${task.id})">删除</button>
        </div>
    `;

    return card;
}

/**
 * 根据状态获取可用操作按钮
 * @param {string} status - 当前状态
 * @returns {Array} - 操作按钮数组
 */
function getStatusActions(status) {
    const actions = [];

    if (status === 'pending') {
        actions.push({
            text: '开始',
            class: 'btn-primary',
            onclick: `updateTaskStatus(${null}, 'in_progress')`
        });
        actions.push({
            text: '完成',
            class: 'btn-secondary',
            onclick: `updateTaskStatus(${null}, 'completed')`
        });
    } else if (status === 'in_progress') {
        actions.push({
            text: '暂停',
            class: 'btn-secondary',
            onclick: `updateTaskStatus(${null}, 'pending')`
        });
        actions.push({
            text: '完成',
            class: 'btn-primary',
            onclick: `updateTaskStatus(${null}, 'completed')`
        });
    } else if (status === 'completed') {
        actions.push({
            text: '重做',
            class: 'btn-secondary',
            onclick: `updateTaskStatus(${null}, 'pending')`
        });
    }

    // 修复onclick中的taskId
    return actions.map(action => ({
        ...action,
        onclick: action.onclick.replace('${null}', 'event.currentTarget.closest(".task-card").dataset.taskId')
    }));
}

/**
 * 转义HTML特殊字符
 * @param {string} text - 原始文本
 * @returns {string} - 转义后的文本
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 格式化日期时间
 * @param {string} dateTimeStr - ISO日期时间字符串
 * @returns {string} - 格式化后的日期时间
 */
function formatDateTime(dateTimeStr) {
    const date = new Date(dateTimeStr);
    const now = new Date();
    const diff = date.getTime() - now.getTime();

    // 如果是今天
    if (date.toDateString() === now.toDateString()) {
        return '今天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }

    // 如果是明天
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    if (date.toDateString() === tomorrow.toDateString()) {
        return '明天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }

    return date.toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 更新任务状态
 * @param {number} taskId - 任务ID
 * @param {string} newStatus - 新状态
 */
async function updateTaskStatus(taskId, newStatus) {
    try {
        const result = await apiRequest(`/tasks/${taskId}`, 'PUT', { status: newStatus });
        showToast('任务状态已更新', 'success');

        // 实时更新界面
        loadTasks();
        loadStats();
    } catch (error) {
        showToast('更新任务状态失败', 'error');
    }
}

/**
 * 编辑任务
 * @param {number} taskId - 任务ID
 */
async function editTask(taskId) {
    try {
        const task = await apiRequest(`/tasks/${taskId}`);
        openEditTaskModal(task);
    } catch (error) {
        showToast('获取任务信息失败', 'error');
    }
}

/**
 * 删除任务
 * @param {number} taskId - 任务ID
 */
async function deleteTask(taskId) {
    if (!confirm('确定要删除这个任务吗？')) {
        return;
    }

    try {
        await apiRequest(`/tasks/${taskId}`, 'DELETE');
        showToast('任务已删除', 'success');

        // 实时更新界面
        loadTasks();
        loadStats();
    } catch (error) {
        showToast('删除任务失败', 'error');
    }
}

/**
 * 处理任务表单提交
 * @param {Event} e - 表单提交事件
 */
async function handleTaskSubmit(e) {
    e.preventDefault();

    const taskId = document.getElementById('task-id').value;
    const title = document.getElementById('task-title').value;
    const description = document.getElementById('task-description').value;
    const priority = document.getElementById('task-priority').value;
    const deadline = document.getElementById('task-deadline').value;
    const status = document.getElementById('task-status').value;

    const taskData = {
        title,
        description: description || null,
        priority,
        status,
        deadline: deadline ? new Date(deadline).toISOString() : null
    };

    try {
        if (taskId) {
            // 更新任务
            await apiRequest(`/tasks/${taskId}`, 'PUT', taskData);
            showToast('任务更新成功', 'success');
        } else {
            // 创建任务
            taskData.user_id = currentUserId;
            await apiRequest('/tasks/', 'POST', taskData);
            showToast('任务创建成功', 'success');
        }

        closeModal();
        loadTasks();
        loadStats();
    } catch (error) {
        showToast(error.message || '操作失败', 'error');
    }
}

/**
 * 处理用户表单提交
 * @param {Event} e - 表单提交事件
 */
async function handleUserSubmit(e) {
    e.preventDefault();

    const username = document.getElementById('user-username').value;
    const email = document.getElementById('user-email').value;
    const password = document.getElementById('user-password').value;

    try {
        const user = await apiRequest('/users/', 'POST', {
            username,
            email,
            password
        });

        // 添加到用户选择器
        const select = document.getElementById('current-user');
        const option = document.createElement('option');
        option.value = user.id;
        option.textContent = user.username;
        select.appendChild(option);

        showToast('用户创建成功', 'success');
        closeUserModal();
    } catch (error) {
        showToast(error.message || '创建用户失败', 'error');
    }
}

/**
 * 打开添加任务模态框
 */
function openAddTaskModal() {
    document.getElementById('modal-title').textContent = '新建任务';
    document.getElementById('task-form').reset();
    document.getElementById('task-id').value = '';
    document.getElementById('task-status').value = 'pending';
    document.getElementById('task-priority').value = 'medium';
    document.getElementById('task-modal').classList.add('active');
}

/**
 * 打开编辑任务模态框
 * @param {Object} task - 任务对象
 */
function openEditTaskModal(task) {
    document.getElementById('modal-title').textContent = '编辑任务';
    document.getElementById('task-id').value = task.id;
    document.getElementById('task-title').value = task.title;
    document.getElementById('task-description').value = task.description || '';
    document.getElementById('task-priority').value = task.priority;
    document.getElementById('task-status').value = task.status;

    // 设置截止时间
    if (task.deadline) {
        const date = new Date(task.deadline);
        const isoString = date.toISOString().slice(0, 16);
        document.getElementById('task-deadline').value = isoString;
    }

    document.getElementById('task-modal').classList.add('active');
}

/**
 * 关闭任务模态框
 */
function closeModal() {
    document.getElementById('task-modal').classList.remove('active');
}

/**
 * 打开添加用户模态框
 */
function openUserModal() {
    document.getElementById('user-form').reset();
    document.getElementById('user-modal').classList.add('active');
}

/**
 * 关闭用户模态框
 */
function closeUserModal() {
    document.getElementById('user-modal').classList.remove('active');
}

/**
 * 显示消息提示
 * @param {string} message - 提示消息
 * @param {string} type - 提示类型 (success, error, info)
 */
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');

    // 3秒后自动隐藏
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

/**
 * 初始化测试数据
 * 如果用户不存在则创建测试用户
 */
async function initTestData() {
    try {
        // 检查用户是否存在
        const users = [1, 2, 3];
        for (const userId of users) {
            try {
                await apiRequest(`/users/${userId}`);
            } catch (error) {
                // 用户不存在，创建测试用户
                const usernames = ['用户A', '用户B', '用户C'];
                const username = usernames[userId - 1];
                await apiRequest('/users/', 'POST', {
                    username: username,
                    email: `${username}@test.com`,
                    password: '123456'
                });
                console.log(`创建测试用户: ${username}`);
            }
        }

        // 如果没有任务，创建一些测试任务
        const tasks = await apiRequest(`/tasks/?user_id=1`);
        if (tasks.length === 0) {
            const testTasks = [
                {
                    title: '完成项目文档',
                    description: '编写项目需求文档和技术文档',
                    priority: 'high',
                    status: 'pending',
                    deadline: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString()
                },
                {
                    title: '代码审查',
                    description: '审查团队成员提交的代码',
                    priority: 'medium',
                    status: 'in_progress'
                },
                {
                    title: '会议准备',
                    description: '准备下周的项目汇报材料',
                    priority: 'low',
                    status: 'pending'
                },
                {
                    title: '修复Bug',
                    description: '修复登录页面的显示问题',
                    priority: 'high',
                    status: 'completed'
                }
            ];

            for (const task of testTasks) {
                await apiRequest('/tasks/', 'POST', {
                    user_id: 1,
                    ...task
                });
            }
            console.log('创建测试任务完成');
        }
    } catch (error) {
        console.log('初始化测试数据失败（可能数据库未配置）:', error.message);
    }
}

// 点击模态框外部关闭
document.getElementById('task-modal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

document.getElementById('user-modal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeUserModal();
    }
});
