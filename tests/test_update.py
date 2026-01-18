"""
update系コマンドのテスト

name / description / order_index の更新が正しく動作することを確認
"""

from pmtool.database import Database
from pmtool.repository import (
    ProjectRepository,
    SubProjectRepository,
    TaskRepository,
    SubTaskRepository,
)


def test_update_project_name(temp_db: Database):
    """Project の name 更新が正しく動作すること"""
    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)

    # Project 作成
    project = project_repo.create("OldName", "Description")

    # name 更新
    updated = project_repo.update(project.id, name="NewName")

    assert updated.name == "NewName"
    assert updated.description == "Description"  # description は変更されていない


def test_update_project_description(temp_db: Database):
    """Project の description 更新が正しく動作すること"""
    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)

    # Project 作成
    project = project_repo.create("Name", "OldDescription")

    # description 更新
    updated = project_repo.update(project.id, description="NewDescription")

    assert updated.name == "Name"  # name は変更されていない
    assert updated.description == "NewDescription"


def test_update_project_both(temp_db: Database):
    """Project の name と description を同時更新できること"""
    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)

    # Project 作成
    project = project_repo.create("OldName", "OldDescription")

    # name と description を同時更新
    updated = project_repo.update(project.id, name="NewName", description="NewDescription")

    assert updated.name == "NewName"
    assert updated.description == "NewDescription"


def test_update_subproject_order_index(temp_db: Database):
    """SubProject の order_index 更新が正しく動作すること"""
    from pmtool.tui.commands import _update_order_index

    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)

    # Project → SubProject 作成
    project = project_repo.create("TestProject", "Description")
    sp1 = subproject_repo.create(project.id, "SP1", None, "Description")
    sp2 = subproject_repo.create(project.id, "SP2", None, "Description")

    # 初期状態: SP1=0, SP2=1
    assert sp1.order_index == 0
    assert sp2.order_index == 1

    # SP1 の order_index を 5 に変更
    _update_order_index(temp_db, "subproject", sp1.id, 5)

    # 確認
    conn = temp_db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT order_index FROM subprojects WHERE id = ?", (sp1.id,))
    assert cursor.fetchone()[0] == 5


def test_update_task_order_index(temp_db: Database):
    """Task の order_index 更新が正しく動作すること"""
    from pmtool.tui.commands import _update_order_index

    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)

    # Project → SubProject → Task 作成
    project = project_repo.create("TestProject", "Description")
    subproject = subproject_repo.create(project.id, "TestSubProject", None, "Description")
    task1 = task_repo.create(project.id, "Task1", subproject.id, "Description")
    task2 = task_repo.create(project.id, "Task2", subproject.id, "Description")

    # 初期状態: Task1=0, Task2=1
    assert task1.order_index == 0
    assert task2.order_index == 1

    # Task1 の order_index を 10 に変更
    _update_order_index(temp_db, "task", task1.id, 10)

    # 確認
    conn = temp_db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT order_index FROM tasks WHERE id = ?", (task1.id,))
    assert cursor.fetchone()[0] == 10


def test_update_subtask_order_index(temp_db: Database):
    """SubTask の order_index 更新が正しく動作すること"""
    from pmtool.tui.commands import _update_order_index

    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)

    # Project → SubProject → Task → SubTask 作成
    project = project_repo.create("TestProject", "Description")
    subproject = subproject_repo.create(project.id, "TestSubProject", None, "Description")
    task = task_repo.create(project.id, "Task", subproject.id, "Description")
    subtask1 = subtask_repo.create(task.id, "SubTask1", "Description")
    subtask2 = subtask_repo.create(task.id, "SubTask2", "Description")

    # 初期状態: SubTask1=0, SubTask2=1
    assert subtask1.order_index == 0
    assert subtask2.order_index == 1

    # SubTask1 の order_index を 3 に変更
    _update_order_index(temp_db, "subtask", subtask1.id, 3)

    # 確認
    conn = temp_db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT order_index FROM subtasks WHERE id = ?", (subtask1.id,))
    assert cursor.fetchone()[0] == 3


def test_update_order_index_negative_value(temp_db: Database):
    """order_index に負の値を設定しようとするとエラーになること"""
    from pmtool.tui.commands import _update_order_index

    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)

    # Project → SubProject 作成
    project = project_repo.create("TestProject", "Description")
    sp = subproject_repo.create(project.id, "SP", None, "Description")

    # 負の値を設定（エラーメッセージが表示されるが例外は発生しない）
    _update_order_index(temp_db, "subproject", sp.id, -1)

    # order_index は変更されていないことを確認
    conn = temp_db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT order_index FROM subprojects WHERE id = ?", (sp.id,))
    assert cursor.fetchone()[0] == 0  # 初期値のまま
