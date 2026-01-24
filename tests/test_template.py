"""
template.py（TemplateManager）のテスト

Phase 5で追加されたテンプレート機能のテスト。
"""

import pytest
import sqlite3
from pathlib import Path

from pmtool.database import Database
from pmtool.template import TemplateManager
from pmtool.repository import ProjectRepository, SubProjectRepository, TaskRepository, SubTaskRepository
from pmtool.dependencies import DependencyManager
from pmtool.exceptions import EntityNotFoundError


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
def template_manager(db):
    """TemplateManager fixture"""
    return TemplateManager(db)


@pytest.fixture
def repos(db):
    """Repository fixtures"""
    return {
        "project": ProjectRepository(db),
        "subproject": SubProjectRepository(db),
        "task": TaskRepository(db),
        "subtask": SubTaskRepository(db),
        "dep": DependencyManager(db),
    }


def test_list_templates_empty(template_manager):
    """テンプレート一覧（空）"""
    templates = template_manager.list_templates()
    assert templates == []


def test_save_template_basic(template_manager, repos):
    """基本的なテンプレート保存（Task含まず）"""
    # Project作成
    project = repos["project"].create("Test Project", "desc")

    # SubProject作成
    subproject = repos["subproject"].create(
        project.id, "Test SubProject", None, "desc"
    )

    # テンプレート保存（include_tasks=False）
    result = template_manager.save_template(
        subproject_id=subproject.id,
        name="Template1",
        description="Test template",
        include_tasks=False,
    )

    assert result.template is not None
    assert result.template.name == "Template1"
    assert result.template.description == "Test template"
    assert result.external_dependencies == []

    # テンプレート一覧で確認
    templates = template_manager.list_templates()
    assert len(templates) == 1
    assert templates[0].name == "Template1"


def test_save_template_with_tasks(template_manager, repos):
    """Task含むテンプレート保存"""
    # Project → SubProject → Task → SubTask 作成
    project = repos["project"].create("Test Project", "desc")
    subproject = repos["subproject"].create(
        project.id, "Test SubProject", None, "desc"
    )
    task = repos["task"].create(project.id, "Task1", subproject.id, "desc")
    subtask = repos["subtask"].create(task.id, "SubTask1", "desc")

    # テンプレート保存（include_tasks=True）
    result = template_manager.save_template(
        subproject_id=subproject.id,
        name="Template2",
        description="Template with tasks",
        include_tasks=True,
    )

    assert result.template is not None
    assert result.external_dependencies == []

    # 詳細取得でTask/SubTaskを確認
    template = template_manager.get_template(result.template.id)
    assert template is not None


def test_save_template_with_external_dependencies(template_manager, repos):
    """外部依存を持つテンプレート保存（警告あり）"""
    # 同一Project内に2つのSubProjectを作成
    project1 = repos["project"].create("Project1", "desc")
    subproject1 = repos["subproject"].create(project1.id, "SubProject1", None, "desc")
    task1 = repos["task"].create(project1.id, "Task1", subproject1.id, "desc")

    # 同じProject1内の別SubProject
    subproject2 = repos["subproject"].create(project1.id, "SubProject2", None, "desc")
    task2 = repos["task"].create(project1.id, "Task2", subproject2.id, "desc")

    # Task1 → Task2 の依存関係（SubProject1の外部、SubProject2に依存）
    repos["dep"].add_task_dependency(task1.id, task2.id)

    # テンプレート保存（SubProject1）
    result = template_manager.save_template(
        subproject_id=subproject1.id,
        name="Template3",
        description="Template with external deps",
        include_tasks=True,
    )

    assert result.template is not None
    assert len(result.external_dependencies) > 0  # 外部依存警告あり


def test_get_template_not_found(template_manager):
    """存在しないテンプレート取得"""
    template = template_manager.get_template(9999)
    assert template is None


def test_get_template_by_name(template_manager, repos):
    """名前でテンプレート取得"""
    project = repos["project"].create("Test Project", "desc")
    subproject = repos["subproject"].create(project.id, "SubProject", None, "desc")

    # テンプレート保存
    result = template_manager.save_template(
        subproject_id=subproject.id,
        name="UniqueTemplate",
        description="desc",
        include_tasks=False,
    )

    # 名前で取得
    template = template_manager.get_template_by_name("UniqueTemplate")
    assert template is not None
    assert template.id == result.template.id


