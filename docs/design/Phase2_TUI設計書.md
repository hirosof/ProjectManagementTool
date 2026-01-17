# Phase 2 TUI設計書

**作成日**: 2026-01-17
**位置づけ**: Phase 2実装の詳細設計書（本設計書に基づいて実装を行う）
**前提**: `P2-3_Phase2実装方針_決定事項.md` および `P2-4_ClaudeCode指示文_Phase2_TUI実装.md`

---

## 1. 概要

### 1.1 Phase 2の目標

**TUIインターフェース（コマンド中心）** を実装し、空DBから以下が一通り操作できる状態にする:
- 作成 → 依存追加 → ステータス更新 → 削除（標準/橋渡し） → ツリー確認

### 1.2 技術スタック

- **TUIフレームワーク**: Rich + prompt_toolkit
- **CLIフレームワーク**: argparse（標準ライブラリ）
- **操作モデル**: サブコマンド方式（git風）

### 1.3 実装範囲（MVP）

**Phase 2に含める:**
- Project一覧表示
- 階層ツリー表示（4階層、ステータス付き）
- 操作コマンド: add, delete, status, deps
- エラーハンドリング（ユーザー向けメッセージ）
- ヘルプ導線（`--help`）

**Phase 2に含めない（Phase 3以降）:**
- フィルタリング/検索
- ソート切替
- エクスポート（JSON/Markdown）
- 依存関係の高度可視化（ASCIIアート）
- 常駐シェル/メニューUI
- update系（名前/説明/order_index変更UI）

---

## 2. アーキテクチャ

### 2.1 レイヤー構成

```
┌─────────────────────────────────────┐
│         TUI層 (src/pmtool/tui/)     │
│  - cli.py (エントリーポイント)       │
│  - commands.py (コマンドハンドラ)    │
│  - display.py (表示ロジック)         │
│  - input.py (入力処理)               │
│  - formatters.py (フォーマット)      │
└─────────────────────────────────────┘
              ↓ 呼び出し
┌─────────────────────────────────────┐
│  ビジネスロジック層 (Phase 1既存)    │
│  - repository.py (CRUD)              │
│  - dependencies.py (依存関係管理)    │
│  - status.py (ステータス管理)        │
│  - validators.py (バリデーション)    │
│  - exceptions.py (例外定義)          │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   データアクセス層 (Phase 0/1既存)   │
│  - database.py (DB接続・初期化)      │
│  - models.py (エンティティ定義)      │
└─────────────────────────────────────┘
```

### 2.2 責務分離

**TUI層の責務:**
- コマンドライン引数のパース
- ユーザー入力の取得（対話的入力）
- ビジネスロジック層の呼び出し
- 結果の表示（Rich）
- 例外のキャッチとユーザー向けメッセージへの変換

**ビジネスロジック層の責務（Phase 1既存、変更なし）:**
- CRUD操作
- 依存関係管理・DAG検証
- ステータス遷移条件の検証
- データバリデーション
- トランザクション管理

**データアクセス層の責務（Phase 0/1既存、変更なし）:**
- DB接続管理
- エンティティ定義

---

## 3. ディレクトリ構成

### 3.1 Phase 2で追加するファイル

```
src/pmtool/
  tui/
    __init__.py           # tuiパッケージ初期化
    cli.py                # エントリーポイント（argparse）
    commands.py           # サブコマンドハンドラ
    display.py            # Rich表示ロジック
    input.py              # prompt_toolkit入力処理
    formatters.py         # ステータス記号・色・共通フォーマット
```

### 3.2 既存ファイル（Phase 1、変更なし）

```
src/pmtool/
  database.py             # Phase 0/1
  models.py               # Phase 0/1
  repository.py           # Phase 1
  dependencies.py         # Phase 1
  status.py               # Phase 1
  validators.py           # Phase 0/1
  exceptions.py           # Phase 0/1
```

---

## 4. モジュール設計

### 4.1 cli.py（エントリーポイント）

**責務:**
- argparseによるコマンドライン引数のパース
- サブコマンドのディスパッチ
- DB接続の初期化
- トップレベルの例外ハンドリング

**主な関数:**
```python
def main() -> None:
    """
    CLIのエントリーポイント

    argparseでサブコマンドをパースし、適切なハンドラにディスパッチする
    """

def create_parser() -> argparse.ArgumentParser:
    """
    argparseパーサーを構築

    サブコマンド: list, show, add, delete, status, deps
    """
```

