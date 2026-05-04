"""BPMS 命令行界面。"""

import argparse

from bpms.engine import ProcessEngine
from bpms.store import Store


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bpms", description="BPMS 流程引擎")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list-processes", help="列出所有流程定义")

    start_p = subparsers.add_parser("start", help="发起新流程")
    start_p.add_argument("process_id", help="流程定义 ID")

    tasks_p = subparsers.add_parser("tasks", help="查看待办任务")
    tasks_p.add_argument("instance_id", nargs="?", help="流程实例 ID（可选）")

    complete_p = subparsers.add_parser("complete", help="完成任务")
    complete_p.add_argument("task_id", help="任务 ID")

    show_p = subparsers.add_parser("show", help="查看实例状态")
    show_p.add_argument("instance_id", help="流程实例 ID")

    serve_p = subparsers.add_parser("serve", help="启动 Web 服务")
    serve_p.add_argument("--host", default="127.0.0.1", help="监听地址")
    serve_p.add_argument("--port", type=int, default=8000, help="监听端口")

    return parser


def run(args: list[str] | None = None) -> None:
    parser = create_parser()
    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return

    store = Store()
    engine = ProcessEngine(store)

    if parsed.command == "list-processes":
        cmd_list_processes(engine)
    elif parsed.command == "start":
        cmd_start(engine, parsed.process_id)
    elif parsed.command == "tasks":
        cmd_tasks(engine, parsed.instance_id)
    elif parsed.command == "complete":
        cmd_complete(engine, parsed.task_id)
    elif parsed.command == "show":
        cmd_show(engine, parsed.instance_id)
    elif parsed.command == "serve":
        from bpms.server import serve
        serve(host=parsed.host, port=parsed.port)
        return


def _safe(engine, handler, *args):
    """包装命令处理器，捕获常见错误并输出友好提示。"""
    try:
        handler(*args)
    except (FileNotFoundError, ValueError) as e:
        print(f"错误: {e}")


def cmd_list_processes(engine: ProcessEngine) -> None:
    _safe(engine, _cmd_list_processes_impl, engine)


def _cmd_list_processes_impl(engine: ProcessEngine) -> None:
    pds = engine.store.list_process_definitions()
    if not pds:
        print("暂无流程定义")
        return
    for pd in pds:
        print(f"{pd.id} ({pd.name}) v{pd.version}")


def cmd_start(engine: ProcessEngine, process_id: str) -> None:
    _safe(engine, _cmd_start_impl, engine, process_id)


def _cmd_start_impl(engine: ProcessEngine, process_id: str) -> None:
    instance = engine.start_instance(process_id)
    print(f"流程实例已创建: {instance.id}")
    pending = engine.get_pending_tasks(instance.id)
    if pending:
        task = pending[0]
        print(f"当前任务: [{task.id}] {task.node_id} (assignee: {task.assignee})")
    else:
        print("流程已直接结束")


def cmd_tasks(engine: ProcessEngine, instance_id: str | None) -> None:
    _safe(engine, _cmd_tasks_impl, engine, instance_id)


def _cmd_tasks_impl(engine: ProcessEngine, instance_id: str | None) -> None:
    if instance_id:
        instances = [engine.get_instance(instance_id)]
    else:
        instances = engine.store.list_instances()

    found = False
    for inst in instances:
        pending = engine.get_pending_tasks(inst.id)
        if pending:
            found = True
            task_ids = ", ".join(f"[{t.id}] {t.node_id} (assignee: {t.assignee})" for t in pending)
            print(f"实例 {inst.id} 待办: {task_ids}")

    if not found:
        print("暂无待办任务")


def cmd_complete(engine: ProcessEngine, task_id: str) -> None:
    _safe(engine, _cmd_complete_impl, engine, task_id)


def _cmd_complete_impl(engine: ProcessEngine, task_id: str) -> None:
    instance = engine.complete_task(task_id)
    print(f"任务完成")

    if instance.status == "completed":
        print(f"流程实例 {instance.id} 已完成")
    else:
        pending = engine.get_pending_tasks(instance.id)
        if pending:
            task = pending[0]
            print(f"当前任务: [{task.id}] {task.node_id} (assignee: {task.assignee})")


def cmd_show(engine: ProcessEngine, instance_id: str) -> None:
    _safe(engine, _cmd_show_impl, engine, instance_id)


def _cmd_show_impl(engine: ProcessEngine, instance_id: str) -> None:
    instance = engine.get_instance(instance_id)
    print(f"实例 ID: {instance.id}")
    print(f"流程定义: {instance.process_id} v{instance.version}")
    print(f"状态: {instance.status}")
    print(f"当前节点: {instance.current_node_id}")
    tasks = engine.store.get_tasks_for_instance(instance_id)
    if tasks:
        print("任务:")
        for t in tasks:
            print(f"  [{t.id}] {t.node_id} - {t.status} (assignee: {t.assignee})")
