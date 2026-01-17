"""
TUI コマンドハンドラ

各サブコマンドの処理ロジックを提供します。
"""

from argparse import Namespace

from rich.console import Console

from ..database import Database
from ..dependencies import DependencyManager
from ..doctor import Doctor
from ..repository import (
    ProjectRepository,
    SubProjectRepository,
    SubTaskRepository,
    TaskRepository,
)
from ..status import StatusManager
from . import display
from . import input as tui_input

console = Console()


# ===== list コマンド =====


def handle_list(db: Database, args: Namespace) -> None:
    """
    listコマンドの処理（Project一覧表示）

    Args:
        db: Database インスタンス
        args: コマンドライン引数
    """
    entity_type = args.entity

    if entity_type == "projects":
        repo = ProjectRepository(db)
        projects = repo.get_all()
        display.show_project_list(projects)


# ===== show コマンド =====


def handle_show(db: Database, args: Namespace) -> None:
    """
    showコマンドの処理（ツリー表示）

    Args:
        db: Database インスタンス
        args: コマンドライン引数
    """
    entity_type = args.entity
    entity_id = args.id

    if entity_type == "project":
        display.show_project_tree(db, entity_id)


# ===== add コマンド =====


def handle_add(db: Database, args: Namespace) -> None:
    """
    addコマンドの処理

    エンティティ種別に応じて、Project/SubProject/Task/SubTaskを追加する。
    未指定の必須項目は対話的入力で取得する。

    Args:
        db: Database インスタンス
        args: コマンドライン引数
    """
    entity_type = args.entity

    if entity_type == "project":
        _add_project(db, args)
    elif entity_type == "subproject":
        _add_subproject(db, args)
    elif entity_type == "task":
        _add_task(db, args)
    elif entity_type == "subtask":
        _add_subtask(db, args)


def _add_project(db: Database, args: Namespace) -> None:
    """Project追加処理"""
    # 名前取得（未指定なら対話入力）
    name = args.name or tui_input.prompt_text("プロジェクト名", required=True)
    description = args.desc or tui_input.prompt_text("説明（オプション）", required=False)

    # リポジトリ呼び出し
    repo = ProjectRepository(db)
    project = repo.create(name=name, description=description)

    # 結果表示
    console.print(
        f"[green]✓[/green] Project作成成功: ID={project.id}, 名前={project.name}"
    )


def _add_subproject(db: Database, args: Namespace) -> None:
    """SubProject追加処理"""
    # 親プロジェクトID取得
    project_id = args.project
    if project_id is None:
        project_id = tui_input.prompt_int("親プロジェクトID", required=True)

    # 名前取得
    name = args.name or tui_input.prompt_text("サブプロジェクト名", required=True)
    description = args.desc or tui_input.prompt_text("説明（オプション）", required=False)

    # リポジトリ呼び出し
    repo = SubProjectRepository(db)
    subproject = repo.create(project_id=project_id, name=name, description=description)

    console.print(
        f"[green]✓[/green] SubProject作成成功: ID={subproject.id}, 名前={subproject.name}"
    )


def _add_task(db: Database, args: Namespace) -> None:
    """Task追加処理"""
    # 親プロジェクト・サブプロジェクトID取得
    project_id = args.project
    if project_id is None:
        project_id = tui_input.prompt_int("親プロジェクトID", required=True)

    subproject_id = args.subproject  # オプション（プロジェクト直下の場合はNone）

    # 名前取得
    name = args.name or tui_input.prompt_text("タスク名", required=True)
    description = args.desc or tui_input.prompt_text("説明（オプション）", required=False)

    # リポジトリ呼び出し
    repo = TaskRepository(db)
    task = repo.create(
        project_id=project_id,
        subproject_id=subproject_id,
        name=name,
        description=description,
    )

    console.print(
        f"[green]✓[/green] Task作成成功: ID={task.id}, 名前={task.name}, ステータス={task.status}"
    )


def _add_subtask(db: Database, args: Namespace) -> None:
    """SubTask追加処理"""
    # 親タスクID取得
    task_id = args.task
    if task_id is None:
        task_id = tui_input.prompt_int("親タスクID", required=True)

    # 名前取得
    name = args.name or tui_input.prompt_text("サブタスク名", required=True)
    description = args.desc or tui_input.prompt_text("説明（オプション）", required=False)

    # リポジトリ呼び出し
    repo = SubTaskRepository(db)
    subtask = repo.create(task_id=task_id, name=name, description=description)

    console.print(
        f"[green]✓[/green] SubTask作成成功: ID={subtask.id}, 名前={subtask.name}, ステータス={subtask.status}"
    )