**サブコマンド体系:**
```
pmtool list projects                                      # Project一覧
pmtool show project <project_id>                          # ツリー表示
pmtool add project [--name NAME] [--desc DESC]            # Project追加
pmtool add subproject --project <id> [--name NAME] ...    # SubProject追加
pmtool add task --project <id> [--subproject <id>] ...    # Task追加
pmtool add subtask --task <id> [--name NAME] ...          # SubTask追加
pmtool delete project <id>                                # Project削除（bridgeなし）
pmtool delete subproject <id>                             # SubProject削除（bridgeなし）
pmtool delete task <id> [--bridge]                        # Task削除（橋渡し可）
pmtool delete subtask <id> [--bridge]                     # SubTask削除（橋渡し可）
pmtool status task <id> <status>                          # Taskステータス変更
pmtool status subtask <id> <status>                       # SubTaskステータス変更
pmtool deps add task --from <id> --to <id>                # Task依存関係追加（--from=先行, --to=後続）
pmtool deps add subtask --from <id> --to <id>             # SubTask依存関係追加（--from=先行, --to=後続）
pmtool deps remove task --from <id> --to <id>             # Task依存関係削除
pmtool deps remove subtask --from <id> --to <id>          # SubTask依存関係削除
pmtool deps list task <id>                                # Task依存関係一覧
pmtool deps list subtask <id>                             # SubTask依存関係一覧
```

**重要な設計ポイント:**
- **--bridge オプションはTask/SubTaskのみ**: Project/SubProjectには依存関係がないため、橋渡し削除は適用されません
- **deps の --from/--to**: --from=先行ノード（predecessor）, --to=後続ノード（successor）

**実装例（骨格）:**
```python
import argparse
import sys
from pathlib import Path

from rich.console import Console

from ..database import Database
from ..exceptions import PMToolError
from . import commands

console = Console()

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pmtool",
        description="階層型プロジェクト管理ツール"
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
        help="追加対象"
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
        help="削除対象"
    )
    delete_parser.add_argument("id", type=int, help="エンティティID")
    delete_parser.add_argument(
        "--bridge",
        action="store_true",
        help="依存関係の橋渡し削除（Task/SubTaskのみ有効）"
    )

    # status コマンド
    status_parser = subparsers.add_parser("status", help="ステータス変更")
    status_parser.add_argument(
        "entity",
        choices=["task", "subtask"],
        help="対象エンティティ"
    )
    status_parser.add_argument("id", type=int, help="エンティティID")
    status_parser.add_argument(
        "status",
        choices=["UNSET", "NOT_STARTED", "IN_PROGRESS", "DONE"],
        help="新しいステータス"
    )

    # deps コマンド
    deps_parser = subparsers.add_parser("deps", help="依存関係管理")
    deps_subparsers = deps_parser.add_subparsers(dest="deps_command")

    # deps add
    deps_add = deps_subparsers.add_parser("add", help="依存関係追加")
    deps_add.add_argument("entity", choices=["task", "subtask"])
    deps_add.add_argument("--from", dest="from_id", type=int, required=True,
                          help="先行ノードID（predecessor）")
    deps_add.add_argument("--to", dest="to_id", type=int, required=True,
                          help="後続ノードID（successor）")

    # deps remove
    deps_remove = deps_subparsers.add_parser("remove", help="依存関係削除")
    deps_remove.add_argument("entity", choices=["task", "subtask"])
    deps_remove.add_argument("--from", dest="from_id", type=int, required=True)
    deps_remove.add_argument("--to", dest="to_id", type=int, required=True)

    # deps list
    deps_list = deps_subparsers.add_parser("list", help="依存関係一覧")
    deps_list.add_argument("entity", choices=["task", "subtask"])
    deps_list.add_argument("id", type=int, help="エンティティID")

    return parser

def main() -> None:
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
        elif args.command == "deps":
            commands.handle_deps(db, args)
        else:
            console.print(f"[red]エラー: 未知のコマンド '{args.command}'[/red]")
            sys.exit(1)

    except PMToolError as e:
        # ビジネスロジック層の例外をキャッチ
        console.print(f"[red]エラー: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        # 予期しない例外
        console.print(f"[red]予期しないエラーが発生しました: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

### 4.2 commands.py（コマンドハンドラ）

**責務:**
- 各サブコマンドの処理ロジック
- 引数チェックと対話的入力の呼び出し
- ビジネスロジック層の呼び出し
- 結果の表示（display.pyを使用）
- 確認プロンプトの表示（delete時など）

**主な関数:**
```python
def handle_list(db: Database, args: argparse.Namespace) -> None:
    """listコマンドの処理（Project一覧表示）"""

def handle_show(db: Database, args: argparse.Namespace) -> None:
    """showコマンドの処理（ツリー表示）"""

def handle_add(db: Database, args: argparse.Namespace) -> None:
    """addコマンドの処理（エンティティ追加）"""

def handle_delete(db: Database, args: argparse.Namespace) -> None:
    """deleteコマンドの処理（エンティティ削除）"""

def handle_status(db: Database, args: argparse.Namespace) -> None:
    """statusコマンドの処理（ステータス変更）"""

def handle_deps(db: Database, args: argparse.Namespace) -> None:
    """depsコマンドの処理（依存関係管理）"""
```

**実装例（handle_add）:**
```python
from argparse import Namespace

from rich.console import Console

from ..database import Database
from ..repository import ProjectRepository, SubProjectRepository, TaskRepository, SubTaskRepository
from . import display, input as tui_input

console = Console()

