#!/usr/bin/env python3
"""
Phase 1 実装の動作検証スクリプト

このスクリプトはPhase 1で実装したすべてのコア機能を検証します。
"""

import io
import sys
from pathlib import Path

# Windows UTF-8 出力対応
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from pmtool.database import Database
from pmtool.dependencies import DependencyManager
from pmtool.exceptions import (
    ConstraintViolationError,
    CyclicDependencyError,
    DeletionError,
    StatusTransitionError,
)
from pmtool.repository import (
    ProjectRepository,
    SubProjectRepository,
    SubTaskRepository,
    TaskRepository,
)
from pmtool.status import StatusManager


def print_section(title: str):
    """セクションタイトルを表示"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def main():
    print_section("Phase 1 実装 動作検証開始")

    # テスト用の一時DBを使用
    db_path = ":memory:"
    db = Database(db_path)

    try:
        # DB初期化
        print("✓ DB初期化中...")
        sql_file = project_root / "scripts" / "init_db.sql"
        db.initialize(sql_file, force=True)
        print("✓ DB初期化完了")

        # リポジトリインスタンス作成
        project_repo = ProjectRepository(db)
        subproject_repo = SubProjectRepository(db)
        task_repo = TaskRepository(db)
        subtask_repo = SubTaskRepository(db)
        dep_manager = DependencyManager(db)
        status_manager = StatusManager(db, dep_manager)

        # ========================================
        # 1. CRUD 操作テスト
        # ========================================
        print_section("1. CRUD 操作テスト")

        # Project作成
        print("✓ Projectを作成...")
        p1 = project_repo.create("プロジェクト1", "テストプロジェクト")
        print(f"  → ID={p1.id}, name='{p1.name}', order_index={p1.order_index}")

        # SubProject作成
        print("✓ SubProjectを作成...")
        sp1 = subproject_repo.create(p1.id, "サブプロジェクト1", description="テストサブプロジェクト")
        print(f"  → ID={sp1.id}, name='{sp1.name}', project_id={sp1.project_id}")

        # Task作成
        print("✓ Taskを作成...")
        t1 = task_repo.create(p1.id, "タスク1", subproject_id=sp1.id, description="テストタスク1")
        t2 = task_repo.create(p1.id, "タスク2", subproject_id=sp1.id, description="テストタスク2")
        print(f"  → Task1: ID={t1.id}, name='{t1.name}', status={t1.status}")
        print(f"  → Task2: ID={t2.id}, name='{t2.name}', status={t2.status}")

        # SubTask作成
        print("✓ SubTaskを作成...")
        st1 = subtask_repo.create(t1.id, "サブタスク1", description="テストサブタスク1")
        st2 = subtask_repo.create(t1.id, "サブタスク2", description="テストサブタスク2")
        print(f"  → SubTask1: ID={st1.id}, name='{st1.name}', status={st1.status}")
        print(f"  → SubTask2: ID={st2.id}, name='{st2.name}', status={st2.status}")

        # Read操作
        print("✓ Read操作テスト...")
        p1_read = project_repo.get_by_id(p1.id)
        assert p1_read.name == p1.name
        print(f"  → Project取得成功: {p1_read.name}")

        # Update操作
        print("✓ Update操作テスト...")
        p1_updated = project_repo.update(p1.id, name="プロジェクト1(更新)")
        assert p1_updated.name == "プロジェクト1(更新)"
        print(f"  → Project更新成功: {p1_updated.name}")

        # ========================================
        # 2. 依存関係管理テスト
        # ========================================
        print_section("2. 依存関係管理テスト")

        # Task間依存関係を追加
        print("✓ Task依存関係を追加 (Task1 → Task2)...")
        dep1 = dep_manager.add_task_dependency(t1.id, t2.id)
        print(f"  → 依存関係作成: predecessor={dep1.predecessor_id}, successor={dep1.successor_id}")

        # SubTask間依存関係を追加
        print("✓ SubTask依存関係を追加 (SubTask1 → SubTask2)...")
        dep2 = dep_manager.add_subtask_dependency(st1.id, st2.id)
        print(f"  → 依存関係作成: predecessor={dep2.predecessor_id}, successor={dep2.successor_id}")

        # 循環依存の検出テスト
        print("✓ 循環依存検出テスト (Task2 → Task1 を追加)...")
        try:
            dep_manager.add_task_dependency(t2.id, t1.id)  # これは循環を作る
            print("  ✗ エラー: 循環依存が検出されませんでした")
            return 1
        except CyclicDependencyError as e:
            print(f"  → 循環依存を正しく検出: {e}")

        # 依存関係取得
        print("✓ 依存関係取得テスト...")
        t1_deps = dep_manager.get_task_dependencies(t1.id)
        print(f"  → Task1の依存関係: {t1_deps}")
        assert t1_deps["successors"] == [t2.id]

        # ========================================
        # 3. ステータス管理テスト
        # ========================================
        print_section("3. ステータス管理テスト")

        # 通常のステータス遷移
        print("✓ SubTask1をDONEに遷移...")
        st1_done = status_manager.update_subtask_status(st1.id, "DONE")
        assert st1_done.status == "DONE"
        print(f"  → SubTask1ステータス: {st1_done.status}")

        print("✓ SubTask2をDONEに遷移...")
        st2_done = status_manager.update_subtask_status(st2.id, "DONE")
        print(f"  → SubTask2ステータス: {st2_done.status}")

        # DONE遷移条件チェック (先行タスクがDONEでない場合)
        print("✓ Task2をDONEに遷移 (先行Task1がDONEでない)...")
        try:
            status_manager.update_task_status(t2.id, "DONE")
            print("  ✗ エラー: DONE遷移条件チェックが機能していません")
            return 1
        except StatusTransitionError as e:
            print(f"  → DONE遷移条件を正しく検出: {e}")

        # 先行タスクをDONEにしてから再試行
        print("✓ Task1をDONEに遷移 (すべての子SubTaskがDONE)...")
        t1_done = status_manager.update_task_status(t1.id, "DONE")
        print(f"  → Task1ステータス: {t1_done.status}")

        print("✓ Task2をDONEに遷移 (先行Task1がDONE)...")
        t2_done = status_manager.update_task_status(t2.id, "DONE")
        print(f"  → Task2ステータス: {t2_done.status}")

        # ========================================
        # 4. 削除制御テスト
        # ========================================
        print_section("4. 削除制御テスト")

        # 新しいテストデータ作成
        p2 = project_repo.create("プロジェクト2", "削除テスト用")
        t3 = task_repo.create(p2.id, "タスク3")
        t4 = task_repo.create(p2.id, "タスク4")
        t5 = task_repo.create(p2.id, "タスク5")

        # 依存関係: t3 → t4 → t5
        dep_manager.add_task_dependency(t3.id, t4.id)
        dep_manager.add_task_dependency(t4.id, t5.id)

        # 子を持つProjectの削除はエラー
        print("✓ 子を持つProjectの削除テスト...")
        try:
            project_repo.delete(p2.id)
            print("  ✗ エラー: 子存在チェックが機能していません")
            return 1
        except ConstraintViolationError as e:
            print(f"  → 子存在を正しく検出: {e}")

        # 橋渡し削除テスト
        print("✓ Task4を橋渡し削除 (t3 → t4 → t5 が t3 → t5 になる)...")
        bridged = task_repo.delete_with_bridge(t4.id)
        print(f"  → 橋渡しされた依存関係: {bridged}")

        # t3 → t5 の依存関係が存在することを確認
        t3_deps_after = dep_manager.get_task_dependencies(t3.id)
        assert t5.id in t3_deps_after["successors"]
        print(f"  → Task3の依存関係(橋渡し後): {t3_deps_after}")

        # 連鎖削除テスト
        t6 = task_repo.create(p2.id, "タスク6")
        st3 = subtask_repo.create(t6.id, "サブタスク3")
        st4 = subtask_repo.create(t6.id, "サブタスク4")

        print("✓ Task6を連鎖削除 (子SubTask含む)...")
        result = task_repo.cascade_delete(t6.id, force=True)
        print(f"  → 削除結果: {result}")
        assert len(result["subtasks_deleted"]) == 2

        # forceフラグなしの連鎖削除はエラー
        t7 = task_repo.create(p2.id, "タスク7")
        subtask_repo.create(t7.id, "サブタスク5")

        print("✓ force=Falseで連鎖削除を試行...")
        try:
            task_repo.cascade_delete(t7.id, force=False)
            print("  ✗ エラー: forceフラグチェックが機能していません")
            return 1
        except DeletionError as e:
            print(f"  → forceフラグを正しく検出: {e}")

        # ========================================
        # 完了
        # ========================================
        print_section("検証完了")
        print("✓ すべてのテストが成功しました!")
        print("\nPhase 1 実装の動作検証が完了しました。")
        return 0

    except Exception as e:
        print(f"\n✗ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
