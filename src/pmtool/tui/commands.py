"""
TUI コマンドハンドラ

各サブコマンドの処理ロジックを提供します。
"""

from argparse import Namespace
from typing import Optional

from rich.console import Console

from ..database import Database
from ..dependencies import DependencyManager
from ..doctor import Doctor
from ..exceptions import DeletionError
from ..repository import (
    ProjectRepository,
    SubProjectRepository,
    SubTaskRepository,
    TaskRepository,
    _now,
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

    標準削除、橋渡し削除、またはカスケード削除を実行する。
    --dry-run が指定された場合は影響範囲のみを表示する。

    Args:
        db: Database インスタンス
        args: コマンドライン引数
    """
    entity_type = args.entity
    entity_id = args.id
    use_bridge = getattr(args, "bridge", False)
    use_cascade = getattr(args, "cascade", False)
    force = getattr(args, "force", False)
    dry_run = getattr(args, "dry_run", False)

    # --bridge と --cascade の排他チェック
    if use_bridge and use_cascade:
        console.print(
            "[red]エラー: --bridge と --cascade は同時に指定できません。[/red]"
        )
        return

    # --bridgeの適用範囲チェック（レビュー指摘A-1対応）
    if use_bridge and entity_type in ("project", "subproject"):
        console.print(
            f"[red]エラー: --bridge オプションは task/subtask でのみ使用できます。[/red]\n"
            f"project/subproject には依存関係がないため、橋渡し削除は適用されません。"
        )
        return

    # --cascade 使用時の --force チェック
    if use_cascade and not force and not dry_run:
        console.print(
            "[red]エラー: --cascade を使用する場合は --force が必要です。[/red]\n"
            "[dim]ヒント: --dry-run で影響範囲を確認してから --force を指定してください。[/dim]"
        )
        return

    # dry-run の場合は影響範囲を表示して終了
    if dry_run:
        _show_delete_impact(db, entity_type, entity_id, use_bridge, use_cascade)
        return

    # 確認プロンプト（レビュー指摘A-2対応）
    if use_cascade:
        msg = (
            f"{entity_type} ID={entity_id} をカスケード削除しますか？\n"
            f"  - すべての子エンティティも削除されます\n"
            f"  - 依存関係も削除されます\n"
            f"  [bold red]※ この操作は取り消せません[/bold red]"
        )
    elif use_bridge:
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
    if use_cascade:
        _delete_cascade(db, entity_type, entity_id)
    elif entity_type == "project":
        _delete_project(db, entity_id)
    elif entity_type == "subproject":
        _delete_subproject(db, entity_id)
    elif entity_type == "task":
        _delete_task(db, entity_id, use_bridge)
    elif entity_type == "subtask":
        _delete_subtask(db, entity_id, use_bridge)


def _show_delete_impact(
    db: Database, entity_type: str, entity_id: int, use_bridge: bool, use_cascade: bool = False
) -> None:
    """
    削除影響範囲を表示する（dry-run）

    トランザクション内で削除処理を実行し、影響範囲を収集してから rollback する。

    Args:
        db: Database インスタンス
        entity_type: 削除対象のエンティティ種別
        entity_id: 削除対象のエンティティID
        use_bridge: 橋渡し削除かどうか
        use_cascade: カスケード削除かどうか
    """
    console.print(
        f"\n[bold cyan]=== Dry-run: Delete {entity_type.title()} {entity_id} ===[/bold cyan]\n"
    )

    # トランザクション開始
    conn = db.connect()
    cursor = conn.cursor()

    try:
        # 削除前の件数を取得
        before_counts = _count_entities(cursor)
        before_deps = _count_dependencies(cursor)

        # 削除処理を実行（トランザクション内）
        try:
            if use_cascade:
                _delete_cascade_in_transaction(db, entity_type, entity_id, conn)
            elif entity_type == "project":
                _delete_project_in_transaction(db, entity_id, conn)
            elif entity_type == "subproject":
                _delete_subproject_in_transaction(db, entity_id, conn)
            elif entity_type == "task":
                _delete_task_in_transaction(db, entity_id, use_bridge, conn)
            elif entity_type == "subtask":
                _delete_subtask_in_transaction(db, entity_id, use_bridge, conn)

            # 削除後の件数を取得
            after_counts = _count_entities(cursor)
            after_deps = _count_dependencies(cursor)

            # 差分を計算して表示
            console.print("[bold]削除対象:[/bold]")
            for entity, before in before_counts.items():
                after = after_counts[entity]
                diff = before - after
                if diff > 0:
                    console.print(f"  {entity}: {diff}件")

            if any(before_counts[k] - after_counts[k] > 0 for k in before_counts):
                console.print("\n[bold]削除される依存関係:[/bold]")
                task_dep_diff = before_deps["task"] - after_deps["task"]
                subtask_dep_diff = before_deps["subtask"] - after_deps["subtask"]
                if task_dep_diff > 0:
                    console.print(f"  Task依存: {task_dep_diff}件")
                if subtask_dep_diff > 0:
                    console.print(f"  SubTask依存: {subtask_dep_diff}件")

            console.print(
                "\n[yellow]※ これは dry-run です。実際には削除されません。[/yellow]"
            )
            console.print("[dim]実行する場合は --dry-run を外してください。[/dim]")

        except DeletionError as e:
            # 子が存在する場合など、削除が失敗する場合でもプレビュー可能にする
            console.print(f"\n[yellow]⚠️  この削除は失敗します: {e}[/yellow]")

            # 子の件数を取得して表示
            from ..exceptions import DeletionFailureReason
            if e.reason == DeletionFailureReason.CHILD_EXISTS:
                _show_child_count(cursor, entity_type, entity_id)

            console.print("\n[dim]ヒント: 子エンティティを先に削除するか、--bridge オプションを使用してください[/dim]")

    finally:
        # 必ず rollback（dry-run なので変更を破棄）
        conn.rollback()
        # 注: Database.connect() はシングルトン接続を返すため、ここで close() しない
        # close() すると他の処理で "Cannot operate on a closed database" エラーになる


def _show_child_count(cursor, entity_type: str, entity_id: int) -> None:
    """
    子エンティティの件数を表示する（DeletionError時のプレビュー用）

    Args:
        cursor: カーソル
        entity_type: エンティティ種別
        entity_id: エンティティID
    """
    console.print("\n[bold]子エンティティ:[/bold]")

    if entity_type == "project":
        cursor.execute("SELECT COUNT(*) FROM subprojects WHERE project_id = ?", (entity_id,))
        subproject_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE project_id = ?", (entity_id,))
        task_count = cursor.fetchone()[0]
        if subproject_count > 0:
            console.print(f"  SubProject: {subproject_count}件")
        if task_count > 0:
            console.print(f"  Task: {task_count}件")

    elif entity_type == "subproject":
        cursor.execute("SELECT COUNT(*) FROM subprojects WHERE parent_subproject_id = ?", (entity_id,))
        child_subproject_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE subproject_id = ?", (entity_id,))
        task_count = cursor.fetchone()[0]
        if child_subproject_count > 0:
            console.print(f"  SubProject（子）: {child_subproject_count}件")
        if task_count > 0:
            console.print(f"  Task: {task_count}件")

    elif entity_type == "task":
        cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id = ?", (entity_id,))
        subtask_count = cursor.fetchone()[0]
        if subtask_count > 0:
            console.print(f"  SubTask: {subtask_count}件")


def _count_entities(cursor) -> dict:
    """現在のエンティティ件数を取得"""
    counts = {}
    cursor.execute("SELECT COUNT(*) FROM projects")
    counts["Project"] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM subprojects")
    counts["SubProject"] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks")
    counts["Task"] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM subtasks")
    counts["SubTask"] = cursor.fetchone()[0]
    return counts


def _count_dependencies(cursor) -> dict:
    """現在の依存関係件数を取得"""
    counts = {}
    cursor.execute("SELECT COUNT(*) FROM task_dependencies")
    counts["task"] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM subtask_dependencies")
    counts["subtask"] = cursor.fetchone()[0]
    return counts


def _delete_project_in_transaction(
    db: Database, project_id: int, conn
) -> None:
    """
    Project削除処理（トランザクション内）

    Repository.delete() は conn パラメータを受け取らないため、
    直接 repository の内部メソッドを呼び出して削除を実行する。
    子チェックは repository 内で実行されるため、DeletionError が発生する可能性がある。
    """
    repo = ProjectRepository(db)
    # 子チェック（子が存在すると DeletionError）
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM subprojects WHERE project_id = ?", (project_id,))
    subproject_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE project_id = ?", (project_id,))
    task_count = cursor.fetchone()[0]

    from ..exceptions import DeletionFailureReason
    if subproject_count > 0 or task_count > 0:
        raise DeletionError(
            f"Cannot delete project {project_id}: child entities exist (SubProject: {subproject_count}, Task: {task_count})",
            reason=DeletionFailureReason.CHILD_EXISTS
        )

    # 実際の削除（トランザクション内）
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))


def _delete_subproject_in_transaction(
    db: Database, subproject_id: int, conn
) -> None:
    """SubProject削除処理（トランザクション内）"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM subprojects WHERE parent_subproject_id = ?", (subproject_id,))
    child_subproject_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE subproject_id = ?", (subproject_id,))
    task_count = cursor.fetchone()[0]

    from ..exceptions import DeletionFailureReason
    if child_subproject_count > 0 or task_count > 0:
        raise DeletionError(
            f"Cannot delete subproject {subproject_id}: child entities exist (SubProject: {child_subproject_count}, Task: {task_count})",
            reason=DeletionFailureReason.CHILD_EXISTS
        )

    cursor.execute("DELETE FROM subprojects WHERE id = ?", (subproject_id,))