def handle_add(db: Database, args: Namespace) -> None:
    """
    addコマンドの処理

    エンティティ種別に応じて、Project/SubProject/Task/SubTaskを追加する。
    未指定の必須項目は対話的入力で取得する。
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
    console.print(f"[green]✓[/green] Project作成成功: ID={project.id}, 名前={project.name}")

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
    subproject = repo.create(
        project_id=project_id,
        name=name,
        description=description
    )

    console.print(f"[green]✓[/green] SubProject作成成功: ID={subproject.id}, 名前={subproject.name}")

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
        description=description
    )

    console.print(f"[green]✓[/green] Task作成成功: ID={task.id}, 名前={task.name}, ステータス={task.status}")

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
    subtask = repo.create(
        task_id=task_id,
        name=name,
        description=description
    )

    console.print(f"[green]✓[/green] SubTask作成成功: ID={subtask.id}, 名前={subtask.name}, ステータス={subtask.status}")
```

**実装例（handle_delete）:**
```python
def handle_delete(db: Database, args: Namespace) -> None:
    """
    deleteコマンドの処理

    標準削除または橋渡し削除を実行する。
    削除前に確認プロンプトを表示する。
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

def _delete_task(db: Database, task_id: int, use_bridge: bool) -> None:
    """Task削除処理"""
    from ..dependencies import DependencyManager

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
```

**実装例（handle_status）:**
```python
def handle_status(db: Database, args: Namespace) -> None:
    """
    statusコマンドの処理

    Task/SubTaskのステータスを変更する。
    DONE遷移条件チェックはStatusManagerに委譲する。
    """
    from ..dependencies import DependencyManager
    from ..status import StatusManager

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
```

**実装例（handle_deps）:**
```python
def handle_deps(db: Database, args: Namespace) -> None:
    """
    depsコマンドの処理

    deps add/remove/list のサブコマンドに応じて依存関係を操作する。
    """
    from ..dependencies import DependencyManager

    deps_command = args.deps_command
    entity_type = args.entity

    dep_manager = DependencyManager(db)

    if deps_command == "add":
        _deps_add(dep_manager, entity_type, args.from_id, args.to_id)
    elif deps_command == "remove":
        _deps_remove(dep_manager, entity_type, args.from_id, args.to_id)
    elif deps_command == "list":
        _deps_list(dep_manager, entity_type, args.id)

def _deps_add(dep_manager: DependencyManager, entity_type: str, from_id: int, to_id: int) -> None:
    """依存関係追加"""
    if entity_type == "task":
        dep = dep_manager.add_task_dependency(from_id, to_id)
        console.print(f"[green]✓[/green] Task依存関係追加: {from_id} → {to_id}")
    elif entity_type == "subtask":
        dep = dep_manager.add_subtask_dependency(from_id, to_id)
        console.print(f"[green]✓[/green] SubTask依存関係追加: {from_id} → {to_id}")

def _deps_remove(dep_manager: DependencyManager, entity_type: str, from_id: int, to_id: int) -> None:
    """依存関係削除"""
    if entity_type == "task":
        dep_manager.remove_task_dependency(from_id, to_id)
        console.print(f"[green]✓[/green] Task依存関係削除: {from_id} → {to_id}")
    elif entity_type == "subtask":
        dep_manager.remove_subtask_dependency(from_id, to_id)
        console.print(f"[green]✓[/green] SubTask依存関係削除: {from_id} → {to_id}")

def _deps_list(dep_manager: DependencyManager, entity_type: str, entity_id: int) -> None:
    """依存関係一覧表示"""
    from . import display

    if entity_type == "task":
        predecessors = dep_manager.get_task_predecessors(entity_id)
        successors = dep_manager.get_task_successors(entity_id)
        display.show_dependencies("Task", entity_id, predecessors, successors)
    elif entity_type == "subtask":
        predecessors = dep_manager.get_subtask_predecessors(entity_id)
        successors = dep_manager.get_subtask_successors(entity_id)
        display.show_dependencies("SubTask", entity_id, predecessors, successors)
```

---

### 4.3 display.py（Rich表示ロジック）

**責務:**
- Rich Treeを使った階層ツリー表示
- Rich Tableを使ったProject一覧表示
- 依存関係の表示
- formatters.pyの呼び出し

**主な関数:**
```python
def show_project_list(projects: list[Project]) -> None:
    """Project一覧をRich Tableで表示"""

def show_project_tree(db: Database, project_id: int) -> None:
    """
    指定したProjectの階層ツリーをRich Treeで表示

    Project → SubProject → Task → SubTask の4階層を表示
    各ノードにステータス記号・色を付与
    """

def show_dependencies(
    entity_type: str,
    entity_id: int,
    predecessors: list,
    successors: list
) -> None:
    """
    依存関係をシンプルなリスト表示

    Args:
        entity_type: "Task" or "SubTask"
        entity_id: 対象エンティティID
        predecessors: 先行ノードのリスト
        successors: 後続ノードのリスト
    """
```

**実装例（show_project_list）:**
```python
from rich.console import Console
from rich.table import Table

from ..models import Project
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

    table = Table(title="プロジェクト一覧", show_header=True, header_style="bold magenta")
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
            proj.created_at[:19]  # "YYYY-MM-DDTHH:MM:SS"
        )

    console.print(table)
