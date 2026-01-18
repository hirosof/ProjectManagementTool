"""
cascade_delete機能のテスト

--cascade --force によるサブツリー一括削除が正しく動作することを確認
"""

from pmtool.database import Database
from pmtool.repository import (
    ProjectRepository,
    SubProjectRepository,
    TaskRepository,
    SubTaskRepository,
)


def test_cascade_delete_project(temp_db: Database):
    """Project のカスケード削除が正しく動作すること"""
    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)

    # Project → SubProject → Task → SubTask を作成
    project = project_repo.create("TestProject", "Description")
    subproject = subproject_repo.create(project.id, "TestSubProject", None, "Description")
    task = task_repo.create(project.id, "Task", subproject.id, "Description")
    subtask = subtask_repo.create(task.id, "SubTask", "Description")

    # カスケード削除実行
    from pmtool.tui.commands import _delete_cascade_in_transaction

    conn = temp_db.connect()
    try:
        conn.execute("BEGIN")
        _delete_cascade_in_transaction(temp_db, "project", project.id, conn)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise

    # すべて削除されていることを確認
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM projects WHERE id = ?", (project.id,))
    assert cursor.fetchone()[0] == 0

    cursor.execute("SELECT COUNT(*) FROM subprojects WHERE id = ?", (subproject.id,))
    assert cursor.fetchone()[0] == 0

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE id = ?", (task.id,))
    assert cursor.fetchone()[0] == 0

    cursor.execute("SELECT COUNT(*) FROM subtasks WHERE id = ?", (subtask.id,))
    assert cursor.fetchone()[0] == 0


def test_cascade_delete_subproject(temp_db: Database):
    """SubProject のカスケード削除が正しく動作すること"""
    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)

    # Project → SubProject → Task → SubTask を作成
    project = project_repo.create("TestProject", "Description")
    subproject = subproject_repo.create(project.id, "TestSubProject", None, "Description")
    task = task_repo.create(project.id, "Task", subproject.id, "Description")
    subtask = subtask_repo.create(task.id, "SubTask", "Description")

    # カスケード削除実行
    from pmtool.tui.commands import _delete_cascade_in_transaction

    conn = temp_db.connect()
    try:
        conn.execute("BEGIN")
        _delete_cascade_in_transaction(temp_db, "subproject", subproject.id, conn)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise

    # SubProject配下が削除され、Projectは残っていることを確認
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM projects WHERE id = ?", (project.id,))
    assert cursor.fetchone()[0] == 1  # Projectは残る

    cursor.execute("SELECT COUNT(*) FROM subprojects WHERE id = ?", (subproject.id,))
    assert cursor.fetchone()[0] == 0

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE id = ?", (task.id,))
    assert cursor.fetchone()[0] == 0

    cursor.execute("SELECT COUNT(*) FROM subtasks WHERE id = ?", (subtask.id,))
    assert cursor.fetchone()[0] == 0


def test_cascade_delete_task(temp_db: Database):
    """Task のカスケード削除が正しく動作すること"""
    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)

    # Project → SubProject → Task → SubTask を作成
    project = project_repo.create("TestProject", "Description")
    subproject = subproject_repo.create(project.id, "TestSubProject", None, "Description")
    task = task_repo.create(project.id, "Task", subproject.id, "Description")
    subtask1 = subtask_repo.create(task.id, "SubTask1", "Description")
    subtask2 = subtask_repo.create(task.id, "SubTask2", "Description")

    # カスケード削除実行
    from pmtool.tui.commands import _delete_cascade_in_transaction

    conn = temp_db.connect()
    try:
        conn.execute("BEGIN")
        _delete_cascade_in_transaction(temp_db, "task", task.id, conn)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise

    # Task配下が削除され、Project/SubProjectは残っていることを確認
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM projects WHERE id = ?", (project.id,))
    assert cursor.fetchone()[0] == 1  # Projectは残る

    cursor.execute("SELECT COUNT(*) FROM subprojects WHERE id = ?", (subproject.id,))
    assert cursor.fetchone()[0] == 1  # SubProjectは残る

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE id = ?", (task.id,))
    assert cursor.fetchone()[0] == 0

    cursor.execute("SELECT COUNT(*) FROM subtasks WHERE id IN (?, ?)", (subtask1.id, subtask2.id))
    assert cursor.fetchone()[0] == 0


def test_cascade_delete_dry_run(temp_db: Database):
    """カスケード削除の dry-run が正しく動作すること"""
    from pmtool.tui.commands import _show_delete_impact

    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)

    # Project → SubProject → Task → SubTask を作成
    project = project_repo.create("TestProject", "Description")
    subproject = subproject_repo.create(project.id, "TestSubProject", None, "Description")
    task = task_repo.create(project.id, "Task", subproject.id, "Description")
    subtask = subtask_repo.create(task.id, "SubTask", "Description")

    # dry-run 実行（例外が発生しないことを確認）
    try:
        _show_delete_impact(temp_db, "project", project.id, use_bridge=False, use_cascade=True)
    except Exception as e:
        raise AssertionError(f"Unexpected exception: {e}")

    # DBが変化していないことを確認
    conn = temp_db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM projects WHERE id = ?", (project.id,))
    assert cursor.fetchone()[0] == 1

    cursor.execute("SELECT COUNT(*) FROM subprojects WHERE id = ?", (subproject.id,))
    assert cursor.fetchone()[0] == 1

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE id = ?", (task.id,))
    assert cursor.fetchone()[0] == 1

    cursor.execute("SELECT COUNT(*) FROM subtasks WHERE id = ?", (subtask.id,))
    assert cursor.fetchone()[0] == 1
