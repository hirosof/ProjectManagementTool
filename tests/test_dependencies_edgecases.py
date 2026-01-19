"""
dependencies層のエッジケース・境界値テスト

サイクル検出、レイヤー制約、橋渡し処理のエッジケース
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


# ========================================
# サイクル検出のエッジケース
# ========================================

def test_detect_self_loop(temp_db: Database):
    """自己ループ（A → A）を検出できること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task = task_repo.create(project.id, "Task", subproject_id=subproject.id, description="Description")

    # 自己ループを作成しようとするとエラー（ConstraintViolationError）
    with pytest.raises(ConstraintViolationError):
        dep_mgr.add_task_dependency(task.id, task.id)


def test_detect_simple_cycle(temp_db: Database):
    """単純なサイクル（A → B → A）を検出できること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task_a = task_repo.create(project.id, "Task A", subproject_id=subproject.id, description="Description")
    task_b = task_repo.create(project.id, "Task B", subproject_id=subproject.id, description="Description")

    # A → B
    dep_mgr.add_task_dependency(task_a.id, task_b.id)

    # B → A を追加しようとするとサイクル検出
    with pytest.raises(CyclicDependencyError):
        dep_mgr.add_task_dependency(task_b.id, task_a.id)


def test_detect_long_cycle(temp_db: Database):
    """長いサイクル（A → B → C → D → A）を検出できること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task_a = task_repo.create(project.id, "Task A", subproject_id=subproject.id, description="Description")
    task_b = task_repo.create(project.id, "Task B", subproject_id=subproject.id, description="Description")
    task_c = task_repo.create(project.id, "Task C", subproject_id=subproject.id, description="Description")
    task_d = task_repo.create(project.id, "Task D", subproject_id=subproject.id, description="Description")

    # A → B → C → D
    dep_mgr.add_task_dependency(task_a.id, task_b.id)
    dep_mgr.add_task_dependency(task_b.id, task_c.id)
    dep_mgr.add_task_dependency(task_c.id, task_d.id)

    # D → A を追加しようとするとサイクル検出
    with pytest.raises(CyclicDependencyError):
        dep_mgr.add_task_dependency(task_d.id, task_a.id)


def test_detect_indirect_cycle(temp_db: Database):
    """間接的なサイクル（A → B, A → C, C → B → A）を検出できること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task_a = task_repo.create(project.id, "Task A", subproject_id=subproject.id, description="Description")
    task_b = task_repo.create(project.id, "Task B", subproject_id=subproject.id, description="Description")
    task_c = task_repo.create(project.id, "Task C", subproject_id=subproject.id, description="Description")

    # A → B, A → C
    dep_mgr.add_task_dependency(task_a.id, task_b.id)
    dep_mgr.add_task_dependency(task_a.id, task_c.id)

    # C → B
    dep_mgr.add_task_dependency(task_c.id, task_b.id)

    # B → A を追加しようとするとサイクル検出（A → B → A）
    with pytest.raises(CyclicDependencyError):
        dep_mgr.add_task_dependency(task_b.id, task_a.id)


# ========================================
# レイヤー制約のエッジケース
# ========================================

def test_cross_layer_task_to_subtask_dependency_is_forbidden(temp_db: Database):
    """Task → SubTask の依存関係は禁止されていること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task = task_repo.create(project.id, "Task", subproject_id=subproject.id, description="Description")
    subtask = subtask_repo.create(task.id, "SubTask", description="Description")

    # Task → SubTask の依存を追加しようとするとエラー
    # 注: 現在の実装では、task_dependency と subtask_dependency のテーブルが分離されているため、
    # この制約は自動的に満たされる（Task同士、SubTask同士しか依存関係を持てない）
    # ここでは、add_task_dependencyにSubTaskのIDを渡すとエラーになることを確認
    with pytest.raises((ConstraintViolationError, ConstraintViolationError, ValueError)):
        dep_mgr.add_task_dependency(task.id, subtask.id)


def test_add_dependency_with_nonexistent_predecessor(temp_db: Database):
    """存在しないpredecessorで依存関係を追加しようとするとエラーが発生すること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task = task_repo.create(project.id, "Task", subproject_id=subproject.id, description="Description")

    # 存在しないpredecessor（9999）で依存関係を追加しようとするとエラー
    with pytest.raises(ConstraintViolationError):
        dep_mgr.add_task_dependency(9999, task.id)


def test_add_dependency_with_nonexistent_successor(temp_db: Database):
    """存在しないsuccessorで依存関係を追加しようとするとエラーが発生すること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task = task_repo.create(project.id, "Task", subproject_id=subproject.id, description="Description")

    # 存在しないsuccessor（9999）で依存関係を追加しようとするとエラー
    with pytest.raises(ConstraintViolationError):
        dep_mgr.add_task_dependency(task.id, 9999)


# ========================================
# 橋渡し処理のエッジケース
# ========================================

