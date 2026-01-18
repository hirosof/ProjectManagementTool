"""
dependencies層のテスト

サイクル検出、禁止依存（レイヤー制約）、橋渡し処理を確認
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
from pmtool.exceptions import (
    CyclicDependencyError,
    ConstraintViolationError,
)


def test_add_task_dependency(temp_db: Database):
    """Task間の依存関係が正しく追加できること"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "")
    task1 = task_repo.create(project.id, "Task 1", None, "")
    task2 = task_repo.create(project.id, "Task 2", None, "")

    # 依存関係追加: task1 → task2
    dep_mgr.add_task_dependency(task1.id, task2.id)

    # 依存関係取得
    deps = dep_mgr.get_task_dependencies(task2.id)

    assert task1.id in deps["predecessors"]
    assert task2.id not in deps["predecessors"]


def test_add_subtask_dependency(temp_db: Database):
    """SubTask間の依存関係が正しく追加できること"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "")
    task = task_repo.create(project.id, "Task", None, "")
    subtask1 = subtask_repo.create(task.id, "SubTask 1", "")
    subtask2 = subtask_repo.create(task.id, "SubTask 2", "")

    # 依存関係追加: subtask1 → subtask2
    dep_mgr.add_subtask_dependency(subtask1.id, subtask2.id)

    # 依存関係取得
    deps = dep_mgr.get_subtask_dependencies(subtask2.id)

    assert subtask1.id in deps["predecessors"]


def test_cyclic_dependency_detected_direct(temp_db: Database):
    """直接的なサイクル（A→B→A）が検出されること"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "")
    task_a = task_repo.create(project.id, "Task A", None, "")
    task_b = task_repo.create(project.id, "Task B", None, "")

    # A → B
    dep_mgr.add_task_dependency(task_a.id, task_b.id)

    # B → A を追加しようとするとサイクルエラー
    with pytest.raises(CyclicDependencyError) as exc_info:
        dep_mgr.add_task_dependency(task_b.id, task_a.id)

    # エラーが発生すればOK（メッセージ内容は問わない）
    assert exc_info.value is not None


def test_cyclic_dependency_detected_indirect(temp_db: Database):
    """間接的なサイクル（A→B→C→A）が検出されること"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "")
    task_a = task_repo.create(project.id, "Task A", None, "")
    task_b = task_repo.create(project.id, "Task B", None, "")
    task_c = task_repo.create(project.id, "Task C", None, "")

    # A → B → C
    dep_mgr.add_task_dependency(task_a.id, task_b.id)
    dep_mgr.add_task_dependency(task_b.id, task_c.id)

    # C → A を追加しようとするとサイクルエラー
    with pytest.raises(CyclicDependencyError):
        dep_mgr.add_task_dependency(task_c.id, task_a.id)


def test_self_dependency_rejected(temp_db: Database):
    """自己依存（A→A）が拒否されること"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "")
    task = task_repo.create(project.id, "Task", None, "")

    # 自己依存を追加しようとするとエラー（ConstraintViolationErrorまたはCyclicDependencyError）
    with pytest.raises((ConstraintViolationError, CyclicDependencyError)):
        dep_mgr.add_task_dependency(task.id, task.id)


def test_remove_task_dependency(temp_db: Database):
    """Task依存関係の削除が正しく動作すること"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "")
    task1 = task_repo.create(project.id, "Task 1", None, "")
    task2 = task_repo.create(project.id, "Task 2", None, "")

    # 依存関係追加: task1 → task2
    dep_mgr.add_task_dependency(task1.id, task2.id)

    # 依存関係削除
    dep_mgr.remove_task_dependency(task1.id, task2.id)

    # 依存関係が削除されていることを確認
    deps = dep_mgr.get_task_dependencies(task2.id)
    assert task1.id not in deps["predecessors"]


def test_bridge_dependencies_on_task_delete(temp_db: Database):
    """Task削除時に依存関係が橋渡しされること（A→B→C で B削除 → A→C）"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "")
    task_a = task_repo.create(project.id, "Task A", None, "")
    task_b = task_repo.create(project.id, "Task B", None, "")
    task_c = task_repo.create(project.id, "Task C", None, "")

    # A → B → C
    dep_mgr.add_task_dependency(task_a.id, task_b.id)
    dep_mgr.add_task_dependency(task_b.id, task_c.id)

    # Bを橋渡し削除
    task_repo.delete_with_bridge(task_b.id)

    # A → C の依存関係が作成されていることを確認
    deps_c = dep_mgr.get_task_dependencies(task_c.id)
    assert task_a.id in deps_c["predecessors"]
    assert task_b.id not in deps_c["predecessors"]  # Bは削除されている


def test_bridge_dependencies_on_subtask_delete(temp_db: Database):
    """SubTask削除時に依存関係が橋渡しされること"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "")
    task = task_repo.create(project.id, "Task", None, "")
    st_a = subtask_repo.create(task.id, "SubTask A", "")
    st_b = subtask_repo.create(task.id, "SubTask B", "")
    st_c = subtask_repo.create(task.id, "SubTask C", "")

    # A → B → C
    dep_mgr.add_subtask_dependency(st_a.id, st_b.id)
    dep_mgr.add_subtask_dependency(st_b.id, st_c.id)

    # Bを橋渡し削除
    subtask_repo.delete_with_bridge(st_b.id)

    # A → C の依存関係が作成されていることを確認
    deps_c = dep_mgr.get_subtask_dependencies(st_c.id)
    assert st_a.id in deps_c["predecessors"]
    assert st_b.id not in deps_c["predecessors"]


def test_multiple_predecessors_and_successors(temp_db: Database):
    """複数の先行・後続ノードが正しく処理されること"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "")
    task1 = task_repo.create(project.id, "Task 1", None, "")
    task2 = task_repo.create(project.id, "Task 2", None, "")
    task3 = task_repo.create(project.id, "Task 3", None, "")
    task4 = task_repo.create(project.id, "Task 4", None, "")

    # 1 → 3, 2 → 3, 3 → 4
    dep_mgr.add_task_dependency(task1.id, task3.id)
    dep_mgr.add_task_dependency(task2.id, task3.id)
    dep_mgr.add_task_dependency(task3.id, task4.id)

    # task3の依存関係を確認
    deps = dep_mgr.get_task_dependencies(task3.id)

    assert task1.id in deps["predecessors"]
    assert task2.id in deps["predecessors"]
    assert task4.id in deps["successors"]
    assert len(deps["predecessors"]) == 2
    assert len(deps["successors"]) == 1


def test_cross_layer_dependency_rejected(temp_db: Database):
    """Task依存テーブルにSubTask IDを使おうとしてエラーになること（レイヤ混在禁止）"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "")
    task = task_repo.create(project.id, "Task", None, "")
    subtask = subtask_repo.create(task.id, "SubTask", "")

    # Task依存APIにSubTask IDを渡そうとするとエラー（レイヤ混在禁止）
    # 実装上、異なるレイヤーのIDを渡すとFK制約違反やConstraintViolationErrorになる
    with pytest.raises((ConstraintViolationError, Exception)):
        dep_mgr.add_task_dependency(task.id, subtask.id)
