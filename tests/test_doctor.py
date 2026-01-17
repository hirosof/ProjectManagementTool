"""
doctor/check機能のテスト

データ整合性チェックが正しく動作することを確認
"""

import sqlite3

from pmtool.database import Database
from pmtool.dependencies import DependencyManager
from pmtool.doctor import Doctor, IssueLevel
from pmtool.repository import (
    ProjectRepository,
    SubProjectRepository,
    SubTaskRepository,
    TaskRepository,
)
from pmtool.status import StatusManager


def test_doctor_healthy_database(temp_db: Database):
    """正常なデータベースではエラーが0件であること"""
    doctor = Doctor(temp_db)
    report = doctor.check_all()

    assert report.is_healthy
    assert report.error_count == 0


def test_doctor_detect_fk_violation(temp_db: Database):
    """FK破綻を検出できること"""
    # 手動でFK違反データを挿入（親Projectが存在しないSubProject）
    conn = temp_db.connect()
    cursor = conn.cursor()

    try:
        # FK制約を一時的に無効化（テスト用）
        cursor.execute("PRAGMA foreign_keys = OFF")

        # 存在しないproject_id=999を参照するSubProjectを挿入
        cursor.execute("""
            INSERT INTO subprojects (id, project_id, name, description, order_index, created_at, updated_at)
            VALUES (1, 999, 'Orphan SubProject', 'Description', 0, datetime('now'), datetime('now'))
        """)

        conn.commit()

        # doctor/checkを実行
        doctor = Doctor(temp_db)
        report = doctor.check_all()

        # FK001エラーが検出されること
        assert report.error_count > 0
        assert any(issue.code == "FK001" for issue in report.errors)

    finally:
        # FK制約を再度有効化
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()


def test_doctor_detect_status_inconsistency(temp_db: Database):
    """ステータス不整合を検出できること"""
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

    # SubTaskをDONEに
    status_manager.update_subtask_status(subtask.id, "DONE")

    # TaskをDONEに
    status_manager.update_task_status(task.id, "DONE")

    # 正常な状態ではエラーなし
    doctor = Doctor(temp_db)
    report = doctor.check_all()
    assert report.is_healthy

    # 手動でSubTaskのステータスをNOT_STARTEDに戻す（不整合状態を作成）
    conn = temp_db.connect()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE subtasks SET status = 'NOT_STARTED' WHERE id = ?", (subtask.id,)
    )
    conn.commit()

    # doctor/checkを実行
    report = doctor.check_all()

    # STATUS001エラーが検出されること
    assert report.error_count > 0
    assert any(issue.code == "STATUS001" for issue in report.errors)


def test_doctor_detect_order_index_duplicate(temp_db: Database):
    """order_index重複を検出できること"""
    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)

    # Project作成
    project = project_repo.create("TestProject", "Description")

    # SubProject2つ作成（異なるorder_index）
    subproject1 = subproject_repo.create(project.id, "SubProject1", None, "Description")
    subproject2 = subproject_repo.create(project.id, "SubProject2", None, "Description")

    # 正常な状態ではエラーなし
    doctor = Doctor(temp_db)
    report = doctor.check_all()
    assert report.is_healthy

    # 手動でorder_indexを重複させる
    conn = temp_db.connect()
    cursor = conn.cursor()
    try:
        # UNIQUE制約を一時的に無効化（テスト用）
        cursor.execute("PRAGMA foreign_keys = OFF")

        # subproject2のorder_indexをsubproject1と同じにする
        cursor.execute(
            """
            UPDATE subprojects
            SET order_index = (SELECT order_index FROM subprojects WHERE id = ?)
            WHERE id = ?
        """,
            (subproject1.id, subproject2.id),
        )

        conn.commit()

        # doctor/checkを実行
        report = doctor.check_all()

        # ORDER001エラーが検出されること
        assert report.error_count > 0
        assert any(issue.code == "ORDER001" for issue in report.errors)

    finally:
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()


def test_doctor_detect_subproject_nesting(temp_db: Database):
    """SubProject入れ子を検出できること（Warning）"""
    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)

    # Project作成
    project = project_repo.create("TestProject", "Description")

    # 親SubProject作成
    parent_subproject = subproject_repo.create(
        project.id, "ParentSubProject", None, "Description"
    )

    # 子SubProject作成（parent_subproject_id指定）
    child_subproject = subproject_repo.create(
        project.id, "ChildSubProject", parent_subproject.id, "Description"
    )

    # doctor/checkを実行
    doctor = Doctor(temp_db)
    report = doctor.check_all()

    # NEST001 Warning が検出されること
    assert report.warning_count > 0
    assert any(issue.code == "NEST001" for issue in report.warnings)
    assert report.is_healthy  # Warningのみなので、is_healthyはTrue
