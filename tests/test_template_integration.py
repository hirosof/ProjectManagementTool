"""
テンプレート機能の統合テスト

Phase 5で追加されたテンプレート機能の保存→適用の一連の流れをテスト。
"""

import pytest
from pathlib import Path

from pmtool.database import Database
from pmtool.template import TemplateManager
from pmtool.repository import (
    ProjectRepository,
    SubProjectRepository,
    TaskRepository,
    SubTaskRepository,
)
from pmtool.dependencies import DependencyManager


@pytest.fixture
def db():
    """テスト用DBセットアップ"""
    db_path = ":memory:"
    database = Database(db_path)

    # init_db.sqlを適用
    init_sql = Path("scripts/init_db.sql")
    database.initialize(init_sql, force=True)

    yield database

    database.close()


@pytest.fixture
def managers(db):
    """Manager/Repository fixtures"""
    return {
        "template": TemplateManager(db),
        "project": ProjectRepository(db),
        "subproject": SubProjectRepository(db),
        "task": TaskRepository(db),
        "subtask": SubTaskRepository(db),
        "dep": DependencyManager(db),
    }


def test_save_and_apply_basic(managers):
    """保存→適用の基本フロー"""
    # ===== 元のSubProject作成 =====
    project1 = managers["project"].create("Project1", "desc")
    subproject1 = managers["subproject"].create(
        project1.id, "SubProject1", None, "desc"
    )
    task1 = managers["task"].create(project1.id, "Task1", subproject1.id, "desc")
    task2 = managers["task"].create(project1.id, "Task2", subproject1.id, "desc")
    subtask1 = managers["subtask"].create(task1.id, "SubTask1", "desc")

    # ===== テンプレート保存 =====
    result = managers["template"].save_template(
        subproject_id=subproject1.id,
        name="SaveApplyTest",
        description="Integration test",
        include_tasks=True,
    )

    assert result.template is not None

    # ===== 別のProjectに適用 =====
    project2 = managers["project"].create("Project2", "desc")

    new_subproject = managers["template"].apply_template(
        template_id=result.template.id,
        project_id=project2.id,
        new_subproject_name="Applied SubProject",
    )

    assert new_subproject is not None
    assert new_subproject.name == "Applied SubProject"
    assert new_subproject.project_id == project2.id

    # ===== 適用後のTask/SubTask確認 =====
    new_tasks = managers["task"].get_tasks_by_subproject(new_subproject.id)
    assert len(new_tasks) == 2

    new_subtasks = managers["subtask"].get_subtasks_by_task(new_tasks[0].id)
    assert len(new_subtasks) == 1


def test_save_and_apply_with_dependencies(managers):
    """依存関係を持つテンプレートの保存→適用"""
    # ===== 元のSubProject作成（依存関係あり） =====
    project1 = managers["project"].create("Project1", "desc")
    subproject1 = managers["subproject"].create(
        project1.id, "SubProject1", None, "desc"
    )
    task1 = managers["task"].create(project1.id, "Task1", subproject1.id, "desc")
    task2 = managers["task"].create(project1.id, "Task2", subproject1.id, "desc")
    task3 = managers["task"].create(project1.id, "Task3", subproject1.id, "desc")

    # Task依存関係: Task1 → Task2, Task2 → Task3
    managers["dep"].add_task_dependency(task1.id, task2.id)
    managers["dep"].add_task_dependency(task2.id, task3.id)

    # ===== テンプレート保存 =====
    result = managers["template"].save_template(
        subproject_id=subproject1.id,
        name="DependencyTest",
        description="With dependencies",
        include_tasks=True,
    )

    assert result.template is not None

    # ===== 適用 =====
    project2 = managers["project"].create("Project2", "desc")
    new_subproject = managers["template"].apply_template(
        template_id=result.template.id,
        project_id=project2.id,
        new_subproject_name="Applied with Deps",
    )

    # ===== 適用後の依存関係確認 =====
    new_tasks = managers["task"].get_tasks_by_subproject(new_subproject.id)
    assert len(new_tasks) == 3

    # Task1の後続確認
    successors = managers["dep"].get_task_successors(new_tasks[0].id)

    assert len(successors) > 0


def test_save_and_apply_large_template(managers):
    """大規模テンプレート（100+ノード）の保存→適用"""
    # ===== 大規模SubProject作成 =====
    project1 = managers["project"].create("LargeProject", "desc")
    subproject1 = managers["subproject"].create(
        project1.id, "LargeSubProject", None, "desc"
    )

    # 50個のTask作成
    for i in range(50):
        task = managers["task"].create(
            project1.id, f"Task{i+1}", subproject1.id, f"desc{i+1}"
        )

        # 各Taskに2個のSubTask作成
        managers["subtask"].create(task.id, f"SubTask{i*2+1}", "desc")
        managers["subtask"].create(task.id, f"SubTask{i*2+2}", "desc")

    # ===== テンプレート保存 =====
    result = managers["template"].save_template(
        subproject_id=subproject1.id,
        name="LargeTemplate",
        description="100+ nodes",
        include_tasks=True,
    )

    assert result.template is not None

    # ===== 適用 =====
    project2 = managers["project"].create("Project2", "desc")
    new_subproject = managers["template"].apply_template(
        template_id=result.template.id,
        project_id=project2.id,
        new_subproject_name="Applied Large",
    )

    # ===== 適用後のノード数確認 =====
    new_tasks = managers["task"].get_tasks_by_subproject(new_subproject.id)
    assert len(new_tasks) == 50

    total_subtasks = 0
    for task in new_tasks:
        subtasks = managers["subtask"].get_subtasks_by_task(task.id)
        total_subtasks += len(subtasks)

    assert total_subtasks == 100