```

**実装例（show_project_tree）:**
```python
from rich.tree import Tree

from ..database import Database
from ..repository import ProjectRepository, SubProjectRepository, TaskRepository, SubTaskRepository
from . import formatters

def show_project_tree(db: Database, project_id: int) -> None:
    """
    指定したProjectの階層ツリーをRich Treeで表示

    Args:
        db: Database インスタンス
        project_id: 表示対象のProject ID
    """
    # リポジトリ初期化
    proj_repo = ProjectRepository(db)
    subproj_repo = SubProjectRepository(db)
    task_repo = TaskRepository(db)
    subtask_repo = SubTaskRepository(db)

    # Project取得
    project = proj_repo.get_by_id(project_id)
    if not project:
        console.print(f"[red]エラー: Project ID={project_id} が見つかりません。[/red]")
        return

    # Treeルート作成
    tree = Tree(
        f"📦 [bold]{project.name}[/bold] (ID={project.id})",
        guide_style="dim"
    )

    # SubProject取得・追加
    subprojects = subproj_repo.get_by_project(project_id)
    for subproj in subprojects:
        subproj_node = tree.add(
            f"📁 {subproj.name} (ID={subproj.id})"
        )

        # Task取得・追加
        tasks = task_repo.get_by_subproject(subproj.id)
        for task in tasks:
            status_display = formatters.format_status(task.status)
            task_node = subproj_node.add(
                f"📝 {task.name} (ID={task.id}) {status_display}"
            )

            # SubTask取得・追加
            subtasks = subtask_repo.get_by_task(task.id)
            for subtask in subtasks:
                subtask_status = formatters.format_status(subtask.status)
                task_node.add(
                    f"✏️  {subtask.name} (ID={subtask.id}) {subtask_status}"
                )

    # プロジェクト直下のTask（subproject_id=None）も追加（レビュー指摘B-9対応）
    direct_tasks = task_repo.get_by_project(project_id, subproject_id=None)
    if direct_tasks:
        # 区画ノードを作成
        direct_tasks_node = tree.add("📝 [dim]Tasks (direct)[/dim]")
        for task in direct_tasks:
            status_display = formatters.format_status(task.status)
            task_node = direct_tasks_node.add(
                f"📝 {task.name} (ID={task.id}) {status_display}"
            )

            subtasks = subtask_repo.get_by_task(task.id)
            for subtask in subtasks:
                subtask_status = formatters.format_status(subtask.status)
                task_node.add(
                    f"✏️  {subtask.name} (ID={subtask.id}) {subtask_status}"
                )

    console.print(tree)
```

**実装例（show_dependencies）:**
```python
def show_dependencies(
    entity_type: str,
    entity_id: int,
    predecessors: list,
    successors: list
) -> None:
    """
    依存関係をシンプルなリスト表示

    Args:
        entity_type: "Task" or "SubTask"
        entity_id: 対象エンティティID
        predecessors: 先行ノードのリスト（Taskまたはsubtask）
        successors: 後続ノードのリスト

    レビュー指摘B-7対応: 親文脈（project_id, subproject_id, task_id）を併記
    """
    console.print(f"\n[bold]{entity_type} ID={entity_id} の依存関係:[/bold]")

    # 先行ノード
    if predecessors:
        console.print("\n  [cyan]先行ノード（predecessor）:[/cyan]")
        for pred in predecessors:
            status_display = formatters.format_status(pred.status)
            # 親文脈の表示
            if entity_type == "Task":
                context = f"Project={pred.project_id}"
                if pred.subproject_id:
                    context += f", SubProject={pred.subproject_id}"
                console.print(f"    - {entity_type} ID={pred.id}: {pred.name} {status_display} [{context}]")
            elif entity_type == "SubTask":
                console.print(f"    - {entity_type} ID={pred.id}: {pred.name} {status_display} [Task={pred.task_id}]")
    else:
        console.print("\n  [dim]先行ノードなし[/dim]")

    # 後続ノード
    if successors:
        console.print("\n  [cyan]後続ノード（successor）:[/cyan]")
        for succ in successors:
            status_display = formatters.format_status(succ.status)
            # 親文脈の表示
            if entity_type == "Task":
                context = f"Project={succ.project_id}"
                if succ.subproject_id:
                    context += f", SubProject={succ.subproject_id}"
                console.print(f"    - {entity_type} ID={succ.id}: {succ.name} {status_display} [{context}]")
            elif entity_type == "SubTask":
                console.print(f"    - {entity_type} ID={succ.id}: {succ.name} {status_display} [Task={succ.task_id}]")
    else:
        console.print("\n  [dim]後続ノードなし[/dim]")

    console.print()
```

---

### 4.4 input.py（prompt_toolkit入力処理）

**責務:**
- prompt_toolkitを使った対話的入力
- 確認プロンプト（Yes/No）
- テキスト入力（必須/オプション）
- 整数入力

**主な関数:**
```python
def prompt_text(prompt_msg: str, required: bool = True) -> str | None:
    """
    テキスト入力プロンプト

    Args:
        prompt_msg: プロンプトメッセージ
        required: 必須入力かどうか

    Returns:
        入力されたテキスト、またはNone（オプションで未入力の場合）
    """

