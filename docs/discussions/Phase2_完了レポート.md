# Phase 2（TUI実装）完了レポート

**作成日:** 2026-01-17
**フェーズ:** Phase 2
**ステータス:** 完了・承認済み

---

## 概要

Phase 2では、Phase 1で実装したビジネスロジック層の上に、Rich + prompt_toolkitを使用したTUI（Text User Interface）層を追加しました。argparseによるサブコマンド方式のCLIインターフェースを採用し、プロジェクト・タスク管理のすべての基本操作をコマンドラインから実行可能にしました。

---

## 実装成果物

### 新規作成ファイル

**TUI層（src/pmtool/tui/）:**
1. `__init__.py` - tuiパッケージ初期化
2. `formatters.py` - ステータスの記号・色付けフォーマッター
3. `input.py` - prompt_toolkit対話的入力処理
4. `display.py` - Rich表示ロジック（テーブル、ツリー、依存関係）
5. `cli.py` - argparse CLIエントリーポイント
6. `commands.py` - コマンドハンドラ（list, show, add, delete, status, deps）

**設定ファイル:**
7. `setup.py` - setuptools設定（CLIエントリーポイント）
8. `pyproject.toml` - 更新（依存関係、バージョン0.2.0、エントリーポイント）
9. `requirements.txt` - 更新（rich, prompt_toolkit）

**検証:**
10. `scripts/verify_phase2.py` - Phase 2検証スクリプト

---

## 実装された機能

### コマンド一覧

| コマンド | サブコマンド | 機能 |
|---------|------------|------|
| `list` | projects | Project一覧をRich Tableで表示 |
| `show` | project <id> | Project階層ツリーをRich Treeで表示（4階層、ステータス記号付き） |
| `add` | project/subproject/task/subtask | エンティティ追加（対話的入力サポート） |
| `delete` | project/subproject/task/subtask | エンティティ削除（標準削除・橋渡し削除） |
| `status` | task/subtask <id> <status> | ステータス変更（DONE遷移条件チェック） |
| `deps add` | task/subtask --from <id> --to <id> | 依存関係追加（サイクル検出） |
| `deps remove` | task/subtask --from <id> --to <id> | 依存関係削除 |
| `deps list` | task/subtask <id> | 依存関係一覧表示（親文脈併記） |

### 主要機能の詳細

#### 1. 階層ツリー表示（show project）
- Rich Treeによる視覚的な4階層表示
- ステータス記号による直感的な進捗確認
  - `[ ]` UNSET（未設定）
  - `[⏸]` NOT_STARTED（未開始）
  - `[▶]` IN_PROGRESS（進行中）
  - `[✓]` DONE（完了）
- Project直下Taskの区画化表示（UX改善）

#### 2. エンティティ追加（add）
- 必須項目の自動検証
- オプション項目の対話的入力サポート
- 親エンティティの存在確認
- 名前重複チェック

#### 3. エンティティ削除（delete）
- 標準削除：子エンティティ存在時はエラー
- 橋渡し削除（--bridge）：依存関係を再接続して削除
  - Task/SubTaskのみ適用可能
  - サイクル発生時は失敗
- 削除前の確認プロンプト

#### 4. ステータス管理（status）
- DONE遷移条件の厳密なチェック
  - すべての先行ノードがDONE
  - すべての子SubTaskがDONE
- 失敗時の理由明示（先行ノード未完了 / 子SubTask未完了）
- 詳細なヒントメッセージ

#### 5. 依存関係管理（deps）
- DAG制約の維持（サイクル検出）
- レイヤー分離（Task間・SubTask間のみ）
- 依存関係一覧での親文脈併記
  - Task: Project ID, SubProject ID
  - SubTask: Task ID

### エラーハンドリング強化

Phase 2設計レビューで指摘された以下の項目をすべて実装：

**必須指摘（A）:**
- A-1: `--bridge` オプションの適用範囲明示（Task/SubTaskのみ）
- A-2: 橋渡し削除時の確認文強化（再接続、循環時失敗を明記）
- A-3: DONE遷移失敗時の理由タイプ表示（先行未完了 / 子未完了）
- A-4: `deps add` の `--from / --to` を先行/後続として明示

**推奨指摘（B）:**
- B-5: 削除エラー時の対処方法案内
- B-6: 循環依存エラー時のヒント表示
- B-7: 依存関係一覧での親文脈併記
- B-8: 橋渡し削除後の案内表示
- B-9: Project直下Taskの区画化表示

