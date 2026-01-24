# CLAUDE.MD

このファイルは、Claudeがこのプロジェクトを理解し、効果的に作業するためのガイドです。

## プロジェクト概要

**プロジェクト名:** ProjectManagementTool

**リポジトリ名:** ProjectManagementTool

**説明:**
階層型プロジェクト管理ツール - DAG依存関係管理とステータス制御を備えた、プロジェクト・タスク管理システム

**主要な目標:**
- 4階層構造（Project → SubProject → Task → SubTask）による柔軟なプロジェクト管理
- DAG（有向非循環グラフ）制約による安全な依存関係管理
- ステータス管理による作業フローの可視化と制御

**現在のフェーズ:** Phase 5 実装中（Group 3完了、Group 4着手可能）

## 技術スタック

**言語:**
- Python 3.10+

**データベース:**
- SQLite3（外部キー制約、トリガー機能を活用）

**ライブラリ:**
- Phase 1: 標準ライブラリのみ（sqlite3, dataclasses, datetime）
- Phase 2: rich>=13.0.0, prompt_toolkit>=3.0.0
- Phase 5: textual==7.3.0（Textual UI用、厳密バージョン固定）

**ツール:**
- Claude Code
- ChatGPT

## プロジェクト構造

```
ProjectManagementTool/
├── src/
│   ├── pmtool/              # コアビジネスロジック
│   │   ├── database.py      # DB接続・初期化（Phase 1）
│   │   ├── models.py        # エンティティモデル（dataclass）（Phase 1）
│   │   ├── repository.py    # CRUD操作（Phase 1 + Phase 5でTemplateRepository追加）
│   │   ├── dependencies.py  # 依存関係管理・DAG検証（Phase 1）
│   │   ├── status.py        # ステータス管理（Phase 1）
│   │   ├── validators.py    # バリデーション（Phase 1）
│   │   ├── exceptions.py    # カスタム例外（Phase 1）
│   │   ├── doctor.py        # 整合性チェック（Phase 3）
│   │   ├── template.py      # テンプレート機能（Phase 5）
│   │   └── tui/             # CLIインターフェース（Phase 2）
│   │       ├── __init__.py
│   │       ├── formatters.py
│   │       ├── input.py
│   │       ├── display.py
│   │       ├── cli.py
│   │       └── commands.py
│   └── pmtool_textual/      # Textual UIインターフェース（Phase 5実装予定）
│       ├── __init__.py
│       ├── app.py           # Textualアプリケーションメイン
│       ├── screens/         # 画面モジュール（7画面）
│       │   └── __init__.py
│       ├── widgets/         # カスタムWidget
│       │   └── __init__.py
│       └── utils/           # ユーティリティ
│           └── __init__.py
├── scripts/                 # ユーティリティスクリプト
│   ├── init_db.sql          # DB初期化SQL
│   ├── verify_phase1.py     # Phase 1 検証スクリプト
│   └── verify_phase2.py     # Phase 2 検証スクリプト
├── docs/                    # ドキュメント
│   ├── README.md            # ドキュメント構造ガイド
│   ├── user/                # ユーザー向けドキュメント
│   ├── specifications/      # 実装仕様書
│   ├── design/              # 設計書・計画書
│   └── discussions/         # 議論ログ・レビュー記録
├── data/                    # データベースファイル
│   └── pmtool.db            # SQLiteデータベース
└── temp/                    # 一時ファイル（Git管理対象外）
```

### ファイル配置とフォルダ管理

**docs/discussions/ フォルダ（Git管理対象）:**
- **目的**: 議論ログや議論過程の記録など、設計・仕様策定のプロセスを保管
- **Git管理**: 管理対象（コミット・プッシュする）
- **用途例**:
  - 設計レビューや確認事項の記録
  - ChatGPT/Claude Codeとの議論過程
  - Phase完了レポート
- **重要**: 議論ログは確定後にこのフォルダに配置します

**docs/design/ フォルダ（Git管理対象）:**
- **目的**: 確定した設計書・計画書を保管
- **Git管理**: 管理対象（コミット・プッシュする）
- **用途例**:
  - Phase計画書
  - DB設計書
  - 実装方針確定メモ
  - Phase間の引き継ぎ事項
- **重要**: 実装時は、このフォルダ内の設計書を参照してください

**docs/specifications/ フォルダ（Git管理対象）:**
- **目的**: コンポーネント・機能の実装仕様書を保管
- **Git管理**: 管理対象（コミット・プッシュする）
- **用途例**:
  - プロジェクト全体の仕様書
  - コンポーネント仕様書
  - 機能仕様書
