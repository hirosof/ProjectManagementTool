"""
test_display_coverage.py

display.pyのカバレッジ向上テスト

戦略:
- Rich Console(record=True)でスモークテスト
- 各display関数の例外なし確認
- 出力に期待される文字列が含まれることを確認（部分一致テスト）
"""

from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from pmtool.doctor import DoctorReport, Issue, IssueLevel
from pmtool.models import Project, SubProject, Task, SubTask
from pmtool.repository import (
    ProjectRepository,
    SubProjectRepository,
    TaskRepository,
    SubTaskRepository,
)
from pmtool.tui import display


@pytest.fixture(autouse=True)
def mock_formatters(monkeypatch):
    """formattersモジュールの存在しない関数をモック"""
    # display.pyが呼び出している存在しない関数をモック
    monkeypatch.setattr("pmtool.tui.formatters.format_task_status", lambda status: f"[{status}]", raising=False)
    monkeypatch.setattr("pmtool.tui.formatters.format_subtask_status", lambda status: f"[{status}]", raising=False)


class TestShowProjectList:
    """show_project_list関数のテスト"""

    def test_show_project_list_with_projects(self, monkeypatch):
        """プロジェクト一覧表示（正常系）"""
        projects = [
            Project(
                id=1,
                name="Test Project 1",
                description="Description 1",
                order_index=0,
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            ),
            Project(
                id=2,
                name="Test Project 2",
                description="Description 2",
                order_index=1,
                created_at="2024-01-02T00:00:00",
                updated_at="2024-01-02T00:00:00",
            ),
        ]

        # Consoleをモック
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        display.show_project_list(projects)

        # 出力を取得
        output = console.export_text()

        # 期待される内容が含まれることを確認
        assert "プロジェクト一覧" in output
        assert "Test Project 1" in output
        assert "Test Project 2" in output

    def test_show_project_list_empty(self, monkeypatch):
        """プロジェクト一覧表示（空）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        display.show_project_list([])

        output = console.export_text()
        assert "プロジェクトが見つかりません" in output


class TestShowProjectTree:
    """show_project_tree関数のテスト"""

    def test_show_project_tree_not_found(self, temp_db, monkeypatch):
        """プロジェクトツリー表示（存在しないID）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        display.show_project_tree(temp_db, 999, use_emoji=True)

        output = console.export_text()
        assert "が見つかりません" in output

    def test_show_project_tree_with_data(self, temp_db, monkeypatch):
        """プロジェクトツリー表示（データあり）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        # テストデータ作成
        proj_repo = ProjectRepository(temp_db)
        subproj_repo = SubProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)

        proj = proj_repo.create("TestProject", "Test description")
        subproj = subproj_repo.create(proj.id, "TestSubProject", description="Test subdesc")
        task = task_repo.create(
            project_id=proj.id,
            subproject_id=subproj.id,
            name="TestTask",
            description="Test task desc",
        )

        display.show_project_tree(temp_db, proj.id, use_emoji=True)

        output = console.export_text()
        assert "TestProject" in output
        assert "TestSubProject" in output
        assert "TestTask" in output

    def test_show_project_tree_with_direct_tasks(self, temp_db, monkeypatch):
        """プロジェクトツリー表示（direct tasks）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        # テストデータ作成
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)

        proj = proj_repo.create("TestProject", "Test description")
        # subproject_id=None のタスク（direct task）
        task = task_repo.create(
            project_id=proj.id,
            subproject_id=None,
            name="DirectTask",
            description="Direct task desc",
        )

        display.show_project_tree(temp_db, proj.id, use_emoji=False)

        output = console.export_text()
        assert "TestProject" in output
        assert "DirectTask" in output
        assert "Tasks (direct)" in output


