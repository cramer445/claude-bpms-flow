"""CLI 模块单元测试。"""

import pytest

from bpms.cli import create_parser


@pytest.mark.unit
class TestCLIParser:
    def test_create_parser_has_all_subcommands(self):
        parser = create_parser()
        subcommands = set()
        for action in parser._subparsers._actions:
            if hasattr(action, "choices") and action.choices:
                subcommands.update(action.choices.keys())

        assert "list-processes" in subcommands
        assert "start" in subcommands
        assert "tasks" in subcommands
        assert "complete" in subcommands
        assert "show" in subcommands
