"""
カバレッジ向上のための追加テスト

未カバー箇所を効率的にカバーするためのテストケース
"""

import pytest
from pmtool.database import Database
from pmtool.repository import (
    ProjectRepository,
    SubProjectRepository,
    TaskRepository,
    SubTaskRepository,
)
from pmtool.dependencies import DependencyManager
from pmtool.status import StatusManager
from pmtool.exceptions import (
    ConstraintViolationError,
    ValidationError,
    StatusTransitionError,
)


# ========================================
# repository.py カバレッジ向上
# ========================================

def test_project_create_duplicate_name(temp_db: Database):
    """重複したプロジェクト名での作成はエラー"""
    repo = ProjectRepository(temp_db)

    # 最初のプロジェクト作成
    repo.create("Test Project", "Description")

    # 同じ名前で作成しようとするとエラー
    with pytest.raises(ConstraintViolationError, match="既に存在します"):
        repo.create("Test Project", "Another Description")


def test_subproject_create_duplicate_name(temp_db: Database):
    """同一プロジェクト内で重複したSubProject名での作成はエラー"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)

    project = proj_repo.create("Project", "Description")

    # 最初のSubProject作成
    subproj_repo.create(project.id, "SubProject", description="Description")

    # 同じ名前で作成しようとするとエラー
    with pytest.raises(ConstraintViolationError, match="既に存在します"):
        subproj_repo.create(project.id, "SubProject", description="Another Description")


def test_task_create_duplicate_name(temp_db: Database):
    """同一プロジェクト/SubProject内で重複したTask名での作成はエラー"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")

    # 最初のTask作成
    task_repo.create(project.id, "Task", subproject_id=subproject.id, description="Description")

    # 同じ名前で作成しようとするとエラー
    with pytest.raises(ConstraintViolationError, match="既に存在します"):
        task_repo.create(project.id, "Task", subproject_id=subproject.id, description="Another Description")


def test_subtask_create_duplicate_name(temp_db: Database):
    """同一Task内で重複したSubTask名での作成はエラー"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task = task_repo.create(project.id, "Task", subproject_id=subproject.id, description="Description")

    # 最初のSubTask作成
    subtask_repo.create(task.id, "SubTask", description="Description")

    # 同じ名前で作成しようとするとエラー
    with pytest.raises(ConstraintViolationError, match="既に存在します"):
        subtask_repo.create(task.id, "SubTask", description="Another Description")


def test_project_update_nonexistent(temp_db: Database):
    """存在しないプロジェクトの更新はエラー"""
    repo = ProjectRepository(temp_db)

    with pytest.raises(ConstraintViolationError, match="存在しません"):
        repo.update(99999, name="New Name")


def test_subproject_update_nonexistent(temp_db: Database):
    """存在しないSubProjectの更新はエラー"""
    repo = SubProjectRepository(temp_db)

    with pytest.raises(ConstraintViolationError, match="存在しません"):
        repo.update(99999, name="New Name")


def test_task_update_nonexistent(temp_db: Database):
    """存在しないTaskの更新はエラー"""
    repo = TaskRepository(temp_db)

    with pytest.raises(ConstraintViolationError, match="存在しません"):
        repo.update(99999, name="New Name")


def test_subtask_update_nonexistent(temp_db: Database):
    """存在しないSubTaskの更新はエラー"""
    repo = SubTaskRepository(temp_db)

    with pytest.raises(ConstraintViolationError, match="存在しません"):
        repo.update(99999, name="New Name")


def test_project_delete_nonexistent(temp_db: Database):
    """存在しないプロジェクトの削除はエラー"""
    repo = ProjectRepository(temp_db)

    with pytest.raises(ConstraintViolationError, match="存在しません"):
        repo.delete(99999)


def test_subproject_delete_nonexistent(temp_db: Database):
    """存在しないSubProjectの削除はエラー"""
    repo = SubProjectRepository(temp_db)

    with pytest.raises(ConstraintViolationError, match="存在しません"):
        repo.delete(99999)


def test_task_delete_nonexistent(temp_db: Database):
    """存在しないTaskの削除はエラー"""
    repo = TaskRepository(temp_db)

    with pytest.raises(ConstraintViolationError, match="存在しません"):
        repo.delete(99999)


def test_subtask_delete_nonexistent(temp_db: Database):
    """存在しないSubTaskの削除はエラー"""
    repo = SubTaskRepository(temp_db)

    with pytest.raises(ConstraintViolationError, match="存在しません"):
        repo.delete(99999)


def test_subproject_create_invalid_parent_project(temp_db: Database):
    """存在しないプロジェクトへのSubProject作成はエラー"""
    repo = SubProjectRepository(temp_db)

    with pytest.raises(ConstraintViolationError, match="存在しません"):
        repo.create(99999, "SubProject", description="Description")


def test_task_create_invalid_project(temp_db: Database):
    """存在しないプロジェクトへのTask作成はエラー"""
    repo = TaskRepository(temp_db)

    with pytest.raises(ConstraintViolationError, match="存在しません"):
        repo.create(99999, "Task", description="Description")


def test_subtask_create_invalid_task(temp_db: Database):
    """存在しないTaskへのSubTask作成はエラー"""
    repo = SubTaskRepository(temp_db)

    with pytest.raises(ConstraintViolationError, match="存在しません"):
        repo.create(99999, "SubTask", description="Description")


# ========================================
# dependencies.py カバレッジ向上
# ========================================

def test_dependency_get_all_successors_recursive(temp_db: Database):
    """再帰的に全後続ノードを取得"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task_a = task_repo.create(project.id, "Task A", subproject_id=subproject.id, description="Description")
    task_b = task_repo.create(project.id, "Task B", subproject_id=subproject.id, description="Description")
    task_c = task_repo.create(project.id, "Task C", subproject_id=subproject.id, description="Description")

    # A → B → C
    dep_mgr.add_task_dependency(task_a.id, task_b.id)
    dep_mgr.add_task_dependency(task_b.id, task_c.id)

    # 全後続ノード取得（Aの後続はB, C）
    successors = dep_mgr.get_all_task_successors_recursive(task_a.id)

    # 結果確認
    assert task_b.id in successors
    assert task_c.id in successors


