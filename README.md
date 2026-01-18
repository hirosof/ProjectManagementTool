# ProjectManagementTool

ProjectManagementTool (Claude Code、ChatGPT使用)

階層型プロジェクト管理ツール - DAG依存関係管理とステータス制御を備えた、プロジェクト・タスク管理システム

## プロジェクトステータス

**現在のフェーズ:** Phase 4 実装中（P4-01 完了、P4-02以降実装予定）

- ✅ Phase 0: 基盤構築（DB設計、初期化スクリプト）
- ✅ Phase 1: コア機能実装（CRUD、依存関係管理、ステータス管理、削除制御）
- ✅ Phase 2: TUIインターフェース実装（CLIコマンド、Rich表示、エラーハンドリング）
- ✅ Phase 3: 拡張機能（P0完了：UX改善、エラーメッセージ強化）
- ⏳ Phase 4: 品質・安定性向上（テスト基盤強化、依存可視化、dry-run拡張、doctor拡充）

## 主要機能

### Phase 1: ビジネスロジック層

#### エンティティ管理
- **4階層構造:** Project → SubProject → Task → SubTask
- **CRUD操作:** 各階層でのCreate/Read/Update/Delete
- **order_index管理:** 表示順序の自動管理
- **updated_at伝播:** 子の変更が親のタイムスタンプに伝播

#### 依存関係管理
- **DAG制約:** 非循環有向グラフの維持（サイクル検出機能）
- **レイヤー分離:** Task間依存、SubTask間依存のみ許可
- **依存関係の橋渡し:** ノード削除時の依存関係再接続

#### ステータス管理
- **ステータス種別:** UNSET, NOT_STARTED, IN_PROGRESS, DONE
- **DONE遷移条件:** すべての先行ノード + すべての子SubTaskがDONE
- **トランザクション整合性:** ステータス遷移時の依存関係検証

#### 削除制御
- **デフォルト削除:** 子ノードが存在する場合はエラー
- **橋渡し削除:** 依存関係を再接続してから削除
- **連鎖削除:** Phase 3 で実装予定（現在は無効化）

### Phase 2: TUIインターフェース

#### CLIコマンド
- `pmtool list projects` - Project一覧表示（Rich Table）
- `pmtool show project <id>` - 階層ツリー表示（Rich Tree、4階層）
- `pmtool add project/subproject/task/subtask` - エンティティ追加
- `pmtool delete <entity> <id> [--bridge]` - エンティティ削除（標準・橋渡し）
- `pmtool status task/subtask <id> <status>` - ステータス変更
- `pmtool deps add/remove/list task/subtask` - 依存関係管理

#### UI/UX機能
- **ステータス記号:** `[ ]` UNSET, `[⏸]` NOT_STARTED, `[▶]` IN_PROGRESS, `[✓]` DONE
- **詳細なエラーメッセージ:** 失敗理由と対処方法のヒント表示
- **確認プロンプト:** 削除時の安全確認
- **親文脈表示:** 依存関係一覧でのproject_id/task_id併記
- **対話的入力:** 未指定項目の自動プロンプト

## 技術スタック

- **言語:** Python 3.10+
- **データベース:** SQLite3
- **UI/UX:** Rich (表示), prompt_toolkit (入力)
- **開発ツール:** Claude Code、ChatGPT
- **テスト:** pytest、pytest-cov（カバレッジ53%、目標80%）、検証スクリプト

## プロジェクト構造

```
ProjectManagementTool/
├── src/pmtool/              # ソースコード
│   ├── database.py          # DB接続・初期化（Phase 1）
│   ├── models.py            # エンティティモデル（dataclass）（Phase 1）
│   ├── repository.py        # CRUD操作（Phase 1）
│   ├── dependencies.py      # 依存関係管理・DAG検証（Phase 1）
│   ├── status.py            # ステータス管理（Phase 1）
│   ├── validators.py        # バリデーション（Phase 1）
│   ├── exceptions.py        # カスタム例外（Phase 1）
│   └── tui/                 # TUIインターフェース（Phase 2）
│       ├── __init__.py      # tuiパッケージ初期化
│       ├── formatters.py    # ステータスフォーマット
│       ├── input.py         # 対話的入力処理
│       ├── display.py       # Rich表示ロジック
│       ├── cli.py           # CLIエントリーポイント
│       └── commands.py      # コマンドハンドラ
├── scripts/                 # ユーティリティスクリプト
│   ├── init_db.sql          # DB初期化SQL
│   ├── verify_phase1.py     # Phase 1 検証スクリプト
│   └── verify_phase2.py     # Phase 2 検証スクリプト
├── tests/                   # テストファイル（Phase 3/4）
│   ├── conftest.py          # pytestフィクスチャ
│   ├── test_*.py            # ユニットテスト
│   └── test_*_edgecases.py  # エッジケース・境界値テスト
├── docs/                    # ドキュメント
│   ├── README.md            # ドキュメント構造ガイド
│   ├── specifications/      # 実装仕様書
│   ├── design/              # 設計書・計画書
│   └── discussions/         # 議論ログ・レビュー記録
├── data/                    # データベースファイル
│   └── pmtool.db            # SQLiteデータベース
├── setup.py                 # パッケージ設定
├── pyproject.toml           # プロジェクト設定
├── requirements.txt         # 依存ライブラリ
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

# 依存ライブラリのインストール
pip install -e .

# データベース初期化
python -c "from src.pmtool.database import Database; db = Database('data/pmtool.db'); db.initialize('scripts/init_db.sql', force=True)"
```