class TestShowDependencies:
    """show_dependencies関数のテスト"""

    def test_show_dependencies_task_with_predecessors_and_successors(
        self, temp_db, monkeypatch
    ):
        """Task依存関係表示（先行・後続あり）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        # テストデータ作成
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)

        proj = proj_repo.create("TestProject", "Test description")
        task1 = task_repo.create(
            project_id=proj.id, subproject_id=None, name="Task1", description="desc1"
        )
        task2 = task_repo.create(
            project_id=proj.id, subproject_id=None, name="Task2", description="desc2"
        )

        display.show_dependencies("Task", task1.id, [task2], [], use_emoji=True)

        output = console.export_text()
        assert f"Task ID={task1.id} の依存関係" in output
        assert "先行ノード" in output
        assert "Task2" in output

    def test_show_dependencies_task_no_predecessors_no_successors(
        self, temp_db, monkeypatch
    ):
        """Task依存関係表示（先行・後続なし）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        display.show_dependencies("Task", 1, [], [], use_emoji=False)

        output = console.export_text()
        assert "先行ノードなし" in output
        assert "後続ノードなし" in output

    def test_show_dependencies_subtask(self, temp_db, monkeypatch):
        """SubTask依存関係表示"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        # テストデータ作成
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        subtask_repo = SubTaskRepository(temp_db)

        proj = proj_repo.create("TestProject", "Test description")
        task = task_repo.create(
            project_id=proj.id, subproject_id=None, name="Task", description="desc"
        )
        subtask1 = subtask_repo.create(task.id, "SubTask1", "desc1")
        subtask2 = subtask_repo.create(task.id, "SubTask2", "desc2")

        display.show_dependencies("SubTask", subtask1.id, [], [subtask2], use_emoji=True)

        output = console.export_text()
        assert f"SubTask ID={subtask1.id} の依存関係" in output
        assert "後続ノード" in output
        assert "SubTask2" in output


class TestShowDoctorReport:
    """show_doctor_report関数のテスト"""

    def test_show_doctor_report_healthy(self, monkeypatch):
        """doctor report表示（正常）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        report = DoctorReport(errors=[], warnings=[])

        display.show_doctor_report(report)

        output = console.export_text()
        assert "Doctor Check Report" in output
        assert "Errors:   0" in output
        assert "Warnings: 0" in output
        assert "問題は検出されませんでした" in output

    def test_show_doctor_report_with_errors(self, monkeypatch):
        """doctor report表示（エラーあり）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        errors = [
            Issue(level=IssueLevel.ERROR, code="E001", message="Test error 1", details={}),
            Issue(level=IssueLevel.ERROR, code="E002", message="Test error 2", details={}),
        ]
        report = DoctorReport(errors=errors, warnings=[])

        display.show_doctor_report(report)

        output = console.export_text()
        assert "Errors:   2" in output
        assert "E001" in output
        assert "Test error 1" in output

    def test_show_doctor_report_with_warnings(self, monkeypatch):
        """doctor report表示（警告あり）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        warnings = [
            Issue(level=IssueLevel.WARNING, code="W001", message="Test warning 1", details={}),
        ]
        report = DoctorReport(errors=[], warnings=warnings)

        display.show_doctor_report(report)

        output = console.export_text()
        assert "Warnings: 1" in output
        assert "W001" in output
        assert "Test warning 1" in output


class TestShowDependencyGraphTask:
    """show_dependency_graph_task関数のテスト"""

    def test_show_dependency_graph_task_not_found(self, temp_db, monkeypatch):
        """Task依存グラフ表示（存在しないID）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        display.show_dependency_graph_task(temp_db, 999, [], [])

        output = console.export_text()
        assert "が見つかりません" in output

    def test_show_dependency_graph_task_with_data(self, temp_db, monkeypatch):
        """Task依存グラフ表示（データあり）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)
        # formatters.format_task_status をモック
        monkeypatch.setattr("pmtool.tui.formatters.format_task_status", lambda status: f"[{status}]")

        # テストデータ作成
        proj_repo = ProjectRepository(temp_db)
        subproj_repo = SubProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)

        proj = proj_repo.create("TestProject", "Test description")
        subproj = subproj_repo.create(proj.id, "TestSubProject", description="Test subdesc")
        task1 = task_repo.create(
            project_id=proj.id,
            subproject_id=subproj.id,
            name="Task1",
            description="desc1",
        )
        task2 = task_repo.create(
            project_id=proj.id,
            subproject_id=subproj.id,
            name="Task2",
            description="desc2",
        )

        display.show_dependency_graph_task(temp_db, task1.id, [], [task2.id])

        output = console.export_text()
        assert "Dependency Graph" in output
        assert "Direct Successors" in output


class TestShowDependencyGraphSubTask:
    """show_dependency_graph_subtask関数のテスト"""

    def test_show_dependency_graph_subtask_not_found(self, temp_db, monkeypatch):
        """SubTask依存グラフ表示（存在しないID）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        display.show_dependency_graph_subtask(temp_db, 999, [], [])

        output = console.export_text()
        assert "が見つかりません" in output

    def test_show_dependency_graph_subtask_with_data(self, temp_db, monkeypatch):
        """SubTask依存グラフ表示（データあり）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        # テストデータ作成
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        subtask_repo = SubTaskRepository(temp_db)

        proj = proj_repo.create("TestProject", "Test description")
        task = task_repo.create(
            project_id=proj.id, subproject_id=None, name="Task", description="desc"
        )
        subtask1 = subtask_repo.create(task.id, "SubTask1", "desc1")
        subtask2 = subtask_repo.create(task.id, "SubTask2", "desc2")

        display.show_dependency_graph_subtask(temp_db, subtask1.id, [], [subtask2.id])

        output = console.export_text()
        assert "Dependency Graph" in output
        assert "Direct Successors" in output