def test_dependency_subtask_dependencies(temp_db: Database):
    """SubTask依存関係の取得"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task = task_repo.create(project.id, "Task", subproject_id=subproject.id, description="Description")
    subtask_a = subtask_repo.create(task.id, "SubTask A", description="Description")
    subtask_b = subtask_repo.create(task.id, "SubTask B", description="Description")

    # A → B
    dep_mgr.add_subtask_dependency(subtask_a.id, subtask_b.id)

    # 依存関係取得
    deps = dep_mgr.get_subtask_dependencies(subtask_b.id)

    # 結果確認
    assert "predecessors" in deps
    assert "successors" in deps
    assert subtask_a.id in deps["predecessors"]


# ========================================
# status.py カバレッジ向上
# ========================================

def test_status_dry_run_success(temp_db: Database):
    """dry-runモードでステータス更新シミュレーション（成功）"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)
    status_mgr = StatusManager(temp_db, dep_mgr)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task = task_repo.create(project.id, "Task", subproject_id=subproject.id, description="Description")

    # dry-run（UNSET → NOT_STARTED）
    # 返り値: (success, message, reason, details)
    success, message, reason, details = status_mgr.dry_run_status_update(task.id, "task", "NOT_STARTED")

    # 成功を確認
    assert success is True
    assert reason is None

    # 実際のステータスは変更されていない
    updated_task = task_repo.get_by_id(task.id)
    assert updated_task.status == "UNSET"


def test_status_dry_run_failure_due_to_prerequisite(temp_db: Database):
    """dry-runモードでステータス更新シミュレーション（先行ノード未完了のため失敗）"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)
    status_mgr = StatusManager(temp_db, dep_mgr)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task_a = task_repo.create(project.id, "Task A", subproject_id=subproject.id, description="Description")
    task_b = task_repo.create(project.id, "Task B", subproject_id=subproject.id, description="Description")

    # A → B
    dep_mgr.add_task_dependency(task_a.id, task_b.id)

    # dry-run（Aが未完了の状態でBをDONEにしようとする）
    success, message, reason, details = status_mgr.dry_run_status_update(task_b.id, "task", "DONE")

    # 失敗を確認
    assert success is False
    assert reason is not None


def test_status_invalid_status_value(temp_db: Database):
    """無効なステータス値での更新はエラー"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)
    status_mgr = StatusManager(temp_db, dep_mgr)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task = task_repo.create(project.id, "Task", subproject_id=subproject.id, description="Description")

    # 無効なステータス値
    with pytest.raises((ValidationError, StatusTransitionError)):
        status_mgr.update_task_status(task.id, "INVALID_STATUS")