def _delete_task_in_transaction(
    db: Database, task_id: int, use_bridge: bool, conn
) -> None:
    """Task削除処理（トランザクション内）"""
    cursor = conn.cursor()

    if use_bridge:
        # 橋渡し削除: DependencyManager を使用
        dep_manager = DependencyManager(db)
        dep_manager.delete_task_with_bridge(task_id, conn=conn)
    else:
        # 通常削除: 子チェック
        cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id = ?", (task_id,))
        subtask_count = cursor.fetchone()[0]

        from ..exceptions import DeletionFailureReason
        if subtask_count > 0:
            raise DeletionError(
                f"Cannot delete task {task_id}: child entities exist (SubTask: {subtask_count})",
                reason=DeletionFailureReason.CHILD_EXISTS
            )

        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def _delete_subtask_in_transaction(
    db: Database, subtask_id: int, use_bridge: bool, conn
) -> None:
    """SubTask削除処理（トランザクション内）"""
    cursor = conn.cursor()

    if use_bridge:
        # 橋渡し削除: DependencyManager を使用
        dep_manager = DependencyManager(db)
        dep_manager.delete_subtask_with_bridge(subtask_id, conn=conn)
    else:
        # 通常削除: SubTaskには子がないので直接削除
        cursor.execute("DELETE FROM subtasks WHERE id = ?", (subtask_id,))


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


