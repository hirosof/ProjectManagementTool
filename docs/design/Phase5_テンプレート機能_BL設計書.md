# テンプレート機能 ビジネスロジック層設計書

**バージョン:** 1.1.1
**作成日:** 2026-01-21
**更新日:** 2026-01-21
**対象フェーズ:** Phase 5（Textual版）
**ステータス:** 承認済み（実装着手OK）

---

## 目次

1. [概要](#1-概要)
2. [設計方針](#2-設計方針)
3. [データ設計](#3-データ設計)
4. [モジュール設計](#4-モジュール設計)
5. [API仕様](#5-api仕様)
6. [処理フロー](#6-処理フロー)
7. [エラーハンドリング](#7-エラーハンドリング)
8. [トランザクション設計](#8-トランザクション設計)
9. [テスト観点](#9-テスト観点)

---

## 1. 概要

### 1.1 目的

本設計書は、Phase 5で実装する**テンプレート機能のビジネスロジック層**（`src/pmtool/template.py`）の設計を定義します。

### 1.2 スコープ

**対象:**
- SubProjectテンプレートの保存・一覧・詳細・適用・削除機能
- dry-run機能（適用前のプレビュー）
- DB内保存方式の実装

**対象外（Phase 6以降）:**
- テンプレートのexport/import
- テンプレートの編集機能
- テンプレートのバージョン管理

### 1.3 前提条件

**Phase 5で確定した実装指示:**
1. 適用時ステータスは**全ノードUNSET固定**（選択UIなし）
2. include_tasksデフォルトは**OFF**（SubProjectのみ保存）
3. テンプレート名重複チェックは**確認画面で実施**（ロジック層は最終防衛）
4. dry-run表示は**件数サマリ + 1階層ツリー**
5. 依存関係の個別列挙は**行わない**

**設計思想:**
- 「安全に増やすUI」を優先
- 既存構造を壊さない
- 単純・迷路化しない

**レビュー履歴:**
- v1.0 → v1.1: ChatGPTレビュー指摘4件（Must fix）+ 2件（Should fix）を反映
  - テンプレート名重複チェックの責務分離を明確化
  - 外部依存の扱いと戻り値設計を修正
  - TemplateRepository新設を明記
  - SQLiteのBOOLEAN表現統一、例外処理方針明記
- v1.1 → v1.1.1: ChatGPT再レビュー指摘2件（必須）+ 2件（推奨）を反映 → **承認済み**

---

## 2. 設計方針

### 2.1 基本方針

#### 方針1: DB内保存方式を採用
- SQLite内にテンプレート専用テーブルを作成
- 既存のpmtool設計（SQLiteベース）との整合性を重視
- データ整合性（FK制約、トランザクション）を保証

#### 方針2: SubProjectテンプレート限定
- Project全体のテンプレート化は行わない
- SubProject配下の構造（Task + SubTask + 内部依存関係）のみ対象

#### 方針3: include_tasksオプション対応
- **デフォルトOFF**: SubProject名・説明のみ保存
- **明示的ON**: SubProject + Task + SubTask + 内部依存関係を保存
- Phase 5では「テンプレート名だけ使いたい」ケースを優先

#### 方針4: 外部依存の扱い（重要）
- **外部依存の定義**: SubProject配下のTaskが、SubProject外のTaskに依存している状態
- **保存時の扱い**:
  - 外部依存は**保存しない**（内部依存のみ保存）
  - 外部依存検出時は**警告情報を返す**（エラーではない）
  - UI側で必ず警告を表示し、ユーザーの明示的な続行判断を求める
- **適用時の保証**:
  - 外部依存は**再現されない**（内部依存のみ再接続）
  - これにより、適用先Projectの既存構造に影響を与えない
- **責務分離**:
  - ロジック層: 外部依存の検出・警告情報の提供
  - UI層: 警告表示・ユーザー確認・続行/キャンセル判断

#### 方針5: 適用時の安全性優先
- 適用先は**新SubProject固定**（既存SubProjectへのマージなし）
- ステータスは**全ノードUNSET固定**
- dry-runを必須とし、事前確認を促す

### 2.2 既存コンポーネントとの関係

```
┌─────────────────────────────────────┐
│   Textual UI (Phase 5)              │
│   - Template Hub                    │
│   - Save Wizard                     │
│   - Apply Wizard                    │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│   TemplateManager (template.py)     │  ← 本設計書の対象
│   - save_template()                 │
│   - list_templates()                │
│   - get_template()                  │
│   - apply_template()                │
│   - delete_template()               │
│   - dry_run()                       │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│   TemplateRepository (repository.py)│  ← 新設
│   - add_template()                  │
│   - get_template()                  │
│   - list_templates()                │
│   - delete_template()               │
│   - add_template_task()             │
│   - get_template_tasks()            │
│   - add_template_subtask()          │
│   - get_template_subtasks()         │
│   - add_template_dependency()       │
│   - get_template_dependencies()     │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│   既存ビジネスロジック層             │
│   - Repository (CRUD)               │
│   - DependencyManager (DAG検証)     │
│   - StatusManager                   │
│   - Database                        │
└─────────────────────────────────────┘
```

**呼び出し方針:**
- Textual UIは`TemplateManager`のみを呼び出す
- `TemplateManager`は内部で`TemplateRepository`、`Repository`、`DependencyManager`を利用
- **テンプレート系テーブル操作は`TemplateRepository`が責務を持つ**（SQL直書きを避ける）
- 既存のProject/SubProject/Task/SubTaskの操作は既存`Repository`を使用

---

## 3. データ設計

### 3.1 DB スキーマ

#### 3.1.1 templates テーブル

```sql
CREATE TABLE templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    include_tasks INTEGER NOT NULL DEFAULT 0,  -- 0: SubProjectのみ, 1: Task含む
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_templates_name ON templates(name);
```

**フィールド説明:**
- `id`: テンプレートID（主キー）
- `name`: テンプレート名（UNIQUE制約、重複時はUNIQUE違反エラー）
- `description`: テンプレート説明（オプション）
- `include_tasks`: Task/SubTask/依存関係を含むか（INTEGER型: 0=False, 1=True）
  - **注**: SQLiteはBOOLEAN型を持たないため、INTEGER型で0/1を使用
- `created_at`: 作成日時（ISO 8601形式）
- `updated_at`: 更新日時（ISO 8601形式）

#### 3.1.2 template_tasks テーブル

```sql
CREATE TABLE template_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    task_order INTEGER NOT NULL,  -- テンプレート内での順序（0, 1, 2, ...）
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE,
    UNIQUE (template_id, task_order)
);

CREATE INDEX idx_template_tasks_template_id ON template_tasks(template_id);
```

**フィールド説明:**
- `id`: template_task ID（主キー）
- `template_id`: 所属するテンプレートID（FK）
- `task_order`: テンプレート内での順序（0始まり）
- `name`: Task名
- `description`: Task説明

**設計のポイント:**
- `task_order`は実際の`order_index`ではなく、テンプレート内での相対的な順序
- 適用時に実際の`order_index`に変換される

#### 3.1.3 template_subtasks テーブル

```sql
CREATE TABLE template_subtasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    task_order INTEGER NOT NULL,      -- 親Taskの順序
    subtask_order INTEGER NOT NULL,   -- SubTaskの順序（0, 1, 2, ...）
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE,
    UNIQUE (template_id, task_order, subtask_order)
);

CREATE INDEX idx_template_subtasks_template_id ON template_subtasks(template_id);
```

**フィールド説明:**
- `id`: template_subtask ID（主キー）
- `template_id`: 所属するテンプレートID（FK）
- `task_order`: 親Taskの順序
- `subtask_order`: SubTask順序（親Task内での順序、0始まり）
- `name`: SubTask名
- `description`: SubTask説明

#### 3.1.4 template_dependencies テーブル

```sql
CREATE TABLE template_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    dep_type TEXT NOT NULL CHECK(dep_type IN ('task', 'subtask')),
    from_task_order INTEGER NOT NULL,       -- 先行Taskの順序
    to_task_order INTEGER NOT NULL,         -- 後続Taskの順序
    from_subtask_order INTEGER,             -- subtask依存の場合の先行SubTask順序
    to_subtask_order INTEGER,               -- subtask依存の場合の後続SubTask順序
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE,
    UNIQUE (template_id, dep_type, from_task_order, to_task_order, from_subtask_order, to_subtask_order)
);

CREATE INDEX idx_template_dependencies_template_id ON template_dependencies(template_id);
```

**フィールド説明:**
- `id`: template_dependency ID（主キー）
- `template_id`: 所属するテンプレートID（FK）
- `dep_type`: 依存関係の種類（'task' or 'subtask'）
- `from_task_order`: 先行Taskの順序
- `to_task_order`: 後続Taskの順序
- `from_subtask_order`: subtask依存の場合の先行SubTask順序（NULL可）
- `to_subtask_order`: subtask依存の場合の後続SubTask順序（NULL可）

**設計のポイント:**
- Task間依存: `dep_type='task'`, `from_subtask_order=NULL`, `to_subtask_order=NULL`
- SubTask間依存: `dep_type='subtask'`, `from_subtask_order`, `to_subtask_order`に値

### 3.2 データモデル（dataclass）

#### 3.2.1 Template

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Template:
    id: int
    name: str
    description: Optional[str]
    include_tasks: bool
    created_at: datetime
    updated_at: datetime
```

#### 3.2.2 TemplateTask

```python
@dataclass
class TemplateTask:
    id: int
    template_id: int
    task_order: int
    name: str
    description: Optional[str]
```

#### 3.2.3 TemplateSubTask

```python
@dataclass
class TemplateSubTask:
    id: int
    template_id: int
    task_order: int
    subtask_order: int
    name: str
    description: Optional[str]
```

#### 3.2.4 TemplateDependency

```python
@dataclass
class TemplateDependency:
    id: int
    template_id: int
    dep_type: str  # 'task' or 'subtask'
    from_task_order: int
    to_task_order: int
    from_subtask_order: Optional[int]
    to_subtask_order: Optional[int]
```

#### 3.2.5 SaveTemplateResult

```python
@dataclass
class ExternalDependencyWarning:
    """外部依存の警告情報"""
    from_task_id: int
    to_task_id: int
    from_task_name: str
    to_task_name: str
    direction: str  # 'outgoing' or 'incoming'

@dataclass
class SaveTemplateResult:
    """save_template()の戻り値"""
    template: Template
    external_dependencies: list[ExternalDependencyWarning]  # 外部依存の警告リスト

    @property
    def has_warnings(self) -> bool:
        """警告があるかどうか"""
        return len(self.external_dependencies) > 0
```

**設計意図:**
- `save_template()`は単なる`Template`ではなく、`SaveTemplateResult`を返す
- 外部依存の警告情報を明示的に含める
- UI側は`has_warnings`で警告の有無を判定し、必要に応じて警告を表示

#### 3.2.6 DryRunResult

```python
@dataclass
class DryRunResult:
    """dry-run結果を格納するデータクラス"""
    subproject_count: int  # 常に1
    task_count: int
    subtask_count: int
    dependency_count: int
    tree_preview: str  # 1階層ツリーのテキスト表現
```

---

## 4. モジュール設計

### 4.1 ファイル構成

```
src/pmtool/
├── template.py          # TemplateManager（本設計書の対象）
├── models.py            # Template, TemplateTask等のデータクラス追加
├── repository.py        # 既存Repository + TemplateRepository追加
├── dependencies.py      # 既存（そのまま利用）
├── database.py          # 既存（スキーマ追加）
└── exceptions.py        # テンプレート関連の例外追加
```

**設計判断: TemplateRepositoryの配置**
- `TemplateRepository`は既存の`repository.py`に追加
- 理由: 既存`Repository`クラスと同じCRUDパターンを使用、ファイル分離の必要性は低い
- `Repository`クラスと`TemplateRepository`クラスは独立して定義

### 4.2 TemplateManager クラス

```python
class TemplateManager:
    """テンプレート機能を管理するクラス"""

    def __init__(self, db: Database):
        self.db = db
        self.repo = Repository(db)
        self.template_repo = TemplateRepository(db)  # テンプレート専用Repository
        self.dep_manager = DependencyManager(db)

    # 保存
    def save_template(
        self,
        subproject_id: int,
        name: str,
        description: Optional[str] = None,
        include_tasks: bool = False,
        conn: Optional[sqlite3.Connection] = None
    ) -> SaveTemplateResult:
        """SubProjectをテンプレートとして保存

        戻り値には外部依存の警告情報が含まれる。
        UI側はhas_warningsで判定し、必要に応じて警告を表示すること。
        """
        pass

    # 一覧
    def list_templates(
        self,
        conn: Optional[sqlite3.Connection] = None
    ) -> list[Template]:
        """テンプレート一覧を取得"""
        pass

    # 詳細
    def get_template(
        self,
        template_id: int,
        conn: Optional[sqlite3.Connection] = None
    ) -> tuple[Template, list[TemplateTask], list[TemplateSubTask], list[TemplateDependency]]:
        """テンプレート詳細を取得"""
        pass

    # 名前検索
    def get_template_by_name(
        self,
        name: str,
        conn: Optional[sqlite3.Connection] = None
    ) -> Optional[Template]:
        """名前でテンプレートを検索"""
        pass

    # 削除
    def delete_template(
        self,
        template_id: int,
        conn: Optional[sqlite3.Connection] = None
    ) -> None:
        """テンプレートを削除"""
        pass

    # dry-run
    def dry_run(
        self,
        template_id: int,
        project_id: int,
        new_subproject_name: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None
    ) -> DryRunResult:
        """テンプレート適用のdry-run（プレビュー）"""
        pass

    # 適用
    def apply_template(
        self,
        template_id: int,
        project_id: int,
        new_subproject_name: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None
    ) -> int:
        """テンプレートを適用（新SubProjectを作成）"""
        pass

    # 内部メソッド
    def _detect_external_dependencies(
        self,
        subproject_id: int,
        conn: sqlite3.Connection
    ) -> list[ExternalDependencyWarning]:
        """外部依存を検出（警告情報として返す）"""
        pass

    def _build_order_mapping(
        self,
        tasks: list[Task]
    ) -> dict[int, int]:
        """実際のTask IDからtask_orderへのマッピングを構築"""
        pass
```

### 4.3 TemplateRepository クラス

```python
class TemplateRepository:
    """テンプレート系テーブルのCRUD操作を担当"""

    def __init__(self, db: Database):
        self.db = db

    # templates テーブル操作
    def add_template(
        self,
        name: str,
        description: Optional[str],
        include_tasks: bool,
        conn: Optional[sqlite3.Connection] = None
    ) -> Template:
        """テンプレートを追加

        name重複時はsqlite3.IntegrityError（UNIQUE制約違反）が発生する。
        呼び出し側でTemplateNameConflictErrorに変換すること。
        """
        pass

    def get_template(
        self,
        template_id: int,
        conn: Optional[sqlite3.Connection] = None
    ) -> Optional[Template]:
        """テンプレートを取得"""
        pass

    def get_template_by_name(
        self,
        name: str,
        conn: Optional[sqlite3.Connection] = None
    ) -> Optional[Template]:
        """名前でテンプレートを取得"""
        pass

    def list_templates(
        self,
        conn: Optional[sqlite3.Connection] = None
    ) -> list[Template]:
        """テンプレート一覧を取得"""
        pass

    def delete_template(
        self,
        template_id: int,
        conn: Optional[sqlite3.Connection] = None
    ) -> None:
        """テンプレートを削除（CASCADE設定により関連レコードも削除）"""
        pass

    # template_tasks テーブル操作
    def add_template_task(
        self,
        template_id: int,
        task_order: int,
        name: str,
        description: Optional[str],
        conn: Optional[sqlite3.Connection] = None
    ) -> TemplateTask:
        """テンプレートTaskを追加"""
        pass

    def get_template_tasks(
        self,
        template_id: int,
        conn: Optional[sqlite3.Connection] = None
    ) -> list[TemplateTask]:
        """テンプレートTask一覧を取得（task_order昇順）"""
        pass

    # template_subtasks テーブル操作
    def add_template_subtask(
        self,
        template_id: int,
        task_order: int,
        subtask_order: int,
        name: str,
        description: Optional[str],
        conn: Optional[sqlite3.Connection] = None
    ) -> TemplateSubTask:
        """テンプレートSubTaskを追加"""
        pass

    def get_template_subtasks(
        self,
        template_id: int,
        conn: Optional[sqlite3.Connection] = None
    ) -> list[TemplateSubTask]:
        """テンプレートSubTask一覧を取得（task_order, subtask_order昇順）"""
        pass

    # template_dependencies テーブル操作
    def add_template_dependency(
        self,
        template_id: int,
        dep_type: str,
        from_task_order: int,
        to_task_order: int,
        from_subtask_order: Optional[int],
        to_subtask_order: Optional[int],
        conn: Optional[sqlite3.Connection] = None
    ) -> TemplateDependency:
        """テンプレート依存関係を追加"""
        pass

    def get_template_dependencies(
        self,
        template_id: int,
        conn: Optional[sqlite3.Connection] = None
    ) -> list[TemplateDependency]:
        """テンプレート依存関係一覧を取得"""
        pass
```

**設計のポイント:**
- テンプレート系テーブルへのすべてのアクセスをこのクラスに集約
- own_connパターンを採用（既存Repositoryと同様）
- SQL直書きを避け、保守性を向上

---

## 5. API仕様

### 5.1 save_template

**シグネチャ:**
```python
def save_template(
    self,
    subproject_id: int,
    name: str,
    description: Optional[str] = None,
    include_tasks: bool = False,
    conn: Optional[sqlite3.Connection] = None
) -> SaveTemplateResult
```

**パラメータ:**
- `subproject_id`: 保存対象のSubProject ID
- `name`: テンプレート名（UNIQUE制約）
- `description`: テンプレート説明（オプション）
- `include_tasks`: Task/SubTask/依存関係を含むか（デフォルト: False）
- `conn`: トランザクション用接続（オプション）

**戻り値:**
- `SaveTemplateResult`オブジェクト
  - `template`: 作成されたTemplateオブジェクト
  - `external_dependencies`: 外部依存の警告リスト（空リストの場合は警告なし）

**処理フロー:**
1. SubProjectの存在確認（`repo.get_subproject()`）
2. 外部依存の検出（`_detect_external_dependencies()`）
   - 外部依存が存在する場合は警告情報を収集（エラーではない）
3. `templates`レコード作成（`template_repo.add_template()`）
   - UNIQUE制約違反時は`sqlite3.IntegrityError`が発生
   - `TemplateNameConflictError`に変換して再送出
4. `include_tasks=True`の場合:
   - Task一覧取得、`template_tasks`に保存（`template_repo.add_template_task()`）
   - SubTask一覧取得、`template_subtasks`に保存（`template_repo.add_template_subtask()`）
   - 内部依存関係取得、`template_dependencies`に保存（`template_repo.add_template_dependency()`）
5. トランザクションコミット
6. `SaveTemplateResult`を返す

**例外:**
- `SubProjectNotFoundError`: SubProjectが存在しない
- `TemplateNameConflictError`: テンプレート名が既に存在する（UNIQUE制約違反から変換）
- `DatabaseError`: DB操作エラー

**責務分離（重要）:**
- **UI側の責務**: 確認画面で`get_template_by_name()`を呼び、事前に重複チェックを実施
- **ロジック層の責務**: UNIQUE制約違反を最終防衛として検出し、適切な例外に変換
- この二段構えにより、ユーザー体験（事前警告）とデータ整合性（最終防衛）を両立

---

### 5.2 list_templates

**シグネチャ:**
```python
def list_templates(
    self,
    conn: Optional[sqlite3.Connection] = None
) -> list[Template]
```

**パラメータ:**
- `conn`: トランザクション用接続（オプション）

**戻り値:**
- `Template`オブジェクトのリスト（作成日時降順）

**処理フロー:**
1. `templates`テーブルから全レコード取得
2. `Template`オブジェクトのリストを返す

**例外:**
- `DatabaseError`: DB操作エラー

---

### 5.3 get_template

**シグネチャ:**
```python
def get_template(
    self,
    template_id: int,
    conn: Optional[sqlite3.Connection] = None
) -> tuple[Template, list[TemplateTask], list[TemplateSubTask], list[TemplateDependency]]
```

**パラメータ:**
- `template_id`: テンプレートID
- `conn`: トランザクション用接続（オプション）

**戻り値:**
- タプル: `(Template, TemplateTasks, TemplateSubTasks, TemplateDependencies)`

**処理フロー:**
1. `templates`テーブルから該当レコード取得
   - 存在しない場合: `TemplateNotFoundError`
2. `template_tasks`から関連Task取得（task_order昇順）
3. `template_subtasks`から関連SubTask取得（task_order, subtask_order昇順）
4. `template_dependencies`から関連依存関係取得
5. タプルで返す

**例外:**
- `TemplateNotFoundError`: テンプレートが存在しない
- `DatabaseError`: DB操作エラー

---

### 5.4 get_template_by_name

**シグネチャ:**
```python
def get_template_by_name(
    self,
    name: str,
    conn: Optional[sqlite3.Connection] = None
) -> Optional[Template]
```

**パラメータ:**
- `name`: テンプレート名
- `conn`: トランザクション用接続（オプション）

**戻り値:**
- `Template`オブジェクト（存在する場合）
- `None`（存在しない場合）

**処理フロー:**
1. `templates`テーブルからname検索
2. 該当レコードがあれば`Template`オブジェクトを返す
3. なければ`None`を返す

**例外:**
- `DatabaseError`: DB操作エラー

---

### 5.5 delete_template

**シグネチャ:**
```python
def delete_template(
    self,
    template_id: int,
    conn: Optional[sqlite3.Connection] = None
) -> None
```

**パラメータ:**
- `template_id`: テンプレートID
- `conn`: トランザクション用接続（オプション）

**戻り値:**
- なし

**処理フロー:**
1. テンプレートの存在確認（`get_template()`）
   - 存在しない場合: `TemplateNotFoundError`
2. `templates`レコード削除
   - CASCADE設定により、関連する`template_tasks`, `template_subtasks`, `template_dependencies`も自動削除
3. トランザクションコミット

**例外:**
- `TemplateNotFoundError`: テンプレートが存在しない
- `DatabaseError`: DB操作エラー

---

### 5.6 dry_run

**シグネチャ:**
```python
def dry_run(
    self,
    template_id: int,
    project_id: int,
    new_subproject_name: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None
) -> DryRunResult
```

**パラメータ:**
- `template_id`: テンプレートID
- `project_id`: 適用先ProjectID
- `new_subproject_name`: 新SubProject名（省略時はテンプレート名を使用）
- `conn`: トランザクション用接続（オプション）

**戻り値:**
- `DryRunResult`オブジェクト

**処理フロー:**
1. テンプレート存在確認（`get_template()`）
2. Project存在確認（`repo.get_project()`）
3. テンプレート内容を取得
4. 件数サマリを計算:
   - `subproject_count`: 常に1
   - `task_count`: `len(template_tasks)`
   - `subtask_count`: `len(template_subtasks)`
   - `dependency_count`: `len(template_dependencies)`
5. 1階層ツリーを生成:
   ```
   [新SubProject] <テンプレート名>
   ├── [Task] Task1
   ├── [Task] Task2 (SubTasks: 3)
   └── [Task] Task3 (SubTasks: 1)
   ```
   - SubTaskは件数のみ表示
6. `DryRunResult`を返す

**例外:**
- `TemplateNotFoundError`: テンプレートが存在しない
- `ProjectNotFoundError`: Projectが存在しない
- `DatabaseError`: DB操作エラー

---

### 5.7 apply_template

**シグネチャ:**
```python
def apply_template(
    self,
    template_id: int,
    project_id: int,
    new_subproject_name: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None
) -> int
```

**パラメータ:**
- `template_id`: テンプレートID
- `project_id`: 適用先ProjectID
- `new_subproject_name`: 新SubProject名（省略時はテンプレート名を使用）
- `conn`: トランザクション用接続（オプション）

**戻り値:**
- 作成されたSubProject ID

**処理フロー:**
1. テンプレート存在確認（`get_template()`）
2. Project存在確認（`repo.get_project()`）
3. テンプレート内容を取得（Task, SubTask, Dependencies）
4. 新SubProjectを作成（`repo.add_subproject()`）
   - 名前: `new_subproject_name` or `template.name`
   - 説明: `template.description`
   - ステータス: `UNSET`
5. `template.include_tasks=True`の場合のみ、以下を実行:
   - Task作成: `template_tasks`の各レコードを`repo.add_task()`
     - ステータス: `UNSET`
     - order_indexは自動計算
     - IDマッピングを構築: `{task_order: actual_task_id}`
   - SubTask作成: `template_subtasks`の各レコードを`repo.add_subtask()`
     - ステータス: `UNSET`
     - order_indexは自動計算
     - IDマッピングを構築: `{(task_order, subtask_order): actual_subtask_id}`
   - 依存関係作成: `template_dependencies`の各レコードを再接続
     - Task間依存: `dep_manager.add_task_dependency()`
     - SubTask間依存: `dep_manager.add_subtask_dependency()`
     - order → 実際のIDへの変換にマッピングを使用
6. トランザクションコミット
7. 作成されたSubProject IDを返す

**例外:**
- `TemplateNotFoundError`: テンプレートが存在しない
- `ProjectNotFoundError`: Projectが存在しない
- `CycleDetectedError`: 依存関係にサイクルが検出された
- `DatabaseError`: DB操作エラー

**例外処理方針（重要）:**
- **CycleDetectedErrorについて**:
  - 理論上、テンプレート保存時に内部依存のみを保存しているため、適用時にサイクルは発生しないはず
  - しかし、以下の理由により適切な例外処理を行う:
    1. データ破損やバグによる予期しない状態
    2. 将来の拡張（テンプレート編集機能等）での混入可能性
  - **発生時の処理**: トランザクションをロールバックし、例外を再送出
  - **UI側での処理**: エラーメッセージを表示し、適用を中止
- **DatabaseErrorについて**:
  - すべてのDB操作エラーを補足し、トランザクションをロールバック
  - 部分的な適用を防ぎ、データ整合性を保証

**注意事項:**
- `template.include_tasks=False`の場合、SubProjectのみ作成（Task/SubTask/依存関係は作成されない）
- すべてのステータスは`UNSET`で初期化

---

## 6. 処理フロー

### 6.1 テンプレート保存フロー

```
[UI] Template Save Wizard
  ↓
  1. SubProject選択
  ↓
  2. include_tasks ON/OFF選択（デフォルト: OFF）
  ↓
  3. テンプレート名入力
  ↓
  4. 確認画面
     - テンプレート名の重複チェック（get_template_by_name）
     - 重複時: 警告表示 + 保存ブロック
  ↓
  5. TemplateManager.save_template() 呼び出し
     - SubProject存在確認
     - 外部依存検出（警告表示、エラーではない）
     - templatesレコード作成
     - include_tasks=Trueの場合:
       - template_tasksレコード作成
       - template_subtasksレコード作成
       - template_dependenciesレコード作成
     - トランザクションコミット
  ↓
  6. 保存完了メッセージ表示
     - 外部依存がある場合は警告も表示
```

### 6.2 テンプレート適用フロー

```
[UI] Template Apply Wizard
  ↓
  1. Template Hub でテンプレート選択
  ↓
  2. 適用先Project選択
  ↓
  3. dry-run実行（TemplateManager.dry_run）
     - 件数サマリ計算
     - 1階層ツリー生成
     - DryRunResult表示
       ┌─────────────────────────────┐
       │ 作成内容:                   │
       │ - SubProject: 1             │
       │ - Task: 5                   │
       │ - SubTask: 12               │
       │ - 依存関係: 3               │
       │                             │
       │ [新SubProject] 開発フロー   │
       │ ├── [Task] 要件定義         │
       │ ├── [Task] 設計 (SubTasks: 3)│
       │ ├── [Task] 実装 (SubTasks: 5)│
       │ ├── [Task] テスト (SubTasks: 4)│
       │ └── [Task] リリース         │
       └─────────────────────────────┘
  ↓
  4. 実行確認
     - 「この内容で適用しますか？」
     - キャンセル可能
  ↓
  5. TemplateManager.apply_template() 呼び出し
     - テンプレート内容取得
     - 新SubProject作成（UNSET）
     - include_tasks=Trueの場合:
       - Task作成（UNSET）
       - SubTask作成（UNSET）
       - 依存関係再接続
     - トランザクションコミット
  ↓
  6. 適用完了
     - 作成されたSubProjectへ遷移
```

### 6.3 外部依存検出の処理

```python
def _detect_external_dependencies(
    self,
    subproject_id: int,
    conn: sqlite3.Connection
) -> list[ExternalDependencyWarning]:
    """
    外部依存を検出する

    外部依存 = SubProject配下のTaskが、SubProject外のTaskに依存している

    Returns:
        ExternalDependencyWarningのリスト
    """
    # 1. SubProject配下のTask IDリストを取得
    tasks = self.repo.list_tasks(subproject_id=subproject_id, conn=conn)
    task_ids = {task.id for task in tasks}
    task_map = {task.id: task for task in tasks}

    # 2. 各Taskの依存関係をチェック
    warnings = []
    for task in tasks:
        dependencies = self.dep_manager.get_task_dependencies(task.id, conn=conn)
        for dep in dependencies:
            # predecessor（先行Task）がSubProject外の場合（outgoing依存）
            if dep.predecessor_id not in task_ids:
                pred_task = self.repo.get_task(dep.predecessor_id, conn=conn)
                warnings.append(ExternalDependencyWarning(
                    from_task_id=dep.predecessor_id,
                    to_task_id=task.id,
                    from_task_name=pred_task.name,
                    to_task_name=task.name,
                    direction='outgoing'
                ))
            # successor（後続Task）がSubProject外の場合（incoming依存）
            if dep.successor_id not in task_ids:
                succ_task = self.repo.get_task(dep.successor_id, conn=conn)
                warnings.append(ExternalDependencyWarning(
                    from_task_id=task.id,
                    to_task_id=dep.successor_id,
                    from_task_name=task.name,
                    to_task_name=succ_task.name,
                    direction='incoming'
                ))

    return warnings
```

**重複排除について:**
- 現状の実装では、同一の依存関係が重複して検出される可能性がある
  - 例: Task A → Task B（外部）の依存が、A側からもB側からも検出される
- Phase 5では重複排除は行わず、そのまま返す（UI側で判断）
- 将来的に重複が問題となる場合は、set化や`(from_task_id, to_task_id)`のユニーク化を検討

**警告表示（UI側の例）:**
```
警告: このSubProjectは外部依存を持っています。
以下の依存関係はテンプレートに保存されません:

- Task "要件定義" は SubProject外のTask "プロジェクト計画" に依存しています（outgoing）
- Task "リリース" は SubProject外のTask "運用準備" に依存されています（incoming）

テンプレート適用時、これらの依存関係は再現されません。

続行しますか？ [はい / いいえ]
```

**UI側の責務（重要）:**
- `SaveTemplateResult.has_warnings`で警告の有無を判定
- 警告がある場合は必ず表示し、ユーザーの明示的な続行判断を求める
- ユーザーがキャンセルした場合、テンプレート保存を中止（ロールバック不要、保存処理未実行のため）

---

## 7. エラーハンドリング

### 7.1 例外クラス（exceptions.py に追加）

```python
class TemplateError(PMToolError):
    """テンプレート関連の基底例外"""
    pass

class TemplateNotFoundError(TemplateError):
    """テンプレートが存在しない"""
    def __init__(self, template_id: Optional[int] = None, name: Optional[str] = None):
        if template_id:
            msg = f"Template ID {template_id} not found"
        elif name:
            msg = f"Template '{name}' not found"
        else:
            msg = "Template not found"
        super().__init__(msg)

class TemplateNameConflictError(TemplateError):
    """テンプレート名が既に存在する"""
    def __init__(self, name: str):
        super().__init__(f"Template name '{name}' already exists")
        self.name = name

class TemplateValidationError(TemplateError):
    """テンプレートのバリデーションエラー"""
    pass
```

### 7.2 エラーハンドリング方針

**UI層での処理:**
- すべての例外をキャッチし、ユーザーフレンドリーなメッセージを表示
- 確認画面での重複チェック時は、保存ボタンを無効化

**ロジック層での処理:**
- 適切な例外を発生させる
- エラーメッセージは明確で、対処方法を示唆する

**トランザクション管理:**
- 例外発生時は自動的にロールバック（own_connパターン）
- DB整合性を必ず維持

---

## 8. トランザクション設計

### 8.1 own_conn パターンの採用

既存の`Repository`、`DependencyManager`と同様に、`TemplateManager`もown_connパターンを採用します。

```python
def save_template(
    self,
    subproject_id: int,
    name: str,
    description: Optional[str] = None,
    include_tasks: bool = False,
    conn: Optional[sqlite3.Connection] = None
) -> SaveTemplateResult:
    own_conn = False
    if conn is None:
        conn = self.db.connect()
        own_conn = True

    try:
        # ... DB操作 ...

        if own_conn:
            conn.commit()
        return SaveTemplateResult(template=template, external_dependencies=warnings)
    except Exception as e:
        if own_conn:
            conn.rollback()
        raise
    finally:
        if own_conn:
            conn.close()
```

**利点:**
- 単独呼び出し時は自動的にトランザクション管理
- 親トランザクション内から呼び出された場合は、同一トランザクション内で実行
- トランザクション境界の明確化

### 8.2 複数DB操作のアトミック性保証

**apply_template の例:**
```python
def apply_template(self, template_id: int, project_id: int, ..., conn=None) -> int:
    own_conn = False
    if conn is None:
        conn = self.db.connect()
        own_conn = True

    try:
        # 1. SubProject作成
        new_sp_id = self.repo.add_subproject(..., conn=conn)

        # 2. Task作成（ループ）
        for template_task in template_tasks:
            task_id = self.repo.add_task(..., conn=conn)
            # IDマッピング構築

        # 3. SubTask作成（ループ）
        for template_subtask in template_subtasks:
            subtask_id = self.repo.add_subtask(..., conn=conn)

        # 4. 依存関係作成（ループ）
        for template_dep in template_dependencies:
            self.dep_manager.add_task_dependency(..., conn=conn)

        if own_conn:
            conn.commit()
        return new_sp_id
    except Exception as e:
        if own_conn:
            conn.rollback()
        raise
    finally:
        if own_conn:
            conn.close()
```

**重要:**
- すべてのDB操作に同一の`conn`を渡す
- エラー発生時は全体がロールバック
- データ整合性を保証

---

## 9. テスト観点

### 9.1 ユニットテスト

**save_template のテストケース:**
1. 正常系:
   - include_tasks=False（SubProjectのみ保存）
   - include_tasks=True（Task/SubTask/依存関係含む）
2. 異常系:
   - SubProjectが存在しない → `SubProjectNotFoundError`
   - テンプレート名が重複 → `TemplateNameConflictError`
3. エッジケース:
   - 外部依存が存在する場合（警告のみ、保存は成功）
   - Task数が0の場合
   - 依存関係が複雑な場合（サイクルなし確認）

**apply_template のテストケース:**
1. 正常系:
   - include_tasks=False（SubProjectのみ作成）
   - include_tasks=True（Task/SubTask/依存関係含む）
   - ステータスがすべてUNSETで初期化されることを確認
   - 依存関係が正しく再接続されることを確認
2. 異常系:
   - テンプレートが存在しない → `TemplateNotFoundError`
   - Projectが存在しない → `ProjectNotFoundError`
3. エッジケース:
   - Task数が多い場合（パフォーマンス確認）
   - 依存関係が複雑な場合（DAG制約維持確認）

**dry_run のテストケース:**
1. 正常系:
   - 件数サマリが正確に計算される
   - 1階層ツリーが正しく生成される
2. エッジケース:
   - Task数が0の場合
   - SubTaskがないTaskの場合

### 9.2 統合テスト

**シナリオ1: テンプレート保存→適用の一連の流れ**
1. SubProjectを作成（Task + SubTask + 依存関係含む）
2. テンプレートとして保存（include_tasks=True）
3. dry-run実行、結果確認
4. 別Projectに適用
5. 作成されたSubProjectの構造を検証
6. ステータスがすべてUNSETであることを確認
7. 依存関係が正しく再接続されていることを確認

**シナリオ2: 外部依存がある場合の警告**
1. 外部依存を持つSubProjectを作成
2. テンプレートとして保存
3. 警告が表示されることを確認
4. テンプレート適用時、外部依存が再現されないことを確認

**シナリオ3: include_tasks=False の場合**
1. Task/SubTask/依存関係を持つSubProjectを作成
2. テンプレートとして保存（include_tasks=False）
3. 適用時、SubProjectのみ作成されることを確認
4. Task/SubTask/依存関係が作成されないことを確認

### 9.3 パフォーマンステスト

**テスト対象:**
- Task数100、SubTask数500の大規模テンプレート
- 保存時間: 2秒以内（目標値、参考）
- 適用時間: 5秒以内（目標値、参考）

**注記:**
- 上記の時間目標は参考値であり、Phase 5の必須受入条件（AC）ではない
- パフォーマンス回帰を監視するための指標として使用
- 実際のパフォーマンスは環境に依存するため、目標未達でもPhase 5完了を妨げない

---

## 10. 実装の優先順位

### Phase 5 での実装順序

**P5-07: テンプレート保存ロジック**
1. DB スキーマ追加（`scripts/init_db.sql`）
2. データモデル追加（`src/pmtool/models.py`）
3. 例外クラス追加（`src/pmtool/exceptions.py`）
4. `TemplateManager.save_template()` 実装
5. `TemplateManager._detect_external_dependencies()` 実装
6. ユニットテスト作成

**P5-08: テンプレート一覧・詳細ロジック**
1. `TemplateManager.list_templates()` 実装
2. `TemplateManager.get_template()` 実装
3. `TemplateManager.get_template_by_name()` 実装
4. `TemplateManager.delete_template()` 実装
5. ユニットテスト作成

**P5-09: テンプレート適用ロジック**
1. `TemplateManager.dry_run()` 実装
2. `DryRunResult` データクラス追加
3. `TemplateManager.apply_template()` 実装
4. IDマッピング処理実装
5. ユニットテスト作成
6. 統合テスト作成

---

## 11. 補足事項

### 11.1 将来拡張の考慮

**Phase 6以降で検討する機能:**
- テンプレートのexport/import（JSON/YAML形式）
- テンプレートの編集機能（保存後の内容変更）
- テンプレートのバージョン管理
- 適用時ステータスの選択式（UNSET / NOT_STARTED / コピー）
- dry-run表示の詳細化（完全ツリー、依存関係個別列挙）

**拡張性を考慮した設計:**
- `include_tasks`フィールドは将来の拡張に備えている
- DBスキーマは拡張可能（新フィールド追加が容易）
- API設計は将来のパラメータ追加を考慮（オプション引数）

### 11.2 CLI版との互換性

**Phase 5での方針:**
- Textual版は別プログラム/別系統
- ただし、ビジネスロジック層（`TemplateManager`）は共有可能
- CLI版でテンプレート機能を実装する場合、同じ`TemplateManager`を使用

**CLI版コマンド案（Phase 6以降）:**
```bash
pmtool template save <subproject_id> --name "テンプレート名" [--include-tasks]
pmtool template list
pmtool template show <template_id>
pmtool template apply <template_id> --project <project_id> [--dry-run]
pmtool template delete <template_id>
```

---

## 変更履歴

### v1.1.1 (2026-01-21)
**ChatGPT再レビュー指摘（条件付き承認）を反映**

**必須修正（2件）:**
1. 8.1節のトランザクション設計サンプルの戻り値型を統一
   - `-> Template` → `-> SaveTemplateResult`
   - 戻り値を`SaveTemplateResult(template=template, external_dependencies=warnings)`に修正

2. apply_template の文言統一
   - 「`include_tasks=True`の場合」→「`template.include_tasks=True`の場合」
   - apply_templateにinclude_tasks引数は無いため、template属性として参照

**推奨修正（2件）:**
3. 外部依存警告の重複排除方針を追記（6.3節）
   - Phase 5では重複排除は行わず、そのまま返す
   - 将来的に重複が問題となる場合は、set化やユニーク化を検討

4. パフォーマンス目標の注記を追加（9.3節）
   - 時間目標は参考値であり、Phase 5の必須AC（受入条件）ではない
   - パフォーマンス回帰監視用の指標として使用

### v1.1.0 (2026-01-21)
**ChatGPTレビュー指摘（Must fix 4件 + Should fix 2件）を反映**

**Must fix対応:**
1. テンプレート名重複チェックの責務分離を明確化
   - UI側: 確認画面で事前チェック（`get_template_by_name()`）
   - ロジック層: UNIQUE制約違反を最終防衛として検出、`TemplateNameConflictError`に変換
   - 5.1節に責務分離セクションを追加

2. 外部依存の扱いと戻り値設計を修正
   - `SaveTemplateResult`型を新設（`Template` + `external_dependencies`）
   - `ExternalDependencyWarning`データクラス追加（from/to task名、direction含む）
   - 2.1節「方針4」を詳細化（保存しない、警告情報を返す、適用時再現しない、を明文化）
   - 6.3節に外部依存検出処理の詳細とUI側責務を追加

3. save_template()の戻り値型を修正
   - 戻り値: `Template` → `SaveTemplateResult`
   - 外部依存警告を戻り値に明示的に含める
   - UI側は`has_warnings`で判定し、警告表示 + ユーザー確認を実施

4. テンプレート系テーブル操作の責務を明確化
   - `TemplateRepository`クラスを新設（`repository.py`に追加）
   - すべてのテンプレート系テーブルアクセスを`TemplateRepository`に集約
   - 4.3節に`TemplateRepository`のAPI仕様を追加
   - SQL直書きを避け、保守性を向上

**Should fix対応:**
5. SQLiteのBOOLEAN表現を統一
   - `include_tasks`フィールドを`BOOLEAN`→`INTEGER`に修正
   - 注記追加: SQLiteはBOOLEAN型を持たないため、INTEGER型で0/1を使用

6. apply時の例外処理方針を明記
   - `CycleDetectedError`について:
     - 理論上発生しないが、データ破損・バグ・将来拡張での混入可能性を考慮
     - 発生時はトランザクションロールバック + 例外再送出
   - `DatabaseError`について:
     - すべてのDB操作エラーを補足、ロールバックしてデータ整合性を保証
   - 5.7節に「例外処理方針」セクションを追加

### v1.0.0 (2026-01-21)
- 初版作成（Phase 5確定事項を反映）

---

**以上**