- **重要**: 実装完了後は、仕様書を最新の実装状態に更新してください

**temp/ フォルダ（Git管理対象外）:**
- **目的**: 一時的なファイル受け渡しやスクラッチスペースとして使用
- **Git管理**: 管理対象外（.gitignoreに登録済み）
- **用途例**:
  - ChatGPTとのファイル受け渡し用の一時領域
  - 実験的なコードやテストファイル
- **重要**: このフォルダ内のファイルパスを、仕様書やドキュメントから参照しないでください

**ワークフロー:**
1. ChatGPTとの議論資料を一時的に`temp/`に配置
2. 議論が確定したら`docs/discussions/`に移動（copyコマンド使用）
3. 確定設計書は`docs/design/`に配置、議論ログは`docs/discussions/`に配置
4. 仕様書から参照する際は`docs/`配下のパスを使用

## 開発ガイドライン

### コーディング規約

- **命名規則:**
  - 関数・変数: snake_case
  - クラス: PascalCase
  - 定数: UPPER_SNAKE_CASE
- **インデント:** スペース4つ
- **コメント:**
  - docstringは必須（公開API）
  - 複雑なロジックには日本語コメント
  - 型ヒントを積極的に使用

### コミット規約

```
<type>: <subject>

<body>

<footer>
```

**Type:**
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメントのみの変更
- `style`: コードの意味に影響しない変更（空白、フォーマットなど）
- `refactor`: リファクタリング
- `test`: テストの追加や修正
- `chore`: ビルドプロセスやツールの変更

## Claude向けの指示

### 優先事項

1. **トランザクション整合性:** DB操作は必ずトランザクション内で完結させる
2. **データ整合性:** 親子関係、依存関係、ステータス遷移条件を厳密に維持
3. **可読性とメンテナンス性:** 複雑なロジックには明確なコメントを付ける

### コミュニケーション方針

**このプロジェクトでは、実装前の議論を重視します。**

1. **実装前の議論を必須とする**
   - 新機能の追加や仕様変更の依頼を受けた際は、**必ず実装前に要件や仕様について議論する**
   - 不明点がある場合は、推測で進めず**必ずユーザーに確認を取る**
   - 複数の実装方法や選択肢がある場合は、**提案してユーザーに選択してもらう**
   - 「おそらくこうだろう」という推測で実装に着手しない

2. **段階的なアプローチ**
   - 要件確認 → 設計議論 → 実装 → 動作確認 の順で進める
   - 各段階でユーザーの合意を得てから次に進む
   - 実装中に疑問が生じた場合は、その場で確認を取る

3. **避けるべき行動**
   - 要件が曖昧なまま実装に着手しない
   - ユーザーが明示的に依頼していない機能を勝手に追加しない
   - 仕様について独断で判断しない

### 作業フロー

1. **仕様・設計の確認**
   - `docs/specifications/` で全体仕様を確認
   - `docs/design/` で設計方針・DB設計を理解
   - `docs/discussions/` で過去の議論・意思決定を参照
2. **既存コードの理解**
   - 関連ファイルを読み、現在の実装を理解
3. **影響範囲の確認**
   - 変更が及ぼす影響を事前に分析
4. **段階的な実装**
   - 小さなステップで実装し、各ステップで動作確認
5. **検証**
   - Phase 1: `scripts/verify_phase1.py` で動作確認
   - Phase 2: `scripts/verify_phase2.py` で動作確認
   - 必要に応じて新しいテストケースを追加

### 避けるべきこと

- 過度な抽象化や不必要な複雑さの導入
- 要求されていない機能の追加
- 既存のコーディングスタイルとの不整合
- トランザクション境界の曖昧な実装
- FK制約やDAG制約を無視した実装

### 重要なファイル

**仕様・設計:**
- **`docs/specifications/プロジェクト管理ツール_ClaudeCode仕様書.md`** - プロジェクト全体の仕様
- **`docs/specifications/テンプレート機能_仕様書.md`** - テンプレート機能仕様書（Phase 5）
- **`docs/design/DB設計書_v2.1_最終版.md`** - データベース設計の詳細
- **`docs/design/実装方針確定メモ.md`** - 実装方針の決定事項
- **`docs/design/Phase2_CLI設計書.md`** - Phase 2 CLI設計書
- **`docs/design/Phase3_拡張機能実装_設計書.md`** - Phase 3 拡張機能設計書
- **`docs/design/Phase4_品質安定性向上_設計書.md`** - Phase 4 品質・安定性向上設計書
- **`docs/design/Phase5_テンプレート機能_BL設計書.md`** - Phase 5 テンプレート機能ビジネスロジック層設計書（承認済み）
- **`docs/design/Phase5_Textual_UI基本構造設計書.md`** - Phase 5 Textual UI基本構造設計書（承認済み）
- **`docs/design/Phase5_詳細実装計画書.md`** - Phase 5 詳細実装計画書（全16タスク、承認済み）

