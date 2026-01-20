# pmtool ユーザーガイド

**バージョン:** 1.0.0（Phase 4 完了版）
**最終更新:** 2026-01-20

---

## 目次

1. [はじめに](#1-はじめに)
2. [インストール](#2-インストール)
3. [基本概念](#3-基本概念)
   - 3.1 [4階層構造](#31-4階層構造)
   - 3.2 [ステータス管理](#32-ステータス管理)
   - 3.3 [依存関係管理](#33-依存関係管理)
4. [コマンドリファレンス](#4-コマンドリファレンス)
   - 4.1 [list コマンド](#41-list-コマンド)
   - 4.2 [show コマンド](#42-show-コマンド)
   - 4.3 [add コマンド](#43-add-コマンド)
   - 4.4 [update コマンド](#44-update-コマンド)
   - 4.5 [delete コマンド](#45-delete-コマンド)
   - 4.6 [status コマンド](#46-status-コマンド)
   - 4.7 [deps コマンド](#47-deps-コマンド)
   - 4.8 [doctor コマンド](#48-doctor-コマンド)
5. [削除操作の詳細](#5-削除操作の詳細)
   - 5.1 [通常削除](#51-通常削除)
   - 5.2 [橋渡し削除（--bridge）](#52-橋渡し削除--bridge)
   - 5.3 [連鎖削除（--cascade）](#53-連鎖削除--cascade)

---

## 1. はじめに

**pmtool** は、階層型プロジェクト管理ツールです。4階層構造（Project → SubProject → Task → SubTask）により、柔軟なプロジェクト管理を実現します。

**主な特徴:**
- **4階層構造**: 大規模プロジェクトを段階的に分解して管理
- **DAG依存関係管理**: タスク間の依存関係を有向非循環グラフ（DAG）として管理
- **ステータス管理**: 4段階のステータス（UNSET、NOT_STARTED、IN_PROGRESS、DONE）による進捗管理
- **安全な削除操作**: 橋渡し削除・連鎖削除により、依存関係を維持しながら安全に削除
- **データ整合性チェック**: doctor コマンドによるデータベース整合性の検証

**このガイドの対象:**
- pmtool を初めて使用する方
- 基本的なコマンドを確認したい方
- 削除操作の詳細を理解したい方

**関連ドキュメント:**
- **TUTORIAL.md**: 実践的なシナリオを使った使い方
- **FAQ.md**: よくある質問とトラブルシューティング

---

## 2. インストール

### 2.1 前提条件

- **Python**: 3.10 以上
- **pip**: 最新版を推奨

### 2.2 インストール手順

```bash
# リポジトリをクローン
git clone <repository_url>
cd ProjectManagementTool

# 依存ライブラリをインストール
pip install -e .

# データベースを初期化
python -c "from src.pmtool.database import Database; db = Database('data/pmtool.db'); db.initialize('scripts/init_db.sql', force=True)"

# インストール確認
pmtool --help
```

### 2.3 動作確認

```bash
# バージョン確認
pmtool --help

# プロジェクト一覧表示（初期状態では空）
pmtool list projects
```

---

## 3. 基本概念

### 用語定義

このガイドで使用する主要な用語を定義します。

- **Task（タスク）**: 具体的な作業単位。ステータスを持ち、依存関係を設定できる。
- **SubTask（サブタスク）**: タスクをさらに細分化した作業。ステータスを持ち、依存関係を設定できる。
- **predecessor（先行ノード）**: 依存関係において、先に完了する必要があるノード。
- **successor（後続ノード）**: 依存関係において、先行ノードが完了した後に作業できるノード。
- **橋渡し削除（bridge）**: ノード削除時に、先行ノードと後続ノードを直接接続して依存関係を維持する削除方法。
- **連鎖削除（cascade）**: エンティティとその子孫（サブツリー）をすべて削除する方法。破壊的操作。

### 3.1 4階層構造

pmtool は、以下の4階層構造でプロジェクトを管理します。

```
Project（プロジェクト）
  ├─ SubProject（サブプロジェクト）
  │    ├─ Task（タスク）
  │    │    └─ SubTask（サブタスク）
  │    └─ Task
  │         └─ SubTask
  └─ Task（Project直下のTask）
       └─ SubTask
```

**各階層の役割:**

| 階層 | 説明 | 例 |
|------|------|-----|
| **Project** | プロジェクト全体を表す最上位階層 | 「Webアプリケーション開発」 |
| **SubProject** | プロジェクト内の大きな区分（機能単位、フェーズ単位など） | 「フロントエンド開発」「バックエンド開発」 |
| **Task** | 具体的な作業単位 | 「ログイン機能実装」「API実装」 |
| **SubTask** | タスクをさらに細分化した作業 | 「画面設計」「実装」「テスト」 |

**注意事項:**
- Project は SubProject と Task の両方を持つことができます（柔軟な構造）
- Task/SubTask には **依存関係** を設定できます（詳細は [3.3 依存関係管理](#33-依存関係管理) を参照）

### 3.2 ステータス管理

各 Task / SubTask は、以下の4段階のステータスを持ちます。

| ステータス | 記号 | 説明 |
|------------|------|------|
| **UNSET** | `[ ]` | 初期状態（未設定） |
| **NOT_STARTED** | `[⏸]` | 作業未開始 |
| **IN_PROGRESS** | `[▶]` | 作業中 |
| **DONE** | `[✓]` | 完了 |

**ステータス遷移の制約:**

Task/SubTask を **DONE** にするには、以下の2つの条件を満たす必要があります。

1. **すべての先行ノード（依存関係の predecessor）が DONE** になっている
2. **すべての子 SubTask が DONE** になっている（Task の場合）

この制約により、作業順序の整合性が保証されます。

**例:**
```
Task A → Task B  （Task A が完了しないと Task B は DONE にできない）
Task C
  └─ SubTask C-1  （SubTask C-1 が完了しないと Task C は DONE にできない）
```

### 3.3 依存関係管理

Task/SubTask 間には **依存関係** を設定できます。依存関係は **DAG（有向非循環グラフ）** として管理され、サイクル（循環）は禁止されています。

**依存関係の制約:**

1. **レイヤー分離**: Task間依存、SubTask間依存のみ許可（Task→SubTask の依存は禁止）
2. **DAG制約**: サイクル（A→B→C→A のような循環）は禁止
3. **ステータス遷移**: 先行ノードが DONE でないと、後続ノードを DONE にできない

**依存関係の表記:**
- **predecessor（先行ノード）**: 先に完了する必要があるノード
- **successor（後続ノード）**: 先行ノードが完了した後に作業できるノード

**例:**
```
Task A → Task B → Task C
     ↘ Task D ↗

この場合:
- Task A は Task B と Task D の先行ノード
- Task B と Task D が完了しないと Task C は DONE にできない
```

---

## 4. コマンドリファレンス

### 4.1 list コマンド

プロジェクト一覧を表示します。

**書式:**
```bash
pmtool list projects [--no-emoji]
```

**オプション:**
- `--no-emoji`: 絵文字なしで表示

**実行例:**
```bash
$ pmtool list projects

Projects
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ ID ┃ Name                 ┃ Created         ┃ Updated             ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ 1  │ Webアプリ開発        │ 2026-01-20      │ 2026-01-20          │
│ 2  │ インフラ構築         │ 2026-01-20      │ 2026-01-20          │
└────┴──────────────────────┴─────────────────┴─────────────────────┘
```

---

### 4.2 show コマンド

プロジェクトの階層ツリーを表示します。

**書式:**
```bash
pmtool show project <project_id> [--no-emoji]
```

**引数:**
- `<project_id>`: 表示するプロジェクトのID

**オプション:**
- `--no-emoji`: 絵文字なしで表示

**実行例:**
```bash
$ pmtool show project 1

📦 Webアプリ開発 (ID: 1)
├── 📁 フロントエンド開発 (ID: 1)
│   ├── 📝 ログイン画面実装 (ID: 1) [✓] DONE
│   │   ├── ✏️ 画面設計 (ID: 1) [✓] DONE
│   │   ├── ✏️ 実装 (ID: 2) [✓] DONE
│   │   └── ✏️ テスト (ID: 3) [✓] DONE
│   └── 📝 ダッシュボード実装 (ID: 2) [▶] IN_PROGRESS
│       ├── ✏️ 画面設計 (ID: 4) [✓] DONE
│       └── ✏️ 実装 (ID: 5) [▶] IN_PROGRESS
└── 📝 (Project直下のTask)
    └── 📝 プロジェクト計画 (ID: 3) [✓] DONE
```

---

### 4.3 add コマンド

エンティティ（Project、SubProject、Task、SubTask）を追加します。

**書式:**
```bash
# Project 追加
pmtool add project [--name <name>] [--desc <description>]

# SubProject 追加
pmtool add subproject --project <project_id> [--name <name>] [--desc <description>]

# Task 追加（SubProject配下）
pmtool add task --subproject <subproject_id> [--name <name>] [--desc <description>]

# Task 追加（Project直下）
pmtool add task --project <project_id> [--name <name>] [--desc <description>]

# SubTask 追加
pmtool add subtask --task <task_id> [--name <name>] [--desc <description>]
```

**オプション:**
- `--name <name>`: エンティティの名前（対話的入力も可能）
- `--desc <description>`: エンティティの説明（対話的入力も可能）
- `--project <id>`: 親プロジェクトID
- `--subproject <id>`: 親サブプロジェクトID
- `--task <id>`: 親タスクID

**実行例:**
```bash
# Project 追加（対話的入力）
$ pmtool add project
Project Name: Webアプリ開発
Description (optional): ECサイトの開発プロジェクト
✓ Project created: Webアプリ開発 (ID: 1)

# SubProject 追加
$ pmtool add subproject --project 1 --name "フロントエンド開発" --desc "React/TypeScriptによるフロント実装"
✓ SubProject created: フロントエンド開発 (ID: 1)

# Task 追加（SubProject配下）
$ pmtool add task --subproject 1 --name "ログイン画面実装"
✓ Task created: ログイン画面実装 (ID: 1)

# SubTask 追加
$ pmtool add subtask --task 1 --name "画面設計"
✓ SubTask created: 画面設計 (ID: 1)
```

---

### 4.4 update コマンド

エンティティの名前・説明・表示順序を更新します。

**書式:**
```bash
pmtool update <entity> <id> [--name <name>] [--description <description>] [--order <order_index>]
```

**引数:**
- `<entity>`: 更新対象（`project`, `subproject`, `task`, `subtask`）
- `<id>`: エンティティID

**オプション:**
- `--name <name>`: 新しい名前
- `--description <description>` または `--desc <description>`: 新しい説明
- `--order <order_index>`: 新しい表示順序

**実行例:**
```bash
# Task の名前を変更
$ pmtool update task 1 --name "ログイン機能実装（修正版）"
✓ Task updated: ログイン機能実装（修正版）

# SubProject の説明を更新
$ pmtool update subproject 1 --desc "React/TypeScript + Tailwind CSS による実装"
✓ SubProject updated

# 表示順序を変更
$ pmtool update task 2 --order 1
✓ Task updated
```

---

### 4.5 delete コマンド

エンティティを削除します。削除方法には、**通常削除**、**橋渡し削除（--bridge）**、**連鎖削除（--cascade）** の3種類があります。

**書式:**
```bash
pmtool delete <entity> <id> [--bridge] [--cascade --force] [--dry-run]
```

**引数:**
- `<entity>`: 削除対象（`project`, `subproject`, `task`, `subtask`）
- `<id>`: エンティティID

**オプション:**
- `--bridge`: 橋渡し削除（Task/SubTaskのみ、依存関係を再接続）
- `--cascade`: 連鎖削除（子エンティティも含めて削除）
- `--force`: 削除を強制実行（--cascade 使用時は必須）
- `--dry-run`: 削除を実行せず、影響範囲のみを表示（注: データベースの状態は変更しませんが、実行可否判定や影響範囲算出のための読み取り処理は行われます）

**詳細は [5. 削除操作の詳細](#5-削除操作の詳細) を参照してください。**

**実行例:**
```bash
# 通常削除
$ pmtool delete task 1
✓ Task deleted (ID: 1)

# 橋渡し削除（依存関係を再接続）
$ pmtool delete task 2 --bridge
✓ Task deleted with bridge (ID: 2)

# 連鎖削除（子も含めて削除）
$ pmtool delete subproject 1 --cascade --force
⚠️  WARNING: This will delete the following entities:
  - SubProject 1: フロントエンド開発
  - 2 Tasks
  - 5 SubTasks
Proceed? [y/N]: y
✓ SubProject and subtree deleted (ID: 1)

# dry-run（影響範囲の確認のみ）
$ pmtool delete project 1 --cascade --dry-run
[DRY RUN] Would delete:
  - Project 1: Webアプリ開発
  - 2 SubProjects
  - 10 Tasks
  - 25 SubTasks
```

---

### 4.6 status コマンド

Task/SubTask のステータスを変更します。

**書式:**
```bash
pmtool status <entity> <id> <status> [--dry-run]
```

**引数:**
- `<entity>`: 対象（`task`, `subtask`）
- `<id>`: エンティティID
- `<status>`: 新しいステータス（`UNSET`, `NOT_STARTED`, `IN_PROGRESS`, `DONE`）

**オプション:**
- `--dry-run`: 実際に変更せず、遷移可否のみをチェック（注: データベースの状態は変更しませんが、遷移可否判定のための読み取り処理は行われます）

**実行例:**
```bash
# ステータスを IN_PROGRESS に変更
$ pmtool status task 1 IN_PROGRESS
✓ Status updated: Task 1 → IN_PROGRESS

# ステータスを DONE に変更（先行ノードと子SubTaskがすべてDONEの場合のみ成功）
$ pmtool status task 1 DONE
✓ Status updated: Task 1 → DONE

# DONE 遷移のdry-run（遷移可否のチェック）
$ pmtool status task 2 DONE --dry-run
[DRY RUN] Can transition to DONE:
  - All predecessors are DONE: ✓
  - All child SubTasks are DONE: ✓
  → Transition is allowed

# DONE 遷移失敗の例（先行ノードが未完了）
$ pmtool status task 3 DONE
❌ Error: Cannot transition to DONE
  Reason: Predecessor Task 2 is not DONE (current: IN_PROGRESS)
  Hint: Complete all predecessor tasks before marking this task as DONE
```

---

### 4.7 deps コマンド

依存関係を管理します。サブコマンドにより、追加・削除・一覧表示・可視化ができます。

#### 4.7.1 deps add（依存関係追加）

**書式:**
```bash
pmtool deps add <entity> --from <predecessor_id> --to <successor_id>
```

**引数:**
- `<entity>`: 対象（`task`, `subtask`）
- `--from <predecessor_id>`: 先行ノードID
- `--to <successor_id>`: 後続ノードID

**実行例:**
```bash
# Task A → Task B の依存関係を追加
$ pmtool deps add task --from 1 --to 2
✓ Dependency added: Task 1 → Task 2

# サイクル検出の例（エラー）
$ pmtool deps add task --from 2 --to 1
❌ Error: Cycle detected: 2 → 1 → 2
  → Cannot add this dependency (would create a cycle)
```

#### 4.7.2 deps remove（依存関係削除）

**書式:**
```bash
pmtool deps remove <entity> --from <predecessor_id> --to <successor_id>
```

**実行例:**
```bash
$ pmtool deps remove task --from 1 --to 2
✓ Dependency removed: Task 1 → Task 2
```

#### 4.7.3 deps list（依存関係一覧）

**書式:**
```bash
pmtool deps list <entity> <id> [--no-emoji]
```

**実行例:**
```bash
$ pmtool deps list task 2

Dependencies for Task 2: ダッシュボード実装

Predecessors (先行ノード):
  Task 1: ログイン画面実装 [✓] DONE (Project: Webアプリ開発, SubProject: フロントエンド開発)

Successors (後続ノード):
  Task 3: API連携実装 [⏸] NOT_STARTED (Project: Webアプリ開発, SubProject: バックエンド開発)
```

#### 4.7.4 deps graph（依存関係グラフ表示）

直接の先行ノード・後続ノードを表示します。

**書式:**
```bash
pmtool deps graph <entity> <id>
```

**実行例:**
```bash
$ pmtool deps graph task 2

Dependency Graph for Task 2: ダッシュボード実装

Direct Predecessors:
  → Task 1: ログイン画面実装 [✓] DONE

Direct Successors:
  → Task 3: API連携実装 [⏸] NOT_STARTED
  → Task 4: レポート機能実装 [⏸] NOT_STARTED
```

#### 4.7.5 deps chain（依存チェーン表示）

2つのノード間の依存経路を表示します。

**書式:**
```bash
pmtool deps chain <entity> --from <from_id> --to <to_id>
```

**実行例:**
```bash
$ pmtool deps chain task --from 1 --to 5

Dependency Chain: Task 1 → Task 5

Task 1: ログイン画面実装 [✓] DONE
  → Task 2: ダッシュボード実装 [▶] IN_PROGRESS
    → Task 3: API連携実装 [⏸] NOT_STARTED
      → Task 5: テスト実装 [⏸] NOT_STARTED
```

#### 4.7.6 deps impact（影響範囲分析）

指定したノードを DONE にすると解放される（DONE にできるようになる）ノードを表示します。

**書式:**
```bash
pmtool deps impact <entity> <id>
```

**実行例:**
```bash
$ pmtool deps impact task 2

Impact Analysis for Task 2: ダッシュボード実装

If Task 2 is marked as DONE, the following tasks can be marked as DONE:
  → Task 3: API連携実装 (if all other conditions are met)
  → Task 4: レポート機能実装 (if all other conditions are met)
```

---

### 4.8 doctor コマンド

データベースの整合性をチェックします。

**書式:**
```bash
pmtool doctor
```

または

```bash
pmtool check
```

**実行例:**
```bash
$ pmtool doctor

Database Integrity Check

Checking FK constraints... ✓ No issues
Checking DAG constraints... ✓ No issues
Checking status consistency... ✓ No issues
Checking order_index uniqueness... ✓ No issues

✓ All checks passed
```

**エラーがある場合の例:**
```bash
$ pmtool doctor

Database Integrity Check

Checking FK constraints... ✓ No issues
Checking DAG constraints... ❌ 1 error found
  - Cycle detected: Task 1 → Task 2 → Task 3 → Task 1
Checking status consistency... ⚠️  1 warning found
  - Task 5 is DONE but predecessor Task 4 is IN_PROGRESS
Checking order_index uniqueness... ✓ No issues

❌ 1 error(s), 1 warning(s)
```

---

## 5. 削除操作の詳細

pmtool では、安全な削除操作のために3種類の削除方法を提供しています。

**削除方法の対比:**

| 項目 | 通常削除 | 橋渡し削除（--bridge） | 連鎖削除（--cascade） |
|------|---------|----------------------|---------------------|
| **目的** | 子が存在しないエンティティを削除 | 依存関係を維持しながら削除 | 子孫を含めて一括削除 |
| **削除対象** | エンティティ本体のみ | エンティティ本体のみ（依存関係は再接続） | エンティティ + すべての子孫 |
| **後続タスクへの影響** | 依存関係がある場合、後続タスクは先行ノードを失う | 依存関係を再接続し、後続タスクの先行ノードを維持 | 削除されたタスクへの依存関係も削除される |

### 5.1 通常削除

**概要:**
- 子エンティティが存在しない場合のみ削除可能
- 子が存在する場合はエラーになる

**使用例:**
```bash
# SubTaskを持たないTaskを削除
$ pmtool delete task 1
✓ Task deleted (ID: 1)

# 子が存在する場合（エラー）
$ pmtool delete task 2
❌ Error: Cannot delete Task 2: child SubTasks exist
  Hint: Use --bridge to reconnect dependencies, or --cascade --force to delete the entire subtree
```

**適用対象:**
- すべてのエンティティ（Project、SubProject、Task、SubTask）

**注意事項:**
- 削除時に確認プロンプトが表示されます
- 子が存在する場合は、--bridge または --cascade を使用してください

---

### 5.2 橋渡し削除（--bridge）

**概要:**
- Task/SubTask を削除する際、依存関係を再接続する
- 削除対象の先行ノードと後続ノードを直接接続することで、依存関係チェーンを維持

**依存関係の橋渡し例:**
```
削除前:  Task A → Task B → Task C
削除後:  Task A → Task C  （Task B を削除、A→C に橋渡し）
```

**使用例:**
```bash
# Task 2 を橋渡し削除
$ pmtool delete task 2 --bridge

⚠️  Bridging dependencies before deletion:
  - Task 1 → Task 2 → Task 3
  After deletion: Task 1 → Task 3

Proceed? [y/N]: y
✓ Task deleted with bridge (ID: 2)
```

**適用対象:**
- Task、SubTask のみ（Project、SubProject には適用不可）

**注意事項:**
- 子エンティティ（SubTask）が存在する場合は、橋渡し削除は使用できません
- 依存関係が存在しない場合は、通常削除と同じ動作になります

---

### 5.3 連鎖削除（--cascade）

**概要:**
- エンティティとその子孫（サブツリー）をすべて削除
- **破壊的操作**のため、`--force` オプションが必須

**削除される範囲の例:**
```
Project を連鎖削除 → Project + すべての SubProject + すべての Task + すべての SubTask
SubProject を連鎖削除 → SubProject + すべての Task + すべての SubTask
Task を連鎖削除 → Task + すべての SubTask
```

**使用例:**
```bash
# SubProject を連鎖削除（--force 必須）
$ pmtool delete subproject 1 --cascade --force

⚠️  WARNING: This will delete the following entities:
  - SubProject 1: フロントエンド開発
  - 5 Tasks
  - 15 SubTasks
  - All dependencies related to these entities

Proceed? [y/N]: y
✓ SubProject and subtree deleted (ID: 1)

# --force を忘れた場合（エラー）
$ pmtool delete subproject 1 --cascade
❌ Error: --cascade requires --force option
  Hint: Use --cascade --force to confirm deletion
```

**dry-run による影響範囲の確認:**
```bash
$ pmtool delete project 1 --cascade --dry-run

[DRY RUN] Would delete:
  - Project 1: Webアプリ開発
  - 2 SubProjects: フロントエンド開発, バックエンド開発
  - 10 Tasks
  - 30 SubTasks
  - All dependencies related to these entities
```

**適用対象:**
- すべてのエンティティ（Project、SubProject、Task、SubTask）

**注意事項:**
- **破壊的操作**のため、必ず `--force` オプションを指定してください
- `--dry-run` で影響範囲を確認してから実行することを推奨します
- `--bridge` と `--cascade` は排他的（同時に指定できません）

---

## まとめ

このガイドでは、pmtool の基本的な使い方を説明しました。

**次のステップ:**
- **TUTORIAL.md**: 実践的なシナリオを使った使い方を学ぶ
- **FAQ.md**: よくある質問とトラブルシューティングを確認

**さらに詳しく:**
- プロジェクト仕様書: `docs/specifications/プロジェクト管理ツール_ClaudeCode仕様書.md`
- DB設計書: `docs/design/DB設計書_v2.1_最終版.md`

---

**ご質問・フィードバック:**
- GitHub Issues: <repository_url>/issues