def prompt_int(prompt_msg: str, required: bool = True) -> int | None:
    """
    整数入力プロンプト

    Args:
        prompt_msg: プロンプトメッセージ
        required: 必須入力かどうか

    Returns:
        入力された整数、またはNone
    """

def confirm(message: str, default: bool = False) -> bool:
    """
    確認プロンプト（Yes/No）

    Args:
        message: 確認メッセージ
        default: デフォルト値（Enterのみの場合）

    Returns:
        True: Yes, False: No
    """
```

**実装例:**
```python
from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator, ValidationError

class IntegerValidator(Validator):
    """整数入力のバリデータ"""

    def validate(self, document):
        text = document.text
        if text and not text.isdigit():
            raise ValidationError(message="整数を入力してください。")

def prompt_text(prompt_msg: str, required: bool = True) -> str | None:
    """
    テキスト入力プロンプト

    Args:
        prompt_msg: プロンプトメッセージ
        required: 必須入力かどうか

    Returns:
        入力されたテキスト、またはNone（オプションで未入力の場合）
    """
    while True:
        result = prompt(f"{prompt_msg}: ")
        if result or not required:
            return result if result else None
        print("必須項目です。入力してください。")

def prompt_int(prompt_msg: str, required: bool = True) -> int | None:
    """
    整数入力プロンプト

    Args:
        prompt_msg: プロンプトメッセージ
        required: 必須入力かどうか

    Returns:
        入力された整数、またはNone
    """
    while True:
        result = prompt(f"{prompt_msg}: ", validator=IntegerValidator() if required else None)
        if result:
            return int(result)
        if not required:
            return None

def confirm(message: str, default: bool = False) -> bool:
    """
    確認プロンプト（Yes/No）

    Args:
        message: 確認メッセージ
        default: デフォルト値（Enterのみの場合）

    Returns:
        True: Yes, False: No
    """
    default_str = "Y/n" if default else "y/N"
    result = prompt(f"{message} ({default_str}): ")

    if not result:
        return default

    return result.lower() in ("y", "yes")
```

---

### 4.5 formatters.py（ステータス記号・色・共通フォーマット）

**責務:**
- ステータスの記号・色付け
- 共通のフォーマット処理

**主な関数:**
```python
def format_status(status: str) -> str:
    """
    ステータスを記号 + 色で表現

    Args:
        status: ステータス文字列（UNSET, NOT_STARTED, IN_PROGRESS, DONE）

    Returns:
        Richマークアップを含むステータス表示文字列
    """
```

**実装例:**
```python
def format_status(status: str) -> str:
    """
    ステータスを記号 + 色で表現

    Args:
        status: ステータス文字列（UNSET, NOT_STARTED, IN_PROGRESS, DONE）

    Returns:
        Richマークアップを含むステータス表示文字列

    Examples:
        >>> format_status("UNSET")
        '[dim][ ] UNSET[/dim]'
        >>> format_status("DONE")
        '[green][✓] DONE[/green]'
    """
    status_map = {
        "UNSET": "[dim][ ] UNSET[/dim]",
        "NOT_STARTED": "[blue][⏸] NOT_STARTED[/blue]",
        "IN_PROGRESS": "[yellow][▶] IN_PROGRESS[/yellow]",
        "DONE": "[green][✓] DONE[/green]",
    }

    return status_map.get(status, f"[dim][?] {status}[/dim]")
```

---

## 5. エラーハンドリング

### 5.1 例外の種類（Phase 1既存）

Phase 1で定義されたカスタム例外:
- `PMToolError` - 基底例外
- `ValidationError` - 入力バリデーションエラー
- `ConstraintViolationError` - 制約違反
- `CyclicDependencyError` - サイクル検出
- `StatusTransitionError` - ステータス遷移エラー
- `DeletionError` - 削除エラー

### 5.2 TUI層でのエラーハンドリング

**基本方針:**
- すべてのPMToolError派生例外をキャッチ
- ユーザー向けのわかりやすいメッセージに変換
- 技術的詳細は必要に応じて表示

**実装例（cli.pyのmain関数）:**
```python
from ..exceptions import (
    ValidationError,
    ConstraintViolationError,
    CyclicDependencyError,
    StatusTransitionError,
    DeletionError,
    PMToolError
)

try:
    # サブコマンド処理
    ...
except ValidationError as e:
    console.print(f"[red]❌ 入力エラー: {e}[/red]")
    sys.exit(1)
except ConstraintViolationError as e:
    console.print(f"[red]❌ 制約違反: {e}[/red]")
    sys.exit(1)
except CyclicDependencyError as e:
    # レビュー指摘B-6対応: 循環検出エラーの表示強化
    console.print(f"[red]❌ 循環依存エラー: {e}[/red]")
    console.print("[yellow]ヒント: この依存関係を追加すると循環が発生します。[/yellow]")
    sys.exit(1)