**ユーザー向けドキュメント（Phase 4）:**
- **`docs/user/USER_GUIDE.md`** - ユーザーガイド（基本概念、コマンドリファレンス）
- **`docs/user/TUTORIAL.md`** - チュートリアル（実践的なシナリオ）
- **`docs/user/FAQ.md`** - よくある質問・トラブルシューティング

**Phase 1（ビジネスロジック層）:**
- **`src/pmtool/repository.py`** - CRUD操作の実装（1300行超の中核ファイル）
- **`src/pmtool/dependencies.py`** - 依存関係管理・DAG検証
- **`src/pmtool/status.py`** - ステータス管理ロジック

**Phase 2（CLI層）:**
- **`src/pmtool/tui/cli.py`** - CLIエントリーポイント（argparse）
- **`src/pmtool/tui/commands.py`** - コマンドハンドラ（list, show, add, delete, status, deps）
- **`src/pmtool/tui/display.py`** - Rich表示ロジック（テーブル、ツリー、依存関係）

## セットアップ手順

```bash
# 依存ライブラリのインストール
pip install -e .

# dataフォルダ作成
mkdir data

# データベース初期化
python -c "from src.pmtool.database import Database; db = Database('data/pmtool.db'); db.initialize('scripts/init_db.sql', force=True)"

# Phase 1 検証スクリプト実行
python scripts/verify_phase1.py

# Phase 2 検証スクリプト実行
python scripts/verify_phase2.py

# CLIコマンド実行例
pmtool --help
pmtool list projects
pmtool add project --name "テストプロジェクト" --desc "説明"
pmtool show project 1
```

期待される出力：すべてのテストが成功（✓ マーク）

## 実装済み機能

### Phase 1: ビジネスロジック層

#### エンティティ管理
- **4階層構造**: Project → SubProject → Task → SubTask
- **CRUD操作**: 各階層でのCreate/Read/Update/Delete
- **order_index管理**: 表示順序の自動管理
- **updated_at伝播**: 子の変更が親のタイムスタンプに伝播

#### 依存関係管理
- **DAG制約**: 非循環有向グラフの維持（サイクル検出機能）
- **レイヤー分離**: Task間依存、SubTask間依存のみ許可（cross-layer依存は禁止）
- **依存関係の橋渡し**: ノード削除時の依存関係再接続（delete_with_bridge）
- **トランザクション整合性**: connection共有によるアトミックな操作

#### ステータス管理
- **ステータス種別**: UNSET, NOT_STARTED, IN_PROGRESS, DONE
- **DONE遷移条件**: すべての先行ノード + すべての子SubTaskがDONE
- **バリデーション**: ステータス遷移時の依存関係検証

#### 削除制御
- **デフォルト削除**: 子ノードが存在する場合はエラー（ChildExistsError）
- **橋渡し削除**: 依存関係を再接続してから削除（delete_with_bridge）
- **連鎖削除**: Phase 3 で実装予定（現在はNotImplementedError）

### Phase 2: CLIインターフェース（完了）

#### CLIコマンド
- **list projects**: Project一覧をRich Tableで表示
- **show project <id>**: Project階層ツリーをRich Treeで表示（4階層、ステータス記号付き）
- **add project/subproject/task/subtask**: エンティティ追加（対話的入力サポート）
- **delete project/subproject/task/subtask <id> [--bridge]**: エンティティ削除（標準削除・橋渡し削除）
- **status task/subtask <id> <status>**: ステータス変更（DONE遷移条件チェック）
- **deps add task/subtask --from <id> --to <id>**: 依存関係追加（サイクル検出）
- **deps remove task/subtask --from <id> --to <id>**: 依存関係削除
- **deps list task/subtask <id>**: 依存関係一覧表示（親文脈併記）