# ===== delete コマンド =====


def handle_delete(db: Database, args: Namespace) -> None:
    """
    deleteコマンドの処理

    標準削除または橋渡し削除を実行する。
    削除前に確認プロンプトを表示する。

    Args:
        db: Database インスタンス
        args: コマンドライン引数
    """
    entity_type = args.entity
    entity_id = args.id
    use_bridge = args.bridge

    # --bridgeの適用範囲チェック（レビュー指摘A-1対応）
    if use_bridge and entity_type in ("project", "subproject"):
        console.print(
            f"[red]エラー: --bridge オプションは task/subtask でのみ使用できます。[/red]\n"
            f"project/subproject には依存関係がないため、橋渡し削除は適用されません。"
        )
        return

    # 確認プロンプト（レビュー指摘A-2対応）
    if use_bridge:
        msg = (
            f"{entity_type} ID={entity_id} を橋渡し削除しますか？\n"
            f"  - 先行ノードと後続ノードを再接続します\n"
            f"  - 循環が発生する場合は失敗します"
        )
    else:
        msg = f"{entity_type} ID={entity_id} を削除しますか？（子がいる場合はエラー）"

    if not tui_input.confirm(msg):
        console.print("[yellow]キャンセルしました。[/yellow]")
        return

    # エンティティ種別に応じて削除処理
    if entity_type == "project":
        _delete_project(db, entity_id)
    elif entity_type == "subproject":
        _delete_subproject(db, entity_id)
    elif entity_type == "task":
        _delete_task(db, entity_id, use_bridge)
    elif entity_type == "subtask":
        _delete_subtask(db, entity_id, use_bridge)


def _delete_project(db: Database, project_id: int) -> None:
    """Project削除処理"""
    repo = ProjectRepository(db)
    repo.delete(project_id)
    console.print(f"[green]✓[/green] Project ID={project_id} を削除しました。")


def _delete_subproject(db: Database, subproject_id: int) -> None:
    """SubProject削除処理"""
    repo = SubProjectRepository(db)
    repo.delete(subproject_id)
    console.print(f"[green]✓[/green] SubProject ID={subproject_id} を削除しました。")


def _delete_task(db: Database, task_id: int, use_bridge: bool) -> None:
    """Task削除処理"""
    if use_bridge:
        # 橋渡し削除
        dep_manager = DependencyManager(db)
        dep_manager.delete_task_with_bridge(task_id)
        console.print(
            f"[green]✓[/green] Task ID={task_id} を橋渡し削除しました。\n"
            f"依存関係が再接続されました。deps list で確認できます。"
        )  # レビュー指摘B-8対応
    else:
        # 標準削除
        repo = TaskRepository(db)
        repo.delete(task_id)
        console.print(f"[green]✓[/green] Task ID={task_id} を削除しました。")


def _delete_subtask(db: Database, subtask_id: int, use_bridge: bool) -> None:
    """SubTask削除処理"""
    if use_bridge:
        # 橋渡し削除
        dep_manager = DependencyManager(db)
        dep_manager.delete_subtask_with_bridge(subtask_id)
        console.print(
            f"[green]✓[/green] SubTask ID={subtask_id} を橋渡し削除しました。\n"
            f"依存関係が再接続されました。deps list で確認できます。"
        )  # レビュー指摘B-8対応
    else:
        # 標準削除
        repo = SubTaskRepository(db)
        repo.delete(subtask_id)
        console.print(f"[green]✓[/green] SubTask ID={subtask_id} を削除しました。")


# ===== status コマンド =====


def handle_status(db: Database, args: Namespace) -> None:
    """
    statusコマンドの処理

    Task/SubTaskのステータスを変更する。
    DONE遷移条件チェックはStatusManagerに委譲する。

    Args:
        db: Database インスタンス
        args: コマンドライン引数
    """
    entity_type = args.entity
    entity_id = args.id
    new_status = args.status

    # StatusManager初期化
    dep_manager = DependencyManager(db)
    status_manager = StatusManager(db, dep_manager)

    # ステータス更新
    if entity_type == "task":
        updated = status_manager.update_task_status(entity_id, new_status)
        console.print(
            f"[green]✓[/green] Task ID={entity_id} のステータスを {updated.status} に変更しました。"
        )
    elif entity_type == "subtask":
        updated = status_manager.update_subtask_status(entity_id, new_status)
        console.print(
            f"[green]✓[/green] SubTask ID={entity_id} のステータスを {updated.status} に変更しました。"
        )


