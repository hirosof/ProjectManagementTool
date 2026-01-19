"""
test_database_coverage.py

database.pyのカバレッジ向上テスト

戦略:
- 未カバーのメソッド（is_initialized, get_schema_version, get_table_list等）をテスト
- context managerのテスト
- 初期化・検証系のテスト
"""

import os
import tempfile
from pathlib import Path

import pytest
import sqlite3

from pmtool.database import Database


class TestDatabaseInitialization:
    """Database初期化テスト"""

    def test_database_path_as_string(self):
        """データベースパスが文字列の場合"""
        db = Database("test.db")
        assert db.db_path == Path("test.db")

    def test_database_path_as_path(self):
        """データベースパスがPathオブジェクトの場合"""
        db = Database(Path("test.db"))
        assert db.db_path == Path("test.db")


class TestDatabaseConnection:
    """Database接続テスト"""

    def test_connect_creates_connection(self, tmp_path):
        """接続作成"""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        conn = db.connect()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)

        # 同じ接続が返されることを確認
        conn2 = db.connect()
        assert conn is conn2

        db.close()

    def test_close_connection(self, tmp_path):
        """接続クローズ"""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        conn = db.connect()
        db.close()

        # クローズ後はNoneになる
        assert db._connection is None

    def test_connect_enables_foreign_keys(self, tmp_path):
        """接続時に外部キー制約が有効化されることを確認"""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()

        assert result[0] == 1

        db.close()


class TestDatabaseIsInitialized:
    """is_initialized関数のテスト"""

    def test_is_initialized_false_when_file_not_exists(self):
        """ファイルが存在しない場合はFalse"""
        db = Database("nonexistent.db")
        assert db.is_initialized() is False

    def test_is_initialized_false_when_no_schema_version_table(self, tmp_path):
        """schema_versionテーブルがない場合はFalse"""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        # 接続だけ作成（スキーマは作成しない）
        conn = db.connect()
        db.close()

        assert db.is_initialized() is False

    def test_is_initialized_true_when_schema_version_exists(self, temp_db):
        """schema_versionテーブルがある場合はTrue"""
        assert temp_db.is_initialized() is True


class TestGetSchemaVersion:
    """get_schema_version関数のテスト"""

    def test_get_schema_version_none_when_not_initialized(self, tmp_path):
        """未初期化の場合はNone"""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        assert db.get_schema_version() is None

    def test_get_schema_version_returns_version(self, temp_db):
        """初期化済みの場合はバージョンを返す"""
        version = temp_db.get_schema_version()
        assert version is not None
        assert isinstance(version, int)


class TestDatabaseInitialize:
    """initialize関数のテスト"""

    def test_initialize_creates_schema(self, tmp_path):
        """初期化によりスキーマが作成される"""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        # init_db.sqlのパスを取得
        project_root = Path(__file__).parent.parent
        init_sql_path = project_root / "scripts" / "init_db.sql"

        db.initialize(init_sql_path)

        assert db.is_initialized() is True

        db.close()

    def test_initialize_raises_error_when_already_initialized(self, temp_db):
        """既に初期化済みの場合はエラー"""
        project_root = Path(__file__).parent.parent
        init_sql_path = project_root / "scripts" / "init_db.sql"

        with pytest.raises(RuntimeError) as exc_info:
            temp_db.initialize(init_sql_path, force=False)

        assert "already initialized" in str(exc_info.value)

    def test_initialize_force_reinitializes(self, temp_db):
        """force=Trueで再初期化"""
        project_root = Path(__file__).parent.parent
        init_sql_path = project_root / "scripts" / "init_db.sql"

        # 再初期化（エラーにならない）
        temp_db.initialize(init_sql_path, force=True)

        assert temp_db.is_initialized() is True

    def test_initialize_raises_error_when_sql_file_not_found(self, tmp_path):
        """SQLファイルが存在しない場合はエラー"""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        with pytest.raises(FileNotFoundError):
            db.initialize("nonexistent.sql")

        db.close()


class TestVerifyForeignKeys:
    """verify_foreign_keys関数のテスト"""

    def test_verify_foreign_keys_enabled(self, temp_db):
        """外部キー制約が有効であることを確認"""
        assert temp_db.verify_foreign_keys() is True


class TestGetTableList:
    """get_table_list関数のテスト"""

    def test_get_table_list_returns_tables(self, temp_db):
        """テーブル一覧を取得"""
        tables = temp_db.get_table_list()

        assert isinstance(tables, list)
        assert len(tables) > 0

        # 期待されるテーブルが含まれることを確認
        expected_tables = [
            "projects",
            "subprojects",
            "tasks",
            "subtasks",
            "task_dependencies",
            "subtask_dependencies",
            "schema_version",
        ]

        for table in expected_tables:
            assert table in tables

    def test_get_table_list_excludes_sqlite_internal_tables(self, temp_db):
        """SQLiteの内部テーブルが除外されることを確認"""
        tables = temp_db.get_table_list()

        # sqlite_ で始まるテーブルは含まれない
        for table in tables:
            assert not table.startswith("sqlite_")


class TestContextManager:
    """context manager（with文）のテスト"""

    def test_context_manager_enter_exit(self, tmp_path):
        """with文でのコンテキストマネージャ"""
        db_path = tmp_path / "test.db"

        with Database(db_path) as db:
            # __enter__ が呼ばれて接続が作成される
            assert db._connection is not None

            # 接続が有効であることを確認
            conn = db.connect()
            assert conn is not None

        # __exit__ が呼ばれて接続がクローズされる
        # (ただし現在の実装では __exit__ で close() が呼ばれる)

    def test_context_manager_with_initialization(self, tmp_path):
        """with文 + 初期化"""
        db_path = tmp_path / "test.db"
        project_root = Path(__file__).parent.parent
        init_sql_path = project_root / "scripts" / "init_db.sql"

        with Database(db_path) as db:
            db.initialize(init_sql_path)
            assert db.is_initialized() is True

            # テーブル一覧を取得
            tables = db.get_table_list()
            assert len(tables) > 0
