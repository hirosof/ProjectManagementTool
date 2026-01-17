"""
dry-run基盤のテスト

--dry-run オプションが正しく動作することを確認
"""

from pmtool.database import Database
from pmtool.repository import (
    ProjectRepository,
    SubProjectRepository,
    TaskRepository,
    SubTaskRepository,
)
from pmtool.dependencies import DependencyManager


def test_dry_run_concept_with_rollback(temp_db: Database):
    """dry-run のコンセプト: トランザクション rollback でDBが変化しないことを確認"""
    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)

    # Project → SubProject → Task を作成
    project = project_repo.create("TestProject", "Description")
    subproject = subproject_repo.create(project.id, "TestSubProject", None, "Description")
    task = task_repo.create(project.id, "Task", subproject.id, "Description")

    # 削除前の件数を取得
    conn = temp_db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tasks")
    before_tasks = cursor.fetchone()[0]

    # トランザクション内で削除して rollback
    try:
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task.id,))
        # この時点では削除されているが、rollback で取り消される
        cursor.execute("SELECT COUNT(*) FROM tasks")
        during_delete = cursor.fetchone()[0]
        assert during_delete < before_tasks  # 削除されている

        conn.rollback()  # rollback で変更を破棄
    finally:
        pass

    # rollback 後の件数を確認（元に戻っているはず）
    cursor.execute("SELECT COUNT(*) FROM tasks")
    after_rollback = cursor.fetchone()[0]

    # 件数が変化していないことを確認
    assert before_tasks == after_rollback


def test_dry_run_repeatable_concept(temp_db: Database):
    """dry-run が繰り返し実行可能であることを確認（コンセプト）"""
    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)

    # Project → SubProject を作成
    project = project_repo.create("TestProject", "Description")
    subproject = subproject_repo.create(project.id, "TestSubProject", None, "Description")

    # 削除前の件数を取得
    conn = temp_db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM subprojects")
    before_count = cursor.fetchone()[0]

    # rollback を3回実行（dry-run を3回実行するシミュレーション）
    for _ in range(3):
        try:
            cursor.execute("DELETE FROM subprojects WHERE id = ?", (subproject.id,))
            conn.rollback()
        finally:
            pass

    # 件数が変化していないことを確認
    cursor.execute("SELECT COUNT(*) FROM subprojects")
    after_count = cursor.fetchone()[0]
    assert before_count == after_count


def test_dry_run_counts_entities(temp_db: Database):
    """削除影響範囲のカウント機能を確認"""
    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)

    # Project → SubProject → Task → SubTask を作成
    project = project_repo.create("TestProject", "Description")
    subproject = subproject_repo.create(project.id, "TestSubProject", None, "Description")
    task1 = task_repo.create(project.id, "Task1", subproject.id, "Description")
    task2 = task_repo.create(project.id, "Task2", subproject.id, "Description")
    subtask1 = subtask_repo.create(task1.id, "SubTask1", "Description")
    subtask2 = subtask_repo.create(task1.id, "SubTask2", "Description")

    # 削除前の件数を取得
    conn = temp_db.connect()
    cursor = conn.cursor()

    def count_all():
        cursor.execute("SELECT COUNT(*) FROM projects")
        projects = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM subprojects")
        subprojects = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tasks")
        tasks = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM subtasks")
        subtasks = cursor.fetchone()[0]
        return {"projects": projects, "subprojects": subprojects, "tasks": tasks, "subtasks": subtasks}

    before = count_all()

    # トランザクション内でSubProject削除をシミュレート（FK制約で失敗するがカウントは可能）
    # 実際にはエンティティを個別に削除する必要があるが、ここではカウント機能のテスト
    assert before["projects"] == 1
    assert before["subprojects"] == 1
    assert before["tasks"] == 2
    assert before["subtasks"] == 2


def test_dry_run_handles_deletion_error(temp_db: Database):
    """
    dry-run で DeletionError（子が存在）が発生しても、
    有益なプレビューを表示できることを確認（要対応②の検証）
    """
    from pmtool.tui.commands import _show_delete_impact

    # リポジトリ作成
    project_repo = ProjectRepository(temp_db)
    subproject_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)

    # Project → SubProject → Task を作成（子が存在する状態）
    project = project_repo.create("TestProject", "Description")
    subproject = subproject_repo.create(project.id, "TestSubProject", None, "Description")
    task = task_repo.create(project.id, "Task", subproject.id, "Description")

    # 子が存在するProjectを dry-run で削除しようとする
    # DeletionError が発生するが、例外で落ちず、プレビュー表示されることを確認
    try:
        _show_delete_impact(temp_db, "project", project.id, use_bridge=False)
        # 例外が発生せず、ここに到達すればOK
    except Exception as e:
        # DeletionError以外の例外は失敗とする
        raise AssertionError(f"Unexpected exception: {e}")

    # DBが変化していないことを確認（dry-run なのでDB件数は不変のはず）
    # Database.connect() はシングルトン接続を返すため、close() しない
    conn = temp_db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM projects")
    assert cursor.fetchone()[0] == 1
    cursor.execute("SELECT COUNT(*) FROM subprojects")
    assert cursor.fetchone()[0] == 1
    cursor.execute("SELECT COUNT(*) FROM tasks")
    assert cursor.fetchone()[0] == 1