#### UI/UX機能
- **ステータス記号**: `[ ]` UNSET, `[⏸]` NOT_STARTED, `[▶]` IN_PROGRESS, `[✓]` DONE
- **エラーハンドリング**: 詳細なヒントメッセージ、理由タイプ表示
- **確認プロンプト**: 削除時の確認、橋渡し削除の説明
- **親文脈表示**: 依存関係一覧でのproject_id/subproject_id/task_id併記
- **Project直下Task区画化**: UX改善のための区画ノード表示

### Phase 3: 拡張機能（P0完了）

#### P0実装済み機能
- **P0-01**: Project直下Task区画化（UX改善）
- **P0-02**: `deps list` コマンド実装
- **P0-03**: 削除時の確認プロンプト
- **P0-04**: `deps` コマンドでの親文脈表示
- **P0-05**: `--bridge` オプション実装
- **P0-06**: ステータスエラー時の詳細ヒント
- **P0-07**: 橋渡し削除の説明追加
- **P0-08**: エラーメッセージの理由タイプ表示

### Phase 4: 品質・安定性向上（完了）

#### P4-01: テストカバレッジ80%達成
- **pytest-cov 設定**: カバレッジ計測環境整備（pyproject.toml、fail-under=80）
- **スモークテスト追加**: test_commands_smoke.py（32本、commands.py: 37%→72%）
- **input.pyカバレッジ100%**: test_input_coverage.py（16本）
- **エッジケーステスト**: test_repository_edgecases.py、test_dependencies_edgecases.py
- **CLI統合テスト**: test_tui_integration.py
- **カバレッジ計測範囲**: src/pmtool のみ、`__init__.py` 除外

**達成カバレッジ:** **80.08%**（2319 stmt / 462 miss）
- exceptions.py, models.py, formatters.py, validators.py, input.py: 100%
- cli.py: 99%, database.py: 91%, display.py: 87%
- doctor.py: 81%, repository.py: 79%
- dependencies.py: 73%, status.py: 72%, commands.py: 72%

#### P4-02〜P4-06: 既存実装の確認・拡充
- **P4-02**: 依存関係の可視化強化（deps graph/chain/impact）
- **P4-03**: dry-run の拡張（status DONE dry-run）
- **P4-04**: doctor/check の拡充（整合性チェック）
- **P4-05**: cascade_delete の実装（--cascade --force）
- **P4-06**: エラーハンドリング改善（理由タイプ、詳細ヒント）

#### P4-07: ユーザードキュメント整備（完了）
- **USER_GUIDE.md**: ユーザーガイド（~700行）
  - インストール手順、基本概念、用語定義
  - コマンドリファレンス（全8コマンドの詳細）
  - 削除操作の詳細（通常削除、橋渡し削除、連鎖削除）
- **TUTORIAL.md**: チュートリアル（~500行）
  - シナリオ1: 基本的なプロジェクト管理
  - シナリオ2: 依存関係管理
  - 実践的な使い方をステップバイステップで解説
- **FAQ.md**: よくある質問（~400行）
  - エラー対処法（FK制約違反、サイクル検出、ステータス遷移エラー等）
  - トラブルシューティング（doctor、dry-run の使い方）
  - Tips & Tricks

#### P4-08: テンプレート機能仕様書作成（完了）
- **テンプレート機能_仕様書.md**: 完全な仕様書（~780行）
  - 機能要件（5項目）、非機能要件（3項目）
  - 設計原則（SubProjectテンプレートのみ、依存関係なし、UNSET初期化）
  - データ設計（DB vs JSON/YAML比較、推奨: DB内テーブル）
  - コマンド仕様（save/list/show/apply/delete）
  - 処理フロー、エラーハンドリング、Phase 5実装計画

## Phase 5: Textual UI + テンプレート機能（実装中）

### 実装完了事項

#### Group 1: 基盤整備（P5-01～P5-03）✅
- **P5-01**: プロジェクト構造整備完了（pmtool_textualパッケージ作成）
- **P5-02**: Textual基本アプリケーション骨格完了（PMToolApp、BaseScreen）
- **P5-03**: DB接続管理モジュール完了（DBManager）

#### Group 2: テンプレート機能BL層（P5-04～P5-06）✅
- **P5-04**: TemplateRepository実装完了（CRUD操作）
- **P5-05**: TemplateManager基本実装完了（save/list/show/delete）
- **P5-06**: TemplateManager高度機能実装完了（apply、dry-run、外部依存検出）

#### Group 3: 基本UI（P5-07～P5-09）✅
- **P5-07**: Home画面実装完了（Project一覧DataTable、起動確認済み）
- **P5-08**: ProjectDetailScreen実装完了（4階層ツリー表示）
- **P5-09**: SubProjectDetailScreen実装完了（Task/SubTaskツリー、テンプレート保存stub）
- **キーバインド統一**: ESC=Back、H=Home（instanceof判定によるHome遷移）

