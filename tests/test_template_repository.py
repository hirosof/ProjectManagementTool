"""
repository_template.py（TemplateRepository）のテスト

Phase 5で追加されたテンプレート系テーブルのCRUD操作のテスト。
"""

import pytest
import sqlite3
from pathlib import Path

from pmtool.database import Database
from pmtool.repository_template import TemplateRepository


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
def template_repo(db):
    """TemplateRepository fixture"""
    return TemplateRepository(db)


def test_add_template(template_repo):
    """テンプレート追加"""
    template = template_repo.add_template(
        name="Test Template",
        description="Test description",
        include_tasks=True,
    )

    assert template.id is not None
    assert template.name == "Test Template"
    assert template.description == "Test description"
    assert template.include_tasks is True


def test_add_template_duplicate_name(template_repo):
    """テンプレート名重複エラー"""
    template_repo.add_template(
        name="Duplicate",
        description="First",
        include_tasks=False,
    )

    # 同じ名前で再度追加 → UNIQUE制約違反
    with pytest.raises(sqlite3.IntegrityError):
        template_repo.add_template(
            name="Duplicate",
            description="Second",
            include_tasks=False,
        )


def test_get_template(template_repo):
    """テンプレート取得"""
    # テンプレート追加
    added = template_repo.add_template(
        name="GetTest",
        description="desc",
        include_tasks=True,
    )

    # 取得
    template = template_repo.get_template(added.id)

    assert template is not None
    assert template.id == added.id
    assert template.name == "GetTest"


def test_get_template_not_found(template_repo):
    """存在しないテンプレート取得"""
    template = template_repo.get_template(9999)
    assert template is None


def test_get_template_by_name(template_repo):
    """名前でテンプレート取得"""
    template_repo.add_template(
        name="ByNameTest",
        description="desc",
        include_tasks=False,
    )

    template = template_repo.get_template_by_name("ByNameTest")

    assert template is not None
    assert template.name == "ByNameTest"


def test_get_template_by_name_not_found(template_repo):
    """存在しない名前でテンプレート取得"""
    template = template_repo.get_template_by_name("NonExistent")
    assert template is None


def test_list_templates(template_repo):
    """テンプレート一覧取得"""
    # 複数のテンプレート追加
    template_repo.add_template("Template1", "desc1", True)
    template_repo.add_template("Template2", "desc2", False)
    template_repo.add_template("Template3", "desc3", True)

    # 一覧取得
    templates = template_repo.list_templates()

    assert len(templates) == 3
    # 作成日時昇順（Template1が最初）
    assert templates[0].name == "Template1"
    assert templates[1].name == "Template2"
    assert templates[2].name == "Template3"


def test_delete_template(template_repo):
    """テンプレート削除"""
    # テンプレート追加
    template = template_repo.add_template("DeleteTest", "desc", False)

    # 削除前確認
    assert template_repo.get_template(template.id) is not None

    # 削除
    template_repo.delete_template(template.id)

    # 削除後確認
    assert template_repo.get_template(template.id) is None


def test_add_template_task(template_repo):
    """TemplateTask追加"""
    # テンプレート追加
    template = template_repo.add_template("Template1", "desc", True)

    # TemplateTask追加
    task = template_repo.add_template_task(
        template_id=template.id,
        task_order=0,
        name="Task1",
        description="Task description",
    )

    assert task.id is not None
    assert task.template_id == template.id
    assert task.name == "Task1"
    assert task.task_order == 0


def test_get_template_tasks(template_repo):
    """TemplateTasks取得"""
    # テンプレート追加
    template = template_repo.add_template("Template1", "desc", True)

    # 複数のTemplateTask追加
    template_repo.add_template_task(template.id, 0, "Task1", "desc")
    template_repo.add_template_task(template.id, 1, "Task2", "desc")
    template_repo.add_template_task(template.id, 2, "Task3", "desc")

    # 取得
    tasks = template_repo.get_template_tasks(template.id)

    assert len(tasks) == 3
    # task_order順
    assert tasks[0].name == "Task1"
    assert tasks[1].name == "Task2"
    assert tasks[2].name == "Task3"


def test_add_template_subtask(template_repo):
    """TemplateSubTask追加"""
    # テンプレート→Task追加
    template = template_repo.add_template("Template1", "desc", True)
    task = template_repo.add_template_task(template.id, 0, "Task1", "desc")

    # TemplateSubTask追加
    subtask = template_repo.add_template_subtask(
        template_task_id=task.id,
        subtask_order=0,
        name="SubTask1",
        description="SubTask description",
    )

    assert subtask.id is not None
    assert subtask.template_task_id == task.id
    assert subtask.name == "SubTask1"
    assert subtask.subtask_order == 0


