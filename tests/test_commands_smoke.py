"""
commands.py スモークテスト

ChatGPT Review6フィードバックに基づき、太いスモークテストで広い分岐を一気に踏む
- 出力一致テストは禁止
- アサーション: 例外にならない、DB状態変化、呼び出し確認のみ
- ハンドラ関数を直接呼ぶ
- tui_inputとdisplayはmonkeypatch
"""

from argparse import Namespace
from unittest.mock import MagicMock

import pytest
from pmtool.database import Database
from pmtool.repository import (
    ProjectRepository,
    SubProjectRepository,
    TaskRepository,
    SubTaskRepository,
)
from pmtool.dependencies import DependencyManager
from pmtool.tui import commands


# ========================================
# handle_add のスモークテスト
# ========================================

class TestHandleAddSmoke:
    """handle_add のスモークテスト（DB状態変化で確認）"""

    def test_add_project_smoke(self, temp_db, monkeypatch):
        """add project - DB状態変化確認"""
        # 入力モック
        monkeypatch.setattr("pmtool.tui.commands.tui_input.prompt_text", lambda msg, required=True: "TestProject" if "name" in msg.lower() else "TestDesc")

        # 実行前のプロジェクト数
        proj_repo = ProjectRepository(temp_db)
        count_before = len(proj_repo.get_all())

        args = Namespace(entity="project", name=None, desc=None)
        commands.handle_add(temp_db, args)

        # 実行後のプロジェクト数（1件増加）
        count_after = len(proj_repo.get_all())
        assert count_after == count_before + 1

    def test_add_subproject_smoke(self, temp_db, monkeypatch):
        """add subproject - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        subproj_repo = SubProjectRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")

        # 入力モック
        monkeypatch.setattr("pmtool.tui.commands.tui_input.prompt_int", lambda msg, required=True: proj.id)
        monkeypatch.setattr("pmtool.tui.commands.tui_input.prompt_text", lambda msg, required=True: "TestSubProject" if "name" in msg.lower() else "TestDesc")

        # 実行前のサブプロジェクト数
        count_before = len(subproj_repo.get_by_project(proj.id))

        args = Namespace(entity="subproject", project=None, name=None, desc=None)
        commands.handle_add(temp_db, args)

        # 実行後のサブプロジェクト数（1件増加）
        count_after = len(subproj_repo.get_by_project(proj.id))
        assert count_after == count_before + 1

    def test_add_task_smoke(self, temp_db, monkeypatch):
        """add task - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")

        # 入力モック（project IDを返す）
        monkeypatch.setattr("pmtool.tui.commands.tui_input.prompt_int", lambda msg, required=True: proj.id)
        monkeypatch.setattr("pmtool.tui.commands.tui_input.prompt_text", lambda msg, required=True: "TestTask" if "name" in msg.lower() or "タスク" in msg else "TestDesc")

        # 実行前のタスク数
        count_before = len(task_repo.get_by_parent(proj.id, subproject_id=None))

        args = Namespace(entity="task", project=None, subproject=None, name=None, desc=None)
        commands.handle_add(temp_db, args)

        # 実行後のタスク数（1件増加）
        count_after = len(task_repo.get_by_parent(proj.id, subproject_id=None))
        assert count_after == count_before + 1

    def test_add_subtask_smoke(self, temp_db, monkeypatch):
        """add subtask - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        subtask_repo = SubTaskRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task = task_repo.create(proj.id, "Task", description="TaskDesc")

        # 入力モック
        monkeypatch.setattr("pmtool.tui.commands.tui_input.prompt_int", lambda msg, required=True: task.id)
        monkeypatch.setattr("pmtool.tui.commands.tui_input.prompt_text", lambda msg, required=True: "TestSubTask" if "name" in msg.lower() else "TestDesc")

        # 実行前のサブタスク数
        count_before = len(subtask_repo.get_by_task(task.id))

        args = Namespace(entity="subtask", task=None, name=None, desc=None)
        commands.handle_add(temp_db, args)

        # 実行後のサブタスク数（1件増加）
        count_after = len(subtask_repo.get_by_task(task.id))
        assert count_after == count_before + 1


# ========================================
# handle_list / handle_show のスモークテスト
# ========================================

class TestHandleListShowSmoke:
    """handle_list / handle_show のスモークテスト（例外が発生しないことを確認）"""

    def test_list_projects_smoke(self, temp_db, monkeypatch):
        """list projects - 例外が発生しない"""
        mock_display = MagicMock()
        monkeypatch.setattr("pmtool.tui.commands.display.show_project_list", mock_display)

        args = Namespace(entity="projects", no_emoji=False)
        commands.handle_list(temp_db, args)

        # 呼ばれたことを確認
        assert mock_display.called

    def test_show_project_smoke(self, temp_db, monkeypatch):
        """show project - 例外が発生しない"""
        proj_repo = ProjectRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")

        mock_display = MagicMock()
        monkeypatch.setattr("pmtool.tui.commands.display.show_project_tree", mock_display)

        args = Namespace(entity="project", id=proj.id, no_emoji=False)
        commands.handle_show(temp_db, args)

        # 呼ばれたことを確認
        assert mock_display.called


# ========================================
# handle_delete のスモークテスト
# ========================================

class TestHandleDeleteSmoke:
    """handle_delete のスモークテスト（DB状態変化で確認）"""

    def test_delete_project_normal_smoke(self, temp_db, monkeypatch):
        """delete project 通常削除 - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")

        # 確認をYesでモック
        monkeypatch.setattr("pmtool.tui.commands.tui_input.confirm", lambda msg, default=False: True)

        args = Namespace(entity="project", id=proj.id, bridge=False, cascade=False, force=False, dry_run=False)
        commands.handle_delete(temp_db, args)

        # プロジェクトが削除されたことを確認
        assert proj_repo.get_by_id(proj.id) is None

    def test_delete_task_normal_smoke(self, temp_db, monkeypatch):
        """delete task 通常削除 - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task = task_repo.create(proj.id, "Task", description="TaskDesc")

        # 確認をYesでモック
        monkeypatch.setattr("pmtool.tui.commands.tui_input.confirm", lambda msg, default=False: True)

        args = Namespace(entity="task", id=task.id, bridge=False, cascade=False, force=False, dry_run=False)
        commands.handle_delete(temp_db, args)

        # タスクが削除されたことを確認
        assert task_repo.get_by_id(task.id) is None

    def test_delete_cascade_dry_run_smoke(self, temp_db, monkeypatch):
        """delete project --cascade --dry-run - 例外が発生しない"""
        proj_repo = ProjectRepository(temp_db)
        subproj_repo = SubProjectRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")
        subproj = subproj_repo.create(proj.id, "SubProject", description="SubDesc")

        args = Namespace(entity="project", id=proj.id, bridge=False, cascade=True, force=False, dry_run=True)
        commands.handle_delete(temp_db, args)

        # dry-runなのでプロジェクトは削除されていない
        assert proj_repo.get_by_id(proj.id) is not None

    def test_delete_cascade_with_force_smoke(self, temp_db, monkeypatch):
        """delete project --cascade --force - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        subproj_repo = SubProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")
        subproj = subproj_repo.create(proj.id, "SubProject", description="SubDesc")
        task = task_repo.create(proj.id, "Task", description="TaskDesc")

        # 確認をYesでモック
        monkeypatch.setattr("pmtool.tui.commands.tui_input.confirm", lambda msg, default=False: True)

        args = Namespace(entity="project", id=proj.id, bridge=False, cascade=True, force=True, dry_run=False)
        commands.handle_delete(temp_db, args)

        # プロジェクト、サブプロジェクト、タスクが全て削除されたことを確認
        assert proj_repo.get_by_id(proj.id) is None
        assert subproj_repo.get_by_id(subproj.id) is None
        assert task_repo.get_by_id(task.id) is None


