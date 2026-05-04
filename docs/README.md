# BPMS 项目文档

## 快速开始

```bash
# 1. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
pip install -e ".[dev]"

# 3. 启动
python -m bpms
```

## 测试

```bash
# 运行全部测试
pytest

# 分层运行
pytest -m unit              # 单元测试
pytest -m integration       # 集成测试
pytest -m e2e               # 端到端测试

# 覆盖率报告
pytest --cov=src/bpms --cov-report=term-missing
```

## 测试分层

| 层级 | 目录 | 标记 | 说明 |
|------|------|------|------|
| 单元测试 | `tests/unit/` | `@pytest.mark.unit` | 隔离的函数/类测试，无外部依赖 |
| 集成测试 | `tests/integration/` | `@pytest.mark.integration` | 涉及数据库、消息队列等外部组件 |
| 端到端测试 | `tests/e2e/` | `@pytest.mark.e2e` | 完整系统流程测试 |

## 目录结构

```
├── docs/              # 项目文档
├── src/bpms/          # 源代码
├── tests/             # 测试代码
│   ├── unit/          # 单元测试
│   ├── integration/   # 集成测试
│   └── e2e/           # 端到端测试
├── .gitignore
├── pyproject.toml     # 项目配置
└── requirements-dev.txt
```
