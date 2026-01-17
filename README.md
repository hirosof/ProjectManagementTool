# ProjectManagementTool

ProjectManagementTool (Claude Code、ChatGPT使用)

階層型プロジェクト管理ツール - DAG依存関係管理とステータス制御を備えた、プロジェクト・タスク管理システム

## プロジェクトステータス

**現在のフェーズ:** Phase 1 完了（フィードバック対応済み）

- ✅ Phase 0: 基盤構築（DB設計、初期化スクリプト）
- ✅ Phase 1: コア機能実装（CRUD、依存関係管理、ステータス管理、削除制御）
- ⏳ Phase 2: TUIインターフェース実装（未着手）
- ⏳ Phase 3: テンプレート機能、バリデーション拡張（未着手）

## 主要機能（Phase 1 時点）

### エンティティ管理
- **4階層構造:** Project → SubProject → Task → SubTask
- **CRUD操作:** 各階層でのCreate/Read/Update/Delete
- **order_index管理:** 表示順序の自動管理
- **updated_at伝播:** 子の変更が親のタイムスタンプに伝播

### 依存関係管理
- **DAG制約:** 非循環有向グラフの維持（サイクル検出機能）
- **レイヤー分離:** Task間依存、SubTask間依存のみ許可
- **依存関係の橋渡し:** ノード削除時の依存関係再接続

### ステータス管理
- **ステータス種別:** UNSET, NOT_STARTED, IN_PROGRESS, DONE
- **DONE遷移条件:** すべての先行ノード + すべての子SubTaskがDONE
- **トランザクション整合性:** ステータス遷移時の依存関係検証

### 削除制御
- **デフォルト削除:** 子ノードが存在する場合はエラー
- **橋渡し削除:** 依存関係を再接続してから削除
- **連鎖削除:** Phase 2/3 で実装予定（現在は無効化）

## 技術スタック

- **言語:** Python 3.10+
- **データベース:** SQLite3
- **開発ツール:** Claude Code、ChatGPT
- **テスト:** pytest（Phase 2 で本格実装予定）

## プロジェクト構造

```
ProjectManagementTool/
├── src/pmtool/              # ソースコード
│   ├── database.py          # DB接続・初期化
│   ├── models.py            # エンティティモデル（dataclass）
│   ├── repository.py        # CRUD操作
│   ├── dependencies.py      # 依存関係管理・DAG検証
│   ├── status.py            # ステータス管理
│   ├── validators.py        # バリデーション
│   └── exceptions.py        # カスタム例外
├── scripts/                 # ユーティリティスクリプト
│   ├── init_db.sql          # DB初期化SQL
│   └── verify_phase1.py     # Phase 1 検証スクリプト
├── docs/                    # ドキュメント
│   ├── README.md            # ドキュメント構造ガイド
│   ├── specifications/      # 実装仕様書
│   ├── design/              # 設計書・計画書
│   └── discussions/         # 議論ログ・レビュー記録
├── data/                    # データベースファイル
│   └── pmtool.db            # SQLiteデータベース
└── temp/                    # 一時ファイル（Git管理対象外）
```

## セットアップ

### 必要要件

- Python 3.10 以上
- pip

### インストール

```bash
# リポジトリのクローン
git clone <repository-url>
cd ProjectManagementTool

# データベース初期化
python -c "from src.pmtool.database import Database; db = Database('data/pmtool.db'); db.initialize('scripts/init_db.sql', force=True)"
```

### 動作確認

```bash
# Phase 1 検証スクリプト実行
python scripts/verify_phase1.py
```

期待される出力：すべてのテストが成功（✓ マーク）

## ドキュメント

プロジェクトの詳細な仕様・設計・議論記録は `docs/` フォルダに整理されています。

**主要ドキュメント:**
- **[docs/README.md](docs/README.md)** - ドキュメント構造ガイド
- **[docs/specifications/](docs/specifications/)** - 実装仕様書
  - プロジェクト管理ツール_ClaudeCode仕様書.md
- **[docs/design/](docs/design/)** - 設計書・計画書
  - DB設計書_v2.1_最終版.md
  - 実装方針確定メモ.md
  - Phase0_完了_Phase1_引き継ぎ事項.md
- **[docs/discussions/](docs/discussions/)** - 議論ログ・レビュー記録
  - Phase1_フィードバック対応完了レポート.md

**開発を開始する前に:**
1. `docs/specifications/` で仕様を確認
2. `docs/design/` で設計方針を理解
3. `docs/discussions/` で過去の議論・意思決定を参照

## 使用例（Phase 1 API）

```python
from src.pmtool.database import Database
from src.pmtool.repository import ProjectRepository, TaskRepository, SubTaskRepository
from src.pmtool.dependencies import DependencyManager
from src.pmtool.status import StatusManager

# データベース接続
db = Database('data/pmtool.db')

# リポジトリ初期化
project_repo = ProjectRepository(db)
task_repo = TaskRepository(db)
subtask_repo = SubTaskRepository(db)
dep_manager = DependencyManager(db)
status_manager = StatusManager(db, dep_manager)

# プロジェクト作成
project = project_repo.create("新プロジェクト", "説明文")

# タスク作成
task1 = task_repo.create(project.id, "タスク1")
task2 = task_repo.create(project.id, "タスク2")

# 依存関係追加 (task1 → task2)
dep_manager.add_task_dependency(task1.id, task2.id)

# ステータス更新
status_manager.update_task_status(task1.id, "DONE")
status_manager.update_task_status(task2.id, "DONE")  # task1がDONEなので成功

# クリーンアップ
db.close()
```

## 開発履歴

### Phase 1 フィードバック対応（2026-01-16）

ChatGPTによるコードレビューフィードバックに対応:
1. ✅ cascade_delete の無効化（Phase 1 スコープ外）
2. ✅ updated_at 更新漏れの修正（3箇所のupdateメソッド）
3. ✅ トランザクション原子性の修正（bridge_dependencies のコネクション共有）

詳細: [docs/discussions/Phase1_フィードバック対応完了レポート.md](docs/discussions/Phase1_フィードバック対応完了レポート.md)

### Phase 1 実装完了（2026-01-16）

コア機能の実装完了:
- CRUD操作（Project, SubProject, Task, SubTask）
- 依存関係管理（DAG検証、レイヤー制約）
- ステータス管理（DONE遷移条件）
- 削除制御（子チェック、橋渡し削除）

### Phase 0 完了（2026-01-15）

基盤構築:
- DB設計 v2.1（FK制約、部分的UNIQUE INDEX）
- Database クラス実装
- 初期化スクリプト（init_db.sql）

## 今後の予定

### Phase 2: TUIインターフェース

- コマンドラインベースの対話的インターフェース実装
- プロジェクト・タスクのツリー表示
- 操作コマンド（add, update, delete, status, deps）

### Phase 3: 拡張機能

- テンプレート機能（プロジェクト・タスク構造のテンプレート化）
- doctor/check バリデーション（データ整合性チェック）
- Dry-run プレビュー（操作前の影響確認）

## ライセンス

（未設定）

## コントリビューション

このプロジェクトは Claude Code と ChatGPT を使用した実験的プロジェクトです。

## 参考資料

- SQLite外部キー制約: https://www.sqlite.org/foreignkeys.html
- Python dataclasses: https://docs.python.org/3/library/dataclasses.html
- DAG（有向非循環グラフ）: https://en.wikipedia.org/wiki/Directed_acyclic_graph
