"""
status層のテスト

DONE遷移の成功/失敗ケース、reason codeを確認
"""

import pytest

from pmtool.database import Database
from pmtool.repository import (
    ProjectRepository,
    TaskRepository,
    SubTaskRepository,
)
from pmtool.dependencies import DependencyManager
from pmtool.status import StatusManager
from pmtool.exceptions import StatusTransitionError, StatusTransitionFailureReason


def test_status_transition_to_done_success(temp_db: Database):
    """前提条件を満たしている場合、TaskをDONEにできること"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)
    status_mgr = StatusManager(temp_db, dep_mgr)

    project = proj_repo.create("Project", "")
    task = task_repo.create(project.id, "Task", None, "")

    # 先行タスクなし、子SubTaskなしの状態でDONEに遷移
    updated = status_mgr.update_task_status(task.id, "DONE")

    assert updated.status == "DONE"


def test_status_transition_to_done_with_prerequisite_not_done(temp_db: Database):
    """先行Taskが完了していない場合、DONEにできないこと"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)
    status_mgr = StatusManager(temp_db, dep_mgr)

    project = proj_repo.create("Project", "")
    task1 = task_repo.create(project.id, "Task 1", None, "")
    task2 = task_repo.create(project.id, "Task 2", None, "")

    # task1 → task2 の依存関係
    dep_mgr.add_task_dependency(task1.id, task2.id)

    # task1がNOT_STARTEDの状態でtask2をDONEにしようとするとエラー
    with pytest.raises(StatusTransitionError) as exc_info:
        status_mgr.update_task_status(task2.id, "DONE")

    # エラーメッセージに「先行」や「task」が含まれていることを確認
    assert "先行" in str(exc_info.value) or "task" in str(exc_info.value).lower()


def test_status_transition_to_done_with_child_not_done(temp_db: Database):
    """子SubTaskが完了していない場合、TaskをDONEにできないこと"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)
    status_mgr = StatusManager(temp_db, dep_mgr)

    project = proj_repo.create("Project", "")
    task = task_repo.create(project.id, "Task", None, "")
    subtask = subtask_repo.create(task.id, "SubTask", "")

    # SubTaskがNOT_STARTEDの状態でTaskをDONEにしようとするとエラー
    with pytest.raises(StatusTransitionError) as exc_info:
        status_mgr.update_task_status(task.id, "DONE")

    assert "子" in str(exc_info.value) or "child" in str(exc_info.value).lower()


def test_status_transition_to_done_with_all_conditions_met(temp_db: Database):
    """先行Taskと子SubTaskがすべてDONEの場合、TaskをDONEにできること"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)
    status_mgr = StatusManager(temp_db, dep_mgr)

    project = proj_repo.create("Project", "")
    task1 = task_repo.create(project.id, "Task 1", None, "")
    task2 = task_repo.create(project.id, "Task 2", None, "")
    subtask = subtask_repo.create(task2.id, "SubTask", "")

    # task1 → task2 の依存関係
    dep_mgr.add_task_dependency(task1.id, task2.id)

    # task1 を DONE にする
    status_mgr.update_task_status(task1.id, "DONE")

    # subtask を DONE にする
    status_mgr.update_subtask_status(subtask.id, "DONE")

    # 全条件を満たしたので task2 を DONE にできる
    updated = status_mgr.update_task_status(task2.id, "DONE")
    assert updated.status == "DONE"


def test_status_transition_to_in_progress(temp_db: Database):
    """IN_PROGRESSへの遷移は制約なく可能であること"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)
    status_mgr = StatusManager(temp_db, dep_mgr)

    project = proj_repo.create("Project", "")
    task = task_repo.create(project.id, "Task", None, "")

    # IN_PROGRESSに遷移
    updated = status_mgr.update_task_status(task.id, "IN_PROGRESS")
    assert updated.status == "IN_PROGRESS"


def test_status_transition_to_not_started(temp_db: Database):
    """NOT_STARTEDへの遷移は制約なく可能であること"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)
    status_mgr = StatusManager(temp_db, dep_mgr)

    project = proj_repo.create("Project", "")
    task = task_repo.create(project.id, "Task", None, "")

    # IN_PROGRESSにしてから NOT_STARTED に戻す
    status_mgr.update_task_status(task.id, "IN_PROGRESS")
    updated = status_mgr.update_task_status(task.id, "NOT_STARTED")

    assert updated.status == "NOT_STARTED"


def test_status_transition_error_contains_reason_code(temp_db: Database):
    """StatusTransitionErrorにreason codeが含まれていること"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)
    status_mgr = StatusManager(temp_db, dep_mgr)

    project = proj_repo.create("Project", "")
    task1 = task_repo.create(project.id, "Task 1", None, "")
    task2 = task_repo.create(project.id, "Task 2", None, "")

    # task1 → task2
    dep_mgr.add_task_dependency(task1.id, task2.id)

    # task1がNOT_STARTEDの状態でtask2をDONEにしようとする
    try:
        status_mgr.update_task_status(task2.id, "DONE")
        assert False, "例外が発生すべき"
    except StatusTransitionError as e:
        # reason code が設定されている
        assert e.reason == StatusTransitionFailureReason.PREREQUISITE_NOT_DONE
        assert e.details is not None


def test_subtask_status_transition_to_done(temp_db: Database):
    """SubTaskのDONE遷移が正しく動作すること"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)
    status_mgr = StatusManager(temp_db, dep_mgr)

    project = proj_repo.create("Project", "")
    task = task_repo.create(project.id, "Task", None, "")
    subtask = subtask_repo.create(task.id, "SubTask", "")

    # SubTaskをDONEにする（先行SubTaskがなければ可能）
    updated = status_mgr.update_subtask_status(subtask.id, "DONE")
    assert updated.status == "DONE"


def test_subtask_status_transition_with_prerequisite(temp_db: Database):
    """SubTaskの先行SubTaskが完了していない場合、DONEにできないこと"""
    # データ準備
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)
    dep_mgr = DependencyManager(temp_db)
    status_mgr = StatusManager(temp_db, dep_mgr)

    project = proj_repo.create("Project", "")
    task = task_repo.create(project.id, "Task", None, "")
    st1 = subtask_repo.create(task.id, "SubTask 1", "")
    st2 = subtask_repo.create(task.id, "SubTask 2", "")

    # st1 → st2
    dep_mgr.add_subtask_dependency(st1.id, st2.id)

    # st1がNOT_STARTEDの状態でst2をDONEにしようとするとエラー
    with pytest.raises(StatusTransitionError):
        status_mgr.update_subtask_status(st2.id, "DONE")