def test_dry_run_preview(managers):
    """dry_runプレビューの統合テスト"""
    # ===== SubProject作成 =====
    project1 = managers["project"].create("Project1", "desc")
    subproject1 = managers["subproject"].create(
        project1.id, "SubProject1", None, "desc"
    )
    task1 = managers["task"].create(project1.id, "Task1", subproject1.id, "desc")
    task2 = managers["task"].create(project1.id, "Task2", subproject1.id, "desc")
    subtask1 = managers["subtask"].create(task1.id, "SubTask1", "desc")
    subtask2 = managers["subtask"].create(task2.id, "SubTask2", "desc")

    # 依存関係追加
    managers["dep"].add_task_dependency(task1.id, task2.id)

    # ===== テンプレート保存 =====
    result = managers["template"].save_template(
        subproject_id=subproject1.id,
        name="DryRunTest",
        description="Preview test",
        include_tasks=True,
    )

    # ===== dry_run実行 =====
    project2 = managers["project"].create("Project2", "desc")
    preview = managers["template"].dry_run(result.template.id, project2.id, "Preview SubProject")

    assert preview["template_name"] == "DryRunTest"
    assert preview["task_count"] == 2
    assert preview["subtask_count"] == 2
    assert preview["dependency_count"] == 1
    assert len(preview["tasks"]) == 2


def test_multiple_templates_same_subproject(managers):
    """同じSubProjectから複数のテンプレートを保存"""
    # ===== SubProject作成 =====
    project1 = managers["project"].create("Project1", "desc")
    subproject1 = managers["subproject"].create(
        project1.id, "SubProject1", None, "desc"
    )
    managers["task"].create(project1.id, "Task1", subproject1.id, "desc")

    # ===== 複数のテンプレート保存 =====
    result1 = managers["template"].save_template(
        subproject_id=subproject1.id,
        name="Template1",
        description="First",
        include_tasks=True,
    )

    result2 = managers["template"].save_template(
        subproject_id=subproject1.id,
        name="Template2",
        description="Second",
        include_tasks=False,
    )

    assert result1.template is not None
    assert result2.template is not None

    # ===== テンプレート一覧確認 =====
    templates = managers["template"].list_templates()
    assert len(templates) == 2


def test_apply_template_multiple_times(managers):
    """同じテンプレートを複数回適用"""
    # ===== テンプレート作成 =====
    project1 = managers["project"].create("Project1", "desc")
    subproject1 = managers["subproject"].create(
        project1.id, "SubProject1", None, "desc"
    )
    managers["task"].create(project1.id, "Task1", subproject1.id, "desc")

    result = managers["template"].save_template(
        subproject_id=subproject1.id,
        name="ReusableTemplate",
        description="Apply multiple times",
        include_tasks=True,
    )

    # ===== 複数のProjectに適用 =====
    project2 = managers["project"].create("Project2", "desc")
    project3 = managers["project"].create("Project3", "desc")

    new_subproject1 = managers["template"].apply_template(
        template_id=result.template.id,
        project_id=project2.id,
        new_subproject_name="Applied1",
    )

    new_subproject2 = managers["template"].apply_template(
        template_id=result.template.id,
        project_id=project3.id,
        new_subproject_name="Applied2",
    )

    assert new_subproject1.project_id == project2.id
    assert new_subproject2.project_id == project3.id


def test_delete_template_does_not_affect_applied(managers):
    """テンプレート削除しても適用済みのSubProjectは影響を受けない"""
    # ===== テンプレート作成→適用 =====
    project1 = managers["project"].create("Project1", "desc")
    subproject1 = managers["subproject"].create(
        project1.id, "SubProject1", None, "desc"
    )
    managers["task"].create(project1.id, "Task1", subproject1.id, "desc")

    result = managers["template"].save_template(
        subproject_id=subproject1.id,
        name="DeleteTest",
        description="desc",
        include_tasks=True,
    )

    project2 = managers["project"].create("Project2", "desc")
    new_subproject = managers["template"].apply_template(
        template_id=result.template.id,
        project_id=project2.id,
        new_subproject_name="Applied",
    )

    # ===== テンプレート削除 =====
    managers["template"].delete_template(result.template.id)

    # ===== 適用済みのSubProjectは影響を受けない =====
    still_exists = managers["subproject"].get_by_id(new_subproject.id)
    assert still_exists is not None

    tasks = managers["task"].get_tasks_by_subproject(new_subproject.id)
    assert len(tasks) == 1