class TestShowDependencyChainTask:
    """show_dependency_chain_task関数のテスト"""

    def test_show_dependency_chain_task(self, temp_db, monkeypatch):
        """Task依存チェーン表示"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        # テストデータ作成
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)

        proj = proj_repo.create("TestProject", "Test description")
        task1 = task_repo.create(
            project_id=proj.id, subproject_id=None, name="Task1", description="desc1"
        )
        task2 = task_repo.create(
            project_id=proj.id, subproject_id=None, name="Task2", description="desc2"
        )

        display.show_dependency_chain_task(temp_db, [task1.id, task2.id])

        output = console.export_text()
        assert "Dependency Chain" in output
        assert "Task1" in output
        assert "Task2" in output


class TestShowDependencyChainSubTask:
    """show_dependency_chain_subtask関数のテスト"""

    def test_show_dependency_chain_subtask(self, temp_db, monkeypatch):
        """SubTask依存チェーン表示"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        # テストデータ作成
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        subtask_repo = SubTaskRepository(temp_db)

        proj = proj_repo.create("TestProject", "Test description")
        task = task_repo.create(
            project_id=proj.id, subproject_id=None, name="Task", description="desc"
        )
        subtask1 = subtask_repo.create(task.id, "SubTask1", "desc1")
        subtask2 = subtask_repo.create(task.id, "SubTask2", "desc2")

        display.show_dependency_chain_subtask(temp_db, [subtask1.id, subtask2.id])

        output = console.export_text()
        assert "Dependency Chain" in output
        assert "SubTask1" in output
        assert "SubTask2" in output


class TestShowImpactAnalysisTask:
    """show_impact_analysis_task関数のテスト"""

    def test_show_impact_analysis_task_not_found(self, temp_db, monkeypatch):
        """Task影響分析表示（存在しないID）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        display.show_impact_analysis_task(temp_db, 999, [])

        output = console.export_text()
        assert "が見つかりません" in output

    def test_show_impact_analysis_task_with_data(self, temp_db, monkeypatch):
        """Task影響分析表示（データあり）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        # テストデータ作成
        proj_repo = ProjectRepository(temp_db)
        subproj_repo = SubProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)

        proj = proj_repo.create("TestProject", "Test description")
        subproj = subproj_repo.create(proj.id, "TestSubProject", description="Test subdesc")
        task1 = task_repo.create(
            project_id=proj.id,
            subproject_id=subproj.id,
            name="Task1",
            description="desc1",
        )
        task2 = task_repo.create(
            project_id=proj.id,
            subproject_id=subproj.id,
            name="Task2",
            description="desc2",
        )

        display.show_impact_analysis_task(temp_db, task1.id, [task2.id])

        output = console.export_text()
        assert "Impact Analysis" in output
        assert "後続Task" in output

    def test_show_impact_analysis_task_no_successors(self, temp_db, monkeypatch):
        """Task影響分析表示（後続なし）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        # テストデータ作成
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)

        proj = proj_repo.create("TestProject", "Test description")
        task = task_repo.create(
            project_id=proj.id, subproject_id=None, name="Task", description="desc"
        )

        display.show_impact_analysis_task(temp_db, task.id, [])

        output = console.export_text()
        assert "影響を受けるTaskはありません" in output


class TestShowImpactAnalysisSubTask:
    """show_impact_analysis_subtask関数のテスト"""

    def test_show_impact_analysis_subtask_not_found(self, temp_db, monkeypatch):
        """SubTask影響分析表示（存在しないID）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        display.show_impact_analysis_subtask(temp_db, 999, [])

        output = console.export_text()
        assert "が見つかりません" in output

    def test_show_impact_analysis_subtask_with_data(self, temp_db, monkeypatch):
        """SubTask影響分析表示（データあり）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        # テストデータ作成
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        subtask_repo = SubTaskRepository(temp_db)

        proj = proj_repo.create("TestProject", "Test description")
        task = task_repo.create(
            project_id=proj.id, subproject_id=None, name="Task", description="desc"
        )
        subtask1 = subtask_repo.create(task.id, "SubTask1", "desc1")
        subtask2 = subtask_repo.create(task.id, "SubTask2", "desc2")

        display.show_impact_analysis_subtask(temp_db, subtask1.id, [subtask2.id])

        output = console.export_text()
        assert "Impact Analysis" in output
        assert "後続SubTask" in output

    def test_show_impact_analysis_subtask_no_successors(self, temp_db, monkeypatch):
        """SubTask影響分析表示（後続なし）"""
        console = Console(record=True)
        monkeypatch.setattr("pmtool.tui.display.console", console)

        # テストデータ作成
        proj_repo = ProjectRepository(temp_db)
        task_repo = TaskRepository(temp_db)
        subtask_repo = SubTaskRepository(temp_db)

        proj = proj_repo.create("TestProject", "Test description")
        task = task_repo.create(
            project_id=proj.id, subproject_id=None, name="Task", description="desc"
        )
        subtask = subtask_repo.create(task.id, "SubTask", "desc")

        display.show_impact_analysis_subtask(temp_db, subtask.id, [])

        output = console.export_text()
        assert "影響を受けるSubTaskはありません" in output
