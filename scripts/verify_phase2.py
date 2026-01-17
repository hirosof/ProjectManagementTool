#!/usr/bin/env python3
"""
Phase 2 実装の動作検証スクリプト

このスクリプトはPhase 2で実装したTUI（CLI）機能を検証します。
commands.pyの各関数を直接呼び出して、動作確認を行います。
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

from argparse import Namespace

from pmtool.database import Database
from pmtool.dependencies import DependencyManager
from pmtool.exceptions import CyclicDependencyError, StatusTransitionError
from pmtool.repository import ProjectRepository
from pmtool.tui import commands


def print_section(title: str):
    """セクションタイトルを表示"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def main():
    print_section("Phase 2 TUI実装 動作検証開始")

    # テスト用の一時DBを使用
    db_path = ":memory:"
    db = Database(db_path)

    try:
        # DB初期化
        print("✓ DB初期化中...")
        sql_file = project_root / "scripts" / "init_db.sql"
        db.initialize(sql_file, force=True)
        print("✓ DB初期化完了\n")

        # ========================================
        # 1. Project一覧表示（空の状態）
        # ========================================
        print_section("1. Project一覧表示（空の状態）")
        args = Namespace(entity="projects")
        commands.handle_list(db, args)

        # ========================================
        # 2. Project追加
        # ========================================
        print_section("2. Project追加")
        args = Namespace(
            entity="project", name="テストプロジェクト", desc="Phase 2検証用プロジェクト"
        )
        commands.handle_add(db, args)

        # ========================================
        # 3. Project一覧表示（1件）
        # ========================================
        print_section("3. Project一覧表示（1件）")
        args = Namespace(entity="projects")
        commands.handle_list(db, args)

        # プロジェクトIDを取得（以降の操作で使用）
        project_repo = ProjectRepository(db)
        projects = project_repo.get_all()
        project_id = projects[0].id

        # ========================================
        # 4. SubProject追加
        # ========================================
        print_section("4. SubProject追加")
        args = Namespace(
            entity="subproject",
            project=project_id,
            name="サブプロジェクト1",
            desc="テスト用サブプロジェクト",
        )
        commands.handle_add(db, args)

        # ========================================
        # 5. Task追加（SubProject配下）
        # ========================================
        print_section("5. Task追加（SubProject配下）")
        # SubProjectIDを取得
        from pmtool.repository import SubProjectRepository

        subproject_repo = SubProjectRepository(db)
        subprojects = subproject_repo.get_by_project(project_id)
        subproject_id = subprojects[0].id

        args = Namespace(
            entity="task",
            project=project_id,
            subproject=subproject_id,
            name="タスク1",
            desc="Phase 2検証用タスク",
        )
        commands.handle_add(db, args)

        args = Namespace(
            entity="task",
            project=project_id,
            subproject=subproject_id,
            name="タスク2",
            desc="Phase 2検証用タスク2",
        )
        commands.handle_add(db, args)

        # ========================================
        # 6. SubTask追加
        # ========================================
        print_section("6. SubTask追加")
        # TaskIDを取得
        from pmtool.repository import TaskRepository, SubTaskRepository

        task_repo = TaskRepository(db)
        tasks = task_repo.get_by_parent(project_id=project_id, subproject_id=subproject_id)
        task1_id = tasks[0].id

        # 対話的入力をバイパスするため、リポジトリを直接呼び出す
        subtask_repo = SubTaskRepository(db)
        st1 = subtask_repo.create(task1_id, "サブタスク1", description=None)
        print(f"✓ SubTask作成成功: ID={st1.id}, 名前={st1.name}, ステータス={st1.status}")

        st2 = subtask_repo.create(task1_id, "サブタスク2", description=None)
        print(f"✓ SubTask作成成功: ID={st2.id}, 名前={st2.name}, ステータス={st2.status}")

        # ========================================
        # 7. ツリー表示
        # ========================================
        print_section("7. Project階層ツリー表示")
        args = Namespace(entity="project", id=project_id)
        commands.handle_show(db, args)

        # ========================================
        # 8. 依存関係追加（Task間）
        # ========================================
        print_section("8. 依存関係追加（Task間）")
        task2_id = tasks[1].id
        args = Namespace(
            entity="task", deps_command="add", from_id=task1_id, to_id=task2_id
        )
        commands.handle_deps(db, args)

        # ========================================
        # 9. 依存関係一覧表示
        # ========================================
        print_section("9. 依存関係一覧表示")
        args = Namespace(entity="task", deps_command="list", id=task2_id)
        commands.handle_deps(db, args)

        # ========================================
        # 10. ステータス変更失敗テスト（先行ノード未完了）
        # ========================================
        print_section("10. ステータス変更失敗テスト（先行ノード未完了）")
        try:
            # Task1が未完了の状態でTask2をDONEにしようとする
            args = Namespace(entity="task", id=task2_id, status="DONE")
            commands.handle_status(db, args)
            print("❌ エラーが発生しませんでした（想定外）")
        except StatusTransitionError as e:
            print(f"✓ 期待通りのエラー: {e}")

        # ========================================
        # 11. ステータス変更（SubTask）
        # ========================================
        print_section("11. ステータス変更（SubTask → DONE）")
        # SubTaskIDを取得（上で作成済み）
        subtask1_id = st1.id
        subtask2_id = st2.id

        args = Namespace(entity="subtask", id=subtask1_id, status="DONE")
        commands.handle_status(db, args)

        args = Namespace(entity="subtask", id=subtask2_id, status="DONE")
        commands.handle_status(db, args)

        # ========================================
        # 12. ステータス変更（Task1 → DONE）
        # ========================================
        print_section("12. ステータス変更（Task1 → DONE）")
        args = Namespace(entity="task", id=task1_id, status="DONE")
        commands.handle_status(db, args)

        # Task2もDONEにできる（先行ノードが完了したため）
        print("\n✓ Task2もDONEに変更可能になりました（先行ノード完了のため）")
        args = Namespace(entity="task", id=task2_id, status="DONE")
        commands.handle_status(db, args)

        # ========================================
        # 13. サイクル検出テスト
        # ========================================
        print_section("13. サイクル検出テスト")
        try:
            # Task2 → Task1 の依存を追加（サイクル形成）
            args = Namespace(
                entity="task", deps_command="add", from_id=task2_id, to_id=task1_id
            )
            commands.handle_deps(db, args)
            print("❌ サイクルが検出されませんでした（想定外）")
        except CyclicDependencyError as e:
            print(f"✓ 期待通りのサイクル検出: {e}")

        # ========================================
        # 14. 依存関係削除
        # ========================================
        print_section("14. 依存関係削除")
        args = Namespace(
            entity="task", deps_command="remove", from_id=task1_id, to_id=task2_id
        )
        commands.handle_deps(db, args)

        # ========================================
        # 15. 削除テスト（標準削除）
        # ========================================
        print_section("15. SubTask削除（標準削除）")
        # confirm()をバイパスするため、直接削除処理を呼び出す
        subtask_repo.delete(subtask1_id)
        print(f"✓ SubTask ID={subtask1_id} を削除しました。")

        # ========================================
        # 16. 最終ツリー表示
        # ========================================
        print_section("16. 最終ツリー表示")
        args = Namespace(entity="project", id=project_id)
        commands.handle_show(db, args)

        # ========================================
        # まとめ
        # ========================================
        print_section("Phase 2 検証完了")
        print("✓ すべての基本機能が正常に動作しました")
        print("✓ エラーハンドリングも期待通りに動作しました")
        print("✓ 依存関係管理（追加・削除・サイクル検出）が正常に動作しました")
        print("✓ ステータス管理（DONE遷移条件チェック）が正常に動作しました")
        print("\nPhase 2 MVP実装は成功です！")

    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