except StatusTransitionError as e:
    # レビュー指摘A-3対応: DONE遷移失敗時の理由明示
    console.print(f"[red]❌ ステータス遷移エラー: {e}[/red]")

    # エラーメッセージから原因を判定
    error_msg = str(e)
    if "先行" in error_msg:
        console.print("[yellow]原因: 先行ノードが未完了です[/yellow]")
        console.print("[dim]ヒント: 先行ノードのステータスをDONEにしてから再度お試しください[/dim]")
    elif "子SubTask" in error_msg:
        console.print("[yellow]原因: 子SubTaskが未完了です[/yellow]")
        console.print("[dim]ヒント: すべての子SubTaskのステータスをDONEにしてから再度お試しください[/dim]")
    else:
        console.print("[yellow]ヒント: DONE遷移条件を満たしていません[/yellow]")
    sys.exit(1)
except DeletionError as e:
    # レビュー指摘B-5対応: ChildExists系エラーの案内強化
    console.print(f"[red]❌ 削除エラー: {e}[/red]")
    console.print("[yellow]ヒント: 子ノードが存在する場合の対処方法:[/yellow]")
    console.print("  1. 先に子ノードを削除してから、親を削除する")
    console.print("  2. Task/SubTaskの場合: --bridge オプションで橋渡し削除を使用する")
    sys.exit(1)
except PMToolError as e:
    console.print(f"[red]❌ エラー: {e}[/red]")
    sys.exit(1)
except Exception as e:
    console.print(f"[red]❌ 予期しないエラー: {e}[/red]")
    import traceback
    traceback.print_exc()
    sys.exit(1)
```

**補足（レビュー指摘A-3: DONE遷移失敗時の詳細表示）:**

より詳細な情報（未完了ノードのリスト）を表示する場合、commands.pyの`handle_status`内でStatusTransitionErrorをキャッチし、DependencyManagerとRepositoryを使って未完了ノードを特定する実装も可能です。ただし、これはPhase 2のMVP範囲を超える可能性があるため、推奨機能（B）として位置づけられます。

**実装例（handle_status内での詳細エラー表示、オプション）:**
```python
def handle_status(db: Database, args: Namespace) -> None:
    from ..dependencies import DependencyManager
    from ..status import StatusManager
    from ..repository import TaskRepository, SubTaskRepository
    from ..exceptions import StatusTransitionError

    entity_type = args.entity
    entity_id = args.id
    new_status = args.status

    dep_manager = DependencyManager(db)
    status_manager = StatusManager(db, dep_manager)

    try:
        if entity_type == "task":
            updated = status_manager.update_task_status(entity_id, new_status)
            console.print(f"[green]✓[/green] Task ID={entity_id} のステータスを {updated.status} に変更しました。")
        elif entity_type == "subtask":
            updated = status_manager.update_subtask_status(entity_id, new_status)
            console.print(f"[green]✓[/green] SubTask ID={entity_id} のステータスを {updated.status} に変更しました。")

    except StatusTransitionError as e:
        # DONE遷移失敗時の詳細表示
        console.print(f"[red]❌ {e}[/red]")

        if new_status == "DONE":
            # 未完了の先行ノードをチェック
            if entity_type == "task":
                deps = dep_manager.get_task_dependencies(entity_id)
                predecessors = deps["predecessors"]
                task_repo = TaskRepository(db)

                incomplete_preds = []
                for pred_id in predecessors:
                    pred = task_repo.get_by_id(pred_id)
                    if pred and pred.status != "DONE":
                        incomplete_preds.append(pred)

                if incomplete_preds:
                    console.print("\n[yellow]未完了の先行Task:[/yellow]")
                    for pred in incomplete_preds:
                        status_display = formatters.format_status(pred.status)
                        console.print(f"  - Task ID={pred.id}: {pred.name} {status_display}")

                # 未完了の子SubTaskをチェック
                subtask_repo = SubTaskRepository(db)
                subtasks = subtask_repo.get_by_task(entity_id)
                incomplete_subtasks = [st for st in subtasks if st.status != "DONE"]

                if incomplete_subtasks:
                    console.print("\n[yellow]未完了の子SubTask:[/yellow]")
                    for st in incomplete_subtasks:
                        status_display = formatters.format_status(st.status)
                        console.print(f"  - SubTask ID={st.id}: {st.name} {status_display}")

            # SubTask の場合も同様の処理

        raise  # 再スローしてcli.pyのエラーハンドリングに任せる
```

---

## 6. トランザクション管理

### 6.1 Phase 1のown_connパターンを活用

TUI層では、基本的にビジネスロジック層のメソッドを単独で呼び出すため、各メソッドが自動的にトランザクション管理を行います（`conn=None` で呼び出し）。

**例:**
```python
# repository.pyのメソッドは自動的にトランザクション管理
repo = ProjectRepository(db)
project = repo.create(name="新プロジェクト")  # conn=Noneなので自動commit
```

### 6.2 複数操作を1トランザクションで実行する場合

将来的に複数のリポジトリ操作を1トランザクションで実行する必要がある場合は、明示的に`conn`を共有します。

**例（将来拡張時）:**
```python
conn = db.connect()
try:
    repo1.method1(conn=conn)
    repo2.method2(conn=conn)
    conn.commit()
