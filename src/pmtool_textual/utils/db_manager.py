"""DB接続管理ユーティリティ"""
from pathlib import Path
from pmtool.database import Database


class DBManager:
    """Textual UI用DB接続マネージャー"""

    def __init__(self, db_path: str = "data/pmtool.db"):
        self.db_path = db_path
        self.db: Database | None = None

    def connect(self) -> Database:
        """DB接続"""
        if self.db is None:
            self.db = Database(self.db_path)
        return self.db

    def is_db_exists(self) -> bool:
        """DBファイルが存在するか確認"""
        return Path(self.db_path).exists()
