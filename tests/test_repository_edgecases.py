"""
repository層のエッジケース・境界値テスト

空文字、NULL、巨大な値、境界値（0, 1, MAX）を確認
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
    ValidationError,
    ConstraintViolationError,
)


# ========================================
# Project のエッジケース
# ========================================

def test_create_project_with_empty_name(temp_db: Database):
    """空の名前でProjectを作成しようとするとValidationErrorが発生すること"""
    repo = ProjectRepository(temp_db)

    with pytest.raises(ValidationError):
        repo.create("", "Description")


def test_create_project_with_whitespace_only_name(temp_db: Database):
    """空白のみの名前でProjectを作成しようとするとValidationErrorが発生すること"""
    repo = ProjectRepository(temp_db)

    with pytest.raises(ValidationError):
        repo.create("   ", "Description")


def test_create_project_with_none_description(temp_db: Database):
    """descriptionがNoneでもProjectを作成できること"""
    repo = ProjectRepository(temp_db)

    project = repo.create("Test Project", None)

    assert project.id is not None
    assert project.name == "Test Project"
    assert project.description is None


def test_create_project_with_empty_description(temp_db: Database):
    """空のdescriptionでProjectを作成できること"""
    repo = ProjectRepository(temp_db)

    project = repo.create("Test Project", "")

    assert project.id is not None
    assert project.name == "Test Project"
    assert project.description == ""


def test_create_project_with_very_long_name(temp_db: Database):
    """非常に長い名前でProjectを作成できること（1000文字）"""
    repo = ProjectRepository(temp_db)

    long_name = "A" * 1000
    project = repo.create(long_name, "Description")

    assert project.id is not None
    assert project.name == long_name


def test_create_project_with_very_long_description(temp_db: Database):
    """非常に長い説明でProjectを作成できること（10000文字）"""
    repo = ProjectRepository(temp_db)

    long_desc = "B" * 10000
    project = repo.create("Test Project", long_desc)

    assert project.id is not None
    assert project.description == long_desc


def test_create_project_with_special_characters_in_name(temp_db: Database):
    """特殊文字を含む名前でProjectを作成できること"""
    repo = ProjectRepository(temp_db)

    special_name = "Project <>&\"'`\n\t\r\0"
    project = repo.create(special_name, "Description")

    assert project.id is not None
    assert project.name == special_name


# ========================================
# SubProject のエッジケース
# ========================================

def test_create_subproject_with_invalid_project_id(temp_db: Database):
    """存在しないproject_idでSubProjectを作成しようとするとエラーが発生すること"""
    repo = SubProjectRepository(temp_db)

    with pytest.raises(ConstraintViolationError):
        repo.create(9999, "SubProject", "Description")


def test_create_subproject_with_project_id_zero(temp_db: Database):
    """project_id=0（存在しない）でSubProjectを作成しようとするとエラーが発生すること"""
    repo = SubProjectRepository(temp_db)

    with pytest.raises(ConstraintViolationError):
        repo.create(0, "SubProject", "Description")


def test_create_subproject_with_negative_project_id(temp_db: Database):
    """負のproject_idでSubProjectを作成しようとするとエラーが発生すること"""
    repo = SubProjectRepository(temp_db)

    with pytest.raises(ConstraintViolationError):
        repo.create(-1, "SubProject", "Description")


# ========================================
# Task のエッジケース
# ========================================

def test_create_task_with_invalid_subproject_id(temp_db: Database):
    """存在しないsubproject_idでTaskを作成しようとするとエラーが発生すること"""
    repo = TaskRepository(temp_db)

    with pytest.raises(ConstraintViolationError):
        repo.create(9999, "Task", "Description")


def test_create_task_with_empty_name(temp_db: Database):
    """空の名前でTaskを作成しようとするとValidationErrorが発生すること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", "Description")

    with pytest.raises(ValidationError):
        task_repo.create(subproject.id, "", "Description")


# ========================================
# SubTask のエッジケース
# ========================================

def test_create_subtask_with_invalid_task_id(temp_db: Database):
    """存在しないtask_idでSubTaskを作成しようとするとエラーが発生すること"""
    repo = SubTaskRepository(temp_db)

    with pytest.raises(ConstraintViolationError):
        repo.create(9999, "SubTask", "Description")


