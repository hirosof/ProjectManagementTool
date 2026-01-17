"""
reason code基盤のテスト

StatusTransitionErrorがreason codeを正しく保持することを確認
"""

from pmtool.database import Database
from pmtool.dependencies import DependencyManager
from pmtool.exceptions import StatusTransitionError, StatusTransitionFailureReason
from pmtool.repository import ProjectRepository, SubProjectRepository, TaskRepository, SubTaskRepository
from pmtool.status import StatusManager


def test_reason_code_node_not_found(temp_db: Database):
    """存在しないノードへのステータス更新でNODE_NOT_FOUNDが返ること"""
    dep_manager = DependencyManager(temp_db)
    status_manager = StatusManager(temp_db, dep_manager)

    try:
        # 存在しないTaskID 999 に対してステータス更新を試みる
        status_manager.update_task_status(999, "DONE")
        assert False, "例外が発生すべき"
    except StatusTransitionError as e:
        assert e.reason == StatusTransitionFailureReason.NODE_NOT_FOUND
        assert e.details["node_id"] == 999
        assert e.details["node_type"] == "task"


def test_reason_code_prerequisite_not_done(temp_db: Database):
    """先行タスクが未完了の場合にPREREQUISITE_NOT_DONEが返ること"""
    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_manager = DependencyManager(temp_db)
    status_manager = StatusManager(temp_db, dep_manager)

    # Project → SubProject → Task1, Task2 を作成
    project = project_repo.create("TestProject", "Description")
    subproject = subproject_repo.create(project.id, "TestSubProject", None, "Description")
    task1 = task_repo.create(project.id, "Task1", subproject.id, "Description")
    task2 = task_repo.create(project.id, "Task2", subproject.id, "Description")

    # Task1 → Task2 の依存関係を作成
    dep_manager.add_task_dependency(task1.id, task2.id)

    # Task1がNOT_STARTEDのまま、Task2をDONEにしようとする
    try:
        status_manager.update_task_status(task2.id, "DONE")
        assert False, "例外が発生すべき"
    except StatusTransitionError as e:
        assert e.reason == StatusTransitionFailureReason.PREREQUISITE_NOT_DONE
        assert e.details["node_id"] == task2.id
        assert e.details["node_type"] == "task"
        assert len(e.details["incomplete_predecessors"]) == 1
        assert e.details["incomplete_predecessors"][0]["id"] == task1.id


def test_reason_code_child_not_done(temp_db: Database):
    """子SubTaskが未完了の場合にCHILD_NOT_DONEが返ること"""
    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)
    dep_manager = DependencyManager(temp_db)
    status_manager = StatusManager(temp_db, dep_manager)

    # Project → SubProject → Task → SubTask を作成
    project = project_repo.create("TestProject", "Description")
    subproject = subproject_repo.create(project.id, "TestSubProject", None, "Description")
    task = task_repo.create(project.id, "Task", subproject.id, "Description")
    subtask = subtask_repo.create(task.id, "SubTask", "Description")

    # SubTaskがUNSETのまま、TaskをDONEにしようとする
    try:
        status_manager.update_task_status(task.id, "DONE")
        assert False, "例外が発生すべき"
    except StatusTransitionError as e:
        assert e.reason == StatusTransitionFailureReason.CHILD_NOT_DONE
        assert e.details["node_id"] == task.id
        assert e.details["node_type"] == "task"
        assert len(e.details["incomplete_children"]) == 1
        assert e.details["incomplete_children"][0]["id"] == subtask.id


def test_reason_code_valid_transition(temp_db: Database):
    """正常なDONE遷移ではreason codeがNoneであること"""
    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_manager = DependencyManager(temp_db)
    status_manager = StatusManager(temp_db, dep_manager)

    # Project → SubProject → Task を作成
    project = project_repo.create("TestProject", "Description")
    subproject = subproject_repo.create(project.id, "TestSubProject", None, "Description")
    task = task_repo.create(project.id, "Task", subproject.id, "Description")

    # 先行タスクも子SubTaskもないため、DONEに遷移可能
    updated_task = status_manager.update_task_status(task.id, "DONE")

    assert updated_task.status == "DONE"
    # 例外が発生しないことを確認（reason codeはNone）
