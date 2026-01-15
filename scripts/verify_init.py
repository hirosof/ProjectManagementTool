"""
DB初期化検証スクリプト

Phase 0: 基盤構築
- データベース初期化の実行
- PRAGMA設定の確認
- テーブル作成の確認
- スキーマバージョンの確認
"""

import sys
import io
from pathlib import Path

# Windows環境でのUnicodeエンコーディング問題を回避
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# src/pmtool をインポートパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from pmtool.database import Database


def main():
    """DB初期化と検証を実行"""
    print("=" * 60)
    print("Phase 0: データベース初期化検証")
    print("=" * 60)
    print()

    # パス設定
    db_path = project_root / "data" / "pmtool.db"
    sql_path = project_root / "scripts" / "init_db.sql"

    # dataディレクトリ作成
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # データベース初期化
    print("1. データベース初期化")
    print("-" * 60)

    db = Database(db_path)

    try:
        # 初期化前の状態確認
        is_initialized_before = db.is_initialized()
        print(f"DB初期化前: {is_initialized_before}")

        # 初期化実行
        print(f"SQLファイル: {sql_path}")

        # 既存のDBがある場合は force=True で再初期化
        if is_initialized_before:
            print("既存のDBを検出（force=Trueで再初期化）")
            db.initialize(sql_path, force=True)
        else:
            db.initialize(sql_path)

        print("✓ 初期化成功")
        print()

        # 初期化後の状態確認
        print(f"DB初期化後: {db.is_initialized()}")
        print()

    except Exception as e:
        print(f"✗ 初期化失敗: {e}")
        return 1

    # PRAGMA確認
    print("2. PRAGMA設定確認")
    print("-" * 60)

    try:
        fk_enabled = db.verify_foreign_keys()
        print(f"外部キー制約: {'有効' if fk_enabled else '無効'}")

        if not fk_enabled:
            print("✗ 外部キー制約が無効です")
            return 1

        print("✓ PRAGMA設定OK")
        print()

    except Exception as e:
        print(f"✗ PRAGMA確認失敗: {e}")
        return 1

    # テーブル一覧確認
    print("3. テーブル作成確認")
    print("-" * 60)

    expected_tables = [
        "projects",
        "schema_version",
        "subprojects",
        "subtask_dependencies",
        "subtasks",
        "task_dependencies",
        "tasks",
    ]

    try:
        tables = db.get_table_list()
        print(f"作成されたテーブル数: {len(tables)}")
        print()

        for table in tables:
            print(f"  - {table}")

        print()

        # 期待されるテーブルがすべて存在するか確認
        missing_tables = set(expected_tables) - set(tables)
        if missing_tables:
            print(f"✗ 不足しているテーブル: {missing_tables}")
            return 1

        print(f"✓ すべてのテーブル作成OK（{len(expected_tables)}テーブル）")
        print()

    except Exception as e:
        print(f"✗ テーブル確認失敗: {e}")
        return 1

    # スキーマバージョン確認
    print("4. スキーマバージョン確認")
    print("-" * 60)

    try:
        version = db.get_schema_version()
        print(f"現在のスキーマバージョン: {version}")

        if version != 1:
            print(f"✗ スキーマバージョンが期待値(1)と異なります: {version}")
            return 1

        print("✓ スキーマバージョンOK")
        print()

    except Exception as e:
        print(f"✗ スキーマバージョン確認失敗: {e}")
        return 1

    # インデックス確認（部分UNIQUEインデックスの存在確認）
    print("5. インデックス確認")
    print("-" * 60)

    try:
        conn = db.connect()
        cursor = conn.cursor()

        # 部分UNIQUEインデックスの確認
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND name LIKE '%unique%'"
        )
        unique_indexes = [row[0] for row in cursor.fetchall()]

        print(f"部分UNIQUEインデックス数: {len(unique_indexes)}")
        print()

        for index in unique_indexes:
            print(f"  - {index}")

        print()

        # 期待されるインデックス
        expected_unique_indexes = [
            "idx_subprojects_unique_project_direct",
            "idx_subprojects_unique_nested",
            "idx_tasks_unique_project_direct",
            "idx_tasks_unique_subproject",
        ]

        missing_indexes = set(expected_unique_indexes) - set(unique_indexes)
        if missing_indexes:
            print(f"✗ 不足しているインデックス: {missing_indexes}")
            return 1

        print(f"✓ 部分UNIQUEインデックスOK（{len(expected_unique_indexes)}個）")
        print()

    except Exception as e:
        print(f"✗ インデックス確認失敗: {e}")
        return 1
    finally:
        db.close()

    # 完了メッセージ
    print("=" * 60)
    print("Phase 0: 初期化検証完了")
    print("=" * 60)
    print()
    print(f"データベースファイル: {db_path}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
