# pmtool FAQ（よくある質問）

**バージョン:** 1.0.0（Phase 4 完了版）
**最終更新:** 2026-01-20

---

## 目次

1. [一般的な質問](#1-一般的な質問)
2. [エラー対処法](#2-エラー対処法)
   - 2.1 [FK制約違反エラー](#21-fk制約違反エラー)
   - 2.2 [サイクル検出エラー](#22-サイクル検出エラー)
   - 2.3 [ステータス遷移エラー](#23-ステータス遷移エラー)
   - 2.4 [削除時の子存在エラー](#24-削除時の子存在エラー)
3. [トラブルシューティング](#3-トラブルシューティング)
   - 3.1 [データ整合性チェックの使い方](#31-データ整合性チェックの使い方)
   - 3.2 [dry-runの使い方](#32-dry-runの使い方)
   - 3.3 [データベースファイルの場所](#33-データベースファイルの場所)
4. [Tips & Tricks](#4-tips--tricks)

---

## 1. 一般的な質問

### Q1: pmtool とは何ですか？

**A:** pmtool は、階層型プロジェクト管理ツールです。4階層構造（Project → SubProject → Task → SubTask）により、大規模プロジェクトを段階的に分解して管理できます。DAG依存関係管理とステータス制御により、作業順序の整合性を保証します。

---

### Q2: 4階層構造の使い分けは？

**A:** 以下のように使い分けることを推奨します。

| 階層 | 使い方の例 |
|------|-----------|
| **Project** | プロジェクト全体（例: 「Webアプリ開発」） |
| **SubProject** | 機能単位・フェーズ単位（例: 「フロントエンド開発」「バックエンド開発」） |
| **Task** | 具体的な作業単位（例: 「ログイン機能実装」「API実装」） |
| **SubTask** | タスクの細分化（例: 「画面設計」「実装」「テスト」） |

柔軟な構造なので、プロジェクトの規模や性質に応じて調整できます。

---

### Q3: Project直下にTaskを作成できますか？

**A:** はい、できます。SubProject を経由せず、Project 直下に Task を作成できます。プロジェクト全体に関わるタスク（例: 「プロジェクト計画」「キックオフ」）などに使用すると便利です。

---

### Q4: 依存関係はどの階層で設定できますか？

**A:** Task間、SubTask間でのみ設定できます。以下の制約があります。

- **OK**: Task → Task、SubTask → SubTask
- **NG**: Task → SubTask、SubTask → Task（レイヤー分離制約）
- **NG**: Project → Project、SubProject → SubProject（依存関係は設定不可）

---

### Q5: ステータスは誰が持ちますか？

**A:** **Task** と **SubTask** のみがステータスを持ちます。Project と SubProject はステータスを持ちません。

---

### Q6: データベースファイルはどこに保存されますか？

**A:** デフォルトでは `data/pmtool.db` に保存されます。別の場所に保存したい場合は、環境変数やコマンドラインオプションで指定できます（詳細はセットアップ手順を参照）。

---

## 2. エラー対処法

### 2.1 FK制約違反エラー

#### エラーメッセージ例:
```
sqlite3.IntegrityError: FOREIGN KEY constraint failed
```

#### 原因:
- 親エンティティが存在しない状態で、子エンティティを作成しようとした
- 削除順序が不適切（子が存在する状態で親を削除しようとした）

#### 対処法:

**1. 親エンティティの存在を確認**
```bash
# Project 一覧を確認
$ pmtool list projects

# Project 詳細を確認
$ pmtool show project 1
```

**2. 削除順序を確認（子→親の順で削除）**
```bash
# 誤った削除順序（エラー）
$ pmtool delete project 1  # 子（SubProject、Task）が存在する場合はエラー

# 正しい削除順序
$ pmtool delete subtask 1   # SubTask を先に削除
$ pmtool delete task 1      # Task を削除
$ pmtool delete subproject 1  # SubProject を削除
$ pmtool delete project 1   # 最後に Project を削除

# または、連鎖削除を使用
$ pmtool delete project 1 --cascade --force
```

**3. データベース整合性チェックを実行**
```bash
$ pmtool doctor
```

---

### 2.2 サイクル検出エラー

#### エラーメッセージ例:
```
pmtool.exceptions.CycleDetectedError: Cycle detected: 1 → 2 → 3 → 1
```

#### 原因:
- 依存関係がサイクル（循環）を形成している
- A → B → C → A のような循環依存

#### 対処法:

**1. 依存関係を確認**
```bash
# Task 1 の依存関係を確認
$ pmtool deps list task 1

# 依存チェーンを確認
$ pmtool deps chain task --from 1 --to 3
```

**2. サイクルを形成する依存関係を削除**
```bash
# サイクルを断ち切る依存関係を削除
$ pmtool deps remove task --from 3 --to 1
```

**3. 依存関係の向きを確認**

依存関係の向きは **predecessor（先行ノード）→ successor（後続ノード）** です。

- **正しい**: 「ログイン機能実装」→「ダッシュボード実装」（ログインが完成してからダッシュボード）
- **誤り**: 「ダッシュボード実装」→「ログイン機能実装」→「ダッシュボード実装」（サイクル）

---

### 2.3 ステータス遷移エラー

#### エラーメッセージ例:
```
pmtool.exceptions.StatusTransitionError: Cannot transition to DONE
  Reason: Predecessor Task 2 is not DONE (current: IN_PROGRESS)
```

#### 原因:
- 先行ノード（依存関係の predecessor）が DONE になっていない
- 子 SubTask が DONE になっていない（Task の場合）

#### 対処法:

**1. 先行ノードの状態を確認**
```bash
# Task の依存関係を確認
$ pmtool deps list task 1

# 先行ノードのステータスを確認
$ pmtool show project 1
```

**2. 先行ノードを先に DONE にする**
```bash
# 先行ノード（Task 2）を DONE に変更
$ pmtool status task 2 DONE

# その後、後続ノード（Task 1）を DONE に変更
$ pmtool status task 1 DONE
```

**3. 子 SubTask の状態を確認（Task の場合）**
```bash
# Task の詳細を確認（SubTaskの状態も表示される）
$ pmtool show project 1

# すべての SubTask を DONE にする
$ pmtool status subtask 1 DONE
$ pmtool status subtask 2 DONE
$ pmtool status subtask 3 DONE

# その後、Task を DONE に変更
$ pmtool status task 1 DONE
```

**4. dry-run で遷移可否を事前チェック**
```bash
$ pmtool status task 1 DONE --dry-run

[DRY RUN] Cannot transition to DONE:
  - All predecessors are DONE: ❌ (Task 2 is IN_PROGRESS)
  - All child SubTasks are DONE: ✓
  → Transition is NOT allowed
```

---

### 2.4 削除時の子存在エラー

#### エラーメッセージ例:
```
pmtool.exceptions.ChildExistsError: Cannot delete Task 1: child SubTasks exist
  Hint: Use --bridge to reconnect dependencies, or --cascade --force to delete the entire subtree
```

#### 原因:
- 子エンティティが存在する状態で、親エンティティを削除しようとした

#### 対処法:

**1. 子エンティティを先に削除（通常削除）**
```bash
# SubTask を先に削除
$ pmtool delete subtask 1
$ pmtool delete subtask 2
$ pmtool delete subtask 3

# その後、Task を削除
$ pmtool delete task 1
```

**2. 橋渡し削除を使用（依存関係を再接続）**

Task/SubTask の場合、`--bridge` オプションで依存関係を橋渡しできます。

```bash
# Task 2 を橋渡し削除（依存関係を再接続）
$ pmtool delete task 2 --bridge

⚠️  Bridging dependencies before deletion:
  - Task 1 → Task 2 → Task 3
  After deletion: Task 1 → Task 3

Proceed? [y/N]: y
✓ Task deleted with bridge (ID: 2)
```

**注意**: 橋渡し削除は、子エンティティ（SubTask）が存在する場合は使用できません。

**3. 連鎖削除を使用（子も含めて削除）**

`--cascade --force` オプションで、子も含めて一括削除できます。

```bash
# Task 1 を連鎖削除（SubTask も含めて削除）
$ pmtool delete task 1 --cascade --force

⚠️  WARNING: This will delete the following entities:
  - Task 1: ログイン画面実装
  - 3 SubTasks

Proceed? [y/N]: y
✓ Task and subtree deleted (ID: 1)
```

**注意**: 連鎖削除は破壊的操作のため、`--dry-run` で影響範囲を事前に確認することを推奨します。

```bash
# dry-run で影響範囲を確認
$ pmtool delete task 1 --cascade --dry-run

[DRY RUN] Would delete:
  - Task 1: ログイン画面実装
  - 3 SubTasks
```

---

## 3. トラブルシューティング

### 3.1 データ整合性チェックの使い方

#### 目的:
データベースの整合性（FK制約、DAG制約、ステータス整合性、order_index重複）をチェックします。

#### 使い方:
```bash
$ pmtool doctor
```

または

```bash
$ pmtool check
```

#### 出力例（問題がない場合）:
```
Database Integrity Check

Checking FK constraints... ✓ No issues
Checking DAG constraints... ✓ No issues
Checking status consistency... ✓ No issues
Checking order_index uniqueness... ✓ No issues

✓ All checks passed
```

#### 出力例（問題がある場合）:
```
Database Integrity Check

Checking FK constraints... ✓ No issues
Checking DAG constraints... ❌ 1 error found
  - Cycle detected: Task 1 → Task 2 → Task 3 → Task 1
Checking status consistency... ⚠️  1 warning found
  - Task 5 is DONE but predecessor Task 4 is IN_PROGRESS
Checking order_index uniqueness... ✓ No issues

❌ 1 error(s), 1 warning(s)
```

#### 対処法:
- **Error**: データベースの整合性が破綻しているため、手動で修正が必要
- **Warning**: 警告レベルの問題（動作には影響しないが、推奨されない状態）

定期的に `pmtool doctor` を実行して、データベースの健全性を確認することを推奨します。

---

### 3.2 dry-runの使い方

#### 目的:
削除やステータス変更を実際に行わず、影響範囲や遷移可否を事前に確認します。

#### 使い方:

**1. 削除時のdry-run**
```bash
# Task 1 を連鎖削除した場合の影響範囲を確認
$ pmtool delete task 1 --cascade --dry-run

[DRY RUN] Would delete:
  - Task 1: ログイン画面実装
  - 3 SubTasks
```

**2. ステータス変更時のdry-run**
```bash
# Task 1 を DONE に変更できるかチェック
$ pmtool status task 1 DONE --dry-run

[DRY RUN] Can transition to DONE:
  - All predecessors are DONE: ✓
  - All child SubTasks are DONE: ✓
  → Transition is allowed
```

dry-run を活用することで、誤操作を防ぎ、安全に作業を進めることができます。

---

### 3.3 データベースファイルの場所

#### デフォルトの場所:
```
ProjectManagementTool/data/pmtool.db
```

#### 確認方法:
```bash
# データベースファイルが存在するか確認（Windows）
$ dir "D:\Code Generate AI\Claude Code\ProjectManagementTool\data\pmtool.db"

# データベースファイルが存在するか確認（Linux/Mac）
$ ls -l data/pmtool.db
```

#### データベースの再初期化:
データベースを初期状態に戻す場合は、以下のコマンドを実行します。

```bash
python -c "from src.pmtool.database import Database; db = Database('data/pmtool.db'); db.initialize('scripts/init_db.sql', force=True)"
```

**注意**: このコマンドを実行すると、**すべてのデータが削除**されます。バックアップを取ってから実行してください。

#### バックアップ方法:
```bash
# データベースファイルをコピー（Windows）
$ copy "data\pmtool.db" "data\pmtool.db.backup"

# データベースファイルをコピー（Linux/Mac）
$ cp data/pmtool.db data/pmtool.db.backup
```

---

## 4. Tips & Tricks

### Tip 1: プロジェクト階層を視覚的に把握する

```bash
# Project全体のツリー表示
$ pmtool show project 1
```

階層ツリー表示により、プロジェクト構造を一目で把握できます。

---

### Tip 2: 依存関係を使って作業順序を明確にする

依存関係を設定することで、DONE遷移条件が自動的に適用され、作業順序が強制されます。

```bash
# API実装 → フロント実装 の依存関係を設定
$ pmtool deps add task --from 1 --to 2
```

これにより、API実装が完了しないとフロント実装をDONEにできなくなります。

---

### Tip 3: dry-runで安全性を確保

削除やステータス変更の前に、必ず `--dry-run` で影響を確認しましょう。

```bash
# 削除の影響範囲を確認
$ pmtool delete project 1 --cascade --dry-run

# ステータス遷移の可否を確認
$ pmtool status task 1 DONE --dry-run
```

---

### Tip 4: 橋渡し削除で依存関係チェーンを維持

Task を削除する際、`--bridge` を使うと依存関係チェーンを維持できます。

```bash
# Task 2 を削除しても、Task 1 → Task 3 の依存関係が維持される
$ pmtool delete task 2 --bridge
```

---

### Tip 5: 定期的にdoctorチェックを実行

データベースの整合性を定期的にチェックすることで、問題の早期発見ができます。

```bash
$ pmtool doctor
```

---

### Tip 6: 大規模プロジェクトでは段階的に分解

大規模プロジェクトでは、Project → SubProject → Task → SubTask の4階層を活用して、段階的に分解しましょう。

**例:**
```
Project: 「ECサイト開発」
  SubProject: 「フロントエンド開発」
    Task: 「ログイン機能」
      SubTask: 「画面設計」「実装」「テスト」
    Task: 「商品一覧機能」
      SubTask: 「画面設計」「実装」「テスト」
  SubProject: 「バックエンド開発」
    Task: 「認証API」
      SubTask: 「設計」「実装」「テスト」
    Task: 「商品API」
      SubTask: 「設計」「実装」「テスト」
```

---

### Tip 7: 絵文字なし表示（--no-emoji）

絵文字が表示されない環境では、`--no-emoji` オプションを使用します。

```bash
$ pmtool list projects --no-emoji
$ pmtool show project 1 --no-emoji
$ pmtool deps list task 1 --no-emoji
```

---

## まとめ

このFAQでは、pmtool の使用中によくある質問とエラー対処法を紹介しました。

**困ったときは:**
1. エラーメッセージのヒントを確認
2. `pmtool doctor` でデータベース整合性をチェック
3. `--dry-run` で影響範囲を事前確認
4. USER_GUIDE.md、TUTORIAL.md を参照

**さらに詳しく:**
- **USER_GUIDE.md**: コマンドリファレンスの詳細
- **TUTORIAL.md**: 実践的なシナリオ

**ご質問・フィードバック:**
- GitHub Issues: <repository_url>/issues

pmtool を使った効果的なプロジェクト管理をお楽しみください！
