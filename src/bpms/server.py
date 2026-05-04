"""BPMS FastAPI 服务启动入口。"""

import uvicorn

from bpms.store import Store


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    """启动 FastAPI 服务。"""
    store = Store()
    from bpms.api.routes import create_app_with_static
    from pathlib import Path
    static_dir = Path(__file__).parent / "static"
    app = create_app_with_static(store, str(static_dir))
    uvicorn.run(app, host=host, port=port)
