# DB設計書 v2.1（最終版）

**作成日**: 2026-01-16
**更新日**: 2026-01-16（SQLite UNIQUE+NULL問題対応）
**対象**: プロジェクト管理ツール
**DB**: SQLite
**前提**: `1_プロジェクト管理ツール_ClaudeCode仕様書.md` および `3_プロジェクト管理ツール_実装方針確定メモ.md`

---

## 変更履歴

### v2.1（2026-01-16）
- **重要**: SQLiteの UNIQUE + NULL 問題に対応
  - `tasks`: 部分UNIQUEインデックスで NULL ケースを個別に制約
  - `subprojects`: 部分UNIQUEインデックスで NULL ケースを個別に制約
- `order_index` に `CHECK(order_index >= 0)` を追加
- `updated_at` はアプリ側で更新することを明記

### v2（2026-01-16）
- 親子関係のFKを `ON DELETE RESTRICT` に変更（D6準拠）
- 依存関係のFKは `ON DELETE CASCADE` を維持
- `order_index` は 0 始まりに統一
- タイムスタンプは UTC 固定を明記
- 論理削除は MVP では実装しない方針を明記

---

## 1. 概要

本ドキュメントは、プロジェクト管理ツールのデータベース設計を定義する。

### 設計方針
- SQLite標準の機能のみを使用
- 外部キー制約を有効化（`PRAGMA foreign_keys = ON`）
- **親子関係は RESTRICT（アプリが明示的に削除制御）**
- **依存関係は CASCADE（削除時の自動クリーンアップ）**
- **SQLiteの UNIQUE + NULL 問題に対応（部分UNIQUEインデックス）**
- トランザクションによる整合性保証
- 将来の拡張性を考慮（SubProjectの入れ子対応など）

### FK削除動作の方針

| 関係種別 | ON DELETE | 理由 |
|---------|-----------|------|
| 親子関係（Project→SubProject等） | **RESTRICT** | D6「子持ち削除デフォルト禁止」に準拠。アプリが明示的に削除制御 |
| 依存関係（Task→Task等） | **CASCADE** | ノード削除時に依存関係も自動削除が自然 |

### タイムスタンプ方針
- SQLiteの `datetime('now')` は UTC で記録
- アプリケーション層でローカルタイムゾーンに変換して表示
- `updated_at` は自動更新されないため、**アプリケーション側で明示的に更新する**

---

## 2. テーブル一覧

| テーブル名 | 説明 |
|-----------|------|
| `projects` | プロジェクト |
| `subprojects` | サブプロジェクト（フォルダ相当） |
| `tasks` | タスク |
| `subtasks` | サブタスク |
| `task_dependencies` | タスク間依存関係 |
| `subtask_dependencies` | サブタスク間依存関係 |
| `templates` | テンプレート定義（Phase 3） |
| `template_nodes` | テンプレート内のノード情報（Phase 3） |
| `schema_version` | スキーマバージョン管理 |

**注**: `templates` および `template_nodes` は Phase 3 で実装予定。Phase 0/1 では作成しない。

---

## 3. テーブル定義

### 3.1 projects

**説明**: プロジェクトを管理するテーブル

```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    order_index INTEGER NOT NULL CHECK(order_index >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_projects_order ON projects(order_index);
```

**カラム説明**:
- `id`: プロジェクトID（主キー）
- `name`: プロジェクト名（全体でユニーク）
- `description`: プロジェクトの説明（任意）
- `order_index`: 表示順（整数、0始まり、手動制御）
- `created_at`: 作成日時（UTC）
- `updated_at`: 更新日時（UTC、アプリ側で更新）

**制約**:
- `name`は全体でユニーク
- `order_index`は0始まり（CHECK制約で保証）

---

### 3.2 subprojects

**説明**: サブプロジェクト（フォルダ相当）を管理するテーブル

