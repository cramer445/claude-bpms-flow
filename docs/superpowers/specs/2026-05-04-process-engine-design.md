# 流程引擎设计文档

## 概述

实现一个可运行的 BPMS 流程引擎，能够读取流程定义文件、发起流程实例，并在人工节点之间流转，最终到达结束节点完成流程。

## 目标

- 从本地 JSON 文件加载流程定义
- 发起新的流程实例并持久化状态
- 在人工节点之间依次流转
- 支持通过命令行界面（CLI）操作
- 使用 JSON 文件存储流程实例和运行时状态

## 非目标

- 不支持网关（排他/并行网关）
- 不提供 HTTP API
- 不支持流程条件分支

## 架构

### 整体结构

```
┌──────────┐     ┌───────────────┐     ┌───────────┐
│   CLI    │ ──▶ │    Engine     │ ──▶ │   Store   │
│ (cli.py) │ ◀── │ (engine.py)   │ ◀── │ (store.py)│
└──────────┘     └───────────────┘     └───────────┘
                        │
                   读写 JSON 文件
```

CLI 直接调用 Engine 的 Python 函数，Engine 通过 Store 读写 JSON 文件持久化状态。

### 数据模型扩展

#### 现有模型（不变）

- `NodeType` — 节点类型枚举（start / end / user_task）
- `BaseNode` — 节点基类（id, name, node_type, incoming, outgoing）
- `UserTaskNode` — 人工任务节点（assignee, candidate_groups）
- `ProcessDefinition` — 流程定义（id, name, version, nodes, start_node_id）

#### 新增模型

**ProcessInstance** — 运行中的流程实例：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | str | 流程实例唯一标识（UUID） |
| process_id | str | 关联的流程定义 ID |
| version | str | 流程版本 |
| current_node_id | str | 当前所在节点 ID |
| status | str | running / completed / terminated |
| created_at | str | 创建时间（ISO 8601） |
| variables | dict[str, Any] | 流程变量（可选上下文数据） |

**TaskInstance** — 人工节点的任务实例：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | str | 任务唯一标识（UUID） |
| process_instance_id | str | 所属流程实例 ID |
| node_id | str | 关联的节点定义 ID |
| status | str | pending / completed / skipped |
| assignee | str | 处理人 |
| started_at | str | 创建时间（ISO 8601） |
| completed_at | str \| None | 完成时间 |

### 流程定义 JSON 格式

流程定义文件存放在 `data/processes/{process_id}.json`：

```json
{
  "id": "leave",
  "name": "请假流程",
  "version": "1.0",
  "start_node_id": "start",
  "nodes": {
    "start": {
      "id": "start",
      "name": "开始",
      "type": "start",
      "outgoing": ["apply"]
    },
    "apply": {
      "id": "apply",
      "name": "提交申请",
      "type": "user_task",
      "assignee": "applicant",
      "incoming": ["start"],
      "outgoing": ["approve"]
    },
    "approve": {
      "id": "approve",
      "name": "主管审批",
      "type": "user_task",
      "assignee": "manager",
      "incoming": ["apply"],
      "outgoing": ["end"]
    },
    "end": {
      "id": "end",
      "name": "结束",
      "type": "end",
      "incoming": ["approve"]
    }
  }
}
```

### 存储层

#### 目录结构

```
data/
├── processes/          # 流程定义文件（{process_id}.json）
└── instances/          # 流程实例文件（{instance_id}.json）
```

#### Store 接口

| 方法 | 说明 |
|------|------|
| `save_process_definition(pd: ProcessDefinition) -> None` | 保存流程定义到 JSON 文件 |
| `load_process_definition(process_id: str) -> ProcessDefinition` | 加载指定流程定义 |
| `list_process_definitions() -> list[ProcessDefinition]` | 列出所有已注册的流程定义 |
| `save_instance(instance: ProcessInstance) -> None` | 保存/更新流程实例 |
| `load_instance(instance_id: str) -> ProcessInstance` | 加载流程实例 |
| `save_task(task: TaskInstance) -> None` | 保存/更新任务实例 |
| `get_tasks_for_instance(instance_id: str) -> list[TaskInstance]` | 获取实例的所有任务 |

流程实例 JSON 文件包含实例信息和关联的任务列表。

### 引擎核心

#### Engine 类接口

| 方法 | 输入 | 输出 | 说明 |
|------|------|------|------|
| `load_process_definition` | `path: Path` | `ProcessDefinition` | 从 JSON 文件加载流程定义并注册 |
| `start_instance` | `process_id: str` | `ProcessInstance` | 发起新实例，自动流转到第一个 user_task |
| `complete_task` | `task_id: str` | `ProcessInstance` | 完成当前任务，流转到下一节点 |
| `get_pending_tasks` | `instance_id: str` | `list[TaskInstance]` | 查询待办任务 |
| `get_instance` | `instance_id: str` | `ProcessInstance` | 获取实例详情 |

#### 流转规则

1. **start_instance**：从 `start_node_id` 出发，沿 `outgoing` 找到第一个 user_task 节点，创建对应的 TaskInstance，状态为 pending
2. **complete_task**：
   - 将当前 TaskInstance 标记为 completed
   - 从当前节点的 `outgoing` 找到下一个节点
   - 如果是 user_task → 创建新 TaskInstance，状态 pending
   - 如果是 end → 流程实例标记为 completed
3. 每个操作后立即持久化

### CLI 命令

```
bpms list-processes          # 列出所有已注册的流程定义
bpms start <process_id>      # 发起新流程，输出实例 ID 和当前任务
bpms tasks                   # 查看所有待办任务
bpms tasks <instance_id>     # 查看指定实例的待办任务
bpms complete <task_id>      # 完成指定任务
bpms show <instance_id>      # 查看流程实例状态
```

### 交互流程示例

```
$ bpms list-processes
leave (请假流程) v1.0

$ bpms start leave
流程实例已创建: 7f3a2b...
当前任务: [t1] 提交申请 (assignee: applicant)

$ bpms tasks
实例 7f3a2b 待办: [t1] 提交申请

$ bpms complete t1
任务完成，流转至下一节点
当前任务: [t2] 主管审批 (assignee: manager)

$ bpms complete t2
任务完成，流转至结束节点
流程实例 7f3a2b 已完成
```

### 目录结构

```
src/bpms/
├── __main__.py              # 入口点
├── models/
│   ├── __init__.py
│   ├── node.py              # 已有，不变
│   ├── process.py           # 已有，增加 JSON 序列化支持
│   ├── instance.py          # 新增：ProcessInstance, TaskInstance
│   └── serialization.py     # 新增：JSON 序列化/反序列化
├── engine.py                 # 新增：流程引擎核心逻辑
├── store.py                  # 新增：JSON 文件存储
├── cli.py                    # 新增：命令行界面
└── data/
    ├── processes/            # 流程定义文件
    └── instances/            # 流程实例文件
```
