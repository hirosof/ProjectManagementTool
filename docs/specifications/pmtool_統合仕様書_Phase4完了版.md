# pmtool 統合仕様書（Phase 4 完了版）

**最終更新日:** 2026-01-20
**対象バージョン:** Phase 4 完了時点
**ドキュメント種別:** 統合仕様書（Phase 0-4の実装内容を統合）

---

## 目次

1. [概要](#1-概要)
2. [システムアーキテクチャ](#2-システムアーキテクチャ)
3. [データモデル](#3-データモデル)
4. [機能仕様](#4-機能仕様)
5. [コマンドリファレンス](#5-コマンドリファレンス)
6. [制約・ルール](#6-制約ルール)
7. [エラーハンドリング](#7-エラーハンドリング)
8. [テスト仕様](#8-テスト仕様)
9. [Phase 5 実装予定機能](#9-phase-5-実装予定機能)

---

## 1. 概要

### 1.1 目的

pmtool は、個人利用を前提とした階層型プロジェクト管理CLIツールです。DAG（有向非循環グラフ）制約による安全な依存関係管理と、厳密なステータス制御を特徴とします。

### 1.2 基本方針

- **拡張性・保守性を最優先**: モジュール分割、トランザクション整合性、データ整合性の厳密な維持
- **明示的な操作**: AI推測・自動補完を排除、ユーザーの明示的な指示のみで動作
- **段階的実装**: Phase 0-4で基盤・コア機能・CLI・拡張機能・品質向上を完了

### 1.3 実行環境

- **UI形式**: CLI（Command Line Interface）with Rich表示
- **実行環境**: ローカル（Windows/macOS/Linux）
- **データベース**: SQLite3（単一DBファイル `data/pmtool.db`）
- **言語**: Python 3.10+
- **主要ライブラリ**: Rich（表示装飾）、prompt_toolkit（対話的入力）

### 1.4 開発履歴

- **Phase 0**: DB設計、基盤構築（2026-01-15完了）
- **Phase 1**: ビジネスロジック層（CRUD、依存関係、ステータス管理）（2026-01-16完了）
- **Phase 2**: CLIインターフェース実装（2026-01-17完了）
- **Phase 3**: 拡張機能（UX改善、エラーメッセージ強化）（2026-01-18完了）
- **Phase 4**: 品質・安定性向上（テストカバレッジ80%、ユーザードキュメント整備）（2026-01-20完了）

---

## 2. システムアーキテクチャ

### 2.1 レイヤー構成

```
┌─────────────────────────────────────┐
│  CLI Layer (src/pmtool/tui/)        │
│  - cli.py: argparse entry point     │
│  - commands.py: command handlers    │
│  - display.py: Rich output          │
│  - input.py: interactive input      │
│  - formatters.py: status symbols    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Business Logic Layer (src/pmtool/) │
│  - repository.py: CRUD operations   │
│  - dependencies.py: DAG management  │
│  - status.py: status transitions    │
│  - validators.py: input validation  │
│  - doctor.py: integrity checks      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Data Layer                         │
│  - database.py: SQLite connection   │
│  - models.py: dataclass entities    │
│  - exceptions.py: custom errors     │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  SQLite Database (data/pmtool.db)   │
│  - projects, subprojects, tasks,    │
│    subtasks, dependencies           │
└─────────────────────────────────────┘
```

### 2.2 主要コンポーネント

#### 2.2.1 Database (database.py)
- SQLite接続管理（外部キー制約有効化）
- DB初期化（`scripts/init_db.sql`）
- トランザクション管理

#### 2.2.2 Repository (repository.py)
- CRUD操作（Project, SubProject, Task, SubTask）
- order_index自動管理（`MAX(order_index) + 1`）
- updated_at伝播（子→親への自動更新）
- 削除制御（通常削除、橋渡し削除、連鎖削除）

#### 2.2.3 DependencyManager (dependencies.py)
- 依存関係CRUD（Task間、SubTask間のみ）
- DAG検証（サイクル検出：DFS）
- レイヤー制約検証（cross-layer依存禁止）
- 橋渡し処理（bridge_dependencies）

#### 2.2.4 StatusManager (status.py)
- ステータス遷移管理
- DONE遷移条件検証（先行ノード + 子SubTask）
- dry-run対応

#### 2.2.5 CLI Commands (tui/commands.py)
- 8コマンド実装（list, show, add, update, delete, status, deps, doctor）
- エラーハンドリング（詳細ヒント、理由タイプ表示）
- 確認プロンプト（削除時）

---

## 3. データモデル

### 3.1 エンティティ階層

```
Project（プロジェクト）
  ├─ SubProject（サブプロジェクト）
  │    ├─ Task（タスク）
  │    │    └─ SubTask（サブタスク）
  │    └─ Task（タスク）
  │         └─ SubTask（サブタスク）
  └─ Task（Project直下タスク）
       └─ SubTask（サブタスク）
```

**制約:**
- Taskは「Project直下」または「SubProject配下」のいずれか一箇所にのみ所属
- SubTaskは必ずTask配下に所属
- 名前の重複は同一階層内で禁止（UNIQUE制約）

### 3.2 テーブル定義

#### 3.2.1 projects テーブル
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

#### 3.2.2 subprojects テーブル
```sql
CREATE TABLE subprojects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    UNIQUE (project_id, name),
    UNIQUE (project_id, order_index)
);
```

#### 3.2.3 tasks テーブル
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    subproject_id INTEGER,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'UNSET',
    order_index INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    FOREIGN KEY (subproject_id) REFERENCES subprojects(id) ON DELETE RESTRICT,
    CHECK ((project_id IS NOT NULL AND subproject_id IS NULL) OR
           (project_id IS NULL AND subproject_id IS NOT NULL)),
    UNIQUE (project_id, name),
    UNIQUE (subproject_id, name),
    UNIQUE (project_id, order_index),
    UNIQUE (subproject_id, order_index)
);
```

#### 3.2.4 subtasks テーブル
```sql
CREATE TABLE subtasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'UNSET',
    order_index INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE RESTRICT,
    UNIQUE (task_id, name),
    UNIQUE (task_id, order_index)
);
```

#### 3.2.5 dependencies テーブル
```sql
CREATE TABLE dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('task', 'subtask')),
    predecessor_id INTEGER NOT NULL,
    successor_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (predecessor_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (successor_id) REFERENCES tasks(id) ON DELETE CASCADE,
    UNIQUE (predecessor_id, successor_id),
    CHECK (predecessor_id != successor_id)
);
```

**注:** SubTaskの依存関係も同じテーブルで管理（entity_type='subtask'）

### 3.3 ステータス定義

| ステータス | 意味 | 記号 |
|-----------|------|------|
| UNSET | 未設定（初期状態） | `[ ]` |
| NOT_STARTED | 未着手 | `[⏸]` |
| IN_PROGRESS | 作業中 | `[▶]` |
| DONE | 完了 | `[✓]` |

---

## 4. 機能仕様

### 4.1 CRUD操作

#### 4.1.1 Create（作成）
- 各階層のエンティティを作成
- order_indexは自動計算（`MAX(order_index) + 1`、初回は0）
- 名前の重複チェック（同一階層内）
- 親エンティティの存在確認（FK制約）

#### 4.1.2 Read（取得）
- 単一エンティティ取得（by ID）
- 一覧取得（親IDでフィルタ）
- 階層ツリー表示（show project <id>）

#### 4.1.3 Update（更新）
- name, description の更新
- updated_at自動更新 + 親への伝播

#### 4.1.4 Delete（削除）
3種類の削除方法を提供:

**通常削除:**
- 子エンティティが存在しない場合のみ削除可能
- 子が存在する場合は ChildExistsError

**橋渡し削除（--bridge）:**
- Task/SubTaskのみ対応
- 削除前に先行ノードと後続ノードを直接接続
- 依存関係チェーンを維持

**連鎖削除（--cascade --force）:**
- エンティティとその子孫をすべて削除
- 破壊的操作のため --force が必須
- dry-run 対応

### 4.2 依存関係管理

#### 4.2.1 依存関係の追加
- Task間依存、SubTask間依存のみ許可
- cross-layer依存は禁止（ValidationError）
- サイクル検出（DFS）→ CycleDetectedError
- 同一依存関係の重複禁止（UNIQUE制約）

#### 4.2.2 依存関係の削除
- predecessor_id, successor_id で特定して削除
- 依存関係が存在しない場合は NotFoundError

#### 4.2.3 依存関係の可視化
- **deps list**: 依存関係一覧（親文脈併記）
- **deps graph**: グラフ表示（ASCII art）
- **deps chain**: 依存チェーン表示
- **deps impact**: 影響範囲表示

### 4.3 ステータス管理

#### 4.3.1 DONE遷移条件
Taskを DONE にするには:
1. すべての先行Task（依存関係のpredecessor）が DONE
2. すべての子SubTaskが DONE

SubTaskを DONE にするには:
1. すべての先行SubTask（依存関係のpredecessor）が DONE

#### 4.3.2 ステータス遷移
- DONE遷移のみ制約あり
- その他のステータス（UNSET, NOT_STARTED, IN_PROGRESS）への遷移は自由
- 遷移条件を満たさない場合は StatusTransitionError

#### 4.3.3 dry-run
- `--dry-run` で遷移可否をチェック
- データベースの状態は変更しない（読み取り処理のみ）

### 4.4 整合性チェック（doctor/check）

#### 4.4.1 チェック項目
- FK制約違反（孤児エンティティ）
- DAG制約違反（サイクル検出）
- ステータス整合性（DONE条件違反）
- order_index重複

#### 4.4.2 実行タイミング
- 大量の削除・更新操作後
- エラー頻発時
- 定期的なメンテナンス（週次・月次）
- データベース直接操作後

---

## 5. コマンドリファレンス

### 5.1 list - 一覧表示

```bash
pmtool list projects
```

**機能:**
- Project一覧をRich Tableで表示
- ID, 名前, 説明, 作成日時, 更新日時を表示

### 5.2 show - 階層ツリー表示

```bash
pmtool show project <id>
```

**機能:**
- Project階層ツリーをRich Treeで表示（4階層）
- ステータス記号付き（`[ ]`, `[⏸]`, `[▶]`, `[✓]`）
- Project直下Taskは「Tasks directly under Project」区画に表示

### 5.3 add - エンティティ追加

```bash
pmtool add project --name "プロジェクト名" --desc "説明"
pmtool add subproject --project-id 1 --name "サブプロジェクト名"
pmtool add task --subproject-id 1 --name "タスク名"
pmtool add task --project-id 1 --name "タスク名"  # Project直下Task
pmtool add subtask --task-id 1 --name "サブタスク名"
```

**機能:**
- 対話的入力サポート（未指定項目をプロンプト）
- 名前の重複チェック
- 親エンティティの存在確認

### 5.4 update - エンティティ更新

```bash
pmtool update task 1 --name "新しい名前" --desc "新しい説明"
```

**機能:**
- name, description の更新
- updated_at自動更新 + 親への伝播

### 5.5 delete - エンティティ削除

```bash
# 通常削除
pmtool delete task 1

# 橋渡し削除
pmtool delete task 1 --bridge

# 連鎖削除（dry-run）
pmtool delete task 1 --cascade --dry-run

# 連鎖削除（実行）
pmtool delete task 1 --cascade --force
```

**オプション:**
- `--bridge`: 橋渡し削除（依存関係を再接続）
- `--cascade`: 連鎖削除（子孫も含めて削除）
- `--force`: 連鎖削除の強制実行（--cascade使用時は必須）
- `--dry-run`: 影響範囲のみ表示（実行しない）

### 5.6 status - ステータス変更

```bash
# ステータス変更
pmtool status task 1 IN_PROGRESS

# DONE遷移（条件チェック）
pmtool status task 1 DONE

# dry-run（遷移可否チェック）
pmtool status task 1 DONE --dry-run
```

**ステータス値:**
- UNSET, NOT_STARTED, IN_PROGRESS, DONE

### 5.7 deps - 依存関係管理

```bash
# 依存関係追加
pmtool deps add task --from 1 --to 2  # Task 1 → Task 2

# 依存関係削除
pmtool deps remove task --from 1 --to 2

# 依存関係一覧
pmtool deps list task 1

# グラフ表示
pmtool deps graph task

# 依存チェーン表示
pmtool deps chain task 1

# 影響範囲表示
pmtool deps impact task 1
```

### 5.8 doctor - 整合性チェック

```bash
pmtool doctor
# または
pmtool check
```

**機能:**
- FK制約、DAG制約、ステータス整合性、order_index重複をチェック
- 問題がある場合は詳細な診断結果を表示

---

## 6. 制約・ルール

### 6.1 FK制約

**親子関係（ON DELETE RESTRICT）:**
- project_id, subproject_id, task_id
- 子が存在する親は削除不可（明示的な削除順序を強制）

**依存関係（ON DELETE CASCADE）:**
- predecessor_id, successor_id
- ノード削除時に依存関係レコードも自動削除

### 6.2 UNIQUE制約

- `projects.name`: Project名の重複禁止
- `(project_id, name)`: 同一Project内でのSubProject名/Task名の重複禁止
- `(subproject_id, name)`: 同一SubProject内でのTask名の重複禁止
- `(task_id, name)`: 同一Task内でのSubTask名の重複禁止
- `(project_id, order_index)`: 同一Project内でのorder_index重複禁止
- `(subproject_id, order_index)`: 同一SubProject内でのorder_index重複禁止
- `(task_id, order_index)`: 同一Task内でのorder_index重複禁止
- `(predecessor_id, successor_id)`: 同一依存関係の重複禁止

### 6.3 DAG制約

- 依存関係はDAG（有向非循環グラフ）を維持
- サイクル検出はDFS（深さ優先探索）で実装
- サイクルが発生する依存関係追加は CycleDetectedError

### 6.4 レイヤー分離制約

- Task間依存のみ許可
- SubTask間依存のみ許可
- cross-layer依存（Task→SubTask、SubTask→Task）は禁止

### 6.5 ステータス遷移制約

- DONE遷移のみ制約あり（先行ノード + 子SubTask）
- その他のステータス遷移は自由

---

## 7. エラーハンドリング

### 7.1 カスタム例外

| 例外名 | 発生条件 | 理由タイプ |
|--------|---------|-----------|
| NotFoundError | エンティティが存在しない | NOT_FOUND |
| ValidationError | 入力値が不正 | INVALID_INPUT |
| CycleDetectedError | DAG制約違反（サイクル検出） | CYCLE_DETECTED |
| StatusTransitionError | DONE遷移条件未達 | TRANSITION_ERROR |
| ChildExistsError | 子エンティティ存在時の削除 | CHILD_EXISTS |
| DependencyExistsError | 依存関係存在時の削除 | DEPENDENCY_EXISTS |

### 7.2 エラーメッセージ形式

```
pmtool.exceptions.StatusTransitionError: Cannot transition to DONE
  Reason: Predecessor Task 2 is not DONE (current: IN_PROGRESS)
  Hint: Complete all predecessor tasks before marking this task as DONE
```

- **Reason:** エラーの理由（内部コード情報）
- **Hint:** ユーザー向けの対処方法

### 7.3 確認プロンプト

削除操作時に確認プロンプトを表示:
```
Delete Task 1: "タスク名"? (y/n):
```

橋渡し削除・連鎖削除時は説明も表示。

---

## 8. テスト仕様

### 8.1 テストカバレッジ

**目標:** 80%以上
**達成:** **80.08%**（2319 stmt / 462 miss）

### 8.2 テストカテゴリ

#### 8.2.1 ユニットテスト
- repository.py: CRUD操作、updated_at伝播、削除制御
- dependencies.py: DAG検証、橋渡し処理
- status.py: DONE遷移条件、dry-run
- validators.py: 入力バリデーション
- doctor.py: 整合性チェック

#### 8.2.2 スモークテスト
- commands.py: 全コマンドの基本動作確認（32本）
- DB状態変化 + 例外なし確認（出力一致テストからの転換）

#### 8.2.3 エッジケーステスト
- 空文字、NULL、巨大な値、境界値
- 依存関係の複雑なパターン（多段チェーン、分岐・合流）

#### 8.2.4 統合テスト
- CLI層 + ビジネスロジック層の統合動作確認
- input.pyカバレッジ100%達成

### 8.3 テスト実行

```bash
# 全テスト実行
pytest

# カバレッジ付き実行
pytest --cov=src/pmtool --cov-report=term-missing

# 特定のテストファイル実行
pytest tests/test_commands_smoke.py
```

---

## 9. Phase 5 実装予定機能

### 9.1 テンプレート機能

**対象:** SubProjectテンプレート（Task + SubTask + 依存関係を含む）

**コマンド:**
- `pmtool template save`: テンプレート保存
- `pmtool template list`: テンプレート一覧
- `pmtool template show`: テンプレート詳細表示
- `pmtool template apply`: テンプレート適用
- `pmtool template delete`: テンプレート削除

**データ設計:**
- 推奨: DB内テーブル（4テーブル: templates, template_tasks, template_subtasks, template_dependencies）
- 最終判断: Phase 5 冒頭で実施（DB vs JSON/YAML）

**詳細:** `docs/specifications/テンプレート機能_仕様書.md` 参照

### 9.2 全画面TUI版

**実装方針:**
- Textual等を使用した全画面TUI
- 別プログラム/別系統として実装（CLIツールとは独立）
- テンプレート機能はTextual版のみに実装

---

## 10. 参考資料

### 10.1 関連ドキュメント

**設計書:**
- `docs/design/DB設計書_v2.1_最終版.md` - データベース設計の詳細
- `docs/design/実装方針確定メモ.md` - 実装方針の決定事項
- `docs/design/Phase2_CLI設計書.md` - CLI設計書（Phase 2）
- `docs/design/Phase3_拡張機能実装_設計書.md` - 拡張機能設計書
- `docs/design/Phase4_品質安定性向上_設計書.md` - 品質・安定性向上設計書

**ユーザードキュメント:**
- `docs/user/USER_GUIDE.md` - ユーザーガイド
- `docs/user/TUTORIAL.md` - チュートリアル
- `docs/user/FAQ.md` - よくある質問

**完了レポート:**
- `docs/discussions/Phase4_完了レポート.md` - Phase 4 完了レポート

### 10.2 技術参考資料

- SQLite外部キー制約: https://www.sqlite.org/foreignkeys.html
- Python dataclasses: https://docs.python.org/3/library/dataclasses.html
- DAG（有向非循環グラフ）: https://en.wikipedia.org/wiki/Directed_acyclic_graph
- Rich: https://rich.readthedocs.io/
- pytest: https://docs.pytest.org/

---

**このドキュメントは Phase 0-4 の実装内容を統合した統合仕様書です。Phase 5 実装時は、本仕様書とテンプレート機能仕様書を参照してください。**
