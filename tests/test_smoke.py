"""
Smoke tests - 基本的な動作確認テスト

pytest環境が正しく動作することを確認するための最小限のテスト
"""
import sqlite3

from pmtool.database import Database


def test_smoke_database_creation(temp_db: Database):
    """
    Smoke test: データベースが正しく作成されることを確認
    """
    assert temp_db is not None
    assert temp_db.db_path is not None


def test_smoke_database_tables_exist(temp_db: Database):
    """
    Smoke test: 必要なテーブルが存在することを確認
    """
    conn = temp_db.connect()
    try:
        cursor = conn.cursor()

        # テーブル一覧を取得
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        # 期待するテーブルが存在することを確認
        expected_tables = [
            'projects',
            'subprojects',
            'tasks',
            'subtasks',
            'task_dependencies',
            'subtask_dependencies',
        ]

        for table in expected_tables:
            assert table in tables, f"Table '{table}' not found"

    finally:
        conn.close()


def test_smoke_database_connection(db_connection: sqlite3.Connection):
    """
    Smoke test: DB接続fixtureが正しく動作することを確認
    """
    assert db_connection is not None

    # 簡単なクエリを実行
    cursor = db_connection.cursor()
    cursor.execute("SELECT 1 as test_value")
    result = cursor.fetchone()

    assert result is not None
    # sqlite3.Row型の場合、インデックスアクセスで値を取得
    assert result[0] == 1