def _delete_cascade(db: Database, entity_type: str, entity_id: int) -> None:
    """
    カスケード削除処理（サブツリー一括削除）

    Args:
        db: Database インスタンス
        entity_type: 削除対象のエンティティ種別
        entity_id: 削除対象のエンティティID
    """
    conn = db.connect()
    cursor = conn.cursor()

    try:
        # トランザクション開始
        conn.execute("BEGIN")

        # エンティティ種別に応じてカスケード削除
        _delete_cascade_in_transaction(db, entity_type, entity_id, conn)

        # コミット
        conn.commit()
        console.print(
            f"[green]✓[/green] {entity_type.title()} ID={entity_id} をカスケード削除しました。"
        )

    except Exception as e:
        conn.rollback()
        console.print(f"[red]ERROR: カスケード削除に失敗しました: {e}[/red]")
        raise


def _delete_cascade_in_transaction(
    db: Database, entity_type: str, entity_id: int, conn
) -> None:
    """
    カスケード削除のトランザクション内処理

    Args:
        db: Database インスタンス
        entity_type: 削除対象のエンティティ種別
        entity_id: 削除対象のエンティティID
        conn: データベース接続
    """
    cursor = conn.cursor()

    if entity_type == "project":
        # Project配下の全エンティティを削除
        # 1. SubTask削除（Task→SubTaskの順）
        cursor.execute("""
            DELETE FROM subtasks
            WHERE task_id IN (SELECT id FROM tasks WHERE project_id = ?)
        """, (entity_id,))

        # 2. Task削除
        cursor.execute("DELETE FROM tasks WHERE project_id = ?", (entity_id,))

        # 3. SubProject削除
        cursor.execute("DELETE FROM subprojects WHERE project_id = ?", (entity_id,))

        # 4. Project削除
        cursor.execute("DELETE FROM projects WHERE id = ?", (entity_id,))

    elif entity_type == "subproject":
        # SubProject配下の全エンティティを削除
        # 1. SubTask削除
        cursor.execute("""
            DELETE FROM subtasks
            WHERE task_id IN (SELECT id FROM tasks WHERE subproject_id = ?)
        """, (entity_id,))

        # 2. Task削除
        cursor.execute("DELETE FROM tasks WHERE subproject_id = ?", (entity_id,))

        # 3. 子SubProject削除（再帰的に）
        cursor.execute("SELECT id FROM subprojects WHERE parent_subproject_id = ?", (entity_id,))
        child_subprojects = cursor.fetchall()
        for child_sp in child_subprojects:
            _delete_cascade_in_transaction(db, "subproject", child_sp[0], conn)

        # 4. SubProject自身を削除
        cursor.execute("DELETE FROM subprojects WHERE id = ?", (entity_id,))

    elif entity_type == "task":
        # Task配下の全SubTaskを削除
        cursor.execute("DELETE FROM subtasks WHERE task_id = ?", (entity_id,))

        # Task自身を削除
        cursor.execute("DELETE FROM tasks WHERE id = ?", (entity_id,))

    elif entity_type == "subtask":
        # SubTaskには子がないので直接削除
        cursor.execute("DELETE FROM subtasks WHERE id = ?", (entity_id,))


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


# ===== update コマンド =====