```sql
CREATE TABLE subprojects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    parent_subproject_id INTEGER DEFAULT NULL,
    name TEXT NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL CHECK(order_index >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    FOREIGN KEY (parent_subproject_id) REFERENCES subprojects(id) ON DELETE RESTRICT
);

-- SQLiteの UNIQUE + NULL 問題に対応: 部分UNIQUEインデックス
-- Project直下のSubProject（parent_subproject_id = NULL）
CREATE UNIQUE INDEX idx_subprojects_unique_project_direct
    ON subprojects(project_id, name)
    WHERE parent_subproject_id IS NULL;

-- 入れ子SubProject（parent_subproject_id IS NOT NULL）
CREATE UNIQUE INDEX idx_subprojects_unique_nested
    ON subprojects(project_id, parent_subproject_id, name)
    WHERE parent_subproject_id IS NOT NULL;

CREATE INDEX idx_subprojects_project ON subprojects(project_id);
CREATE INDEX idx_subprojects_parent ON subprojects(parent_subproject_id);
CREATE INDEX idx_subprojects_order ON subprojects(project_id, parent_subproject_id, order_index);
```

**カラム説明**:
- `id`: サブプロジェクトID（主キー）
- `project_id`: 所属するプロジェクトID
- `parent_subproject_id`: 親サブプロジェクトID（NULL = Project直下、将来の入れ子対応用）
- `name`: サブプロジェクト名
- `description`: 説明（任意）
- `order_index`: 表示順（0始まり、同一親配下で管理）
- `created_at`: 作成日時（UTC）
- `updated_at`: 更新日時（UTC、アプリ側で更新）

**制約**:
- **部分UNIQUEインデックス**で名前の重複を防止:
  - Project直下: `(project_id, name)` がユニーク（`parent_subproject_id IS NULL`）
  - 入れ子: `(project_id, parent_subproject_id, name)` がユニーク（`parent_subproject_id IS NOT NULL`）
- MVP実装では`parent_subproject_id`は常にNULL（1階層のみ）
- 将来の入れ子拡張に備えたカラム設計

**FK削除動作**:
- `ON DELETE RESTRICT`: 子SubProject/Taskが存在する場合、削除は拒否される
- アプリケーション層で明示的な連鎖削除を実装

---

### 3.3 tasks

**説明**: タスクを管理するテーブル

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    subproject_id INTEGER DEFAULT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'UNSET',
    order_index INTEGER NOT NULL CHECK(order_index >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    FOREIGN KEY (subproject_id) REFERENCES subprojects(id) ON DELETE RESTRICT,
    CHECK(status IN ('UNSET', 'NOT_STARTED', 'IN_PROGRESS', 'DONE'))
);

-- SQLiteの UNIQUE + NULL 問題に対応: 部分UNIQUEインデックス
-- Project直下のTask（subproject_id = NULL）
CREATE UNIQUE INDEX idx_tasks_unique_project_direct
    ON tasks(project_id, name)
    WHERE subproject_id IS NULL;

-- SubProject配下のTask（subproject_id IS NOT NULL）
CREATE UNIQUE INDEX idx_tasks_unique_subproject
    ON tasks(project_id, subproject_id, name)
    WHERE subproject_id IS NOT NULL;

CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_subproject ON tasks(subproject_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_order ON tasks(project_id, subproject_id, order_index);
```

**カラム説明**:
- `id`: タスクID（主キー）
- `project_id`: 所属するプロジェクトID
- `subproject_id`: 所属するサブプロジェクトID（NULL = Project直下）
- `name`: タスク名
- `description`: タスクの説明（任意）
- `status`: ステータス（UNSET, NOT_STARTED, IN_PROGRESS, DONE）
- `order_index`: 表示順（0始まり）
- `created_at`: 作成日時（UTC）
- `updated_at`: 更新日時（UTC、アプリ側で更新）

**制約**:
- **部分UNIQUEインデックス**で名前の重複を防止:
  - Project直下: `(project_id, name)` がユニーク（`subproject_id IS NULL`）
  - SubProject配下: `(project_id, subproject_id, name)` がユニーク（`subproject_id IS NOT NULL`）
- TaskはProject直下（subproject_id = NULL）またはSubProject配下のいずれか一箇所にのみ所属
- `status`はCHECK制約で定義された値のみ許可

**FK削除動作**:
- `ON DELETE RESTRICT`: 子SubTaskが存在する場合、Task削除は拒否される
- アプリケーション層で明示的な連鎖削除を実装

---

### 3.4 subtasks

**説明**: サブタスクを管理するテーブル

```sql
CREATE TABLE subtasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'UNSET',
    order_index INTEGER NOT NULL CHECK(order_index >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE RESTRICT,
    UNIQUE(task_id, name),
    CHECK(status IN ('UNSET', 'NOT_STARTED', 'IN_PROGRESS', 'DONE'))
);

CREATE INDEX idx_subtasks_task ON subtasks(task_id);
CREATE INDEX idx_subtasks_status ON subtasks(status);
CREATE INDEX idx_subtasks_order ON subtasks(task_id, order_index);
```

**カラム説明**:
- `id`: サブタスクID（主キー）
- `task_id`: 所属するタスクID
- `name`: サブタスク名
- `description`: サブタスクの説明（任意）
- `status`: ステータス（UNSET, NOT_STARTED, IN_PROGRESS, DONE）
- `order_index`: 表示順（0始まり、同一Task配下）
- `created_at`: 作成日時（UTC）
- `updated_at`: 更新日時（UTC、アプリ側で更新）

**制約**:
- `task_id + name`の組み合わせでユニーク
- `status`はCHECK制約で定義された値のみ許可

**FK削除動作**:
- `ON DELETE RESTRICT`: 依存関係が存在する場合、SubTask削除は拒否される可能性
- アプリケーション層で依存関係の橋渡し処理を実装

---

### 3.5 task_dependencies

**説明**: タスク間の依存関係を管理するテーブル（Finish-to-Start）

```sql
CREATE TABLE task_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    predecessor_id INTEGER NOT NULL,
    successor_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (predecessor_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (successor_id) REFERENCES tasks(id) ON DELETE CASCADE,
    UNIQUE(predecessor_id, successor_id),
    CHECK(predecessor_id != successor_id)
);

CREATE INDEX idx_task_deps_predecessor ON task_dependencies(predecessor_id);
CREATE INDEX idx_task_deps_successor ON task_dependencies(successor_id);
```

**カラム説明**:
- `id`: 依存関係ID（主キー）
- `predecessor_id`: 先行タスクID
- `successor_id`: 後続タスクID
- `created_at`: 作成日時（UTC）

**制約**:
- `predecessor_id + successor_id`の組み合わせでユニーク
- 自己参照禁止（CHECK制約）
- 同一Project内のTaskのみ依存可能（アプリケーション層でチェック）
- DAG制約（循環禁止）はアプリケーション層でチェック

**FK削除動作**:
- `ON DELETE CASCADE`: Task削除時、関連する依存関係も自動削除
- アプリケーション層で削除前に橋渡し再接続処理を実装（D6準拠）

---

### 3.6 subtask_dependencies

**説明**: サブタスク間の依存関係を管理するテーブル（Finish-to-Start）

```sql
CREATE TABLE subtask_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    predecessor_id INTEGER NOT NULL,
    successor_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (predecessor_id) REFERENCES subtasks(id) ON DELETE CASCADE,
    FOREIGN KEY (successor_id) REFERENCES subtasks(id) ON DELETE CASCADE,
    UNIQUE(predecessor_id, successor_id),
    CHECK(predecessor_id != successor_id)
);

CREATE INDEX idx_subtask_deps_predecessor ON subtask_dependencies(predecessor_id);
CREATE INDEX idx_subtask_deps_successor ON subtask_dependencies(successor_id);
```

**カラム説明**:
- `id`: 依存関係ID（主キー）
- `predecessor_id`: 先行サブタスクID
- `successor_id`: 後続サブタスクID
- `created_at`: 作成日時（UTC）

**制約**:
- `predecessor_id + successor_id`の組み合わせでユニーク
- 自己参照禁止（CHECK制約）
- 同一Task内のSubTaskのみ依存可能（アプリケーション層でチェック）
- DAG制約（循環禁止）はアプリケーション層でチェック

**FK削除動作**:
- `ON DELETE CASCADE`: SubTask削除時、関連する依存関係も自動削除
- アプリケーション層で削除前に橋渡し再接続処理を実装（D6準拠）

---

### 3.7 templates（Phase 3）

**説明**: テンプレート定義を管理するテーブル（Phase 3で実装）

```sql
-- Phase 3 で作成
CREATE TABLE templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    base_type TEXT NOT NULL,
    base_id INTEGER NOT NULL,
    include_tasks BOOLEAN NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK(base_type IN ('project', 'subproject', 'task'))
);

