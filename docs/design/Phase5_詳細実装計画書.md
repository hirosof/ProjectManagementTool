# Phase 5 詳細実装計画書

**文書ID:** P5-17
**バージョン:** 1.0.1
**作成日:** 2026-01-22
**更新日:** 2026-01-22
**対象フェーズ:** Phase 5（Textual版）
**ステータス:** 承認済み（実装着手可能）

---

## 目次

1. [概要](#1-概要)
2. [前提条件](#2-前提条件)
3. [実装タスク一覧](#3-実装タスク一覧)
4. [詳細実装計画](#4-詳細実装計画)
5. [実装順序とマイルストーン](#5-実装順序とマイルストーン)
6. [品質目標](#6-品質目標)

---

## 1. 概要

### 1.1 目的

Phase 5（Textual版）の実装を円滑に進めるため、全16タスク（P5-01～P5-16）の詳細実装手順を定義します。

### 1.2 参照設計書

- **P5-9**: テンプレート機能 ビジネスロジック層設計書 v1.1.1（承認済み）
- **P5-12**: Textual UI基本構造設計書 v1.0.2（承認済み）
- **P5-4-1**: Phase 5スコープ定義

### 1.3 実装方針

1. **段階的実装**: 基盤整備 → 基本UI → テンプレート機能 → 補助機能
2. **動作確認の徹底**: 各タスク完了時に動作確認
3. **設計書準拠**: P5-9、P5-12の仕様を厳密に守る
4. **Phase 4品質**: テストカバレッジ80%を目指す

---

## 2. 前提条件

### 2.1 開発環境

- Python 3.10+
- 既存のpmtoolパッケージ（Phase 4完了版）
- textual==7.3.0（Phase 5で追加）

### 2.2 既存資産

**既存モジュール（Phase 1～4）:**
```
src/pmtool/
├── database.py          # DB接続・初期化
├── models.py            # エンティティモデル
├── repository.py        # CRUD操作
├── dependencies.py      # 依存関係管理
├── status.py            # ステータス管理
├── validators.py        # バリデーション
├── exceptions.py        # カスタム例外
├── doctor.py            # 整合性チェック
└── tui/                 # CLI（Phase 2）
    ├── cli.py
    ├── commands.py
    ├── display.py
    ├── formatters.py
    └── input.py
```

**Phase 5で追加するモジュール:**
```
src/
├── pmtool/
│   └── template.py          # テンプレート機能（新規）
└── pmtool_textual/          # Textual UI（新規パッケージ、pmtoolと並列）
    ├── __init__.py
    ├── app.py
    ├── screens/
    │   └── __init__.py
    ├── widgets/
    │   └── __init__.py
    └── utils/
        └── __init__.py
```

**重要:** `pmtool_textual`は`src/pmtool`の内部ではなく、`src/`直下に`pmtool`と並列で配置します。

---

## 3. 実装タスク一覧

### グループ1: 基盤整備（P5-01～P5-03）

| タスクID | タスク名 | 推定工数 | 依存関係 |
|---------|---------|---------|---------|
| P5-01 | プロジェクト構造整備 | 0.5h | - |
| P5-02 | Textual基本アプリケーション骨格 | 1h | P5-01 |
| P5-03 | DB接続管理モジュール | 0.5h | P5-02 |

### グループ2: テンプレート機能BL層（P5-04～P5-06）

| タスクID | タスク名 | 推定工数 | 依存関係 |
|---------|---------|---------|---------|
| P5-04 | TemplateRepository実装 | 2h | P5-03 |
| P5-05 | TemplateManager実装（基本） | 3h | P5-04 |
| P5-06 | TemplateManager実装（高度） | 3h | P5-05 |

### グループ3: 基本UI（P5-07～P5-09）

| タスクID | タスク名 | 推定工数 | 依存関係 |
|---------|---------|---------|---------|
| P5-07 | Home画面実装 | 2h | P5-03 |
| P5-08 | Project Detail画面実装 | 3h | P5-07 |
| P5-09 | SubProject Detail画面実装 | 2h | P5-08 |

### グループ4: テンプレート機能UI（P5-10～P5-12）

| タスクID | タスク名 | 推定工数 | 依存関係 |
|---------|---------|---------|---------|
| P5-10 | Template Hub画面実装 | 2h | P5-06, P5-09 |
| P5-11 | Template Save Wizard実装 | 3h | P5-10 |
| P5-12 | Template Apply Wizard実装 | 3h | P5-11 |

### グループ5: 補助機能・品質向上（P5-13～P5-16）

| タスクID | タスク名 | 推定工数 | 依存関係 |
|---------|---------|---------|---------|
| P5-13 | Settings画面実装 | 1h | P5-12 |
| P5-14 | 初回セットアップ支援 | 2h | P5-13 |
| P5-15 | テスト整備・品質向上 | 5h | P5-14 |
| P5-16 | Phase 5完了レポート | 1h | P5-15 |

**合計推定工数:** 約34時間

---

## 4. 詳細実装計画

### P5-01: プロジェクト構造整備

**目的:** Textual UI用のディレクトリ構造を作成

**作成するファイル・フォルダ:**
```
src/pmtool_textual/
├── __init__.py          # パッケージ初期化
├── app.py               # Textualアプリケーションメインクラス
├── screens/             # 画面モジュール
│   └── __init__.py
├── widgets/             # カスタムWidget
│   └── __init__.py
└── utils/               # ユーティリティ
    └── __init__.py
```

**実装手順:**

1. **ディレクトリ作成**
   ```bash
   mkdir -p src/pmtool_textual/screens
   mkdir -p src/pmtool_textual/widgets
   mkdir -p src/pmtool_textual/utils
   ```

2. **__init__.py作成**
   - `src/pmtool_textual/__init__.py`: 空ファイル
   - `src/pmtool_textual/screens/__init__.py`: 空ファイル
   - `src/pmtool_textual/widgets/__init__.py`: 空ファイル
   - `src/pmtool_textual/utils/__init__.py`: 空ファイル

3. **app.py骨格作成**
   ```python
   """Textual UI アプリケーションメインクラス"""
   from textual.app import App

   class PMToolApp(App):
       """Project Management Tool - Textual UI"""

       TITLE = "Project Management Tool"

       def on_mount(self) -> None:
           """アプリケーション起動時の処理"""
           pass

   def main() -> None:
       """エントリーポイント"""
       app = PMToolApp()
       app.run()

   if __name__ == "__main__":
       main()
   ```

4. **pyproject.toml更新**
   - `dependencies`に`textual==7.3.0`を追加
   - `[project.scripts]`に`pmtool-ui = "pmtool_textual.app:main"`を追加

**完了条件:**
- ディレクトリ構造が作成されている
- `python -c "import pmtool_textual"`が成功する
- `python -m pmtool_textual.app`で空のTextualアプリが起動する

---

### P5-02: Textual基本アプリケーション骨格

**目的:** 画面遷移・キーバインド・基本レイアウトの骨格実装

**実装内容:**

1. **app.py拡張**
   - グローバルキーバインド（H: Home, Q: Quit）
   - 画面スタック管理
   - CSS基本設定

2. **BaseScreen作成**（`screens/base.py`）
   ```python
   """基底Screen クラス"""
   from textual.screen import Screen
   from textual.widgets import Header, Footer
   from textual.app import ComposeResult

   class BaseScreen(Screen):
       """全画面の基底クラス"""

       def compose(self) -> ComposeResult:
           yield Header()
           yield Footer()

       def on_mount(self) -> None:
           """画面表示時の処理"""
           pass
   ```

3. **ダミーHome画面作成**（`screens/home.py`）
   ```python
   """Home画面（ダミー）"""
   from textual.containers import Container
   from textual.widgets import Static
   from .base import BaseScreen

   class HomeScreen(BaseScreen):
       def compose(self):
           yield from super().compose()
           yield Container(
               Static("Home Screen (WIP)", id="content"),
               id="main"
           )
   ```

4. **app.pyに画面登録**
   ```python
   from .screens.home import HomeScreen

   class PMToolApp(App):
       SCREENS = {"home": HomeScreen}

       def on_mount(self) -> None:
           self.push_screen("home")

       def action_quit(self) -> None:
           """Qキーでアプリ終了"""
           self.exit()
   ```

**完了条件:**
- `pmtool-ui`コマンドでTextualアプリが起動
- Header/Footerが表示される
- Qキーでアプリが終了する

---

### P5-03: DB接続管理モジュール

**目的:** Textual UI からpmtoolのDB機能にアクセスするためのユーティリティ実装

**実装内容:**

1. **db_manager.py作成**（`utils/db_manager.py`）
   ```python
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
   ```

2. **app.pyに統合**
   ```python
   from .utils.db_manager import DBManager

   class PMToolApp(App):
       def __init__(self):
           super().__init__()
           self.db_manager = DBManager()
   ```

**完了条件:**
- `app.db_manager.connect()`でDatabase インスタンスが取得できる
- `app.db_manager.is_db_exists()`でDB存在確認ができる

---

### P5-04: TemplateRepository実装

**目的:** テンプレートテーブルのCRUD操作実装（P5-9設計書準拠）

**実装場所:** `src/pmtool/repository.py`（既存ファイルに追加）

**実装するメソッド:**

```python
class TemplateRepository:
    """Template テーブルCRUD操作"""

    def __init__(self, db: Database):
        self.db = db

    def add_template(
        self,
        name: str,
        description: str | None,
        include_tasks: bool,
        conn: sqlite3.Connection | None = None
    ) -> Template:
        """テンプレート追加"""
        pass

    def get_template(
        self,
        template_id: int,
        conn: sqlite3.Connection | None = None
    ) -> Template | None:
        """テンプレート取得"""
        pass

    def get_template_by_name(
        self,
        name: str,
        conn: sqlite3.Connection | None = None
    ) -> Template | None:
        """テンプレート名で取得"""
        pass

    def list_templates(
        self,
        conn: sqlite3.Connection | None = None
    ) -> list[Template]:
        """テンプレート一覧取得"""
        pass

    def delete_template(
        self,
        template_id: int,
        conn: sqlite3.Connection | None = None
    ) -> None:
        """テンプレート削除"""
        pass

    # TemplateTask, TemplateSubTask, TemplateDependency用メソッドも同様に実装
```

**実装順序:**
1. Template基本CRUD（add/get/get_by_name/list/delete）
2. TemplateTask CRUD
3. TemplateSubTask CRUD
4. TemplateDependency CRUD

**テスト方針:**
- 各メソッドごとに手動テストスクリプト作成
- `scripts/test_template_repository.py`で動作確認

**完了条件:**
- すべてのCRUDメソッドが実装済み
- own_connパターンが正しく実装されている
- 手動テストで基本動作確認完了

---

### P5-05: TemplateManager実装（基本）

**目的:** テンプレート機能の基本ロジック実装（保存・一覧・取得・削除）

**実装場所:** `src/pmtool/template.py`（新規ファイル）

**実装内容:**

1. **models.py にデータクラス追加**
   ```python
   @dataclass
   class Template:
       """テンプレートエンティティ"""
       id: int
       name: str
       description: str | None
       include_tasks: bool
       created_at: str
       updated_at: str

   @dataclass
   class ExternalDependencyWarning:
       """外部依存警告情報"""
       from_task_id: int
       to_task_id: int
       from_task_name: str
       to_task_name: str
       direction: str  # 'outgoing' or 'incoming'

   @dataclass
   class SaveTemplateResult:
       """save_template() 戻り値"""
       template: Template
       external_dependencies: list[ExternalDependencyWarning]

       @property
       def has_warnings(self) -> bool:
           return len(self.external_dependencies) > 0
   ```

2. **template.py基本実装**
   ```python
   """テンプレート機能ビジネスロジック層"""
   from pmtool.database import Database
   from pmtool.repository import TemplateRepository
   from pmtool.models import SaveTemplateResult, Template
   import sqlite3

   class TemplateManager:
       """テンプレート管理"""

       def __init__(self, db: Database):
           self.db = db
           self.template_repo = TemplateRepository(db)

       def list_templates(
           self,
           conn: sqlite3.Connection | None = None
       ) -> list[Template]:
           """テンプレート一覧取得"""
           return self.template_repo.list_templates(conn)

       def get_template(
           self,
           template_id: int,
           conn: sqlite3.Connection | None = None
       ) -> Template | None:
           """テンプレート取得"""
           return self.template_repo.get_template(template_id, conn)

       def delete_template(
           self,
           template_id: int,
           conn: sqlite3.Connection | None = None
       ) -> None:
           """テンプレート削除"""
           self.template_repo.delete_template(template_id, conn)
   ```

**実装順序:**
1. TemplateManager基本構造
2. list_templates
3. get_template
4. delete_template

**テスト方針:**
- `scripts/test_template_manager_basic.py`で動作確認

**完了条件:**
- 基本メソッド（一覧・取得・削除）が実装済み
- 手動テストで動作確認完了

---

### P5-06: TemplateManager実装（高度）

**目的:** テンプレート保存・適用の高度な機能実装（P5-9設計書準拠）

**実装内容:**

1. **save_template実装**
   - SubProject メタデータ保存
   - include_tasks=true時のTask/SubTask/Dependency保存
   - 外部依存検出（_detect_external_dependencies）
   - SaveTemplateResult返却

2. **apply_template実装**
   - 新SubProject作成（UNSET ステータス）
   - Task/SubTask/Dependency複製
   - 内部依存関係の再接続
   - 新SubProject IDを返却

3. **dry_run実装**
   - 適用予定内容のプレビュー
   - 件数サマリ + 1階層ツリー

4. **_detect_external_dependencies実装**（private）
   - SubProject配下のTask依存関係をチェック
   - SubProject外への依存・被依存を検出
   - ExternalDependencyWarningリスト生成

   **設計判断:** このメソッドはprivate（`_`プレフィックス）だが、UI層（Template Save Wizard）から呼び出される。
   - **Phase 5では暫定的にprivateメソッド直接呼び出しを許容**する
   - 理由: `save_template()`実行前に警告表示が必要なため、事前検出用の公開APIを別途用意すると重複が生じる
   - Phase 6で公開API化（`detect_external_dependencies()`）を検討

5. **_validate_template_structure実装**（private）
   - テンプレート整合性チェック
   - サイクル検出

**実装順序:**
1. _detect_external_dependencies（外部依存検出）
2. save_template（include_tasks=False版）
3. save_template（include_tasks=True版）
4. apply_template（基本）
5. apply_template（依存関係再接続）
6. dry_run
7. _validate_template_structure

**テスト方針:**
- `scripts/test_template_manager_advanced.py`で動作確認
- 外部依存検出のエッジケースをテスト
- apply_template後のDB状態を確認

**完了条件:**
- P5-9のAPI仕様に完全準拠
- 外部依存検出が正しく動作
- apply_template後の依存関係が正しく再接続されている
- dry_runが期待通りのプレビューを返す

---

## 5. 実装順序とマイルストーン

### マイルストーン1: 基盤完成（P5-01～P5-03完了）
- Textual アプリが起動する
- DB接続ができる
- **所要時間:** 約2時間

### マイルストーン2: テンプレート機能BL完成（P5-04～P5-06完了）
- テンプレート保存・適用がCLIから実行可能
- 外部依存検出が動作する
- **所要時間:** 約8時間
- **累計:** 約10時間

### マイルストーン3: 基本UI完成（P5-07～P5-09完了）
- Project一覧・詳細表示ができる
- SubProject詳細表示ができる
- **所要時間:** 約7時間
- **累計:** 約17時間

### マイルストーン4: テンプレート機能UI完成（P5-10～P5-12完了）
- テンプレート保存・適用がTextual UIから実行可能
- dry-runプレビューが表示される
- **所要時間:** 約8時間
- **累計:** 約25時間

### マイルストーン5: Phase 5完成（P5-13～P5-16完了）
- Settings画面完成
- 初回セットアップ支援完成
- テストカバレッジ80%達成
- Phase 5完了レポート作成
- **所要時間:** 約9時間
- **累計:** 約34時間

---

## 6. 品質目標

### 6.1 テストカバレッジ

**目標:** 80%以上（Phase 4と同水準）

**対象モジュール:**
- `src/pmtool/template.py`: 80%以上
- `src/pmtool/repository.py`（Template関連追加部分）: 80%以上
- `src/pmtool_textual/`: ベストエフォート（UI層はカバレッジ測定が難しい）

**テスト戦略:**
- ビジネスロジック層（template.py）: pytest自動テスト
- Repository層: pytest自動テスト + 手動テスト
- UI層: 手動テスト中心

### 6.2 コード品質

- **型ヒント:** すべての公開APIに型ヒント必須
- **docstring:** すべての公開APIにdocstring必須
- **コメント:** 複雑なロジックには日本語コメント
- **命名規則:** Phase 1～4の規約に準拠

### 6.3 パフォーマンス目標

- **テンプレート保存:** 1000ノード以下のSubProjectで1秒以内
- **テンプレート適用:** 1000ノード以下のテンプレートで2秒以内
- **UI応答性:** すべての画面遷移が0.5秒以内

---

### P5-07: Home画面実装

**目的:** Project一覧表示画面の実装（P5-12設計書 6.1節準拠）

**実装場所:** `src/pmtool_textual/screens/home.py`

**実装内容:**

1. **HomeScreen クラス**
   ```python
   """Home画面（Project一覧）"""
   from textual.widgets import DataTable, Header, Footer
   from textual.app import ComposeResult
   from textual.binding import Binding
   from .base import BaseScreen
   from pmtool.repository import ProjectRepository

   class HomeScreen(BaseScreen):
       BINDINGS = [
           Binding("t", "template_hub", "Template Hub"),
           Binding("s", "settings", "Settings"),
           Binding("q", "quit", "Quit"),
       ]

       def compose(self) -> ComposeResult:
           yield Header()
           yield DataTable(id="project_table")
           yield Footer()

       def on_mount(self) -> None:
           """画面表示時にProject一覧を読み込む"""
           table = self.query_one(DataTable)
           table.add_columns("ID", "Name", "Description", "Status", "Updated")
           self.load_projects()

       def load_projects(self) -> None:
           """Project一覧をDBから取得して表示"""
           db = self.app.db_manager.connect()
           repo = ProjectRepository(db)
           projects = repo.list_projects()

           table = self.query_one(DataTable)
           table.clear()
           for proj in projects:
               table.add_row(
                   str(proj.id),
                   proj.name,
                   proj.description or "",
                   proj.status,
                   proj.updated_at
               )

       def on_data_table_row_selected(self, event) -> None:
           """Project選択時にProject Detail画面へ遷移"""
           row_key = event.row_key
           project_id = int(self.query_one(DataTable).get_row(row_key)[0])
           self.app.push_screen("project_detail", project_id=project_id)

       def action_template_hub(self) -> None:
           """Tキーで Template Hub へ遷移"""
           self.app.push_screen("template_hub")

       def action_settings(self) -> None:
           """Sキーで Settings へ遷移"""
           self.app.push_screen("settings")

       def action_quit(self) -> None:
           """Qキーでアプリ終了"""
           self.app.exit()
   ```

2. **app.pyに画面登録**
   ```python
   SCREENS = {
       "home": HomeScreen,
   }
   ```

**実装順序:**
1. DataTable基本表示
2. DB からProject一覧取得
3. 行選択イベントハンドリング
4. キーバインド（T, S, Q）

**テスト方針:**
- pmtool-ui起動後、Project一覧が表示されるか確認
- Project選択で画面遷移するか確認（遷移先は未実装でエラーでOK）
- T/S/Qキーが動作するか確認

**完了条件:**
- Project一覧が正しく表示される
- キーバインドが動作する
- 行選択で画面遷移が試行される

---

### P5-08: Project Detail画面実装

**目的:** Project詳細・4階層ツリー表示画面の実装（P5-12設計書 6.2節準拠）

**実装場所:** `src/pmtool_textual/screens/project_detail.py`

**実装内容:**

1. **ProjectDetailScreen クラス**
   ```python
   """Project Detail画面（4階層ツリー）"""
   from textual.widgets import Tree, Static, Header, Footer
   from textual.containers import Container, Vertical
   from textual.app import ComposeResult
   from textual.binding import Binding
   from .base import BaseScreen
   from pmtool.repository import ProjectRepository

   class ProjectDetailScreen(BaseScreen):
       BINDINGS = [
           Binding("escape", "back", "Back"),
           Binding("h", "home", "Home"),
       ]

       def __init__(self, project_id: int):
           super().__init__()
           self.project_id = project_id

       def compose(self) -> ComposeResult:
           yield Header()
           yield Vertical(
               Static("", id="project_info"),
               Tree("Project", id="project_tree"),
               id="main"
           )
           yield Footer()

       def on_mount(self) -> None:
           """Project情報とツリーを読み込む"""
           db = self.app.db_manager.connect()
           repo = ProjectRepository(db)
           project = repo.get_project(self.project_id)

           if project is None:
               self.app.pop_screen()
               return

           # Project情報表示
           info = self.query_one("#project_info", Static)
           info.update(
               f"[bold]{project.name}[/bold]\n"
               f"ID: {project.id} | Status: {project.status}\n"
               f"{project.description or ''}"
           )

           # 4階層ツリー構築
           self.build_tree(project)

       def build_tree(self, project) -> None:
           """4階層ツリーを構築"""
           tree = self.query_one("#project_tree", Tree)
           tree.clear()

           db = self.app.db_manager.connect()
           repo = ProjectRepository(db)

           # SubProject一覧取得
           subprojects = repo.list_subprojects(project.id)

           for sp in subprojects:
               sp_node = tree.root.add(f"📁 {sp.name} [{sp.status}]", data={"type": "subproject", "id": sp.id})

               # Task一覧取得
               tasks = repo.list_tasks(subproject_id=sp.id)
               for task in tasks:
                   task_node = sp_node.add(f"📋 {task.name} [{task.status}]", data={"type": "task", "id": task.id})

                   # SubTask一覧取得
                   subtasks = repo.list_subtasks(task_id=task.id)
                   for st in subtasks:
                       task_node.add(f"✓ {st.name} [{st.status}]", data={"type": "subtask", "id": st.id})

           # Project直下Task区画（グレーアウト）
           direct_tasks = repo.list_tasks(project_id=project.id, subproject_id=None)
           if direct_tasks:
               direct_node = tree.root.add("[dim]Project直下のTask（操作不可）[/dim]", data={"type": "section"})
               for task in direct_tasks:
                   direct_node.add(f"[dim]📋 {task.name}[/dim]", data={"type": "readonly"})

           tree.root.expand()

       def on_tree_node_selected(self, event) -> None:
           """ツリーノード選択時の処理"""
           node_data = event.node.data
           if node_data.get("type") == "subproject":
               subproject_id = node_data["id"]
               self.app.push_screen("subproject_detail", subproject_id=subproject_id)

       def action_back(self) -> None:
           """ESCキーで一つ前の画面に戻る"""
           self.app.pop_screen()

       def action_home(self) -> None:
           """HキーでHomeに戻る（画面スタックをクリア）"""
           self.app.pop_screen()
   ```

2. **app.pyに画面登録**
   ```python
   def push_screen(self, screen_name: str, **kwargs):
       if screen_name == "project_detail":
           screen = ProjectDetailScreen(project_id=kwargs["project_id"])
           super().push_screen(screen)
   ```

**実装順序:**
1. Project情報表示部分
2. SubProject一覧取得・ツリー表示
3. Task/SubTask取得・ツリー表示
4. Project直下Task区画表示
5. SubProject選択イベントハンドリング
6. キーバインド（ESC, H）

**完了条件:**
- 4階層ツリーが正しく表示される
- SubProject選択で画面遷移が試行される
- Project直下Taskがグレーアウト表示される
- ESC/Hキーで戻れる

---

### P5-09: SubProject Detail画面実装

**目的:** SubProject詳細表示画面の実装（P5-12設計書 6.3節準拠）

**実装場所:** `src/pmtool_textual/screens/subproject_detail.py`

**実装内容:**

1. **SubProjectDetailScreen クラス**
   - SubProject情報表示
   - Task/SubTaskツリー表示
   - Sキーで Template Save Wizardへ遷移

2. **実装パターン:**
   - ProjectDetailScreen とほぼ同じ構造
   - SubProject配下のTask/SubTaskのみ表示
   - Save Template ボタン/キーバインド追加

**実装順序:**
1. SubProject情報表示
2. Task/SubTaskツリー表示
3. Sキーバインド（Template Save Wizard遷移）
4. ESC/Hキーバインド

**完了条件:**
- SubProject詳細が正しく表示される
- Sキーで Template Save Wizardへ遷移が試行される
- ESC/Hキーで戻れる

---

### P5-10: Template Hub画面実装

**目的:** Template一覧・管理画面の実装（P5-12設計書 6.4節準拠）

**実装場所:** `src/pmtool_textual/screens/template_hub.py`

**実装内容:**

1. **TemplateHubScreen クラス**
   - Template一覧をDataTableで表示（P5-12 5.2節準拠）
   - Template選択で詳細表示（下部パネル）
   - Aキー: Apply Wizard遷移
   - Dキー: Template削除（確認ダイアログ）

2. **削除確認ダイアログ**
   - ModalScreenを使用（P5-12 8.3節準拠）
   - 「削除する」「キャンセル」

**実装順序:**
1. Template一覧取得・表示
2. Template選択・詳細表示
3. Aキーバインド（Apply Wizard遷移）
4. 削除確認ダイアログ実装
5. Dキーバインド（削除）

**完了条件:**
- Template一覧が表示される
- Template選択で詳細が表示される
- 削除が正しく動作する
- Aキーで Apply Wizard遷移が試行される

---

### P5-11: Template Save Wizard実装

**目的:** Template保存ウィザードの実装（P5-12設計書 6.5節準拠）

**実装場所:** `src/pmtool_textual/screens/template_save_wizard.py`

**実装内容:**

1. **4ステップWizard実装**
   - Step 1: SubProject選択
   - Step 2: テンプレート名入力
   - Step 3: include_tasks選択
   - Step 4: 確認・保存

2. **Step 4の詳細実装**（P5-12 v1.0.1 修正版準拠）
   ```python
   def on_step4_confirm(self):
       """Step 4: 確認画面での処理"""
       # 1. テンプレート名重複チェック
       existing = template_manager.get_template_by_name(self.template_name)
       if existing:
           self.show_error("テンプレート名が既に存在します")
           return

       # 2. 外部依存事前検出
       # NOTE: _detect_external_dependencies はprivateメソッドだが、
       #       save_template()実行前に警告表示が必要なため、Phase 5では暫定的に直接呼び出しを許容
       #       （P5-06の設計判断参照）
       external_warnings = template_manager._detect_external_dependencies(
           subproject_id=self.selected_subproject_id
       )

       # 3. 警告表示・確認
       if external_warnings:
           confirmed = self.show_warning_dialog(external_warnings)
           if not confirmed:
               return  # キャンセル

       # 4. 保存実行
       result = template_manager.save_template(
           subproject_id=self.selected_subproject_id,
           name=self.template_name,
           description=self.template_description,
           include_tasks=self.include_tasks
       )

       self.show_success(f"テンプレート '{result.template.name}' を保存しました")
       self.app.pop_screen()
   ```

3. **警告ダイアログ実装**
   - 外部依存一覧表示
   - 「続行する」「キャンセル」

**実装順序:**
1. Step 1: SubProject選択画面
2. Step 2: 名前入力画面
3. Step 3: include_tasks選択画面
4. Step 4: 確認画面（名前重複チェック）
5. Step 4: 外部依存検出・警告
6. Step 4: 保存実行
7. 画面遷移・キャンセル処理

**完了条件:**
- 4ステップすべてが実装されている
- 外部依存警告が正しく表示される
- テンプレート保存が正しく動作する
- キャンセルで元の画面に戻れる

---

### P5-12: Template Apply Wizard実装

**目的:** Template適用ウィザードの実装（P5-12設計書 6.6節準拠）

**実装場所:** `src/pmtool_textual/screens/template_apply_wizard.py`

**実装内容:**

1. **4ステップWizard実装**
   - Step 1: Template選択
   - Step 2: 適用先Project選択
   - Step 3: dry-run プレビュー
   - Step 4: 適用実行

2. **Step 3: dry-run プレビュー実装**
   ```python
   def show_dry_run_preview(self):
       """dry-run プレビュー表示"""
       preview = template_manager.dry_run(
           template_id=self.selected_template_id,
           project_id=self.selected_project_id
       )

       # 件数サマリ表示
       summary = (
           f"作成されるノード数:\n"
           f"  SubProject: 1\n"
           f"  Task: {preview.task_count}\n"
           f"  SubTask: {preview.subtask_count}\n"
           f"  依存関係: {preview.dependency_count}\n"
       )

       # 1階層ツリー表示（Task名のみ）
       tree_text = "\nTask一覧:\n"
       for task_name in preview.task_names:
           tree_text += f"  📋 {task_name}\n"

       self.query_one("#preview_content").update(summary + tree_text)
   ```

3. **Step 4: 適用実行**
   ```python
   def on_step4_apply(self):
       """Step 4: 適用実行"""
       new_subproject_name = self.query_one("#new_name_input").value

       new_subproject_id = template_manager.apply_template(
           template_id=self.selected_template_id,
           project_id=self.selected_project_id,
           new_subproject_name=new_subproject_name
       )

       self.show_success(
           f"テンプレートを適用しました\n"
           f"新SubProject ID: {new_subproject_id}"
       )
       self.app.pop_screen()
       # SubProject Detail画面へ遷移
       self.app.push_screen("subproject_detail", subproject_id=new_subproject_id)
   ```

**実装順序:**
1. Step 1: Template選択画面
2. Step 2: Project選択画面
3. Step 3: dry-runプレビュー表示
4. Step 4: 新SubProject名入力・適用実行
5. 適用後の画面遷移

**完了条件:**
- 4ステップすべてが実装されている
- dry-runプレビューが正しく表示される
- テンプレート適用が正しく動作する
- 適用後に新SubProject Detail画面へ遷移する

---

### P5-13: Settings画面実装

**目的:** 設定画面の実装（DBパス表示・バックアップ案内）（P5-12設計書 6.7節準拠）

**実装場所:** `src/pmtool_textual/screens/settings.py`

**実装内容:**

1. **SettingsScreen クラス**
   ```python
   """Settings画面"""
   from textual.widgets import Static, Header, Footer
   from textual.containers import Vertical
   from .base import BaseScreen

   class SettingsScreen(BaseScreen):
       def compose(self):
           yield Header()
           yield Vertical(
               Static("[bold]設定[/bold]", id="title"),
               Static("", id="db_info"),
               Static("", id="backup_guide"),
               id="main"
           )
           yield Footer()

       def on_mount(self):
           db_path = self.app.db_manager.db_path
           self.query_one("#db_info").update(
               f"[bold]データベース:[/bold]\n"
               f"  {db_path}\n"
           )

           self.query_one("#backup_guide").update(
               "[bold]バックアップ:[/bold]\n"
               "上記のデータベースファイルを定期的にコピーして\n"
               "バックアップすることを推奨します。\n\n"
               "手順:\n"
               "  1. アプリを終了する\n"
               f"  2. {db_path} をコピーする\n"
               "  3. 安全な場所に保存する\n"
           )
   ```

**実装順序:**
1. DBパス表示
2. バックアップ手順案内表示
3. キーバインド（ESC, H）

**完了条件:**
- DBパスが正しく表示される
- バックアップ手順が表示される
- ESC/Hキーで戻れる

---

### P5-14: 初回セットアップ支援

**目的:** DB未作成時の初回セットアップ導線実装

**実装場所:** `src/pmtool_textual/screens/setup.py`

**実装内容:**

1. **SetupScreen クラス**
   - DB未作成検出
   - DBファイルパス入力
   - DB初期化実行
   - init_db.sql適用

2. **app.py起動フロー修正**
   ```python
   def on_mount(self):
       if not self.db_manager.is_db_exists():
           self.push_screen("setup")
       else:
           self.push_screen("home")
   ```

**実装順序:**
1. SetupScreen基本構造
2. DBファイルパス入力UI
3. DB初期化処理
4. app.py起動フロー修正

**完了条件:**
- DB未作成時にSetup画面が表示される
- DBファイルパスを入力・作成できる
- DB初期化後にHome画面へ遷移する

---

### P5-15: テスト整備・品質向上

**目的:** Phase 5コードのテスト整備・カバレッジ80%達成

**実装内容:**

1. **template.py のテスト**（`tests/test_template.py`）
   - save_template: include_tasks=False/True
   - apply_template: 基本・依存関係再接続
   - _detect_external_dependencies: エッジケース
   - dry_run: プレビュー内容検証
   - 各例外ケース

2. **repository.py（Template関連）のテスト**（`tests/test_template_repository.py`）
   - Template CRUD
   - TemplateTask/SubTask/Dependency CRUD
   - own_connパターン動作確認

3. **統合テスト**（`tests/test_template_integration.py`）
   - 保存→適用の一連の流れ
   - 外部依存を持つケース
   - 大規模テンプレート（100+ ノード）

4. **カバレッジ測定**
   ```bash
   pytest --cov=src/pmtool/template --cov=src/pmtool/repository --cov-report=term-missing
   ```

**実装順序:**
1. template.py基本テスト（save/apply/dry_run）
2. template.py エッジケーステスト
3. repository.py Template関連テスト
4. 統合テスト
5. カバレッジ測定・80%達成確認

**完了条件:**
- テストカバレッジ80%以上達成
- すべてのテストがパスする
- エッジケースがカバーされている

---

### P5-16: Phase 5完了レポート

**目的:** Phase 5完了報告書の作成

**実装場所:** `docs/discussions/Phase5_完了レポート.md`

**記載内容:**

1. **実装完了機能**
   - テンプレート機能（保存・一覧・適用・削除・dry-run）
   - Textual UI（7画面）
   - 初回セットアップ支援

2. **実装統計**
   - 追加ファイル数
   - 追加行数
   - テストカバレッジ

3. **既知の制約事項**
   - Phase 6以降に持ち越す機能

4. **次フェーズへの引き継ぎ事項**

**完了条件:**
- Phase 5完了レポートが作成されている
- 実装統計が記載されている
- 次フェーズへの引き継ぎ事項が明確

---

## 変更履歴

### v1.0.1 (2026-01-22)
ChatGPTレビュー結果（P5-16）を反映:

**Must fix対応:**
1. pmtool_textual配置の統一（2.2節）
   - 修正前: `src/pmtool/pmtool_textual`と`src/pmtool_textual`が混在
   - 修正後: `src/pmtool_textual`に統一（`src/pmtool`と並列配置）

2. 文書ID重複の解消
   - 修正前: P5-15が文書IDとタスクIDで重複
   - 修正後: 文書IDをP5-17に変更（タスクIDはP5-15のまま）

3. キーバインド規約の統一（P5-08）
   - 修正前: action_backのコメント「ESCキーでHomeに戻る」が不正確
   - 修正後: 「ESCキーで一つ前の画面に戻る」に修正（P5-12準拠）

4. TemplateRepository実装場所の確認
   - P5-04記述は正しい（`repository.py`に追加、P5-9設計準拠）

**Should fix対応:**
5. Template Hub Widget統一（P5-10）
   - 修正前: ListViewで表示
   - 修正後: DataTableで表示（P5-12 5.2節準拠）

6. privateメソッド呼び出し方針明確化（P5-06、P5-11）
   - `_detect_external_dependencies`はprivateだが、UI層から呼び出す必要がある
   - Phase 5では暫定的にprivate直接呼び出しを許容（Phase 6で公開API化検討）
   - P5-06とP5-11に設計判断の注釈を追加

### v1.0.0 (2026-01-22)
- 初版作成（P5-01～P5-16詳細実装計画）

---

**以上**
