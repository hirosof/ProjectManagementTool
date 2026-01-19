"""
TUI層の統合テスト

CLI引数パース → コマンドハンドラ呼び出し → 出力文字列確認（擬似統合テスト）

注: 現在のTUI層は argparse.Namespace を受け取るため、
リポジトリ層の直接テストで代替します。
"""

import pytest
import io
import sys
from contextlib import redirect_stdout

from pmtool.database import Database
from pmtool.repository import (
    ProjectRepository,
    SubProjectRepository,
    TaskRepository,
)


# ========================================
# list projects コマンド（リポジトリ層直接テスト）
# ========================================

def test_list_projects_empty(temp_db: Database):
    """プロジェクトが存在しない場合のlist all操作"""
    repo = ProjectRepository(temp_db)
    projects = repo.list_all()

    # 空のリスト
    assert len(projects) == 0


def test_list_projects_with_data(temp_db: Database):
    """プロジェクトが存在する場合のlist all操作"""
    repo = ProjectRepository(temp_db)
    repo.create("Project 1", "Description 1")
    repo.create("Project 2", "Description 2")

    projects = repo.list_all()

    # プロジェクトが2件存在
    assert len(projects) == 2
    assert projects[0].name == "Project 1"
    assert projects[1].name == "Project 2"


# ========================================
# show project コマンド（リポジトリ層直接テスト）
# ========================================

