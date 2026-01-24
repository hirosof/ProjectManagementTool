"""
データベース接続および初期化モジュール

Phase 0: 基盤構築
- SQLite接続管理
- DB初期化
- PRAGMA設定

重要な注意事項:
    SQLiteの外部キー制約（PRAGMA foreign_keys）は接続単位で設定されます。
    本モジュールのDatabaseクラスは、connect()時に自動的に外部キー制約を有効化します。

    そのため、データベース操作を行う際は必ず本Databaseクラス経由で接続してください。
    sqlite3.connect()を直接使用すると、外部キー制約が無効のまま動作する可能性があります。
"""

import sqlite3
from pathlib import Path
from typing import Optional


class Database:
    """
    SQLiteデータベース接続を管理するクラス

    このクラスは、データベース接続時に自動的に以下の設定を行います:
    - PRAGMA foreign_keys = ON（外部キー制約の有効化）
    - Row factory設定（カラム名でのアクセスを可能にする）

    重要:
        外部キー制約はSQLiteでは接続単位で設定されるため、
        データベース操作を行う際は必ず本クラス経由で接続してください。
    """

    def __init__(self, db_path: str | Path):
        """
        データベース接続を初期化

        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = Path(db_path)
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """
        データベースに接続

        Returns:
            sqlite3.Connection: データベース接続オブジェクト
        """
        # 既存のコネクションがcloseされている場合は再作成
        if self._connection is not None:
            try:
                # コネクションの有効性をチェック
                self._connection.execute("SELECT 1")
            except sqlite3.ProgrammingError:
                # closeされている場合は再作成
                self._connection = None

        if self._connection is None:
            self._connection = sqlite3.connect(str(self.db_path))
            # Row factoryを設定（カラム名でアクセス可能にする）
            self._connection.row_factory = sqlite3.Row
            # 外部キー制約を有効化
            self._connection.execute("PRAGMA foreign_keys = ON")

        return self._connection

    def close(self):
        """データベース接続を閉じる"""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def is_initialized(self) -> bool:
        """
        データベースが初期化済みかチェック

        Returns:
            bool: 初期化済みの場合True
        """
        if not self.db_path.exists():
            return False

        conn = self.connect()
        cursor = conn.cursor()

        try:
            # schema_versionテーブルの存在確認
            cursor.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='schema_version'"
            )
            result = cursor.fetchone()
            return result is not None
        except sqlite3.Error:
            return False

    def get_schema_version(self) -> Optional[int]:
        """
        現在のスキーマバージョンを取得

        Returns:
            Optional[int]: スキーマバージョン（未初期化の場合None）
        """
        if not self.is_initialized():
            return None

        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error:
            return None

    def initialize(self, sql_file: str | Path, force: bool = False):
        """
        データベースを初期化

        Args:
            sql_file: 初期化SQLファイルのパス
            force: すでに初期化済みの場合でも強制的に再初期化する場合True（デフォルト: False）

        Raises:
            FileNotFoundError: SQLファイルが存在しない場合
            RuntimeError: すでに初期化済みの場合（force=Falseの場合のみ）
            sqlite3.Error: SQL実行エラーが発生した場合

        注意:
            force=Trueで再初期化すると、既存のデータはすべて失われます。
        """
        # 初期化済みチェック
        if self.is_initialized() and not force:
            raise RuntimeError(
                f"Database is already initialized at {self.db_path}. "
                "Use force=True to reinitialize (WARNING: all data will be lost)."
            )

        sql_path = Path(sql_file)
        if not sql_path.exists():
            raise FileNotFoundError(f"SQL file not found: {sql_path}")

        # SQLファイルを読み込み
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        # 接続とSQL実行
        conn = self.connect()
        cursor = conn.cursor()

        try:
            # force=Trueの場合、既存のテーブルをすべて削除
            if force and self.is_initialized():
                # 既存のテーブル一覧を取得
                cursor.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                tables = [row[0] for row in cursor.fetchall()]

                # 外部キー制約を一時的に無効化
                cursor.execute("PRAGMA foreign_keys = OFF")

                # すべてのテーブルを削除
                for table in tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")

                # 外部キー制約を再度有効化
                cursor.execute("PRAGMA foreign_keys = ON")

                conn.commit()

            # SQLスクリプトを実行
            cursor.executescript(sql_script)
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise e

    def verify_foreign_keys(self) -> bool:
        """
        外部キー制約が有効化されているか確認

        Returns:
            bool: 有効化されている場合True
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        return result[0] == 1 if result else False

    def get_table_list(self) -> list[str]:
        """
        データベース内のテーブル一覧を取得

        Returns:
            list[str]: テーブル名のリスト
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        )

        return [row[0] for row in cursor.fetchall()]

    def __enter__(self):
        """コンテキストマネージャのエントリ"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャの終了"""
        self.close()