except Exception as e:
    conn.rollback()
    raise
finally:
    conn.close()
```

---

## 7. テスト戦略

### 7.1 Phase 2のテスト方針

**pytest導入は必須としない。**
代わりに、`scripts/verify_phase2.py` を作成して手動検証を行う。

### 7.2 verify_phase2.pyの要件

以下のシナリオを一通り実行できること:

1. **空DBからの作成**
   - Project作成
   - SubProject作成
   - Task作成
   - SubTask作成

2. **依存関係追加**
   - Task間依存追加
   - SubTask間依存追加
   - サイクル検出のテスト

3. **ステータス更新**
   - Task/SubTaskのステータス変更
   - DONE遷移条件のテスト

4. **削除操作**
   - 標準削除（子がいる場合はエラー）
   - 橋渡し削除（依存関係再接続）

5. **表示確認**
   - Project一覧表示
   - ツリー表示
   - 依存関係表示

**実装方針:**
- `verify_phase1.py` を参考にしつつ、TUIコマンドを直接実行する形式
- subprocess経由でCLIコマンドを実行し、出力を検証
- または、commands.pyの関数を直接呼び出して検証

---

## 8. 実装の進め方

### 8.1 推奨実装順序

**ステップ1: 基本構造の構築**
1. `src/pmtool/tui/__init__.py` 作成
2. `src/pmtool/tui/formatters.py` 実装（ステータス表示）
3. `src/pmtool/tui/input.py` 実装（プロンプト処理）

**ステップ2: 表示機能の実装**
4. `src/pmtool/tui/display.py` 実装
   - `show_project_list()` 実装
   - `show_project_tree()` 実装
   - `show_dependencies()` 実装

**ステップ3: CLIフレームワークの構築**
5. `src/pmtool/tui/cli.py` 実装
   - `create_parser()` 実装（すべてのサブコマンド定義）
   - `main()` 実装（基本的なディスパッチとエラーハンドリング）

**ステップ4: コマンドハンドラの実装**
6. `src/pmtool/tui/commands.py` 実装
   - `handle_list()` 実装
   - `handle_show()` 実装
   - `handle_add()` 実装（Project/SubProject/Task/SubTask）
   - `handle_delete()` 実装
   - `handle_status()` 実装
   - `handle_deps()` 実装

**ステップ5: エントリーポイントの設定**
7. `setup.py` または `pyproject.toml` でCLIエントリーポイントを設定
   - `pmtool = src.pmtool.tui.cli:main` のような設定

**ステップ6: 検証スクリプトの作成**
8. `scripts/verify_phase2.py` 実装
   - すべてのコマンドの動作確認シナリオを実装

### 8.2 各ステップでの動作確認

- ステップ2終了時: `display.py`の関数を直接呼び出して表示確認
- ステップ3終了時: `pmtool --help` でヘルプ表示確認
- ステップ4終了時: 各サブコマンドの動作確認（`pmtool list projects` など）
- ステップ6終了時: `scripts/verify_phase2.py` 実行で総合確認

---

## 9. 依存ライブラリ

### 9.1 新規追加が必要なライブラリ

Phase 2で新たに追加する依存ライブラリ:
- **Rich**: コンソール出力・ツリー表示・テーブル表示
  ```bash
  pip install rich
  ```
- **prompt_toolkit**: 対話的入力
  ```bash
  pip install prompt_toolkit
  ```

### 9.2 requirements.txtの更新

```txt
# Phase 2 dependencies
rich>=13.0.0
prompt_toolkit>=3.0.0
```

---

## 10. CLIエントリーポイントの設定

### 10.1 setup.pyまたはpyproject.tomlの設定

**setup.py の例:**
```python
from setuptools import setup, find_packages

setup(
    name="pmtool",
    version="0.2.0",  # Phase 2
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "rich>=13.0.0",
        "prompt_toolkit>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "pmtool=pmtool.tui.cli:main",
        ],
    },
    python_requires=">=3.10",
)
```

**pyproject.toml の例:**
```toml
[project]
name = "pmtool"
version = "0.2.0"
requires-python = ">=3.10"
dependencies = [
    "rich>=13.0.0",
    "prompt_toolkit>=3.0.0",
]