def test_show_project_simple(temp_db: Database):
    """単純なプロジェクト構造のget_by_id操作"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)

    project = proj_repo.create("Test Project", "Test Description")
    subproject = subproj_repo.create(project.id, "SubProject 1", "SubProject Description")
    task = task_repo.create(subproject.id, "Task 1", "Task Description")

    # プロジェクトを取得
    retrieved = proj_repo.get_by_id(project.id)

    assert retrieved is not None
    assert retrieved.name == "Test Project"


def test_show_project_nonexistent(temp_db: Database):
    """存在しないプロジェクトのget_by_id操作はNoneを返す"""
    repo = ProjectRepository(temp_db)

    # 存在しないプロジェクトID（9999）
    result = repo.get_by_id(9999)

    assert result is None


# ========================================
# add project コマンド（リポジトリ層直接テスト）
# ========================================

def test_add_project_success(temp_db: Database):
    """create操作でプロジェクトを追加できる"""
    repo = ProjectRepository(temp_db)
    project = repo.create("New Project", "New Description")

    assert project.id is not None
    assert project.name == "New Project"
    assert project.description == "New Description"

    # プロジェクトが作成されたことを確認
    retrieved = repo.get_by_id(project.id)
    assert retrieved is not None
    assert retrieved.name == "New Project"


# ========================================
# delete project コマンド（リポジトリ層直接テスト）
# ========================================

def test_delete_project_success(temp_db: Database):
    """delete操作でプロジェクトを削除できる"""
    repo = ProjectRepository(temp_db)
    project = repo.create("Project to Delete", "Description")

    # 削除前に存在することを確認
    assert repo.get_by_id(project.id) is not None

    # 削除（子がない場合）
    repo.delete(project.id)

    # 削除後に存在しないことを確認
    assert repo.get_by_id(project.id) is None


def test_delete_project_with_children_fails(temp_db: Database):
    """子エンティティが存在するプロジェクトの削除はエラーになる"""
    from pmtool.exceptions import DeletionError

    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", "Description")

    # 子が存在する場合、削除はエラー
    with pytest.raises(DeletionError):
        proj_repo.delete(project.id)


# ========================================
# ステータス関連のコマンド
# ========================================

def test_status_transition_success(temp_db: Database):
    """ステータス遷移が成功する"""
    from pmtool.repository import TaskRepository
    from pmtool.status import StatusManager
    from pmtool.dependencies import DependencyManager

    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)
    status_mgr = StatusManager(temp_db, dep_mgr)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", "Description")
    task = task_repo.create(subproject.id, "Task", "Description")

    # 初期状態はUNSET
    assert task.status == "UNSET"

    # NOT_STARTEDに遷移
    status_mgr.update_task_status(task.id, "NOT_STARTED")

    # 確認
    updated_task = task_repo.get_by_id(task.id)
    assert updated_task.status == "NOT_STARTED"


def test_status_transition_to_done_with_prerequisites(temp_db: Database):
    """先行タスクが未完了の場合、DONEに遷移できない"""
    from pmtool.repository import TaskRepository
    from pmtool.status import StatusManager
    from pmtool.dependencies import DependencyManager
    from pmtool.exceptions import StatusTransitionError

    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)
    status_mgr = StatusManager(temp_db, dep_mgr)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", "Description")
    task_a = task_repo.create(subproject.id, "Task A", "Description")
    task_b = task_repo.create(subproject.id, "Task B", "Description")

    # A → B
    dep_mgr.add_task_dependency(task_a.id, task_b.id)

    # A が未完了の状態で B を DONE にしようとするとエラー
    with pytest.raises(StatusTransitionError):
        status_mgr.update_task_status(task_b.id, "DONE")


# ========================================
# 依存関係関連のコマンド
# ========================================

def test_add_dependency_success(temp_db: Database):
    """依存関係を追加できる"""
    from pmtool.dependencies import DependencyManager

    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", "Description")
    task_a = task_repo.create(subproject.id, "Task A", "Description")
    task_b = task_repo.create(subproject.id, "Task B", "Description")

    # A → B
    dep_mgr.add_task_dependency(task_a.id, task_b.id)

    # 依存関係が存在することを確認
    deps = dep_mgr.get_task_dependencies(task_b.id)
    assert task_a.id in deps


def test_remove_dependency_success(temp_db: Database):
    """依存関係を削除できる"""
    from pmtool.dependencies import DependencyManager

    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", "Description")
    task_a = task_repo.create(subproject.id, "Task A", "Description")
    task_b = task_repo.create(subproject.id, "Task B", "Description")

    # A → B
    dep_mgr.add_task_dependency(task_a.id, task_b.id)

    # 削除
    dep_mgr.remove_task_dependency(task_a.id, task_b.id)

    # 依存関係が存在しないことを確認
    deps = dep_mgr.get_task_dependencies(task_b.id)
    assert task_a.id not in deps


# ========================================
# エラーハンドリング
# ========================================

def test_command_handles_invalid_input_gracefully(temp_db: Database):
    """無効な入力に対してリポジトリが適切にNoneを返す"""
    repo = ProjectRepository(temp_db)

    # 存在しないプロジェクトIDでget_by_id操作
    result = repo.get_by_id(99999)

    # Noneを返す
    assert result is None


# ========================================
# コマンド統合テスト（複合操作）
# ========================================

def test_full_workflow_create_show_delete(temp_db: Database):
    """作成 → 表示 → 削除の一連のワークフローが正常に動作する"""
    proj_repo = ProjectRepository(temp_db)

    # 作成
    project = proj_repo.create("Workflow Test Project", "Description")

    # 表示（get_by_id操作）
    retrieved = proj_repo.get_by_id(project.id)
    assert retrieved is not None
    assert retrieved.name == "Workflow Test Project"

    # 削除
    proj_repo.delete(project.id)

    # 削除後は存在しない
    assert proj_repo.get_by_id(project.id) is None


def test_full_workflow_with_dependencies(temp_db: Database):
    """依存関係を含む一連のワークフローが正常に動作する"""
    from pmtool.dependencies import DependencyManager
    from pmtool.status import StatusManager

    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)
    status_mgr = StatusManager(temp_db, dep_mgr)

    # プロジェクト構造を作成
    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", "Description")
    task_a = task_repo.create(subproject.id, "Task A", "Description")
    task_b = task_repo.create(subproject.id, "Task B", "Description")

    # 依存関係を追加（A → B）
    dep_mgr.add_task_dependency(task_a.id, task_b.id)

    # A を DONE にする
    status_mgr.update_task_status(task_a.id, "DONE")

    # B を DONE にする（A が DONE なので成功する）
    status_mgr.update_task_status(task_b.id, "DONE")

    # 確認
    task_b_updated = task_repo.get_by_id(task_b.id)
    assert task_b_updated.status == "DONE"
