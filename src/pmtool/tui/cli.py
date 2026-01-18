"""
TUI CLIエントリーポイント

argparseによるサブコマンド方式のCLIインターフェースを提供します。
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console

from ..database import Database
from ..exceptions import (
    ConstraintViolationError,
    CyclicDependencyError,
    DeletionError,
    PMToolError,
    StatusTransitionError,
    ValidationError,
)
from . import commands

console = Console()


def create_parser() -> argparse.ArgumentParser:
    """
    argparseパーサーを構築

    サブコマンド: list, show, add, delete, status, deps
    """
    parser = argparse.ArgumentParser(
        prog="pmtool", description="階層型プロジェクト管理ツール"
    )

    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # list コマンド
    list_parser = subparsers.add_parser("list", help="一覧表示")
    list_parser.add_argument("entity", choices=["projects"], help="表示対象")

    # show コマンド
    show_parser = subparsers.add_parser("show", help="ツリー表示")
    show_parser.add_argument("entity", choices=["project"], help="表示対象")
    show_parser.add_argument("id", type=int, help="エンティティID")

    # add コマンド
    add_parser = subparsers.add_parser("add", help="エンティティ追加")
    add_parser.add_argument(
        "entity",
        choices=["project", "subproject", "task", "subtask"],
        help="追加対象",
    )
    add_parser.add_argument("--project", type=int, help="親プロジェクトID")
    add_parser.add_argument("--subproject", type=int, help="親サブプロジェクトID")
    add_parser.add_argument("--task", type=int, help="親タスクID")
    add_parser.add_argument("--name", help="名前")
    add_parser.add_argument("--desc", help="説明")

    # delete コマンド
    delete_parser = subparsers.add_parser("delete", help="エンティティ削除")
    delete_parser.add_argument(
        "entity",
        choices=["project", "subproject", "task", "subtask"],
        help="削除対象",
    )
    delete_parser.add_argument("id", type=int, help="エンティティID")
    delete_parser.add_argument(
        "--bridge",
        action="store_true",
        help="依存関係の橋渡し削除（Task/SubTaskのみ有効）",
    )
    delete_parser.add_argument(
        "--cascade",
        action="store_true",
        help="サブツリー一括削除（子エンティティも含めて削除）",
    )
    delete_parser.add_argument(
        "--force",
        action="store_true",
        help="削除を強制実行（--cascade 使用時は必須）",
    )
    delete_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="削除を実行せず、影響範囲のみを表示",
    )

    # status コマンド
    status_parser = subparsers.add_parser("status", help="ステータス変更")
    status_parser.add_argument(
        "entity", choices=["task", "subtask"], help="対象エンティティ"
    )
    status_parser.add_argument("id", type=int, help="エンティティID")
    status_parser.add_argument(
        "status",
        choices=["UNSET", "NOT_STARTED", "IN_PROGRESS", "DONE"],
        help="新しいステータス",
    )

    # update コマンド
    update_parser = subparsers.add_parser("update", help="エンティティ更新")
    update_parser.add_argument(
        "entity",
        choices=["project", "subproject", "task", "subtask"],
        help="更新対象",
    )
    update_parser.add_argument("id", type=int, help="エンティティID")
    update_parser.add_argument("--name", type=str, help="新しい名前")
    update_parser.add_argument("--description", "--desc", type=str, help="新しい説明")
    update_parser.add_argument("--order", type=int, help="新しいorder_index")

    # deps コマンド
    deps_parser = subparsers.add_parser("deps", help="依存関係管理")
    deps_subparsers = deps_parser.add_subparsers(dest="deps_command")

    # deps add
    deps_add = deps_subparsers.add_parser("add", help="依存関係追加")
    deps_add.add_argument("entity", choices=["task", "subtask"])
    deps_add.add_argument(
        "--from",
        dest="from_id",
        type=int,
        required=True,
        help="先行ノードID（predecessor）",
    )
    deps_add.add_argument(
        "--to", dest="to_id", type=int, required=True, help="後続ノードID（successor）"
    )

    # deps remove
    deps_remove = deps_subparsers.add_parser("remove", help="依存関係削除")
    deps_remove.add_argument("entity", choices=["task", "subtask"])
    deps_remove.add_argument("--from", dest="from_id", type=int, required=True)
    deps_remove.add_argument("--to", dest="to_id", type=int, required=True)

    # deps list
    deps_list = deps_subparsers.add_parser("list", help="依存関係一覧")
    deps_list.add_argument("entity", choices=["task", "subtask"])
    deps_list.add_argument("id", type=int, help="エンティティID")

    # doctor/check コマンド
    doctor_parser = subparsers.add_parser(
        "doctor", help="データベース整合性チェック", aliases=["check"]
    )

    return parser


def main() -> None:
    """
    CLIのエントリーポイント

    argparseでサブコマンドをパースし、適切なハンドラにディスパッチする
    """
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # DB初期化
    db_path = Path("data/pmtool.db")
    db = Database(str(db_path))

    try:
        # サブコマンドディスパッチ
        if args.command == "list":
            commands.handle_list(db, args)
        elif args.command == "show":
            commands.handle_show(db, args)
        elif args.command == "add":
            commands.handle_add(db, args)
        elif args.command == "delete":
            commands.handle_delete(db, args)
        elif args.command == "status":
            commands.handle_status(db, args)
        elif args.command == "update":
            commands.handle_update(db, args)
        elif args.command == "deps":
            commands.handle_deps(db, args)
        elif args.command in ("doctor", "check"):
            commands.handle_doctor(db, args)
        else:
            console.print(f"[red]エラー: 未知のコマンド '{args.command}'[/red]")
            sys.exit(1)

    except ValidationError as e:
        console.print(f"[red]ERROR: 入力エラー: {e}[/red]")
        sys.exit(1)
    except ConstraintViolationError as e:
        console.print(f"[red]ERROR: 制約違反: {e}[/red]")
        sys.exit(1)
    except CyclicDependencyError as e:
        # レビュー指摘B-6対応: 循環検出エラーの表示強化
        console.print(f"[red]ERROR: 循環依存エラー: {e}[/red]")
        console.print("[yellow]ヒント: この依存関係を追加すると循環が発生します。[/yellow]")
        sys.exit(1)
    except StatusTransitionError as e:
        # P0-02: reason code 優先の判定（文字列判定から脱却）
        console.print(f"[red]ERROR: ステータス遷移エラー: {e}[/red]")

        # reason code で分岐
        from ..exceptions import StatusTransitionFailureReason

        if e.reason == StatusTransitionFailureReason.PREREQUISITE_NOT_DONE:
            console.print("[yellow]原因: 先行ノードが未完了です[/yellow]")
            console.print(
                "[dim]ヒント: 先行ノードのステータスをDONEにしてから再度お試しください[/dim]"
            )
        elif e.reason == StatusTransitionFailureReason.CHILD_NOT_DONE:
            console.print("[yellow]原因: 子SubTaskが未完了です[/yellow]")
            console.print(
                "[dim]ヒント: すべての子SubTaskのステータスをDONEにしてから再度お試しください[/dim]"
            )
        elif e.reason == StatusTransitionFailureReason.NODE_NOT_FOUND:
            console.print("[yellow]原因: 対象ノードが存在しません[/yellow]")
            console.print("[dim]ヒント: IDを確認してください[/dim]")
        else:
            # reason が None または INVALID_TRANSITION の場合
            console.print("[yellow]ヒント: DONE遷移条件を満たしていません[/yellow]")
        sys.exit(1)
    except DeletionError as e:
        # レビュー指摘B-5対応: ChildExists系エラーの案内強化
        console.print(f"[red]ERROR: 削除エラー: {e}[/red]")
        console.print("[yellow]ヒント: 子ノードが存在する場合の対処方法:[/yellow]")
        console.print("  1. 先に子ノードを削除してから、親を削除する")
        console.print("  2. Task/SubTaskの場合: --bridge オプションで橋渡し削除を使用する")
        sys.exit(1)
    except PMToolError as e:
        console.print(f"[red]ERROR: エラー: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]ERROR: 予期しないエラー: {e}[/red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