# ===== deps コマンド =====


def handle_deps(db: Database, args: Namespace) -> None:
    """
    depsコマンドの処理

    deps add/remove/list のサブコマンドに応じて依存関係を操作する。

    Args:
        db: Database インスタンス
        args: コマンドライン引数
    """
    deps_command = args.deps_command
    entity_type = args.entity

    dep_manager = DependencyManager(db)

    if deps_command == "add":
        _deps_add(dep_manager, entity_type, args.from_id, args.to_id)
    elif deps_command == "remove":
        _deps_remove(dep_manager, entity_type, args.from_id, args.to_id)
    elif deps_command == "list":
        _deps_list(dep_manager, entity_type, args.id)


def _deps_add(
    dep_manager: DependencyManager, entity_type: str, from_id: int, to_id: int
) -> None:
    """依存関係追加"""
    if entity_type == "task":
        dep_manager.add_task_dependency(from_id, to_id)
        console.print(f"[green]✓[/green] Task依存関係追加: {from_id} → {to_id}")
    elif entity_type == "subtask":
        dep_manager.add_subtask_dependency(from_id, to_id)
        console.print(f"[green]✓[/green] SubTask依存関係追加: {from_id} → {to_id}")


def _deps_remove(
    dep_manager: DependencyManager, entity_type: str, from_id: int, to_id: int
) -> None:
    """依存関係削除"""
    if entity_type == "task":
        dep_manager.remove_task_dependency(from_id, to_id)
        console.print(f"[green]✓[/green] Task依存関係削除: {from_id} → {to_id}")
    elif entity_type == "subtask":
        dep_manager.remove_subtask_dependency(from_id, to_id)
        console.print(f"[green]✓[/green] SubTask依存関係削除: {from_id} → {to_id}")


def _deps_list(dep_manager: DependencyManager, entity_type: str, entity_id: int) -> None:
    """依存関係一覧表示"""
    from ..database import Database

    db = dep_manager.db

    if entity_type == "task":
        # 依存関係ID取得
        deps = dep_manager.get_task_dependencies(entity_id)

        # TaskオブジェクトをID から取得
        task_repo = TaskRepository(db)
        predecessors = [task_repo.get_by_id(tid) for tid in deps["predecessors"]]
        successors = [task_repo.get_by_id(tid) for tid in deps["successors"]]

        # None除外
        predecessors = [t for t in predecessors if t is not None]
        successors = [t for t in successors if t is not None]

        display.show_dependencies("Task", entity_id, predecessors, successors)

    elif entity_type == "subtask":
        # 依存関係ID取得
        deps = dep_manager.get_subtask_dependencies(entity_id)

        # SubTaskオブジェクトをID から取得
        subtask_repo = SubTaskRepository(db)
        predecessors = [subtask_repo.get_by_id(stid) for stid in deps["predecessors"]]
        successors = [subtask_repo.get_by_id(stid) for stid in deps["successors"]]

        # None除外
        predecessors = [st for st in predecessors if st is not None]
        successors = [st for st in successors if st is not None]

        display.show_dependencies("SubTask", entity_id, predecessors, successors)


# ===== doctor/check コマンド =====


def handle_doctor(db: Database, args: Namespace) -> None:
    """
    doctor/checkコマンドの処理（データ整合性チェック）

    Args:
        db: Database インスタンス
        args: コマンドライン引数
    """
    doctor = Doctor(db)

    console.print("[bold cyan]データベース整合性チェック実行中...[/bold cyan]\n")

    # チェック実行
    report = doctor.check_all()

    # レポート表示
    display.show_doctor_report(report)

    # 結果サマリー
    if report.is_healthy:
        console.print("\n[bold green]OK: データベースは正常です[/bold green]")
    else:
        console.print(
            f"\n[bold red]NG: {report.error_count}件のエラーが検出されました[/bold red]"
        )