[project.scripts]
pmtool = "pmtool.tui.cli:main"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
```

### 10.2 インストール方法

開発モードでインストール:
```bash
pip install -e .
```

これにより、`pmtool` コマンドがシステムで使用可能になります。

---

## 11. 受け入れ基準（Done条件）

Phase 2の実装完了の基準:

### 11.1 機能要件
- ✅ 空DBからTUI（CLI）操作だけで、以下が一通り実行できる:
  - Project/SubProject/Task/SubTask の作成
  - 依存関係の追加・削除
  - ステータスの更新（DONE遷移条件チェック含む）
  - 削除（標準削除・橋渡し削除）
  - ツリー表示・依存関係表示

### 11.2 品質要件
- ✅ 主要例外がユーザー向けメッセージで表示される
- ✅ `--help` でヘルプが表示される
- ✅ `scripts/verify_phase2.py` ですべてのシナリオが成功する

### 11.3 非機能要件
- ✅ Phase 2の範囲外機能（検索/フィルタ/ソート/エクスポート/高度可視化/常駐シェル/メニュー/update系）を実装していない
- ✅ Phase 1のビジネスロジック層を変更していない（TUI層のみ追加）

---

## 12. Phase 3への引き継ぎ事項

Phase 2完了後、以下の機能がPhase 3の候補となります:

### 12.1 Phase 3候補機能
- フィルタリング・検索機能
- ソート機能（created_at, order_indexなど）
- エクスポート機能（JSON/Markdown）
- 依存関係の高度可視化（ASCIIアート、グラフ）
- update系コマンド（名前/説明/order_index変更UI）
- Textualによる全画面TUI（再検討）
- pytestによる自動テスト導入
- doctor/checkコマンド（データ整合性チェック）
- Dry-runプレビュー機能
- cascade_deleteの正式実装

### 12.2 技術的負債・改善点
- Phase 2実装時に発見した問題点
- パフォーマンスボトルネック
- ユーザビリティ改善の余地

---

## 13. 参考資料

### 13.1 Phase 1ドキュメント
- `docs/specifications/プロジェクト管理ツール_ClaudeCode仕様書.md`
- `docs/design/DB設計書_v2.1_最終版.md`
- `docs/design/実装方針確定メモ.md`
- `CLAUDE.md`
- `README.md`

### 13.2 Phase 1実装
- `src/pmtool/repository.py` - CRUD操作の実装例
- `src/pmtool/dependencies.py` - 依存関係管理
- `src/pmtool/status.py` - ステータス管理
- `scripts/verify_phase1.py` - 使用例とテストケース

### 13.3 外部リソース
- **Rich ドキュメント**: https://rich.readthedocs.io/
- **prompt_toolkit ドキュメント**: https://python-prompt-toolkit.readthedocs.io/
- **argparse ドキュメント**: https://docs.python.org/3/library/argparse.html

---

## 14. レビュー指摘対応まとめ

ChatGPTによる設計書レビュー（`temp/Phase2/P2-5_Phase 2（TUI実装）設計書レビュー結果（差し戻し項目）_by_ChatGPT.md`）の指摘事項に対応しました。

### 14.1 必須対応（A）

| 指摘No | 内容 | 対応箇所 | 対応内容 |
|--------|------|----------|----------|
| A-1 | delete の --bridge を Task/SubTask に限定 | 4.1 cli.py, 4.2 commands.py | サブコマンド体系のコメント修正、handle_delete内で適用範囲チェックを実装 |
| A-2 | bridge削除の確認メッセージ強化 | 4.2 commands.py | 確認プロンプトに「先行×後続を再接続」「循環発生時は失敗」を明記 |
| A-3 | DONE遷移失敗時の理由明示 | 5.2 エラーハンドリング | StatusTransitionErrorキャッチ時に原因タイプを判定して表示、詳細表示の実装例も追加 |
| A-4 | deps add の --from/--to 明示 | 4.1 cli.py | argparseのhelpテキストに「先行ノード（predecessor）」「後続ノード（successor）」を明記 |

### 14.2 推奨対応（B）

| 指摘No | 内容 | 対応箇所 | 対応内容 |
|--------|------|----------|----------|
| B-5 | ChildExists系エラーの案内強化 | 5.2 エラーハンドリング | DeletionErrorキャッチ時に対処方法（子削除、--bridge使用）を明示 |
| B-6 | 循環検出エラー表示強化 | 5.2 エラーハンドリング | CyclicDependencyErrorキャッチ時にヒントメッセージを追加 |
| B-7 | deps list に親文脈を併記 | 4.3 display.py | show_dependencies関数で親文脈（project_id, subproject_id, task_id）を表示 |
| B-8 | delete --bridge 実行後の案内 | 4.2 commands.py | 橋渡し削除成功時に「依存が再接続された」旨と確認方法を表示 |
| B-9 | Project直下Taskの区画化 | 4.3 display.py | show_project_tree関数でProject直下Taskを「Tasks (direct)」区画ノードにグループ化 |

### 14.3 任意対応（C）

以下は現時点では対応せず、実装中または将来的に検討:
- 日時表示の `[:19]` スライス依存を避ける → 実装時に適切な整形を検討
- 絵文字・記号のフォールバック余地 → Phase 3以降で検討

### 14.4 追加確認事項

以下は必要に応じて確認予定:
- 表示が order_index 順になる保証（取得SQLの ORDER BY） → 実装時に確認
- SubProject取得が parent_subproject_id をどう扱うか → Phase 1のget_by_projectメソッドの動作に従う

---

## 15. 更新履歴

- 2026-01-17: 初版作成（Phase 2実装前の設計書）
- 2026-01-17: ChatGPTレビュー指摘対応（必須A-1～4、推奨B-5～9）

---

**作成者**: Claude Code
**レビュアー**: ChatGPT
**ステータス**: レビュー承認待ち → 実装開始可能
**次のアクション**: ChatGPTによる再レビュー → 承認後、Phase 2実装開始