CREATE INDEX idx_templates_name ON templates(name);
```

**注**: Phase 0/1 では作成しない。Phase 3 で追加予定。

---

### 3.8 template_nodes（Phase 3）

**説明**: テンプレート内のノード情報を管理するテーブル（Phase 3で実装）

```sql
-- Phase 3 で作成
CREATE TABLE template_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    node_type TEXT NOT NULL,
    original_id INTEGER NOT NULL,
    parent_original_id INTEGER DEFAULT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    order_index INTEGER NOT NULL CHECK(order_index >= 0),
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE,
    CHECK(node_type IN ('project', 'subproject', 'task', 'subtask')),
    CHECK(status IN ('UNSET', 'NOT_STARTED', 'IN_PROGRESS', 'DONE'))
);

CREATE INDEX idx_template_nodes_template ON template_nodes(template_id);
CREATE INDEX idx_template_nodes_original ON template_nodes(template_id, original_id);
```

**注**: Phase 0/1 では作成しない。Phase 3 で追加予定。

---

### 3.9 schema_version

**説明**: スキーマバージョン管理テーブル

```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 初期バージョンを挿入
INSERT INTO schema_version (version) VALUES (1);
```

**カラム説明**:
- `version`: スキーマバージョン（主キー）
- `applied_at`: 適用日時（UTC）

**用途**:
- マイグレーション管理
- バージョン互換性チェック

---

## 4. 初期化SQL（Phase 0 用）

### 4.1 データベース初期化スクリプト

**Phase 0/1 で作成するテーブル**:
- `schema_version`
- `projects`
- `subprojects`
- `tasks`
- `subtasks`
- `task_dependencies`
- `subtask_dependencies`

**Phase 3 で追加するテーブル**:
- `templates`
- `template_nodes`
- `template_dependencies`（依存関係保存用）

```sql
-- 外部キー制約を有効化
PRAGMA foreign_keys = ON;

-- スキーマバージョンテーブル作成
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 初期バージョン挿入
INSERT INTO schema_version (version) VALUES (1);

