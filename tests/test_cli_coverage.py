"""
test_cli_coverage.py

cli.pyのカバレッジ向上テスト

戦略:
- argparseのサブコマンド解析をテスト
- monkeypatchでhandlerをダミー化（commands側のテストは別ファイル）
- 各サブコマンドの正常系・エラー系を網羅
"""

import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from pmtool.tui.cli import create_parser, main


class TestCreateParser:
    """create_parser関数のテスト"""

    def test_create_parser_basic(self):
        """基本的なパーサー作成"""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "pmtool"

    def test_list_command_parser(self):
        """listコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(["list", "projects"])
        assert args.command == "list"
        assert args.entity == "projects"
        assert args.no_emoji is False

    def test_list_command_no_emoji(self):
        """listコマンド --no-emoji"""
        parser = create_parser()
        args = parser.parse_args(["list", "projects", "--no-emoji"])
        assert args.no_emoji is True

    def test_show_command_parser(self):
        """showコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(["show", "project", "1"])
        assert args.command == "show"
        assert args.entity == "project"
        assert args.id == 1
        assert args.no_emoji is False

    def test_show_command_no_emoji(self):
        """showコマンド --no-emoji"""
        parser = create_parser()
        args = parser.parse_args(["show", "project", "1", "--no-emoji"])
        assert args.no_emoji is True

    def test_add_project_parser(self):
        """add projectコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(
            ["add", "project", "--name", "TestProject", "--desc", "Test description"]
        )
        assert args.command == "add"
        assert args.entity == "project"
        assert args.name == "TestProject"
        assert args.desc == "Test description"

    def test_add_subproject_parser(self):
        """add subprojectコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(
            [
                "add",
                "subproject",
                "--project",
                "1",
                "--name",
                "SubProject",
                "--desc",
                "Desc",
            ]
        )
        assert args.command == "add"
        assert args.entity == "subproject"
        assert args.project == 1
        assert args.name == "SubProject"

    def test_add_task_parser(self):
        """add taskコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(
            ["add", "task", "--subproject", "1", "--name", "Task", "--desc", "Desc"]
        )
        assert args.entity == "task"
        assert args.subproject == 1

    def test_add_subtask_parser(self):
        """add subtaskコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(
            ["add", "subtask", "--task", "1", "--name", "SubTask", "--desc", "Desc"]
        )
        assert args.entity == "subtask"
        assert args.task == 1

    def test_delete_project_parser(self):
        """delete projectコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(["delete", "project", "1"])
        assert args.command == "delete"
        assert args.entity == "project"
        assert args.id == 1
        assert args.bridge is False
        assert args.cascade is False
        assert args.force is False
        assert args.dry_run is False

    def test_delete_task_bridge(self):
        """delete task --bridgeの解析"""
        parser = create_parser()
        args = parser.parse_args(["delete", "task", "1", "--bridge"])
        assert args.bridge is True

    def test_delete_cascade_force_dry_run(self):
        """delete --cascade --force --dry-runの解析"""
        parser = create_parser()
        args = parser.parse_args(
            ["delete", "project", "1", "--cascade", "--force", "--dry-run"]
        )
        assert args.cascade is True
        assert args.force is True
        assert args.dry_run is True

    def test_status_command_parser(self):
        """statusコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(["status", "task", "1", "DONE"])
        assert args.command == "status"
        assert args.entity == "task"
        assert args.id == 1
        assert args.status == "DONE"
        assert args.dry_run is False

    def test_status_dry_run(self):
        """status --dry-runの解析"""
        parser = create_parser()
        args = parser.parse_args(["status", "task", "1", "DONE", "--dry-run"])
        assert args.dry_run is True

    def test_status_all_choices(self):
        """statusコマンドの全ステータス"""
        parser = create_parser()
        for status in ["UNSET", "NOT_STARTED", "IN_PROGRESS", "DONE"]:
            args = parser.parse_args(["status", "task", "1", status])
            assert args.status == status

    def test_update_command_parser(self):
        """updateコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(
            ["update", "project", "1", "--name", "NewName", "--desc", "NewDesc"]
        )
        assert args.command == "update"
        assert args.entity == "project"
        assert args.id == 1
        assert args.name == "NewName"
        assert args.description == "NewDesc"

    def test_update_order(self):
        """update --orderの解析"""
        parser = create_parser()
        args = parser.parse_args(["update", "task", "1", "--order", "5"])
        assert args.order == 5

    def test_deps_add_parser(self):
        """deps addコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(["deps", "add", "task", "--from", "1", "--to", "2"])
        assert args.command == "deps"
        assert args.deps_command == "add"
        assert args.entity == "task"
        assert args.from_id == 1
        assert args.to_id == 2

    def test_deps_remove_parser(self):
        """deps removeコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(["deps", "remove", "task", "--from", "1", "--to", "2"])
        assert args.deps_command == "remove"

    def test_deps_list_parser(self):
        """deps listコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(["deps", "list", "task", "1"])
        assert args.deps_command == "list"
        assert args.id == 1
        assert args.no_emoji is False

    def test_deps_list_no_emoji(self):
        """deps list --no-emoji"""
        parser = create_parser()
        args = parser.parse_args(["deps", "list", "task", "1", "--no-emoji"])
        assert args.no_emoji is True

    def test_deps_graph_parser(self):
        """deps graphコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(["deps", "graph", "task", "1"])
        assert args.deps_command == "graph"
        assert args.id == 1

    def test_deps_chain_parser(self):
        """deps chainコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(["deps", "chain", "task", "--from", "1", "--to", "2"])
        assert args.deps_command == "chain"
        assert args.from_id == 1
        assert args.to_id == 2

    def test_deps_impact_parser(self):
        """deps impactコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(["deps", "impact", "task", "1"])
        assert args.deps_command == "impact"
        assert args.id == 1

    def test_doctor_command_parser(self):
        """doctorコマンドの解析"""
        parser = create_parser()
        args = parser.parse_args(["doctor"])
        assert args.command == "doctor"

    def test_check_alias_parser(self):
        """checkコマンド（doctorのalias）の解析"""
        parser = create_parser()
        args = parser.parse_args(["check"])
        assert args.command == "check"


class TestMainFunction:
    """main関数のテスト（ディスパッチロジック）"""

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_list")
    def test_main_list_dispatch(self, mock_handle_list, mock_db_class):
        """listコマンドのディスパッチ"""
        with patch("sys.argv", ["pmtool", "list", "projects"]):
            main()
            mock_handle_list.assert_called_once()

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_show")
    def test_main_show_dispatch(self, mock_handle_show, mock_db_class):
        """showコマンドのディスパッチ"""
        with patch("sys.argv", ["pmtool", "show", "project", "1"]):
            main()
            mock_handle_show.assert_called_once()

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_add")
    def test_main_add_dispatch(self, mock_handle_add, mock_db_class):
        """addコマンドのディスパッチ"""
        with patch("sys.argv", ["pmtool", "add", "project", "--name", "Test"]):
            main()
            mock_handle_add.assert_called_once()

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_delete")
    def test_main_delete_dispatch(self, mock_handle_delete, mock_db_class):
        """deleteコマンドのディスパッチ"""
        with patch("sys.argv", ["pmtool", "delete", "project", "1"]):
            main()
            mock_handle_delete.assert_called_once()

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_status")
    def test_main_status_dispatch(self, mock_handle_status, mock_db_class):
        """statusコマンドのディスパッチ"""
        with patch("sys.argv", ["pmtool", "status", "task", "1", "DONE"]):
            main()
            mock_handle_status.assert_called_once()

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_update")
    def test_main_update_dispatch(self, mock_handle_update, mock_db_class):
        """updateコマンドのディスパッチ"""
        with patch("sys.argv", ["pmtool", "update", "project", "1", "--name", "New"]):
            main()
            mock_handle_update.assert_called_once()

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_deps")
    def test_main_deps_dispatch(self, mock_handle_deps, mock_db_class):
        """depsコマンドのディスパッチ"""
        with patch("sys.argv", ["pmtool", "deps", "add", "task", "--from", "1", "--to", "2"]):
            main()
            mock_handle_deps.assert_called_once()

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_doctor")
    def test_main_doctor_dispatch(self, mock_handle_doctor, mock_db_class):
        """doctorコマンドのディスパッチ"""
        with patch("sys.argv", ["pmtool", "doctor"]):
            main()
            mock_handle_doctor.assert_called_once()

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_doctor")
    def test_main_check_dispatch(self, mock_handle_doctor, mock_db_class):
        """checkコマンド（alias）のディスパッチ"""
        with patch("sys.argv", ["pmtool", "check"]):
            main()
            mock_handle_doctor.assert_called_once()

    def test_main_no_command_exits(self):
        """コマンド未指定時のエラー"""
        with patch("sys.argv", ["pmtool"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_list")
    def test_main_validation_error(self, mock_handle_list, mock_db_class):
        """ValidationErrorのハンドリング"""
        from pmtool.exceptions import ValidationError

        mock_handle_list.side_effect = ValidationError("Invalid input")

        with patch("sys.argv", ["pmtool", "list", "projects"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_list")
    def test_main_constraint_violation_error(self, mock_handle_list, mock_db_class):
        """ConstraintViolationErrorのハンドリング"""
        from pmtool.exceptions import ConstraintViolationError

        mock_handle_list.side_effect = ConstraintViolationError("Constraint violated")

        with patch("sys.argv", ["pmtool", "list", "projects"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_deps")
    def test_main_cyclic_dependency_error(self, mock_handle_deps, mock_db_class):
        """CyclicDependencyErrorのハンドリング"""
        from pmtool.exceptions import CyclicDependencyError

        mock_handle_deps.side_effect = CyclicDependencyError("Cycle detected: 1 -> 2 -> 1")

        with patch("sys.argv", ["pmtool", "deps", "add", "task", "--from", "1", "--to", "2"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_status")
    def test_main_status_transition_error_prerequisite(self, mock_handle_status, mock_db_class):
        """StatusTransitionError（先行ノード未完了）のハンドリング"""
        from pmtool.exceptions import (
            StatusTransitionError,
            StatusTransitionFailureReason,
        )

        mock_handle_status.side_effect = StatusTransitionError(
            "Cannot transition",
            reason=StatusTransitionFailureReason.PREREQUISITE_NOT_DONE,
        )

        with patch("sys.argv", ["pmtool", "status", "task", "1", "DONE"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_status")
    def test_main_status_transition_error_child(self, mock_handle_status, mock_db_class):
        """StatusTransitionError（子未完了）のハンドリング"""
        from pmtool.exceptions import (
            StatusTransitionError,
            StatusTransitionFailureReason,
        )

        mock_handle_status.side_effect = StatusTransitionError(
            "Cannot transition", reason=StatusTransitionFailureReason.CHILD_NOT_DONE
        )

        with patch("sys.argv", ["pmtool", "status", "task", "1", "DONE"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_status")
    def test_main_status_transition_error_node_not_found(
        self, mock_handle_status, mock_db_class
    ):
        """StatusTransitionError（ノード不在）のハンドリング"""
        from pmtool.exceptions import (
            StatusTransitionError,
            StatusTransitionFailureReason,
        )

        mock_handle_status.side_effect = StatusTransitionError(
            "Node not found", reason=StatusTransitionFailureReason.NODE_NOT_FOUND
        )

        with patch("sys.argv", ["pmtool", "status", "task", "1", "DONE"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_status")
    def test_main_status_transition_error_generic(self, mock_handle_status, mock_db_class):
        """StatusTransitionError（reasonなし）のハンドリング"""
        from pmtool.exceptions import StatusTransitionError

        mock_handle_status.side_effect = StatusTransitionError(
            "Cannot transition", reason=None
        )

        with patch("sys.argv", ["pmtool", "status", "task", "1", "DONE"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_delete")
    def test_main_deletion_error(self, mock_handle_delete, mock_db_class):
        """DeletionErrorのハンドリング"""
        from pmtool.exceptions import DeletionError

        mock_handle_delete.side_effect = DeletionError("Child exists")

        with patch("sys.argv", ["pmtool", "delete", "project", "1"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_list")
    def test_main_generic_pmtool_error(self, mock_handle_list, mock_db_class):
        """PMToolError（汎用）のハンドリング"""
        from pmtool.exceptions import PMToolError

        mock_handle_list.side_effect = PMToolError("Generic error")

        with patch("sys.argv", ["pmtool", "list", "projects"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("pmtool.tui.cli.Database")
    @patch("pmtool.tui.cli.commands.handle_list")
    def test_main_unexpected_exception(self, mock_handle_list, mock_db_class):
        """予期しない例外のハンドリング"""
        mock_handle_list.side_effect = RuntimeError("Unexpected error")

        with patch("sys.argv", ["pmtool", "list", "projects"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
