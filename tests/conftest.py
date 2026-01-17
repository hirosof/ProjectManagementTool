"""
pytest configuration and shared fixtures
"""
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from pmtool.database import Database


@pytest.fixture
def temp_db() -> Generator[Database, None, None]:
    """
    一時的なテスト用データベースを作成するfixture

    各テストで独立したDBを使用し、テスト終了後に自動削除される
    """
    # 一時ファイルを作成
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    db = None
    try:
        # Databaseインスタンスを作成
        db = Database(db_path)

        # init_db.sqlのパスを取得
        project_root = Path(__file__).parent.parent
        init_sql_path = project_root / "scripts" / "init_db.sql"

        # データベース初期化
        db.initialize(str(init_sql_path), force=True)

        yield db

    finally:
        # すべての接続を明示的に閉じる
        if db is not None:
            # Databaseクラスに接続プールがある場合は閉じる処理を追加
            # 現状は個別に接続を管理しているため、GCに任せる
            pass

        # 短い待機時間を設ける（Windows環境でのファイルロック解放を待つ）
        import time
        time.sleep(0.1)

        # テスト終了後、一時ファイルを削除
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
        except PermissionError:
            # Windows環境でファイルが使用中の場合はスキップ
            # テストの成否には影響しない
            pass


@pytest.fixture
def db_connection(temp_db: Database) -> Generator[sqlite3.Connection, None, None]:
    """
    テスト用のDB接続を提供するfixture

    トランザクション管理が必要なテストで使用
    """
    conn = temp_db.connect()
    try:
        yield conn
    finally:
        conn.close()