def handle_update(db: Database, args: Namespace) -> None:
    """
    updateコマンドの処理

    name / description / order_index を更新する。
    少なくとも1つのオプションが必要。

    Args:
        db: Database インスタンス
        args: コマンドライン引数
    """
    entity_type = args.entity
    entity_id = args.id
    name = getattr(args, "name", None)
    description = getattr(args, "description", None)
    order = getattr(args, "order", None)

    # 少なくとも1つのオプションが必要
    if name is None and description is None and order is None:
        console.print(
            "[red]エラー: 少なくとも1つの更新オプション（--name, --description, --order）が必要です[/red]"
        )
        return

    # エンティティ種別に応じて更新処理
    if entity_type == "project":
        _update_project(db, entity_id, name, description, order)
    elif entity_type == "subproject":
        _update_subproject(db, entity_id, name, description, order)
    elif entity_type == "task":
        _update_task(db, entity_id, name, description, order)
    elif entity_type == "subtask":
        _update_subtask(db, entity_id, name, description, order)


def _update_project(
    db: Database, project_id: int, name: Optional[str], description: Optional[str], order: Optional[int]
) -> None:
    """Project更新処理"""
    repo = ProjectRepository(db)

    # name/description更新
    if name is not None or description is not None:
        updated = repo.update(project_id, name=name, description=description)
        console.print(f"[green]✓[/green] Project ID={project_id} を更新しました。")

    # order_index更新（Projectにはorder_indexの論理的な意味がないため警告）
    if order is not None:
        console.print(
            f"[yellow]警告: Project に order_index はありません。--order オプションは無視されます。[/yellow]"
        )


def _update_subproject(
    db: Database, subproject_id: int, name: Optional[str], description: Optional[str], order: Optional[int]
) -> None:
    """SubProject更新処理"""
    repo = SubProjectRepository(db)

    # name/description更新
    if name is not None or description is not None:
        updated = repo.update(subproject_id, name=name, description=description)
        console.print(f"[green]✓[/green] SubProject ID={subproject_id} を更新しました。")

    # order_index更新
    if order is not None:
        _update_order_index(db, "subproject", subproject_id, order)


def _update_task(
    db: Database, task_id: int, name: Optional[str], description: Optional[str], order: Optional[int]
) -> None:
    """Task更新処理"""
    repo = TaskRepository(db)

    # name/description更新
    if name is not None or description is not None:
        updated = repo.update(task_id, name=name, description=description)
        console.print(f"[green]✓[/green] Task ID={task_id} を更新しました。")

    # order_index更新
    if order is not None:
        _update_order_index(db, "task", task_id, order)


def _update_subtask(
    db: Database, subtask_id: int, name: Optional[str], description: Optional[str], order: Optional[int]
) -> None:
    """SubTask更新処理"""
    repo = SubTaskRepository(db)

    # name/description更新
    if name is not None or description is not None:
        updated = repo.update(subtask_id, name=name, description=description)
        console.print(f"[green]✓[/green] SubTask ID={subtask_id} を更新しました。")

    # order_index更新
    if order is not None:
        _update_order_index(db, "subtask", subtask_id, order)


def _update_order_index(db: Database, entity_type: str, entity_id: int, new_order: int) -> None:
    """
    order_index を更新する

    Args:
        db: Database インスタンス
        entity_type: エンティティ種別 ("subproject" | "task" | "subtask")
        entity_id: エンティティID
        new_order: 新しいorder_index
    """
    conn = db.connect()
    cursor = conn.cursor()

    try:
        # テーブル名を決定
        table_name = {
            "subproject": "subprojects",
            "task": "tasks",
            "subtask": "subtasks",
        }[entity_type]

        # 存在確認
        cursor.execute(f"SELECT order_index FROM {table_name} WHERE id = ?", (entity_id,))
        row = cursor.fetchone()
        if not row:
            console.print(f"[red]エラー: {entity_type} ID={entity_id} は存在しません[/red]")
            return

        current_order = row[0]

        # 既に同じ値の場合はスキップ
        if current_order == new_order:
            console.print(f"[yellow]order_index は既に {new_order} です（変更なし）[/yellow]")
            return

        # 負の値チェック
        if new_order < 0:
            console.print(f"[red]エラー: order_index は 0 以上である必要があります[/red]")
            return

        # order_index 更新
        now = _now()
        cursor.execute(
            f"UPDATE {table_name} SET order_index = ?, updated_at = ? WHERE id = ?",
            (new_order, now, entity_id),
        )
        conn.commit()
        console.print(f"[green]✓[/green] {entity_type.title()} ID={entity_id} の order_index を {new_order} に更新しました。")

    except Exception as e:
        conn.rollback()
        console.print(f"[red]ERROR: order_index 更新に失敗しました: {e}[/red]")
        raise


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