def test_create_subtask_with_empty_name(temp_db: Database):
    """空の名前でSubTaskを作成しようとするとValidationErrorが発生すること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", "Description")
    task = task_repo.create(subproject.id, "Task", "Description")

    with pytest.raises(ValidationError):
        subtask_repo.create(task.id, "", "Description")


# ========================================
# order_index の境界値テスト
# ========================================

def test_order_index_starts_from_zero(temp_db: Database):
    """order_indexは0から始まること"""
    repo = ProjectRepository(temp_db)

    project = repo.create("Project", "Description")

    assert project.order_index == 0


def test_order_index_increments_correctly(temp_db: Database):
    """order_indexが正しく増加すること（0, 1, 2, ...）"""
    repo = ProjectRepository(temp_db)

    p1 = repo.create("Project 1", "Description")
    p2 = repo.create("Project 2", "Description")
    p3 = repo.create("Project 3", "Description")

    assert p1.order_index == 0
    assert p2.order_index == 1
    assert p3.order_index == 2


def test_order_index_after_deletion(temp_db: Database):
    """削除後に新規作成すると、削除されたorder_indexを飛ばして次の番号が割り当てられること"""
    repo = ProjectRepository(temp_db)

    p1 = repo.create("Project 1", "Description")
    p2 = repo.create("Project 2", "Description")

    # p1を削除
    repo.delete(p1.id)

    # 新規作成すると、order_index=2が割り当てられる（0は欠番）
    p3 = repo.create("Project 3", "Description")

    assert p3.order_index == 2


# ========================================
# 更新操作のエッジケース
# ========================================

def test_update_project_with_empty_name(temp_db: Database):
    """空の名前でProjectを更新しようとするとValidationErrorが発生すること"""
    repo = ProjectRepository(temp_db)

    project = repo.create("Project", "Description")

    with pytest.raises(ValidationError):
        repo.update_project(project.id, name="")


def test_update_project_with_none_description(temp_db: Database):
    """descriptionをNoneで更新できること"""
    repo = ProjectRepository(temp_db)

    project = repo.create("Project", "Description")
    updated = repo.update_project(project.id, description=None)

    assert updated.description is None


def test_update_project_with_very_long_name(temp_db: Database):
    """非常に長い名前でProjectを更新できること"""
    repo = ProjectRepository(temp_db)

    project = repo.create("Project", "Description")
    long_name = "C" * 1000

    updated = repo.update_project(project.id, name=long_name)

    assert updated.name == long_name


# ========================================
# トランザクション境界のエッジケース
# ========================================

def test_create_and_delete_in_same_transaction(temp_db: Database):
    """同一トランザクション内で作成と削除を行うと、コミット後には削除済みになること"""
    repo = ProjectRepository(temp_db)

    conn = temp_db.connect()
    try:
        # 同一トランザクション内で作成
        project = repo.create("Project", "Description", conn=conn)
        project_id = project.id

        # 同一トランザクション内で削除
        repo.delete(project_id, conn=conn)

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    # 削除されていることを確認
    assert repo.get_by_id(project_id) is None


def test_rollback_after_error(temp_db: Database):
    """エラー発生後にロールバックされること"""
    repo = ProjectRepository(temp_db)

    conn = temp_db.connect()
    try:
        # 正常な作成
        project = repo.create("Project", "Description", conn=conn)

        # 意図的にエラーを発生させる（存在しないIDの削除）
        with pytest.raises(ConstraintViolationError):
            repo.delete(9999, conn=conn)

        # ロールバック
        conn.rollback()
    finally:
        conn.close()

    # ロールバックされたので、projectは存在しない
    assert repo.get_by_id(project.id) is None


# ========================================
# 複数エンティティの関連エッジケース
# ========================================

def test_create_deep_hierarchy(temp_db: Database):
    """深い階層（Project → SubProject → Task → SubTask）を作成できること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", "Description")
    task = task_repo.create(subproject.id, "Task", "Description")
    subtask = subtask_repo.create(task.id, "SubTask", "Description")

    assert project.id is not None
    assert subproject.id is not None
    assert subproject.project_id == project.id
    assert task.id is not None
    assert task.subproject_id == subproject.id
    assert subtask.id is not None
    assert subtask.task_id == task.id


def test_create_multiple_subprojects_under_same_project(temp_db: Database):
    """同一Project下に複数のSubProjectを作成できること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)

    project = proj_repo.create("Project", "Description")

    sp1 = subproj_repo.create(project.id, "SubProject 1", "Description")
    sp2 = subproj_repo.create(project.id, "SubProject 2", "Description")
    sp3 = subproj_repo.create(project.id, "SubProject 3", "Description")

    assert sp1.order_index == 0
    assert sp2.order_index == 1
    assert sp3.order_index == 2

    # すべて同じprojectを参照している
    assert sp1.project_id == project.id
    assert sp2.project_id == project.id
    assert sp3.project_id == project.id