**動作確認:** `python -m pmtool_textual.app` で起動成功、H キーでのHome遷移動作確認済み

#### Group 4: テンプレート機能UI（P5-10～P5-12）✅
- **P5-10**: Template Hub画面実装完了（テンプレート一覧、選択、詳細表示、削除）
- **P5-11**: Template Save Wizard実装完了（4ステップ、外部依存警告、保存）
- **P5-12**: Template Apply Wizard実装完了（4ステップ、dry-runプレビュー、適用）
- **DBコネクション管理改善**: Must fix対応完了（own_connパターン、接続有効性チェック）
- **キーバインド**: T=Template Hub、S=Save Wizard（SubProject Detail）、A=Apply Wizard、D=Delete

**動作確認:** テンプレート保存・適用の全フロー動作確認済み、接続リークなし

#### Group 5: 補助機能・品質向上（P5-13～P5-16）🔄
- **P5-13**: Settings画面実装完了（DBパス表示、バックアップ案内）✅
- **P5-14**: 初回セットアップ支援完了（DB未作成時の導線）✅
- **P5-15**: テスト整備・品質向上（テストカバレッジ80%目標）🔄
- **P5-16**: Phase 5完了レポート作成 ⏳

**P5-13（Settings画面）完了内容:**
- Settings画面クラス作成（`src/pmtool_textual/screens/settings.py`）
- DBパス表示（絶対パス変換）、バックアップ手順案内（3ステップ）
- ESCキーで前画面に戻る、app.pyに`push_settings()`追加
- コミット: 3ba9455

**P5-14（初回セットアップ支援）完了内容:**
- Setup画面クラス作成（`src/pmtool_textual/screens/setup.py`）
- シンプルなUI、DB初期化処理、`__file__`から相対パスで`scripts/init_db.sql`取得
- 初期化成功後のHome画面遷移、app.pyの`on_mount()`でDB存在チェック
- DBパス: 固定パス（`data/pmtool.db`）で自動作成
- コミット: e8a5668

**P5-15（テスト整備）実装途中:**
- テストファイル作成完了: `test_template.py`、`test_template_repository.py`、`test_template_integration.py`
- テストコードのメソッド名修正が必要（`create_project` → `create`等）
- カバレッジ測定・80%達成確認が未完了

### 実装予定機能（残タスク）

#### Group 5完了予定（残2タスク）
- **P5-15**: テスト整備・品質向上（修正中、カバレッジ80%目標）
- **P5-16**: Phase 5完了レポート作成

### Phase 6以降（予定）
- 検索・絞り込み機能
- メモ機能
- 関連リンク管理
- 外部ファイル添付
- 変更履歴（ログ）
- 一括操作
- 複数DB管理
- テンプレートexport/import

## 未実装機能

上記Phase 5、Phase 6以降の機能が未実装です。

## テスト

**Phase 1:**
- `scripts/verify_phase1.py` による機能検証
- ビジネスロジック層の完全な動作確認

**Phase 2:**
- `scripts/verify_phase2.py` による機能検証
- CLI層の完全な動作確認
- 統合テスト（ビジネスロジック層 + CLI層）

**Phase 3:**
- pytest による自動テスト（P0-08で導入）
- コア層の代表的テストケース（repository、dependencies、status、doctor）

**Phase 4:**
- pytest-cov によるカバレッジ測定（**80.08%達成**）
- スモークテスト（commands.py: 32本、DB状態変化＋例外なし確認）
- エッジケース・境界値テスト（空文字、NULL、巨大な値、境界値）
- CLI層の統合テスト、input.pyカバレッジ100%

**テスト実行:**
```bash
# 全テスト実行
pytest

# カバレッジ付き実行
pytest --cov=src/pmtool --cov-report=term-missing

# 特定のテストファイル実行
pytest tests/test_commands_smoke.py
```

## トラブルシューティング

### よくある問題

**問題1: FK制約違反（FOREIGN KEY constraint failed）**
```
sqlite3.IntegrityError: FOREIGN KEY constraint failed
```
解決方法:
- 親エンティティが存在することを確認
- 削除順序を確認（子→親の順で削除）
- 外部キー制約が有効になっていることを確認（`PRAGMA foreign_keys = ON`）