def test_delete_template(template_manager, repos):
    """テンプレート削除"""
    project = repos["project"].create("Test Project", "desc")
    subproject = repos["subproject"].create(project.id, "SubProject", None, "desc")

    # テンプレート保存
    result = template_manager.save_template(
        subproject_id=subproject.id,
        name="DeleteTest",
        description="desc",
        include_tasks=False,
    )

    template_id = result.template.id

    # 削除前確認
    assert template_manager.get_template(template_id) is not None

    # 削除
    template_manager.delete_template(template_id)

    # 削除後確認
    assert template_manager.get_template(template_id) is None


def test_apply_template_basic(template_manager, repos):
    """基本的なテンプレート適用"""
    # 元のSubProject作成
    project1 = repos["project"].create("Project1", "desc")
    subproject1 = repos["subproject"].create(project1.id, "SubProject1", None, "desc")
    task1 = repos["task"].create(project1.id, "Task1", subproject1.id, "desc")

    # テンプレート保存
    result = template_manager.save_template(
        subproject_id=subproject1.id,
        name="Template1",
        description="desc",
        include_tasks=True,
    )

    # 別のProjectに適用
    project2 = repos["project"].create("Project2", "desc")

    new_subproject_id = template_manager.apply_template(
        template_id=result.template.id,
        project_id=project2.id,
        new_subproject_name="Applied SubProject",
    )

    # apply_template()はSubProject IDを返すので、get_by_id()で取得
    new_subproject = repos["subproject"].get_by_id(new_subproject_id)
    assert new_subproject is not None
    assert new_subproject.name == "Applied SubProject"
    assert new_subproject.project_id == project2.id


def test_apply_template_not_found(template_manager, repos):
    """存在しないテンプレート適用"""
    project = repos["project"].create("Project", "desc")

    with pytest.raises(EntityNotFoundError):
        template_manager.apply_template(
            template_id=9999,
            project_id=project.id,
            new_subproject_name="New SubProject",
        )


def test_dry_run(template_manager, repos):
    """dry_runテスト"""
    # SubProject作成（Task含む）
    project = repos["project"].create("Project1", "desc")
    subproject = repos["subproject"].create(project.id, "SubProject1", None, "desc")
    task1 = repos["task"].create(project.id, "Task1", subproject.id, "desc")
    task2 = repos["task"].create(project.id, "Task2", subproject.id, "desc")

    # テンプレート保存
    result = template_manager.save_template(
        subproject_id=subproject.id,
        name="DryRunTest",
        description="desc",
        include_tasks=True,
    )

    # dry_run実行（別のProjectに適用想定）
    project2 = repos["project"].create("Project2", "desc")
    preview = template_manager.dry_run(result.template.id, project2.id, "Preview SubProject")

    assert preview["template_name"] == "DryRunTest"
    assert preview["task_count"] == 2
    assert preview["subtask_count"] == 0
    assert preview["dependency_count"] == 0
    assert len(preview["tasks"]) == 2


def test_detect_external_dependencies_none(template_manager, repos):
    """外部依存なしのケース"""
    # SubProject作成（内部依存のみ）
    project = repos["project"].create("Project1", "desc")
    subproject = repos["subproject"].create(project.id, "SubProject1", None, "desc")
    task1 = repos["task"].create(project.id, "Task1", subproject.id, "desc")
    task2 = repos["task"].create(project.id, "Task2", subproject.id, "desc")

    # Task1 → Task2 依存（内部）
    repos["dep"].add_task_dependency(task1.id, task2.id)

    # 外部依存検出
    warnings = template_manager.detect_external_dependencies(subproject.id)

    assert warnings == []


def test_detect_external_dependencies_exists(template_manager, repos):
    """外部依存ありのケース"""
    # 同一Project内に2つのSubProjectを作成
    project1 = repos["project"].create("Project1", "desc")
    subproject1 = repos["subproject"].create(project1.id, "SubProject1", None, "desc")
    task1 = repos["task"].create(project1.id, "Task1", subproject1.id, "desc")

    # 同じProject1内の別SubProject
    subproject2 = repos["subproject"].create(project1.id, "SubProject2", None, "desc")
    task2 = repos["task"].create(project1.id, "Task2", subproject2.id, "desc")

    # Task1 → Task2 依存（SubProject1の外部、SubProject2に依存）
    repos["dep"].add_task_dependency(task1.id, task2.id)

    # 外部依存検出
    warnings = template_manager.detect_external_dependencies(subproject1.id)

    assert len(warnings) > 0
    # Task2(SubProject2)がTask1(SubProject1)に依存している = SubProject1の外部依存
    # direction='incoming'なので、from=Task2, to=Task1
    assert warnings[0].from_task_id == task2.id
    assert warnings[0].to_task_id == task1.id
    assert warnings[0].direction == 'incoming'
