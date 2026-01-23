# ProjectManagementTool

ProjectManagementTool (Claude Code、ChatGPT使用)

階層型プロジェクト管理ツール - DAG依存関係管理とステータス制御を備えた、プロジェクト・タスク管理システム

## プロジェクトステータス

**現在のフェーズ:** Phase 5 実装中（Group 3完了、Group 4着手可能）

- ✅ Phase 0: 基盤構築（DB設計、初期化スクリプト）
- ✅ Phase 1: コア機能実装（CRUD、依存関係管理、ステータス管理、削除制御）
- ✅ Phase 2: CLIインターフェース実装（Rich表示、エラーハンドリング）
- ✅ Phase 3: 拡張機能（P0完了：UX改善、エラーメッセージ強化）
- ✅ Phase 4: 品質・安定性向上（テストカバレッジ80%、ユーザードキュメント整備、テンプレート仕様書作成）
- 🔨 Phase 5: Textual UI + テンプレート機能（Group 1-3完了、Group 4着手可能）
  - ✅ Group 1: 基盤整備（P5-01～P5-03）
  - ✅ Group 2: テンプレート機能BL層（P5-04～P5-06）
  - ✅ Group 3: 基本UI（P5-07～P5-09）
  - 🔨 Group 4: テンプレート機能UI（P5-10～P5-12）
  - 🔨 Group 5: 補助機能・品質向上（P5-13～P5-16）

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

### Phase 2: CLIインターフェース

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
- **テスト:** pytest、pytest-cov（**カバレッジ80.08%達成**）、検証スクリプト

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
│   └── tui/                 # CLIインターフェース（Phase 2）
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
│   ├── user/                # ユーザー向けドキュメント
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

# dataフォルダ作成
mkdir data

# データベース初期化
python -c "from src.pmtool.database import Database; db = Database('data/pmtool.db'); db.initialize('scripts/init_db.sql', force=True)"
```

### 動作確認

```bash
# Phase 1 検証（ビジネスロジック層）
python scripts/verify_phase1.py

# Phase 2 検証（CLI層）
python scripts/verify_phase2.py