**問題2: サイクル検出エラー（CycleDetectedError）**
```
pmtool.exceptions.CycleDetectedError: Cycle detected: ...
```
解決方法:
- 依存関係がDAG（有向非循環グラフ）になっていることを確認
- サイクルを形成する依存関係を削除
- 依存関係の向きを確認（predecessor → successor）

**問題3: ステータス遷移エラー（StatusTransitionError）**
```
pmtool.exceptions.StatusTransitionError: Cannot transition to DONE: ...
```
解決方法:
- すべての先行ノードがDONEになっていることを確認
- すべての子SubTaskがDONEになっていることを確認
- 依存関係が正しく設定されていることを確認

**問題4: トランザクション原子性の問題**
解決方法:
- 複数のDB操作を含む処理では、同一connectionを共有する
- `conn` パラメータを活用して、トランザクション境界を明確にする
- own_conn パターンを使用（conn=None なら新規作成、conn渡されたらそれを使用）

## 参考資料

- **SQLite外部キー制約**: https://www.sqlite.org/foreignkeys.html
- **Python dataclasses**: https://docs.python.org/3/library/dataclasses.html
- **DAG（有向非循環グラフ）**: https://en.wikipedia.org/wiki/Directed_acyclic_graph
- **プロジェクト仕様書**: `docs/specifications/プロジェクト管理ツール_ClaudeCode仕様書.md`
- **DB設計書**: `docs/design/DB設計書_v2.1_最終版.md`

## アーキテクチャと設計

### コンポーネント構成
- **Database (database.py)**: SQLite接続管理、DB初期化
- **Models (models.py)**: dataclassによるエンティティ定義
- **Repository (repository.py)**: CRUD操作の実装（Project, SubProject, Task, SubTask）
- **DependencyManager (dependencies.py)**: 依存関係管理、DAG検証、橋渡し処理
- **StatusManager (status.py)**: ステータス管理、遷移条件の検証
- **Validators (validators.py)**: 入力バリデーション
- **Exceptions (exceptions.py)**: カスタム例外定義

### データベース設計の特徴

**FK制約の使い分け:**
- **親子関係（project_id, subproject_id, task_id）**: `ON DELETE RESTRICT`
  - 子が存在する親は削除不可（明示的な削除順序を強制）
- **依存関係（predecessor_id, successor_id）**: `ON DELETE CASCADE`
  - ノード削除時に依存関係レコードも自動削除

**UNIQUE INDEX:**
- `(project_id, order_index)`: 同一プロジェクト内でのorder_index重複を防止
- `(subproject_id, order_index)`: 同一サブプロジェクト内でのorder_index重複を防止
- `(task_id, order_index)`: 同一タスク内でのorder_index重複を防止
- `(predecessor_id, successor_id)`: 同一依存関係の重複を防止

### トランザクション設計パターン

**own_conn パターン:**
```python
def method(self, ..., conn: Optional[sqlite3.Connection] = None) -> ...:
    own_conn = False
    if conn is None:
        conn = self.db.connect()
        own_conn = True

    try:
        # ... DB操作 ...

        if own_conn:
            conn.commit()
        return result
    except Exception as e:
        if own_conn:
            conn.rollback()
        raise
    finally:
        if own_conn:
            conn.close()
```

このパターンにより:
- 単独呼び出し時は自動的にトランザクション管理＋接続close
- 親トランザクション内から呼び出された場合は、同一トランザクション内で実行
- リソースリークを防止（Phase 5 Group 4で全メソッドに適用）

### 特徴的な実装

#### 依存関係の橋渡し（bridge_dependencies）
ノード削除時に、削除対象ノードの先行ノードと後続ノードを直接接続することで、依存関係チェーンを維持します。

例: A → B → C の状態で B を削除すると、A → C に橋渡しされます。

#### ステータス遷移条件の厳密な管理
TaskをDONEにするには:
1. すべての先行Task（依存関係のpredecessor）がDONE
2. すべての子SubTaskがDONE

この2条件を満たさない場合、StatusTransitionErrorが発生します。

#### order_indexの自動管理
新規作成時に `MAX(order_index) + 1` を自動計算し、表示順序を維持します。

## 開発履歴

### Phase 5 Group 5実装途中（2026-01-25）
補助機能・品質向上（P5-13～P5-16）実装中:
- **P5-13完了**: Settings画面実装（DBパス表示、バックアップ案内）
  - Settings画面クラス作成（`src/pmtool_textual/screens/settings.py`）
  - DBパス表示（絶対パス変換）、バックアップ手順案内（3ステップ）
  - コミット: 3ba9455