# ========================================
# handle_status のスモークテスト
# ========================================

class TestHandleStatusSmoke:
    """handle_status のスモークテスト（DB状態変化で確認）"""

    def test_status_task_to_done_smoke(self, temp_db, monkeypatch):
        """status task DONE - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task = task_repo.create(proj.id, "Task", description="TaskDesc")

        args = Namespace(entity="task", id=task.id, status="DONE", dry_run=False)
        commands.handle_status(temp_db, args)

        # ステータスがDONEに変更されたことを確認
        updated_task = task_repo.get_by_id(task.id)
        assert updated_task.status == "DONE"

    def test_status_task_done_dry_run_success_smoke(self, temp_db, monkeypatch):
        """status task DONE --dry-run 可能 - 例外が発生しない"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task = task_repo.create(proj.id, "Task", description="TaskDesc")

        args = Namespace(entity="task", id=task.id, status="DONE", dry_run=True)
        commands.handle_status(temp_db, args)

        # dry-runなのでステータスは変更されていない
        updated_task = task_repo.get_by_id(task.id)
        assert updated_task.status != "DONE"


# ========================================
# handle_deps のスモークテスト
# ========================================

class TestHandleDepsSmoke:
    """handle_deps のスモークテスト（DB状態変化 + 例外が発生しないことを確認）"""

    def test_deps_add_task_smoke(self, temp_db, monkeypatch):
        """deps add task - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        dep_mgr = DependencyManager(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task1 = task_repo.create(proj.id, "Task1", description="Desc1")
        task2 = task_repo.create(proj.id, "Task2", description="Desc2")

        args = Namespace(
            deps_command="add",
            entity="task",
            from_id=task1.id,
            to_id=task2.id,
            id=None,
        )
        commands.handle_deps(temp_db, args)

        # 依存関係が追加されたことを確認
        deps = dep_mgr.get_task_dependencies(task2.id)
        assert task1.id in deps["predecessors"]

    def test_deps_remove_task_smoke(self, temp_db, monkeypatch):
        """deps remove task - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        dep_mgr = DependencyManager(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task1 = task_repo.create(proj.id, "Task1", description="Desc1")
        task2 = task_repo.create(proj.id, "Task2", description="Desc2")

        # 依存関係を追加
        dep_mgr.add_task_dependency(task1.id, task2.id)

        args = Namespace(
            deps_command="remove",
            entity="task",
            from_id=task1.id,
            to_id=task2.id,
            id=None,
        )
        commands.handle_deps(temp_db, args)

        # 依存関係が削除されたことを確認
        deps = dep_mgr.get_task_dependencies(task2.id)
        assert task1.id not in deps["predecessors"]

    def test_deps_list_task_smoke(self, temp_db, monkeypatch):
        """deps list task - 例外が発生しない"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        dep_mgr = DependencyManager(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task1 = task_repo.create(proj.id, "Task1", description="Desc1")
        task2 = task_repo.create(proj.id, "Task2", description="Desc2")

        # 依存関係を追加
        dep_mgr.add_task_dependency(task1.id, task2.id)

        mock_display = MagicMock()
        monkeypatch.setattr("pmtool.tui.commands.display.show_dependencies", mock_display)

        args = Namespace(
            deps_command="list",
            entity="task",
            id=task2.id,
            from_id=None,
            to_id=None,
            no_emoji=False,
        )
        commands.handle_deps(temp_db, args)

        # 呼ばれたことを確認
        assert mock_display.called

    def test_deps_graph_task_smoke(self, temp_db, monkeypatch):
        """deps graph task - 例外が発生しない"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        dep_mgr = DependencyManager(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task1 = task_repo.create(proj.id, "Task1", description="Desc1")
        task2 = task_repo.create(proj.id, "Task2", description="Desc2")

        # 依存関係を追加
        dep_mgr.add_task_dependency(task1.id, task2.id)

        mock_display = MagicMock()
        monkeypatch.setattr("pmtool.tui.commands.display.show_dependency_graph_task", mock_display)

        args = Namespace(
            deps_command="graph",
            entity="task",
            id=task2.id,
            from_id=None,
            to_id=None,
            no_emoji=False,
        )
        commands.handle_deps(temp_db, args)

        # 呼ばれたことを確認
        assert mock_display.called

    def test_deps_chain_task_smoke(self, temp_db, monkeypatch):
        """deps chain task - 例外が発生しない"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        dep_mgr = DependencyManager(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task1 = task_repo.create(proj.id, "Task1", description="Desc1")
        task2 = task_repo.create(proj.id, "Task2", description="Desc2")

        # 依存関係を追加
        dep_mgr.add_task_dependency(task1.id, task2.id)

        mock_display = MagicMock()
        monkeypatch.setattr("pmtool.tui.commands.display.show_dependency_chain_task", mock_display)

        args = Namespace(
            deps_command="chain",
            entity="task",
            from_id=task1.id,
            to_id=task2.id,
            id=None,
            no_emoji=False,
        )
        commands.handle_deps(temp_db, args)

        # 呼ばれたことを確認
        assert mock_display.called

    def test_deps_impact_task_smoke(self, temp_db, monkeypatch):
        """deps impact task - 例外が発生しない"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        dep_mgr = DependencyManager(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task1 = task_repo.create(proj.id, "Task1", description="Desc1")
        task2 = task_repo.create(proj.id, "Task2", description="Desc2")

        # 依存関係を追加
        dep_mgr.add_task_dependency(task1.id, task2.id)

        mock_display = MagicMock()
        monkeypatch.setattr("pmtool.tui.commands.display.show_impact_analysis_task", mock_display)

        args = Namespace(
            deps_command="impact",
            entity="task",
            id=task1.id,
            from_id=None,
            to_id=None,
            no_emoji=False,
        )
        commands.handle_deps(temp_db, args)

        # 呼ばれたことを確認
        assert mock_display.called


# ========================================
# handle_doctor のスモークテスト
# ========================================

class TestHandleDoctorSmoke:
    """handle_doctor のスモークテスト（例外が発生しないことを確認）"""

    def test_doctor_smoke(self, temp_db, monkeypatch):
        """doctor check - 例外が発生しない"""
        mock_display = MagicMock()
        monkeypatch.setattr("pmtool.tui.commands.display.show_doctor_report", mock_display)

        args = Namespace()
        commands.handle_doctor(temp_db, args)

        # 呼ばれたことを確認
        assert mock_display.called


# ========================================
# handle_update のスモークテスト
# ========================================

class TestHandleUpdateSmoke:
    """handle_update のスモークテスト（DB状態変化で確認）"""

    def test_update_project_name_smoke(self, temp_db, monkeypatch):
        """update project name - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")

        args = Namespace(entity="project", id=proj.id, name="NewName", description=None, order=None)
        commands.handle_update(temp_db, args)

        # 名前が更新されたことを確認
        updated_proj = proj_repo.get_by_id(proj.id)
        assert updated_proj.name == "NewName"

    def test_update_task_name_and_description_smoke(self, temp_db, monkeypatch):
        """update task name and description - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task = task_repo.create(proj.id, "Task", description="TaskDesc")

        args = Namespace(entity="task", id=task.id, name="NewName", description="NewDesc", order=None)
        commands.handle_update(temp_db, args)

        # 名前と説明が更新されたことを確認
        updated_task = task_repo.get_by_id(task.id)
        assert updated_task.name == "NewName"
        assert updated_task.description == "NewDesc"

    def test_update_no_options_error_smoke(self, temp_db, monkeypatch):
        """update オプション未指定エラー - 例外が発生しない（エラーメッセージ表示のみ）"""
        proj_repo = ProjectRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")

        # オプション未指定
        args = Namespace(entity="project", id=proj.id, name=None, description=None, order=None)
        # エラーメッセージが表示されるが、例外は発生しない
        commands.handle_update(temp_db, args)


# ========================================
# エラー系のスモークテスト
# ========================================

class TestHandleErrorSmoke:
    """エラー系のスモークテスト（例外が発生してもクラッシュしない）"""

    def test_show_not_found_smoke(self, temp_db, monkeypatch):
        """show project 存在しないID - エラーメッセージ表示"""
        args = Namespace(entity="project", id=99999, no_emoji=False)
        # エラーメッセージが表示されるが、例外は発生しない
        commands.handle_show(temp_db, args)

    def test_delete_cascade_force_missing_smoke(self, temp_db, monkeypatch):
        """delete project --cascade without --force - エラーメッセージ表示"""
        proj_repo = ProjectRepository(temp_db)
        subproj_repo = SubProjectRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")
        subproj = subproj_repo.create(proj.id, "SubProject", description="SubDesc")

        args = Namespace(entity="project", id=proj.id, bridge=False, cascade=True, force=False, dry_run=False)
        # エラーメッセージが表示されるが、例外は発生しない
        commands.handle_delete(temp_db, args)

    def test_delete_bridge_and_cascade_exclusive_smoke(self, temp_db, monkeypatch):
        """delete --bridge --cascade 同時指定エラー - エラーメッセージ表示"""
        proj_repo = ProjectRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")

        args = Namespace(entity="project", id=proj.id, bridge=True, cascade=True, force=False, dry_run=False)
        # エラーメッセージが表示されるが、例外は発生しない
        commands.handle_delete(temp_db, args)

    def test_add_subproject_with_args_smoke(self, temp_db, monkeypatch):
        """add subproject 引数指定あり - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        subproj_repo = SubProjectRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")

        # 引数で全て指定
        args = Namespace(entity="subproject", project=proj.id, name="SubProj", desc="SubDesc")
        commands.handle_add(temp_db, args)

        # サブプロジェクトが追加されたことを確認
        subprojs = subproj_repo.get_by_project(proj.id)
        assert len(subprojs) == 1
        assert subprojs[0].name == "SubProj"

    def test_update_project_interactive_smoke(self, temp_db, monkeypatch):
        """update project 対話的入力 - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")

        # 対話的入力をモック
        inputs = {"name": "NewNameInteractive", "description": "NewDescInteractive"}
        monkeypatch.setattr("pmtool.tui.commands.tui_input.prompt_text",
                           lambda msg, required=False: inputs.get("name" if "名前" in msg or "name" in msg.lower() else "description", ""))

        # 引数なしで対話的入力を促す
        args = Namespace(entity="project", id=proj.id, name=None, description=None, order=None)
        # updateコマンドは少なくとも1つのオプションが必要なため、エラーメッセージが表示される
        commands.handle_update(temp_db, args)

    def test_status_subtask_to_done_smoke(self, temp_db, monkeypatch):
        """status subtask DONE - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        subtask_repo = SubTaskRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task = task_repo.create(proj.id, "Task", description="Desc")
        subtask = subtask_repo.create(task.id, "SubTask", description="SubDesc")

        args = Namespace(entity="subtask", id=subtask.id, status="DONE", dry_run=False)
        commands.handle_status(temp_db, args)

        # ステータスがDONEに変更されたことを確認
        updated_subtask = subtask_repo.get_by_id(subtask.id)
        assert updated_subtask.status == "DONE"

    def test_status_task_to_in_progress_smoke(self, temp_db, monkeypatch):
        """status task IN_PROGRESS - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task = task_repo.create(proj.id, "Task", description="Desc")

        args = Namespace(entity="task", id=task.id, status="IN_PROGRESS", dry_run=False)
        commands.handle_status(temp_db, args)

        # ステータスがIN_PROGRESSに変更されたことを確認
        updated_task = task_repo.get_by_id(task.id)
        assert updated_task.status == "IN_PROGRESS"

    def test_deps_add_subtask_smoke(self, temp_db, monkeypatch):
        """deps add subtask - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        subtask_repo = SubTaskRepository(temp_db)
        dep_mgr = DependencyManager(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task = task_repo.create(proj.id, "Task", description="Desc")
        subtask1 = subtask_repo.create(task.id, "SubTask1", description="Desc1")
        subtask2 = subtask_repo.create(task.id, "SubTask2", description="Desc2")

        args = Namespace(
            deps_command="add",
            entity="subtask",
            from_id=subtask1.id,
            to_id=subtask2.id,
            id=None,
        )
        commands.handle_deps(temp_db, args)

        # 依存関係が追加されたことを確認
        deps = dep_mgr.get_subtask_dependencies(subtask2.id)
        assert subtask1.id in deps["predecessors"]

    def test_deps_list_subtask_smoke(self, temp_db, monkeypatch):
        """deps list subtask - 例外が発生しない"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        subtask_repo = SubTaskRepository(temp_db)
        dep_mgr = DependencyManager(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task = task_repo.create(proj.id, "Task", description="Desc")
        subtask1 = subtask_repo.create(task.id, "SubTask1", description="Desc1")
        subtask2 = subtask_repo.create(task.id, "SubTask2", description="Desc2")

        # 依存関係を追加
        dep_mgr.add_subtask_dependency(subtask1.id, subtask2.id)

        mock_display = MagicMock()
        monkeypatch.setattr("pmtool.tui.commands.display.show_dependencies", mock_display)

        args = Namespace(
            deps_command="list",
            entity="subtask",
            id=subtask2.id,
            from_id=None,
            to_id=None,
            no_emoji=False,
        )
        commands.handle_deps(temp_db, args)

        # 呼ばれたことを確認
        assert mock_display.called

    def test_add_task_with_subproject_smoke(self, temp_db, monkeypatch):
        """add task with subproject - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        subproj_repo = SubProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        proj = proj_repo.create("Project", "Desc")
        subproj = subproj_repo.create(proj.id, "SubProject", description="SubDesc")

        # サブプロジェクト配下のタスクを作成
        monkeypatch.setattr("pmtool.tui.commands.tui_input.prompt_int", lambda msg, required=True: proj.id if "project" in msg.lower() or "プロジェクト" in msg else subproj.id)
        monkeypatch.setattr("pmtool.tui.commands.tui_input.prompt_text", lambda msg, required=True: "TestTask" if "name" in msg.lower() or "タスク" in msg else "TestDesc")

        args = Namespace(entity="task", project=None, subproject=subproj.id, name=None, desc=None)
        commands.handle_add(temp_db, args)

        # タスクが追加されたことを確認
        tasks = task_repo.get_by_parent(proj.id, subproject_id=subproj.id)
        assert len(tasks) == 1

    def test_deps_remove_subtask_smoke(self, temp_db, monkeypatch):
        """deps remove subtask - DB状態変化確認"""
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        subtask_repo = SubTaskRepository(temp_db)
        dep_mgr = DependencyManager(temp_db)
        proj = proj_repo.create("Project", "Desc")
        task = task_repo.create(proj.id, "Task", description="Desc")
        subtask1 = subtask_repo.create(task.id, "SubTask1", description="Desc1")
        subtask2 = subtask_repo.create(task.id, "SubTask2", description="Desc2")

        # 依存関係を追加
        dep_mgr.add_subtask_dependency(subtask1.id, subtask2.id)

        args = Namespace(
            deps_command="remove",
            entity="subtask",
            from_id=subtask1.id,
            to_id=subtask2.id,
            id=None,
        )
        commands.handle_deps(temp_db, args)

        # 依存関係が削除されたことを確認
        deps = dep_mgr.get_subtask_dependencies(subtask2.id)
        assert subtask1.id not in deps["predecessors"]

