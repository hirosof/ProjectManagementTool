"""
TUI 表示ロジック

Rich を使った階層ツリー表示、テーブル表示、依存関係表示を提供します。
"""

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from ..database import Database
from ..doctor import DoctorReport, IssueLevel
from ..models import Project
from ..repository import (
    ProjectRepository,
    SubProjectRepository,
    SubTaskRepository,
    TaskRepository,
)
from . import formatters

console = Console()


def show_project_list(projects: list[Project]) -> None:
    """
    Project一覧をRich Tableで表示

    Args:
        projects: Projectのリスト
    """
    if not projects:
        console.print("[yellow]プロジェクトが見つかりません。[/yellow]")
        return

    table = Table(
        title="プロジェクト一覧", show_header=True, header_style="bold magenta"
    )
    table.add_column("ID", style="cyan", width=6)
    table.add_column("名前", style="white")
    table.add_column("説明", style="dim")
    table.add_column("表示順序", justify="right", width=10)
    table.add_column("作成日時", style="dim", width=20)

    for proj in projects:
        table.add_row(
            str(proj.id),
            proj.name,
            proj.description or "",
            str(proj.order_index),
            proj.created_at[:19],  # "YYYY-MM-DDTHH:MM:SS"
        )

    console.print(table)


def show_project_tree(db: Database, project_id: int, use_emoji: bool = True) -> None:
    """
    指定したProjectの階層ツリーをRich Treeで表示

    Args:
        db: Database インスタンス
        project_id: 表示対象のProject ID
        use_emoji: 絵文字を使用するかどうか（デフォルト: True）
    """
    # リポジトリ初期化
    proj_repo = ProjectRepository(db)
    subproj_repo = SubProjectRepository(db)
    task_repo = TaskRepository(db)
    subtask_repo = SubTaskRepository(db)

    # Project取得
    project = proj_repo.get_by_id(project_id)
    if not project:
        console.print(
            f"[red]エラー: Project ID={project_id} が見つかりません。[/red]"
        )
        return

    # 記号取得
    project_symbol = formatters.get_entity_symbol("project", use_emoji)
    subproject_symbol = formatters.get_entity_symbol("subproject", use_emoji)
    task_symbol = formatters.get_entity_symbol("task", use_emoji)
    subtask_symbol = formatters.get_entity_symbol("subtask", use_emoji)

    # Treeルート作成
    tree = Tree(
        f"{project_symbol} [bold]{project.name}[/bold] (ID={project.id})", guide_style="dim"
    )

    # SubProject取得・追加
    subprojects = subproj_repo.get_by_project(project_id)
    for subproj in subprojects:
        subproj_node = tree.add(f"{subproject_symbol} {subproj.name} (ID={subproj.id})")

        # Task取得・追加
        tasks = task_repo.get_by_parent(project_id=project_id, subproject_id=subproj.id)
        for task in tasks:
            status_display = formatters.format_status(task.status, use_emoji)
            task_node = subproj_node.add(
                f"{task_symbol} {task.name} (ID={task.id}) {status_display}"
            )

            # SubTask取得・追加
            subtasks = subtask_repo.get_by_task(task.id)
            for subtask in subtasks:
                subtask_status = formatters.format_status(subtask.status, use_emoji)
                task_node.add(
                    f"{subtask_symbol}  {subtask.name} (ID={subtask.id}) {subtask_status}"
                )

    # プロジェクト直下のTask（subproject_id=None）も追加（レビュー指摘B-9対応）
    direct_tasks = task_repo.get_by_parent(project_id=project_id, subproject_id=None)
    if direct_tasks:
        # 区画ノードを作成
        direct_tasks_node = tree.add(f"{task_symbol} [dim]Tasks (direct)[/dim]")
        for task in direct_tasks:
            status_display = formatters.format_status(task.status, use_emoji)
            task_node = direct_tasks_node.add(
                f"{task_symbol} {task.name} (ID={task.id}) {status_display}"
            )

            subtasks = subtask_repo.get_by_task(task.id)
            for subtask in subtasks:
                subtask_status = formatters.format_status(subtask.status, use_emoji)
                task_node.add(
                    f"{subtask_symbol}  {subtask.name} (ID={subtask.id}) {subtask_status}"
                )

    console.print(tree)


def show_dependencies(
    entity_type: str, entity_id: int, predecessors: list, successors: list, use_emoji: bool = True
) -> None:
    """
    依存関係をシンプルなリスト表示

    Args:
        entity_type: "Task" or "SubTask"
        entity_id: 対象エンティティID
        predecessors: 先行ノードのリスト（TaskまたはSubTask）
        successors: 後続ノードのリスト
        use_emoji: 絵文字を使用するかどうか（デフォルト: True）

    レビュー指摘B-7対応: 親文脈（project_id, subproject_id, task_id）を併記
    """
    console.print(f"\n[bold]{entity_type} ID={entity_id} の依存関係:[/bold]")

    # 先行ノード
    if predecessors:
        console.print("\n  [cyan]先行ノード（predecessor）:[/cyan]")
        for pred in predecessors:
            status_display = formatters.format_status(pred.status, use_emoji)
            # 親文脈の表示
            if entity_type == "Task":
                context = f"Project={pred.project_id}"
                if pred.subproject_id:
                    context += f", SubProject={pred.subproject_id}"
                console.print(
                    f"    - {entity_type} ID={pred.id}: {pred.name} {status_display} [{context}]"
                )
            elif entity_type == "SubTask":
                console.print(
                    f"    - {entity_type} ID={pred.id}: {pred.name} {status_display} [Task={pred.task_id}]"
                )
    else:
        console.print("\n  [dim]先行ノードなし[/dim]")

    # 後続ノード
    if successors:
        console.print("\n  [cyan]後続ノード（successor）:[/cyan]")
        for succ in successors:
            status_display = formatters.format_status(succ.status, use_emoji)
            # 親文脈の表示
            if entity_type == "Task":
                context = f"Project={succ.project_id}"
                if succ.subproject_id:
                    context += f", SubProject={succ.subproject_id}"
                console.print(
                    f"    - {entity_type} ID={succ.id}: {succ.name} {status_display} [{context}]"
                )
            elif entity_type == "SubTask":
                console.print(
                    f"    - {entity_type} ID={succ.id}: {succ.name} {status_display} [Task={succ.task_id}]"
                )
    else:
        console.print("\n  [dim]後続ノードなし[/dim]")

    console.print()


def show_doctor_report(report: DoctorReport) -> None:
    """
    doctor/checkレポートを表示

    Args:
        report: DoctorReport インスタンス
    """
    # サマリー表示
    console.print("[bold]===  Doctor Check Report ===[/bold]\n")
    console.print(f"[bold]Summary:[/bold]")
    console.print(f"  Errors:   [red]{report.error_count}[/red]")
    console.print(f"  Warnings: [yellow]{report.warning_count}[/yellow]")
    console.print()

    # エラー表示
    if report.errors:
        console.print("[bold red]Errors:[/bold red]")
        for issue in report.errors:
            console.print(f"  [red][{issue.code}] {issue.message}[/red]")
        console.print()

    # 警告表示
    if report.warnings:
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for issue in report.warnings:
            console.print(f"  [yellow][{issue.code}] {issue.message}[/yellow]")
        console.print()

    # 正常時のメッセージ
    if report.is_healthy and report.warning_count == 0:
        console.print("[dim]問題は検出されませんでした[/dim]")