- **P5-14完了**: 初回セットアップ支援実装
  - Setup画面クラス作成（`src/pmtool_textual/screens/setup.py`）
  - DB未作成時の自動検出、固定パス（`data/pmtool.db`）で自動初期化
  - `__file__`から相対パスで`scripts/init_db.sql`取得
  - コミット: e8a5668
- **P5-15実装途中**: テスト整備・品質向上
  - テストファイル作成完了: `test_template.py`（18ケース）、`test_template_repository.py`（22ケース）、`test_template_integration.py`（9ケース）
  - テストコード修正が必要（メソッド名の誤り）
  - カバレッジ測定・80%達成確認が未完了
- **P5-16未着手**: Phase 5完了レポート作成

### Phase 5 Group 4完了（2026-01-24）
テンプレート機能UI（P5-10～P5-12）実装完了・ChatGPTレビュー承認:
- **P5-10～P5-12実装**: Template Hub、Save Wizard、Apply Wizard完了
  - Template Hub: テンプレート一覧、詳細表示、削除（worker）
  - Save Wizard: 4ステップ（SubProject選択、名前入力、オプション、確認・保存）
  - Apply Wizard: 4ステップ（Template選択、Project選択、dry-run、新SubProject名・適用）
- **外部依存検出機能**: 警告ダイアログ表示、ユーザー確認
- **dry-runプレビュー**: 適用前の内容確認（件数サマリ、Task一覧）
- **Must fix対応**: DBコネクション管理改善
  - Database.connect()に接続有効性チェック追加（閉接続の自動再作成）
  - TemplateManagerの全メソッドにfinally句追加（接続リーク防止）
  - detect_external_dependencies()を公開API化（own_connパターン追加）
- **動作確認**: テンプレート保存・適用の全フロー動作確認済み

コミット履歴:
- d2a8a43: feat: Phase 5 グループ4実装（テンプレート機能UI）
- 96f0895: fix: DBコネクション管理の改善（Must fix対応）

### Phase 5 Group 3完了（2026-01-24）
基本UI画面（P5-07～P5-09）実装完了・ChatGPTレビュー承認:
- **P5-07～P5-09実装**: Home、ProjectDetail、SubProjectDetail画面完了
  - HomeScreen: Project一覧DataTable表示
  - ProjectDetailScreen: 4階層ツリー表示（Project→SubProject→Task→SubTask）
  - SubProjectDetailScreen: Task/SubTaskツリー + テンプレート保存stub
- **Repository方法名修正**: 設計書の仮定メソッド名を実際のRepository APIに修正
  - `list_projects()` → `get_all()`、`get_project()` → `get_by_id()` 等
- **H キー動作修正**: 6回の反復修正によりHome画面遷移を実現
  - 最終版: `isinstance(self.screen, HomeScreen)` 判定によるpopループ
  - Screen-level bindingをApp-level bindingに委譲
- **動作確認**: `python -m pmtool_textual.app` 起動成功、レビュー承認

コミット履歴:
- 85b151b: feat: Phase 5 グループ3実装（基本UI画面）
- c501e39: fix: Repositoryメソッド名修正
- cc5ed21～703c425: fix: H キー動作修正（6コミット）

### Phase 5 Group 2完了（2026-01-22）
テンプレート機能BL層（P5-04～P5-06）実装完了・ChatGPTレビュー承認:
- **P5-04**: TemplateRepository実装完了（CRUD操作）
- **P5-05**: TemplateManager基本実装完了（save/list/show/delete）
- **P5-06**: TemplateManager高度機能実装完了（apply、dry-run、外部依存検出）

### Phase 5 Group 1完了（2026-01-22）
基盤整備（P5-01～P5-03）実装完了・ChatGPTレビュー承認:
- **P5-01**: プロジェクト構造整備（pmtool_textualパッケージ作成）
- **P5-02**: Textual基本アプリケーション骨格（PMToolApp、BaseScreen）
- **P5-03**: DB接続管理モジュール（DBManager）

### Phase 5 設計完了（2026-01-22）
Textual UI + テンプレート機能の設計完了・実装着手可能:
- **テンプレート機能BL設計書（P5-9 v1.1.1）**: TemplateManager/TemplateRepository設計（ChatGPTレビュー承認）
  - SaveTemplateResult、ExternalDependencyWarning設計
  - own_connパターンによるトランザクション設計
  - 外部依存検出ロジック設計