def test_get_template_subtasks(template_repo):
    """TemplateSubTasks取得"""
    # テンプレート→Task追加
    template = template_repo.add_template("Template1", "desc", True)
    task = template_repo.add_template_task(template.id, 0, "Task1", "desc")

    # 複数のTemplateSubTask追加
    template_repo.add_template_subtask(task.id, 0, "SubTask1", "desc")
    template_repo.add_template_subtask(task.id, 1, "SubTask2", "desc")

    # 取得
    subtasks = template_repo.get_template_subtasks(task.id)

    assert len(subtasks) == 2
    # subtask_order順
    assert subtasks[0].name == "SubTask1"
    assert subtasks[1].name == "SubTask2"


def test_add_template_dependency(template_repo):
    """TemplateDependency追加"""
    # テンプレート→Task追加
    template = template_repo.add_template("Template1", "desc", True)
    task1 = template_repo.add_template_task(template.id, 0, "Task1", "desc")
    task2 = template_repo.add_template_task(template.id, 1, "Task2", "desc")

    # TemplateDependency追加（Task1 → Task2）
    dep = template_repo.add_template_dependency(
        template_id=template.id,
        predecessor_order=0,
        successor_order=1,
    )

    assert dep.id is not None
    assert dep.template_id == template.id
    assert dep.predecessor_order == 0
    assert dep.successor_order == 1


def test_get_template_dependencies(template_repo):
    """TemplateDependencies取得"""
    # テンプレート→Task追加
    template = template_repo.add_template("Template1", "desc", True)
    template_repo.add_template_task(template.id, 0, "Task1", "desc")
    template_repo.add_template_task(template.id, 1, "Task2", "desc")
    template_repo.add_template_task(template.id, 2, "Task3", "desc")

    # 複数のTemplateDependency追加
    template_repo.add_template_dependency(template.id, 0, 1)  # Task1 → Task2
    template_repo.add_template_dependency(template.id, 1, 2)  # Task2 → Task3

    # 取得
    deps = template_repo.get_template_dependencies(template.id)

    assert len(deps) == 2
    assert deps[0].predecessor_order == 0
    assert deps[0].successor_order == 1
    assert deps[1].predecessor_order == 1
    assert deps[1].successor_order == 2


def test_own_conn_pattern(template_repo):
    """own_connパターンのテスト"""
    # 外部トランザクション内での操作
    conn = template_repo.db.connect()

    try:
        # conn渡してテンプレート追加
        template = template_repo.add_template(
            name="TransactionTest",
            description="desc",
            include_tasks=False,
            conn=conn,
        )

        # コミット前は他の接続から見えない
        template2 = template_repo.get_template(template.id)
        # ただし、同じconnでは見える
        template3 = template_repo.get_template(template.id, conn=conn)
        assert template3 is not None

        conn.commit()

        # コミット後は見える
        template4 = template_repo.get_template(template.id)
        assert template4 is not None

    finally:
        conn.close()


def test_cascade_delete_template_tasks(template_repo):
    """テンプレート削除時のCASCADE確認（TemplateTask）"""
    # テンプレート→Task追加
    template = template_repo.add_template("CascadeTest", "desc", True)
    task = template_repo.add_template_task(template.id, 0, "Task1", "desc")

    # 削除前確認
    assert len(template_repo.get_template_tasks(template.id)) == 1

    # テンプレート削除
    template_repo.delete_template(template.id)

    # TemplateTaskも削除されている
    assert len(template_repo.get_template_tasks(template.id)) == 0


def test_cascade_delete_template_dependencies(template_repo):
    """テンプレート削除時のCASCADE確認（TemplateDependency）"""
    # テンプレート→Task→Dependency追加
    template = template_repo.add_template("CascadeTest", "desc", True)
    template_repo.add_template_task(template.id, 0, "Task1", "desc")
    template_repo.add_template_task(template.id, 1, "Task2", "desc")
    template_repo.add_template_dependency(template.id, 0, 1)

    # 削除前確認
    assert len(template_repo.get_template_dependencies(template.id)) == 1

    # テンプレート削除
    template_repo.delete_template(template.id)

    # TemplateDependencyも削除されている
    assert len(template_repo.get_template_dependencies(template.id)) == 0