---

## 検証結果

### verify_phase2.py 実行結果

すべてのテストケースが成功：

```
✓ すべての基本機能が正常に動作しました
✓ エラーハンドリングも期待通りに動作しました
✓ 依存関係管理（追加・削除・サイクル検出）が正常に動作しました
✓ ステータス管理（DONE遷移条件チェック）が正常に動作しました

Phase 2 MVP実装は成功です！
```

### テスト内容

1. Project一覧表示（空の状態）
2. Project追加
3. Project一覧表示（1件）
4. SubProject追加
5. Task追加（SubProject配下）
6. SubTask追加
7. Project階層ツリー表示
8. 依存関係追加（Task間）
9. 依存関係一覧表示
10. ステータス変更失敗テスト（先行ノード未完了）
11. ステータス変更（SubTask → DONE）
12. ステータス変更（Task1 → DONE）
13. サイクル検出テスト
14. 依存関係削除
15. SubTask削除（標準削除）
16. 最終ツリー表示

---

## ChatGPTレビュー結果

**結論:** Phase 2 完了承認

### 総合評価

- Phase 2設計書に基づいた実装が行われており、仕様逸脱・設計不整合なし
- Phase 1のビジネスロジック層を変更せず、TUI層のみを追加する構成が守られている
- 検証スクリプトによる動作確認が実施され、実行時に見つかった不具合も修正済み

### 設計レビュー差し戻し項目の反映状況

**必須指摘（A）:** すべて適切に反映済み
**推奨指摘（B）:** Phase 2の範囲として十分に対応済み

---

## Phase 3への引き継ぎ事項

以下は Phase 2 の完了を妨げるものではなく、将来的な改善余地として記録：

### 改善余地（優先度：低）

1. **DONE遷移失敗理由の判定強化**
   - 現状：例外メッセージの文字列パターンマッチング
   - 改善案：reason codeや例外型分離で堅牢化

2. **SubProjectの入れ子データ表示**
   - 現状：parent_subproject_id を含む場合の表示方針未定義
   - 改善案：将来的な仕様拡張時に対応

3. **表示順序の保証強化**
   - 現状：repository の取得順に依存
   - 改善案：ORDER BY order_index の明示的な指定

4. **絵文字・記号表示の端末依存対応**
   - 現状：Windows環境でUnicodeエラーが発生する場合がある
   - 改善案：フォールバック文字の提供、または環境検出による切り替え

### Phase 3 実装予定機能

Phase 1で未実装とした以下の機能の実装を検討：

- テンプレート機能（プロジェクト・タスク構造のテンプレート化）
- doctor/check バリデーション（データ整合性チェック）
- Dry-run プレビュー（操作前の影響確認）
- cascade_delete の正式実装（連鎖削除）

---

## 技術仕様

### 依存ライブラリ

- **rich** >= 13.0.0 - Rich text and beautiful formatting
- **prompt_toolkit** >= 3.0.0 - Interactive command line interface

### エントリーポイント

- コマンド名: `pmtool`
- モジュールパス: `pmtool.tui.cli:main`

### パッケージ構成

```
src/pmtool/
├── database.py          # Phase 1: DB接続・初期化
├── models.py            # Phase 1: エンティティモデル
├── repository.py        # Phase 1: CRUD操作
├── dependencies.py      # Phase 1: 依存関係管理
├── status.py            # Phase 1: ステータス管理
├── validators.py        # Phase 1: バリデーション
├── exceptions.py        # Phase 1: カスタム例外
└── tui/                 # Phase 2: TUI層（新規）
    ├── __init__.py
    ├── formatters.py
    ├── input.py
    ├── display.py
    ├── cli.py
    └── commands.py
```

---

## まとめ

Phase 2では、Phase 1で実装した堅牢なビジネスロジック層の上に、使いやすいTUI層を構築しました。設計レビューで指摘されたすべての項目に対応し、エラーハンドリングとユーザビリティを大幅に向上させました。

検証スクリプトによる動作確認、およびChatGPTによるレビューを経て、Phase 2は正式に完了承認されました。Phase 3以降の拡張機能実装に向けた安定した基盤が確立されています。

**Phase 2 実装完了日:** 2026-01-17
**レビュー承認日:** 2026-01-17