### 動作確認

```bash
# Phase 1 検証（ビジネスロジック層）
python scripts/verify_phase1.py

# Phase 2 検証（TUI層）
python scripts/verify_phase2.py

# CLIコマンド実行例
pmtool --help
pmtool list projects
pmtool add project --name "テストプロジェクト" --desc "説明"
pmtool show project 1
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
  - Phase2_TUI設計書.md
- **[docs/discussions/](docs/discussions/)** - 議論ログ・レビュー記録
  - Phase2_完了レポート.md
  - Phase1_フィードバック対応完了レポート.md

**開発を開始する前に:**
1. `docs/specifications/` で仕様を確認
2. `docs/design/` で設計方針を理解
3. `docs/discussions/` で過去の議論・意思決定を参照

## 使用例

### Phase 2: CLIコマンド（推奨）

```bash
# プロジェクト一覧表示
pmtool list projects

# プロジェクト作成
pmtool add project --name "新プロジェクト" --desc "説明文"

# サブプロジェクト作成
pmtool add subproject --project 1 --name "サブプロジェクト1"

# タスク作成
pmtool add task --project 1 --subproject 1 --name "タスク1"
pmtool add task --project 1 --subproject 1 --name "タスク2"

# 依存関係追加（タスク1 → タスク2）
pmtool deps add task --from 1 --to 2

# 階層ツリー表示
pmtool show project 1

# ステータス変更
pmtool status task 1 DONE
pmtool status task 2 DONE

# 依存関係一覧表示
pmtool deps list task 2

# タスク削除（橋渡し削除）
pmtool delete task 1 --bridge
```

### Phase 1: Python API（高度な用途）

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

### Phase 4 実装中（2026-01-19〜）

品質・安定性向上フェーズ:
- ✅ **P4-01**: テスト基盤強化（pytest-cov、エッジケース・境界値テスト）
  - カバレッジ53%（目標80%）
  - test_repository_edgecases.py、test_dependencies_edgecases.py 追加
- ⏳ **P4-02以降**: 依存可視化、dry-run拡張、doctor拡充、cascade_delete、エラーハンドリング改善

### Phase 3 実装完了（P0）（2026-01-18）

拡張機能実装（P0完了、P1はPhase 4へ移管）:
- **P0-01**: Project直下Task区画化（UX改善）
- **P0-02**: `deps list` コマンド実装
- **P0-03**: 削除時の確認プロンプト
- **P0-04**: `deps` コマンドでの親文脈表示
- **P0-05**: `--bridge` オプション実装
- **P0-06**: ステータスエラー時の詳細ヒント
- **P0-07**: 橋渡し削除の説明追加
- **P0-08**: エラーメッセージの理由タイプ表示

### Phase 2 実装完了・承認（2026-01-17）

TUI層の実装完了・ChatGPTレビュー承認:
- Rich + prompt_toolkit によるTUI実装
- argparseによるサブコマンド方式CLI（全8コマンド）
- 設計レビュー指摘A-1～4、B-5～9すべて対応
- verify_phase2.py による動作確認完了

詳細: [docs/discussions/Phase2_完了レポート.md](docs/discussions/Phase2_完了レポート.md)

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

## 今後の予定（Phase 3）

### 実装候補機能

- **update系コマンド:** 名前・説明・order_index変更
- **doctor/checkコマンド:** データ整合性チェック
- **dry-run機能:** 破壊的操作のプレビュー
- **テンプレート機能:** プロジェクト・タスク構造のテンプレート化
- **検索・フィルタ:** エンティティ検索、ステータスフィルタ
- **依存関係可視化強化:** グラフ表示、クリティカルパス分析

### 改善候補（技術的負債）

- ステータス遷移エラーの理由表現強化（reason code、例外型分離）
- SubProject入れ子データの表示方針確定
- 表示順（order_index）の明示的保証
- 絵文字・記号の端末依存対応
- pytest自動テスト導入

## ライセンス

（未設定）

## コントリビューション

このプロジェクトは Claude Code と ChatGPT を使用した実験的プロジェクトです。

## 参考資料

- SQLite外部キー制約: https://www.sqlite.org/foreignkeys.html
- Python dataclasses: https://docs.python.org/3/library/dataclasses.html
- DAG（有向非循環グラフ）: https://en.wikipedia.org/wiki/Directed_acyclic_graph