-- projects テーブル作成
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    order_index INTEGER NOT NULL CHECK(order_index >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_projects_order ON projects(order_index);

-- subprojects テーブル作成
CREATE TABLE subprojects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    parent_subproject_id INTEGER DEFAULT NULL,
    name TEXT NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL CHECK(order_index >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    FOREIGN KEY (parent_subproject_id) REFERENCES subprojects(id) ON DELETE RESTRICT
);

-- 部分UNIQUEインデックス（UNIQUE + NULL 問題対応）
CREATE UNIQUE INDEX idx_subprojects_unique_project_direct
    ON subprojects(project_id, name)
    WHERE parent_subproject_id IS NULL;

CREATE UNIQUE INDEX idx_subprojects_unique_nested
    ON subprojects(project_id, parent_subproject_id, name)
    WHERE parent_subproject_id IS NOT NULL;

CREATE INDEX idx_subprojects_project ON subprojects(project_id);
CREATE INDEX idx_subprojects_parent ON subprojects(parent_subproject_id);
CREATE INDEX idx_subprojects_order ON subprojects(project_id, parent_subproject_id, order_index);

-- tasks テーブル作成
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    subproject_id INTEGER DEFAULT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'UNSET',
    order_index INTEGER NOT NULL CHECK(order_index >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    FOREIGN KEY (subproject_id) REFERENCES subprojects(id) ON DELETE RESTRICT,
    CHECK(status IN ('UNSET', 'NOT_STARTED', 'IN_PROGRESS', 'DONE'))
);

-- 部分UNIQUEインデックス（UNIQUE + NULL 問題対応）
CREATE UNIQUE INDEX idx_tasks_unique_project_direct
    ON tasks(project_id, name)
    WHERE subproject_id IS NULL;

CREATE UNIQUE INDEX idx_tasks_unique_subproject
    ON tasks(project_id, subproject_id, name)
    WHERE subproject_id IS NOT NULL;

CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_subproject ON tasks(subproject_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_order ON tasks(project_id, subproject_id, order_index);

-- subtasks テーブル作成
CREATE TABLE subtasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'UNSET',
    order_index INTEGER NOT NULL CHECK(order_index >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE RESTRICT,
    UNIQUE(task_id, name),
    CHECK(status IN ('UNSET', 'NOT_STARTED', 'IN_PROGRESS', 'DONE'))
);

CREATE INDEX idx_subtasks_task ON subtasks(task_id);
CREATE INDEX idx_subtasks_status ON subtasks(status);
CREATE INDEX idx_subtasks_order ON subtasks(task_id, order_index);

-- task_dependencies テーブル作成
CREATE TABLE task_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    predecessor_id INTEGER NOT NULL,
    successor_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (predecessor_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (successor_id) REFERENCES tasks(id) ON DELETE CASCADE,
    UNIQUE(predecessor_id, successor_id),
    CHECK(predecessor_id != successor_id)
);

CREATE INDEX idx_task_deps_predecessor ON task_dependencies(predecessor_id);
CREATE INDEX idx_task_deps_successor ON task_dependencies(successor_id);

-- subtask_dependencies テーブル作成
CREATE TABLE subtask_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    predecessor_id INTEGER NOT NULL,
    successor_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (predecessor_id) REFERENCES subtasks(id) ON DELETE CASCADE,
    FOREIGN KEY (successor_id) REFERENCES subtasks(id) ON DELETE CASCADE,
    UNIQUE(predecessor_id, successor_id),
    CHECK(predecessor_id != successor_id)
);

CREATE INDEX idx_subtask_deps_predecessor ON subtask_dependencies(predecessor_id);
CREATE INDEX idx_subtask_deps_successor ON subtask_dependencies(successor_id);
```

---

## 5. DB制約とアプリケーション制約の責務分離

### 5.1 DB制約（SQLiteで強制）

- 外部キー制約（参照整合性）
- **部分UNIQUEインデックス（名前の重複禁止、NULL対応）**
- CHECK制約（ステータス値の妥当性、order_index >= 0）
- NOT NULL制約（必須カラム）
- 自己参照禁止（依存関係）
- **親子関係の削除制限（RESTRICT）**

### 5.2 アプリケーション制約（Pythonコードで強制）

- DAG制約（循環検出）
- レイヤ跨ぎ依存の禁止
- 同一Project/Task内の依存関係チェック
- DONE遷移条件チェック
- **子ノード存在チェック（削除前）**
- **依存関係の橋渡し再接続（削除時）**
- **明示的な連鎖削除（強制削除フラグ）**
- テンプレート外部参照チェック
- **updated_at の更新**

**理由**:
- DAG検証は再帰的探索が必要でSQLでは困難
- 階層制約は複数テーブル横断のため、アプリケーション層が適切
- ステータス遷移ロジックはビジネスルールのため、柔軟性を保つ
- **削除制御はD6の安全要件を満たすため、アプリケーション層で詳細制御**
- **SQLiteはトリガーなしでupdated_atを自動更新できないため、アプリ側で管理**

---

## 6. 削除操作の実装方針（D6準拠）

### 6.1 通常削除（デフォルト）

**手順**:
1. 子ノードの存在チェック
   - SubProjectがある場合 → エラー
   - Taskがある場合 → エラー
   - SubTaskがある場合 → エラー
2. 依存関係の橋渡し処理
   - 直接先行ノードを取得
   - 直接後続ノードを取得
   - 先行 × 後続の組み合わせで新規依存を作成
3. ノード削除
   - 依存関係は CASCADE で自動削除

**コード例（疑似コード）**:
```python
def delete_task(task_id):
    # 1. 子チェック
    if has_subtasks(task_id):
        raise Error("SubTaskが存在するため削除できません")

    # 2. 橋渡し
    predecessors = get_predecessors(task_id)
    successors = get_successors(task_id)

    with transaction:
        # 依存関係の橋渡し
        for pred in predecessors:
            for succ in successors:
                # 循環チェック
                if creates_cycle(pred, succ):
                    raise Error("循環依存が発生します")
                create_dependency(pred, succ)

        # Task削除（依存関係はCASCADEで自動削除）
        db.execute("DELETE FROM tasks WHERE id = ?", task_id)

        # updated_at は親の更新時にアプリ側で設定
```

### 6.2 連鎖削除（強制削除フラグ付き）

**手順**:
1. 削除対象のノードとすべての子孫を特定
2. dry-run プレビュー表示（削除されるノード一覧）
3. ユーザー確認
4. トランザクション内で削除実行

**コード例（疑似コード）**:
```python
def cascade_delete_project(project_id, force=False, dry_run=False):
    # 削除対象の収集
    targets = collect_all_descendants(project_id)

    if dry_run:
        return targets  # プレビュー

    if not force:
        raise Error("強制削除フラグが必要です")

    with transaction:
        # 依存関係の橋渡し（各Taskごと）
        for task in targets.tasks:
            bridge_dependencies(task)

        # 子から順に削除
        for subtask in targets.subtasks:
            db.execute("DELETE FROM subtasks WHERE id = ?", subtask.id)
        for task in targets.tasks:
            db.execute("DELETE FROM tasks WHERE id = ?", task.id)
        for subproject in targets.subprojects:
            db.execute("DELETE FROM subprojects WHERE id = ?", subproject.id)
        db.execute("DELETE FROM projects WHERE id = ?", project_id)
```

---

## 7. インデックス戦略

### 7.1 主要なクエリパターン

**Project一覧取得（order順）**:
```sql
SELECT * FROM projects ORDER BY order_index;
-- 使用インデックス: idx_projects_order
```

**SubProject一覧取得（Project配下、order順）**:
```sql
SELECT * FROM subprojects
WHERE project_id = ? AND parent_subproject_id IS NULL
ORDER BY order_index;
-- 使用インデックス: idx_subprojects_order
```

**Task一覧取得（SubProject配下、order順）**:
```sql
SELECT * FROM tasks
WHERE project_id = ? AND subproject_id = ?
ORDER BY order_index;
-- 使用インデックス: idx_tasks_order
```

**依存関係取得（先行・後続）**:
```sql
-- 先行タスク取得
SELECT t.* FROM tasks t
JOIN task_dependencies d ON t.id = d.predecessor_id
WHERE d.successor_id = ?;
-- 使用インデックス: idx_task_deps_successor

-- 後続タスク取得
SELECT t.* FROM tasks t
JOIN task_dependencies d ON t.id = d.successor_id
WHERE d.predecessor_id = ?;
-- 使用インデックス: idx_task_deps_predecessor
```

**ステータス検索**:
```sql
SELECT * FROM tasks WHERE status = 'IN_PROGRESS';
-- 使用インデックス: idx_tasks_status
```

**子ノード存在チェック**:
```sql
-- SubProject の子チェック
SELECT COUNT(*) FROM tasks WHERE subproject_id = ?;
-- 使用インデックス: idx_tasks_subproject

-- Task の子チェック
SELECT COUNT(*) FROM subtasks WHERE task_id = ?;
-- 使用インデックス: idx_subtasks_task
```

**名前重複チェック（Project直下のTask）**:
```sql
SELECT COUNT(*) FROM tasks
WHERE project_id = ? AND subproject_id IS NULL AND name = ?;
-- 使用インデックス: idx_tasks_unique_project_direct（部分UNIQUE）
```

---

## 8. トランザクション方針

### 8.1 基本方針

- すべての書き込み操作はトランザクション内で実行
- 読み込みのみの操作はトランザクション不要
- 複数テーブルにまたがる操作は必ずトランザクションで保護
- **削除操作は必ず橋渡し処理とセットでトランザクション化**
- **updated_at の更新もトランザクション内で実施**

### 8.2 トランザクション例

**ノード削除（依存関係の橋渡し）**:
```python
with db.transaction():
    # 1. 子ノード存在チェック
    if has_children(node_id):
        raise Error("子ノードが存在します")

    # 2. 削除対象の先行・後続を取得
    predecessors = get_predecessors(node_id)
    successors = get_successors(node_id)

    # 3. 橋渡し再接続
    for pred in predecessors:
        for succ in successors:
            # 循環チェック
            if creates_cycle(pred, succ):
                raise Error("循環依存が発生します")
            create_dependency(pred, succ)

    # 4. ノード削除（依存関係はCASCADEで自動削除）
    delete_node(node_id)
```

**ステータス変更（DONE遷移チェック + updated_at更新）**:
```python
with db.transaction():
    # 1. DONE遷移条件チェック
    if new_status == 'DONE':
        # 先行ノードがすべてDONEか
        predecessors = get_predecessors(node_id)
        if not all(p.status == 'DONE' for p in predecessors):
            raise Error("先行ノードが未完了です")

        # 親Taskの場合、子SubTaskがすべてDONEか
        if is_task(node_id):
            subtasks = get_subtasks(node_id)
            if subtasks and not all(s.status == 'DONE' for s in subtasks):
                raise Error("子SubTaskが未完了です")

    # 2. ステータス更新 + updated_at更新
    now = datetime.utcnow().isoformat()
    update_status(node_id, new_status, updated_at=now)
```

**並び順変更（order_index更新 + updated_at更新）**:
```python
with db.transaction():
    # 複数ノードのorder_indexを一括更新
    for node, new_order in reorder_list:
        now = datetime.utcnow().isoformat()
        db.execute(
            "UPDATE tasks SET order_index = ?, updated_at = ? WHERE id = ?",
            (new_order, now, node.id)
        )
```

---

## 9. マイグレーション方針

### 9.1 スキーマ変更時の手順

1. `schema_version`テーブルで現在のバージョン確認
2. 必要なマイグレーションSQLを順次実行
3. `schema_version`テーブルを更新

### 9.2 マイグレーション例

**Phase 3: テンプレートテーブル追加（v1 → v2）**:
```sql
-- バージョンチェック
SELECT version FROM schema_version;

-- マイグレーション実行
CREATE TABLE templates ( ... );
CREATE TABLE template_nodes ( ... );
CREATE TABLE template_dependencies ( ... );

-- バージョン更新
INSERT INTO schema_version (version) VALUES (2);
```

---

## 10. 設計方針の確定事項

### ✅ ChatGPT レビュー v2.1 対応済み

1. **FK削除動作**: 親子関係は RESTRICT、依存関係は CASCADE
2. **UNIQUE + NULL 問題対応**: 部分UNIQUEインデックスで解決
3. **order_index**: 0始まり + CHECK制約
4. **タイムスタンプ**: UTC固定（`datetime('now')`）
5. **updated_at**: アプリ側で明示的に更新
6. **論理削除**: MVPでは実装しない
7. **テンプレートテーブル**: Phase 3 で追加
8. **削除制御**: アプリケーション層で子チェック + 橋渡し処理

### ⚠️ アプリケーション層で実装必須の制約

- DAG循環検出
- レイヤ跨ぎ依存の禁止
- 同一Project/Task内の依存関係チェック
- DONE遷移条件チェック
- 子ノード存在チェック（削除前）
- 依存関係の橋渡し再接続（削除時）
- 明示的な連鎖削除（強制削除フラグ）
- **updated_at の更新（INSERT/UPDATE時）**

---

## 11. SQLite UNIQUE + NULL 問題の詳細

### 問題の背景

SQLiteでは、UNIQUE制約に含まれるカラムがNULLの場合、**NULL値は互いに異なるとみなされ**、重複チェックが機能しません。

**問題例**:
```sql
-- この制約では、subproject_id = NULL の行は重複可能
UNIQUE(project_id, subproject_id, name)

-- 以下が両方挿入できてしまう
INSERT INTO tasks (project_id, subproject_id, name) VALUES (1, NULL, 'Task A');
INSERT INTO tasks (project_id, subproject_id, name) VALUES (1, NULL, 'Task A');  -- エラーにならない
```

### 解決策: 部分UNIQUEインデックス

SQLiteの部分インデックス（Partial Index）を使用して、NULLケースを個別に制約します。

```sql
-- Project直下（subproject_id = NULL）のTaskは (project_id, name) でユニーク
CREATE UNIQUE INDEX idx_tasks_unique_project_direct
    ON tasks(project_id, name)
    WHERE subproject_id IS NULL;

-- SubProject配下（subproject_id IS NOT NULL）のTaskは (project_id, subproject_id, name) でユニーク
CREATE UNIQUE INDEX idx_tasks_unique_subproject
    ON tasks(project_id, subproject_id, name)
    WHERE subproject_id IS NOT NULL;
```

この方法により、公式仕様「同一階層内で名前重複禁止」が正しく実現されます。

---

## 12. 次のステップ

本DB設計書（v2.1）は **実装可能な最終版** です。

次の作業:

1. **Phase 0 実装開始**:
   - プロジェクト構造セットアップ
   - DB初期化スクリプト作成（本設計書の SQL を使用）
   - 基本的な接続確認
2. **Phase 1 実装**:
   - CRUD操作の実装
   - 依存関係管理
   - ステータス管理
   - 削除制御（橋渡し処理）
   - updated_at の自動更新ロジック

---

（以上）
