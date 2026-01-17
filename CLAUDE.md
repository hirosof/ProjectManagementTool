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

**現在のフェーズ:** Phase 2 完了（レビュー承認済み）

## 技術スタック

**言語:**
- Python 3.10+

**データベース:**
- SQLite3（外部キー制約、トリガー機能を活用）

**ライブラリ:**
- Phase 1: 標準ライブラリのみ（sqlite3, dataclasses, datetime）
- Phase 2: rich>=13.0.0, prompt_toolkit>=3.0.0

**ツール:**
- Claude Code
- ChatGPT

## プロジェクト構造

```
ProjectManagementTool/
├── src/pmtool/              # ソースコード
│   ├── database.py          # DB接続・初期化（Phase 1）
│   ├── models.py            # エンティティモデル（dataclass）（Phase 1）
│   ├── repository.py        # CRUD操作（Project, SubProject, Task, SubTask）（Phase 1）
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
├── docs/                    # ドキュメント
│   ├── README.md            # ドキュメント構造ガイド
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
- **`docs/design/DB設計書_v2.1_最終版.md`** - データベース設計の詳細
- **`docs/design/実装方針確定メモ.md`** - 実装方針の決定事項
- **`docs/design/Phase2_TUI設計書.md`** - Phase 2 TUI設計書

**Phase 1（ビジネスロジック層）:**
- **`src/pmtool/repository.py`** - CRUD操作の実装（1300行超の中核ファイル）
- **`src/pmtool/dependencies.py`** - 依存関係管理・DAG検証
- **`src/pmtool/status.py`** - ステータス管理ロジック

**Phase 2（TUI層）:**
- **`src/pmtool/tui/cli.py`** - CLIエントリーポイント（argparse）
- **`src/pmtool/tui/commands.py`** - コマンドハンドラ（list, show, add, delete, status, deps）
- **`src/pmtool/tui/display.py`** - Rich表示ロジック（テーブル、ツリー、依存関係）

## セットアップ手順

```bash
# 依存ライブラリのインストール
pip install -e .

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

### Phase 2: TUIインターフェース（完了）

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

## 未実装機能

### Phase 3: 拡張機能（予定）
- テンプレート機能（プロジェクト・タスク構造のテンプレート化）
- doctor/check バリデーション（データ整合性チェック）
- Dry-run プレビュー（操作前の影響確認）
- cascade_delete の正式実装（連鎖削除）

## テスト

**Phase 1:**
- `scripts/verify_phase1.py` による機能検証
- ビジネスロジック層の完全な動作確認

**Phase 2:**
- `scripts/verify_phase2.py` による機能検証
- TUI層の完全な動作確認
- 統合テスト（ビジネスロジック層 + TUI層）

**今後（Phase 3以降）:**
- pytest による自動テスト導入
- ユニットテスト・インテグレーションテストの充実

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
```

このパターンにより:
- 単独呼び出し時は自動的にトランザクション管理
- 親トランザクション内から呼び出された場合は、同一トランザクション内で実行

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

### Phase 2 実装完了・承認（2026-01-17）
TUI層の実装完了・ChatGPTレビュー承認:
- Rich + prompt_toolkit によるTUI実装
- argparseによるサブコマンド方式CLI
- 全コマンド実装（list, show, add, delete, status, deps）
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

- 2026-01-17: Phase 2 完了状態を反映（TUI層追加、コマンド一覧、検証スクリプト追加）
- 2026-01-17: Phase 1 完了状態を反映した更新（実装済み機能、アーキテクチャ詳細追加）
- 2026-01-16: 初版作成（CLAUDE_TEMPLATE.mdベース）