# CLIコマンド実行例
pmtool --help
pmtool list projects
pmtool add project --name "テストプロジェクト" --desc "説明"
pmtool show project 1
```

期待される出力：すべてのテストが成功（✓ マーク）

## ドキュメント

### ユーザー向けドキュメント

pmtool の使い方を学ぶための詳細なドキュメントが用意されています。

- **[docs/user/USER_GUIDE.md](docs/user/USER_GUIDE.md)** - ユーザーガイド
  - インストール手順
  - 基本概念（4階層構造、ステータス管理、依存関係管理）
  - コマンドリファレンス（全8コマンドの詳細）
  - 削除操作の詳細（通常削除、橋渡し削除、連鎖削除）
- **[docs/user/TUTORIAL.md](docs/user/TUTORIAL.md)** - チュートリアル
  - シナリオ1: 基本的なプロジェクト管理
  - シナリオ2: 依存関係管理
  - 実践的な使い方をステップバイステップで解説
- **[docs/user/FAQ.md](docs/user/FAQ.md)** - よくある質問
  - エラー対処法（FK制約違反、サイクル検出、ステータス遷移エラー等）
  - トラブルシューティング（doctor、dry-run の使い方）
  - Tips & Tricks

**初めて使う方は、USER_GUIDE.md から始めることをお勧めします。**

### 開発者向けドキュメント

プロジェクトの詳細な仕様・設計・議論記録は `docs/` フォルダに整理されています。

**主要ドキュメント:**
- **[docs/README.md](docs/README.md)** - ドキュメント構造ガイド
- **[docs/specifications/](docs/specifications/)** - 実装仕様書
  - プロジェクト管理ツール_ClaudeCode仕様書.md
- **[docs/design/](docs/design/)** - 設計書・計画書
  - DB設計書_v2.1_最終版.md
  - 実装方針確定メモ.md
  - Phase2_CLI設計書.md
  - Phase4_品質安定性向上_設計書.md
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

### Phase 5 Group 3完了（2026-01-24）

基本UI画面（P5-07～P5-09）実装完了・ChatGPTレビュー承認:
- **P5-07**: HomeScreen実装（Project一覧DataTable表示）
- **P5-08**: ProjectDetailScreen実装（4階層ツリー表示）
- **P5-09**: SubProjectDetailScreen実装（Task/SubTaskツリー + テンプレート保存stub）
- **Repositoryメソッド名修正**: 設計書の仮定メソッド名を実際のAPIに修正
- **H キー動作修正**: instanceof判定によるHome画面遷移を実現（6回の反復修正）
- **動作確認**: `python -m pmtool_textual.app` 起動成功

コミット: 85b151b（初回実装）、c501e39（メソッド名修正）、cc5ed21～703c425（H キー修正6コミット）

### Phase 5 Group 2完了（2026-01-22）

テンプレート機能BL層（P5-04～P5-06）実装完了・ChatGPTレビュー承認:
- **P5-04**: TemplateRepository実装（CRUD操作）
- **P5-05**: TemplateManager基本実装（save/list/show/delete）
- **P5-06**: TemplateManager高度機能実装（apply、dry-run、外部依存検出）

### Phase 5 Group 1完了（2026-01-22）

基盤整備（P5-01～P5-03）実装完了・ChatGPTレビュー承認:
- **P5-01**: プロジェクト構造整備（pmtool_textualパッケージ作成）
- **P5-02**: Textual基本アプリケーション骨格（PMToolApp、BaseScreen）
- **P5-03**: DB接続管理モジュール（DBManager）

### Phase 5 設計完了（2026-01-22）

Textual UI + テンプレート機能の設計完了・実装着手可能:
- **テンプレート機能BL設計書（P5-9 v1.1.1）承認**: TemplateManager/TemplateRepository設計
  - SaveTemplateResult、ExternalDependencyWarning設計
  - own_connパターンによるトランザクション設計
  - 外部依存検出ロジック設計
- **Textual UI基本構造設計書（P5-12 v1.0.2）承認**: 7画面構成・Widget設計
  - Home, Project Detail, SubProject Detail, Template Hub, Save/Apply Wizard, Settings
  - キーバインド統一（ESC=Back, H=Home）
  - Textual 7.3.0バージョン固定
- **詳細実装計画書（P5-17 v1.0.1）承認**: 全16タスクの詳細実装手順
  - P5-01～P5-16の実装順序・マイルストーン（推定34時間）
  - 具体的なコード例・完了条件
  - 品質目標（テストカバレッジ80%）

詳細:
- [docs/design/Phase5_テンプレート機能_BL設計書.md](docs/design/Phase5_テンプレート機能_BL設計書.md)
- [docs/design/Phase5_Textual_UI基本構造設計書.md](docs/design/Phase5_Textual_UI基本構造設計書.md)
- [docs/design/Phase5_詳細実装計画書.md](docs/design/Phase5_詳細実装計画書.md)

### Phase 4 P4-01完了（2026-01-20）

テストカバレッジ80%達成・ChatGPTレビュー承認:
- **カバレッジ80.08%達成**（71% → 80.08%、+9.08%）
- test_commands_smoke.py（32本）: commands.py 37%→72% (+35%)
- test_input_coverage.py（16本）: input.py 100%達成
- エッジケース・境界値テスト（repository、dependencies）
- CLI統合テスト（最低限）
- スモークテスト戦略の転換成功（出力一致 → DB状態変化＋例外なし確認）
- ChatGPT Review7承認（Phase 4 P4-01完了）

**達成カバレッジ:** 80.08%（2319 stmt / 462 miss）
- exceptions.py, models.py, formatters.py, validators.py, input.py: 100%
- cli.py: 99%, database.py: 91%, display.py: 87%
- doctor.py: 81%, repository.py: 79%
- dependencies.py: 73%, status.py: 72%, commands.py: 72%

**P4-02〜P4-06完了（既存実装）:**
- P4-02: 依存関係の可視化強化（deps graph/chain/impact）
- P4-03: dry-run の拡張（status DONE dry-run）
- P4-04: doctor/check の拡充（整合性チェック）
- P4-05: cascade_delete の実装（--cascade --force）
- P4-06: エラーハンドリング改善（理由タイプ、詳細ヒント）

**P4-07〜P4-08（実装予定）:**
- P4-07: ユーザードキュメント整備（user guide、tutorial、FAQ）
- P4-08: テンプレート機能仕様確定（実装は Phase 5）

### Phase 3 P0完了（2026-01-18）

拡張機能実装（P0-01〜P0-08完了）:
- Project直下Task区画化（UX改善）
- deps list/graph/chain/impact コマンド実装
- 削除時の確認プロンプト、親文脈表示
- --bridge/--cascade オプション実装
- ステータスエラー時の詳細ヒント、理由タイプ表示
- pytest自動テスト導入（P0-08）

詳細: [docs/discussions/Phase3_P0完了レポート.md](docs/discussions/Phase3_P0完了レポート.md)

### Phase 2 実装完了・承認（2026-01-17）

CLI層の実装完了・ChatGPTレビュー承認:
- Rich + prompt_toolkit による Rich-enhanced CLI実装
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

## 今後の予定

### Phase 5 実装継続（Group 4以降）

**残タスク:**
- **P5-10～P5-12**: テンプレート機能UI（Template Hub、Save/Apply Wizard）
- **P5-13～P5-16**: 補助機能・品質向上（Settings、初回セットアップ、テスト整備、完了レポート）

**完了タスク:**
- ✅ **P5-01～P5-03**: 基盤整備（プロジェクト構造、Textual骨格、DB接続）
- ✅ **P5-04～P5-06**: テンプレート機能BL層（TemplateRepository、TemplateManager）
- ✅ **P5-07～P5-09**: 基本UI（Home、Project Detail、SubProject Detail）

残推定工数: 約12時間（Group 4: 8h、Group 5: 9h、Phase 5完了レポート: 1h）

### Phase 6 以降（予定）

- 検索・絞り込み機能
- メモ機能
- 関連リンク管理
- 外部ファイル添付
- 変更履歴（ログ）
- 一括操作
- 複数DB管理
- テンプレートexport/import

## ライセンス

（未設定）

## コントリビューション

このプロジェクトは Claude Code と ChatGPT を使用した実験的プロジェクトです。

## 参考資料

- SQLite外部キー制約: https://www.sqlite.org/foreignkeys.html
- Python dataclasses: https://docs.python.org/3/library/dataclasses.html
- DAG（有向非循環グラフ）: https://en.wikipedia.org/wiki/Directed_acyclic_graph