def test_bridge_with_no_predecessors_and_no_successors(temp_db: Database):
    """先行も後続もないノードを橋渡し削除すると、単純に削除されること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task = task_repo.create(project.id, "Task", subproject_id=subproject.id, description="Description")

    # 橋渡し削除
    task_repo.delete_with_bridge(task.id)

    # 削除されていることを確認
    assert task_repo.get_by_id(task.id) is None


def test_bridge_with_one_predecessor_and_one_successor(temp_db: Database):
    """A → B → C の B を橋渡し削除すると A → C になること"""
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

    # B を橋渡し削除
    task_repo.delete_with_bridge(task_b.id)

    # B は削除されている
    assert task_repo.get_by_id(task_b.id) is None

    # A → C の依存関係が存在する
    deps = dep_mgr.get_task_dependencies(task_c.id)
    assert task_a.id in deps["predecessors"]


def test_bridge_with_multiple_predecessors_and_successors(temp_db: Database):
    """複数の先行・後続ノードがある場合の橋渡し削除"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task_a = task_repo.create(project.id, "Task A", subproject_id=subproject.id, description="Description")
    task_b = task_repo.create(project.id, "Task B", subproject_id=subproject.id, description="Description")
    task_c = task_repo.create(project.id, "Task C", subproject_id=subproject.id, description="Description")
    task_d = task_repo.create(project.id, "Task D", subproject_id=subproject.id, description="Description")
    task_e = task_repo.create(project.id, "Task E", subproject_id=subproject.id, description="Description")

    # A → C, B → C
    dep_mgr.add_task_dependency(task_a.id, task_c.id)
    dep_mgr.add_task_dependency(task_b.id, task_c.id)

    # C → D, C → E
    dep_mgr.add_task_dependency(task_c.id, task_d.id)
    dep_mgr.add_task_dependency(task_c.id, task_e.id)

    # C を橋渡し削除
    task_repo.delete_with_bridge(task_c.id)

    # C は削除されている
    assert task_repo.get_by_id(task_c.id) is None

    # A → D, A → E, B → D, B → E の依存関係が存在する
    deps_d = dep_mgr.get_task_dependencies(task_d.id)
    deps_e = dep_mgr.get_task_dependencies(task_e.id)

    assert task_a.id in deps_d["predecessors"]
    assert task_b.id in deps_d["predecessors"]
    assert task_a.id in deps_e["predecessors"]
    assert task_b.id in deps_e["predecessors"]


# ========================================
# 依存関係の削除エッジケース
# ========================================

def test_remove_nonexistent_dependency(temp_db: Database):
    """存在しない依存関係を削除しようとするとエラーが発生すること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task_a = task_repo.create(project.id, "Task A", subproject_id=subproject.id, description="Description")
    task_b = task_repo.create(project.id, "Task B", subproject_id=subproject.id, description="Description")

    # A → B の依存関係が存在しない状態で削除しようとするとエラー
    with pytest.raises(ConstraintViolationError):
        dep_mgr.remove_task_dependency(task_a.id, task_b.id)


def test_remove_dependency_twice(temp_db: Database):
    """同じ依存関係を2回削除しようとすると2回目にエラーが発生すること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task_a = task_repo.create(project.id, "Task A", subproject_id=subproject.id, description="Description")
    task_b = task_repo.create(project.id, "Task B", subproject_id=subproject.id, description="Description")

    # A → B
    dep_mgr.add_task_dependency(task_a.id, task_b.id)

    # 1回目の削除は成功
    dep_mgr.remove_task_dependency(task_a.id, task_b.id)

    # 2回目の削除はエラー
    with pytest.raises(ConstraintViolationError):
        dep_mgr.remove_task_dependency(task_a.id, task_b.id)


# ========================================
# 複雑な依存関係グラフのエッジケース
# ========================================

def test_diamond_dependency_graph(temp_db: Database):
    """ダイヤモンド型の依存関係グラフ（A → B, A → C, B → D, C → D）を作成できること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")
    task_a = task_repo.create(project.id, "Task A", subproject_id=subproject.id, description="Description")
    task_b = task_repo.create(project.id, "Task B", subproject_id=subproject.id, description="Description")
    task_c = task_repo.create(project.id, "Task C", subproject_id=subproject.id, description="Description")
    task_d = task_repo.create(project.id, "Task D", subproject_id=subproject.id, description="Description")

    # A → B, A → C
    dep_mgr.add_task_dependency(task_a.id, task_b.id)
    dep_mgr.add_task_dependency(task_a.id, task_c.id)

    # B → D, C → D
    dep_mgr.add_task_dependency(task_b.id, task_d.id)
    dep_mgr.add_task_dependency(task_c.id, task_d.id)

    # D の依存関係を確認（B と C が先行ノード）
    deps_d = dep_mgr.get_task_dependencies(task_d.id)

    assert task_b.id in deps_d["predecessors"]
    assert task_c.id in deps_d["predecessors"]


def test_large_dependency_chain(temp_db: Database):
    """長い依存関係チェーン（A → B → C → D → E → F → G → H → I → J）を作成できること"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)

    project = proj_repo.create("Project", "Description")
    subproject = subproj_repo.create(project.id, "SubProject", description="Description")

    tasks = []
    for i in range(10):
        task = task_repo.create(project.id, f"Task {chr(65 + i)}", subproject_id=subproject.id, description="Description")
        tasks.append(task)

    # A → B → C → ... → J
    for i in range(9):
        dep_mgr.add_task_dependency(tasks[i].id, tasks[i + 1].id)

    # 最後のタスク（J）の依存関係を確認
    deps_j = dep_mgr.get_task_dependencies(tasks[9].id)

    # 直接の先行ノードは I のみ
    assert tasks[8].id in deps_j["predecessors"]
    assert len(deps_j["predecessors"]) == 1