- **Textual UI基本構造設計書（P5-12 v1.0.2）**: 7画面構成・Widget設計（ChatGPTレビュー承認）
  - Home, Project Detail, SubProject Detail, Template Hub, Save/Apply Wizard, Settings
  - キーバインド統一（ESC=Back, H=Home）
  - Textual 7.3.0バージョン固定
- **詳細実装計画書（P5-17 v1.0.1）**: 全16タスクの詳細実装手順（ChatGPTレビュー承認）
  - P5-01～P5-16の実装順序・マイルストーン（推定34時間）
  - 具体的なコード例・完了条件
  - 品質目標（テストカバレッジ80%）

### Phase 4 完了（2026-01-20）
品質・安定性向上・ドキュメント整備完了:
- **P4-01**: テストカバレッジ80.08%達成（71% → 80.08%、+9.08%）
  - test_commands_smoke.py（32本）: commands.py 37%→72%
  - test_input_coverage.py（16本）: input.py 100%達成
  - スモークテスト戦略の転換成功（出力一致 → DB状態変化＋例外なし確認）
- **P4-02〜P4-06**: 既存実装の確認・拡充（deps graph/chain/impact、dry-run拡張、doctor拡充、cascade_delete、エラーハンドリング改善）
- **P4-07**: ユーザードキュメント整備（~1,600行）
  - USER_GUIDE.md, TUTORIAL.md, FAQ.md 作成
  - ChatGPTレビュー承認・7箇所の改善反映
- **P4-08**: テンプレート機能仕様書作成（~780行）
  - 機能要件、設計原則、データ設計、コマンド仕様、Phase 5実装計画
  - ChatGPTレビュー承認

### Phase 3 P0完了（2026-01-18）
拡張機能実装（P0-01〜P0-08完了）:
- Project直下Task区画化（UX改善）
- deps list/graph/chain/impact コマンド実装
- 削除時の確認プロンプト、親文脈表示
- --bridge/--cascade オプション実装
- ステータスエラー時の詳細ヒント、理由タイプ表示
- pytest自動テスト導入（P0-08）

### Phase 2 実装完了・承認（2026-01-17）
CLI層の実装完了・ChatGPTレビュー承認:
- Rich + prompt_toolkit によるCLI実装
- argparseによるサブコマンド方式CLI
- 全コマンド実装（list, show, add, delete, status, deps, update, doctor）
- 設計レビュー指摘A-1～4、B-5～9すべて対応
- verify_phase2.py による動作確認完了

### Phase 1 フィードバック対応（2026-01-16）
ChatGPTによるコードレビューフィードバックに対応:
1. ✅ cascade_delete の無効化（NotImplementedError）
2. ✅ updated_at 更新漏れの修正（3箇所のupdateメソッド）
3. ✅ トランザクション原子性の修正（bridge_dependencies のコネクション共有）

### Phase 1 実装完了（2026-01-16）
コア機能の実装完了:
- CRUD操作（4階層すべて）
- 依存関係管理（DAG検証、レイヤー制約、橋渡し）
- ステータス管理（DONE遷移条件）
- 削除制御（子チェック、橋渡し削除）

### Phase 0 完了（2026-01-15）
基盤構築:
- DB設計 v2.1（FK制約、部分的UNIQUE INDEX）
- Database クラス実装
- 初期化スクリプト（init_db.sql）

## 更新履歴

- 2026-01-25: Phase 5 Group 5実装途中状態を反映（P5-13, P5-14完了、P5-15実装途中、P5-16未着手）
- 2026-01-24: Phase 5 Group 4完了状態を反映（テンプレート機能UI実装完了、DBコネクション管理改善）
- 2026-01-24: Phase 5 Group 3完了状態を反映（基本UI画面実装完了、H キー動作修正完了）
- 2026-01-22: Phase 5 Group 1-2完了状態を反映（基盤整備、テンプレート機能BL層実装完了）
- 2026-01-22: Phase 5設計完了状態を反映（BL設計書、UI設計書、詳細実装計画書承認）
- 2026-01-20: Phase 4完了状態を反映（P4-01〜P4-08全タスク完了、ユーザードキュメント整備、テンプレート仕様書作成）
- 2026-01-18: Phase 3 P0完了状態を反映（拡張機能、pytest導入）
- 2026-01-17: Phase 2 完了状態を反映（CLI層追加、コマンド一覧、検証スクリプト追加）
- 2026-01-17: Phase 1 完了状態を反映（実装済み機能、アーキテクチャ詳細追加）
- 2026-01-16: 初版作成（CLAUDE_TEMPLATE.mdベース）
