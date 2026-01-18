"""
repository層のテスト

CRUD操作、FK制約違反、トランザクション整合性を確認
"""

import pytest
import sqlite3

from pmtool.database import Database
from pmtool.repository import (
    ProjectRepository,
    SubProjectRepository,
    TaskRepository,
    SubTaskRepository,
)
from pmtool.exceptions import (
    ConstraintViolationError,
)


def test_create_project(temp_db: Database):
    """Projectの作成が正しく動作すること"""
    repo = ProjectRepository(temp_db)
    project = repo.create("Test Project", "Test Description")

    assert project.id is not None
    assert project.name == "Test Project"
    assert project.description == "Test Description"
    assert project.order_index == 0  # 最初のProjectはorder_index=0


def test_create_multiple_projects_order_index(temp_db: Database):
    """複数のProjectを作成すると自動的にorder_indexが増加すること"""
    repo = ProjectRepository(temp_db)

    p1 = repo.create("Project 1", "Desc 1")
    p2 = repo.create("Project 2", "Desc 2")
    p3 = repo.create("Project 3", "Desc 3")

    assert p1.order_index == 0
    assert p2.order_index == 1
    assert p3.order_index == 2


def test_delete_project_with_no_children(temp_db: Database):
    """子エンティティがないProjectは削除できること"""
    repo = ProjectRepository(temp_db)
    project = repo.create("Test Project", "Test Description")

    # 削除実行
    repo.delete(project.id)

    # 削除確認
    assert repo.get_by_id(project.id) is None


def test_delete_project_with_children_raises_error(temp_db: Database):
    """子SubProjectがあるProjectは削除できないこと（ChildExistsError）"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)

    project = proj_repo.create("Parent Project", "")
    subproject = subproj_repo.create(project.id, None, "Child SubProject", "")

    # 子がある状態で削除しようとするとエラー
    with pytest.raises(ConstraintViolationError) as exc_info:
        proj_repo.delete(project.id)

    assert "子エンティティが存在します" in str(exc_info.value)


def test_delete_nonexistent_entity_silent_success(temp_db: Database):
    """存在しないエンティティを削除しようとしてもエラーにならないこと（冪等性）"""
    repo = ProjectRepository(temp_db)

    # 存在しないIDを削除してもエラーにならない
    repo.delete(99999)  # エラーにならずに完了


def test_fk_constraint_violation_on_create_subproject(temp_db: Database):
    """存在しないproject_idでSubProjectを作成しようとするとエラーになること"""
    repo = SubProjectRepository(temp_db)

    # 存在しないproject_id=99999を指定
    with pytest.raises(ConstraintViolationError):
        repo.create(99999, None, "Invalid SubProject", "")


def test_fk_constraint_violation_on_create_task(temp_db: Database):
    """存在しないproject_idでTaskを作成しようとするとエラーになること"""
    repo = TaskRepository(temp_db)

    # 存在しないproject_id=99999を指定
    with pytest.raises(ConstraintViolationError):
        repo.create(99999, None, "Invalid Task", "")


def test_cascade_on_delete_with_subtasks(temp_db: Database):
    """Taskを削除するとSubTaskも削除されること（FK ON DELETE CASCADE）"""
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)

    # データ作成
    project = proj_repo.create("Project", "")
    task = task_repo.create(project.id, None, "Task", "")
    subtask = subtask_repo.create(task.id, "SubTask", "")

    # SubTaskが存在することを確認
    assert subtask_repo.get_by_id(subtask.id) is not None

    # Taskを削除（SubTaskも連鎖削除される）
    task_repo.delete(task.id)

    # SubTaskも削除されていることを確認
    assert subtask_repo.get_by_id(subtask.id) is None


def test_transaction_rollback_on_error(temp_db: Database):
    """トランザクション内でエラーが発生した場合、変更がロールバックされること"""
    proj_repo = ProjectRepository(temp_db)

    # 正常にProjectを作成
    project = proj_repo.create("Initial Project", "")
    initial_count = len(proj_repo.get_all())

    # トランザクション内でエラーを発生させる
    conn = temp_db.connect()
    try:
        # 新しいProjectを作成（コミット前）
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO projects (name, description, order_index, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            ("New Project", "Desc", 99, "2024-01-01T00:00:00", "2024-01-01T00:00:00")
        )

        # 意図的にエラーを発生させる（存在しないテーブル）
        cursor.execute("INSERT INTO nonexistent_table (id) VALUES (1)")

        conn.commit()  # ここには到達しない
    except sqlite3.OperationalError:
        conn.rollback()
    finally:
        # connectionはDatabase.connect()が返すシングルトンなので、closeしない
        pass

    # ロールバックされたため、Project数は変わらない
    assert len(proj_repo.get_all()) == initial_count


def test_get_by_id_returns_none_for_nonexistent(temp_db: Database):
    """存在しないIDでget_by_idを呼ぶとNoneを返すこと"""
    repo = ProjectRepository(temp_db)

    result = repo.get_by_id(99999)
    assert result is None


def test_update_project_preserves_other_fields(temp_db: Database):
    """Projectのname更新時に、他のフィールドが保持されること"""
    repo = ProjectRepository(temp_db)

    # 初期作成
    project = repo.create("Original Name", "Original Description")
    original_id = project.id
    original_order = project.order_index
    original_created = project.created_at

    # name のみ更新
    updated = repo.update(project.id, name="Updated Name")

    # name が更新されている
    assert updated.name == "Updated Name"

    # 他のフィールドは保持されている
    assert updated.id == original_id
    assert updated.description == "Original Description"
    assert updated.order_index == original_order
    assert updated.created_at == original_created

    # updated_at は変更されている
    assert updated.updated_at != original_created
