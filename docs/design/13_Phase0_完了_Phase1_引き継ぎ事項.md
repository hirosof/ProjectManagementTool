# Phase 0 完了 → Phase 1 引き継ぎ事項

**作成日**: 2026-01-16
**Phase 0 完了日**: 2026-01-16
**次フェーズ**: Phase 1（コア機能実装）

---

## Phase 0 完了サマリー

### ✅ 実装完了項目

1. **プロジェクト構造の最小セットアップ**
   - `src/pmtool/` パッケージ作成
   - `pyproject.toml`, `requirements.txt` 設定
   - `.gitignore` 更新

2. **DB初期化SQL作成**
   - `scripts/init_db.sql` (DB設計書 v2.1 準拠)
   - Phase 0対象テーブル（7テーブル）のみ実装
   - 部分UNIQUEインデックス実装（SQLite UNIQUE+NULL問題対応）

3. **SQLite接続および初期化確認**
   - `src/pmtool/database.py` モジュール作成
   - `scripts/verify_init.py` 検証スクリプト作成
   - 初期化検証実行・成功確認

### ✅ レビュー完了

すべての成果物がChatGPTによるレビューを通過:
- init_db.sql ✅
- database.py ✅（PRAGMA注意事項追加、initialize()ガード追加）
- verify_init.py ✅
- 実装完了レポート ✅
- pyproject.toml / requirements.txt ✅

---

## Phase 0 成果物一覧

### コード

1. `src/pmtool/__init__.py` - パッケージ初期化
2. `src/pmtool/database.py` - データベース管理モジュール
3. `scripts/init_db.sql` - DB初期化SQL（Phase 0対象）
4. `scripts/verify_init.py` - 初期化検証スクリプト

### 設定ファイル

5. `pyproject.toml` - プロジェクト設定
6. `requirements.txt` - 依存関係
7. `.gitignore` - Git管理設定（更新）

### データベース

8. `data/pmtool.db` - SQLiteデータベース（自動生成、.gitignore対象）

### ドキュメント（temp/）

9. `1_プロジェクト管理ツール_ClaudeCode仕様書.md` - 公式仕様書
10. `2_ClaudeCodeからの確認事項.md` - 初期確認事項
11. `3_プロジェクト管理ツール_実装方針確定メモ.md` - 実装方針（D1〜D7）
12. `4_DB設計書.md` - DB設計書 v1
13. `5_DB設計書_Review_by_ChatGPT.md` - v1レビュー
14. `6_DB設計書_v2_修正版.md` - DB設計書 v2
15. `7_DB設計書_v2_修正版_Review_by_ChatGPT.md` - v2レビュー
16. `8_DB設計書_v2.1_最終版.md` - **DB設計書 v2.1（最終版）** ⭐
17. `9_Phase0_実装完了レポート.md` - Phase 0実装完了レポート
18. `10_Phase0_レビュー対応完了レポート.md` - レビュー対応レポート
19. `11_Phase0_レポート最終確認事項.md` - 最終確認事項
20. `12_Phase0_pyproject_requirements_確認用.md` - 設定ファイル確認
21. `13_Phase0_完了_Phase1_引き継ぎ事項.md` - 本ファイル

---

## 重要な設計決定事項

### DB設計（v2.1 最終版）

**ファイル**: `temp/8_DB設計書_v2.1_最終版.md`

#### 主要な設計方針

1. **FK削除動作**
   - 親子関係: `ON DELETE RESTRICT`（アプリが明示的に削除制御）
   - 依存関係: `ON DELETE CASCADE`（削除時の自動クリーンアップ）

2. **UNIQUE + NULL 問題対応**
   - SQLiteの部分UNIQUEインデックスで解決
   - `idx_subprojects_unique_project_direct` / `idx_subprojects_unique_nested`
   - `idx_tasks_unique_project_direct` / `idx_tasks_unique_subproject`

3. **order_index**
   - 0始まり
   - `CHECK(order_index >= 0)` 制約

4. **タイムスタンプ**
   - UTC固定（`datetime('now')`）
   - `updated_at` はアプリ側で明示的に更新

5. **外部キー制約**
   - 接続単位で設定（`PRAGMA foreign_keys = ON`）
   - **必ず `Database` クラス経由で接続すること**

### 実装方針（D1〜D7）

**ファイル**: `temp/3_プロジェクト管理ツール_実装方針確定メモ.md`

- **D1**: Python + textual + SQLite（標準ライブラリ）
- **D2**: order整数カラム方式
- **D3**: SubProject入れ子は DB に `parent_subproject_id` を持たせるが、MVP では操作不可
- **D4**: doctor/check の検査範囲（Error/Warning）
- **D5**: UNSET は手動設定・解除可能
- **D6**: 子持ち削除デフォルト禁止、明示フラグで連鎖削除
- **D7**: 依存関係は2テーブル方式

---

## Phase 1 への引き継ぎ事項

### Phase 1 の範囲

**ファイル**: `temp/2_ClaudeCodeからの確認事項.md` の「補足: 実装フェーズの提案」

1. **CRUD操作の実装**
   - Project, SubProject, Task, SubTask の基本操作
   - `updated_at` の自動更新

2. **依存関係管理**
   - 依存関係の追加・削除
   - DAG循環検出
   - レイヤ跨ぎ依存チェック

3. **ステータス管理**
   - ステータス変更
   - DONE遷移条件チェック

4. **削除制御**
   - 子ノード存在チェック
   - 依存関係の橋渡し処理
   - 連鎖削除（強制フラグ）

### Phase 1 で実装しないこと

- TUI実装（Phase 2）
- テンプレート機能（Phase 3）
- doctor/check機能（Phase 3）
- dry-runプレビュー（Phase 3）

---

## 重要な制約・注意事項

### 1. 外部キー制約の接続単位

**重要**: `PRAGMA foreign_keys` は接続単位で設定されます。

- **必ず** `Database` クラス経由で接続すること
- `sqlite3.connect()` を直接使用しないこと
- `Database.connect()` が自動的に `PRAGMA foreign_keys = ON` を実行

**参考**: `src/pmtool/database.py` のモジュールdocstring

### 2. updated_at の更新

- SQLiteはトリガーなしで `updated_at` を自動更新できない
- **アプリケーション側で明示的に更新すること**
- INSERT/UPDATE時に `updated_at = datetime.utcnow().isoformat()` を設定

### 3. 部分UNIQUEインデックス

- `subprojects`: `parent_subproject_id` が NULL の場合の名前重複防止
- `tasks`: `subproject_id` が NULL の場合の名前重複防止
- SQLiteの UNIQUE + NULL 問題に対応済み

### 4. 削除操作の実装方針（D6）

- **通常削除**: 子ノード存在チェック → エラー
- **連鎖削除**: 強制フラグ付き + dry-run プレビュー
- **依存関係の橋渡し**: 削除前に直接先行・直接後続を再接続

---

## 技術的な判断履歴

### 1. Unicode出力問題の対応

**問題**: Windows環境でUnicode文字が表示できない

**対応**: `sys.stdout` を UTF-8 でラップ

```python
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

### 2. initialize()の初期化済みチェック

**問題**: 初期化済みDBに対して再実行すると失敗

**対応**: `force` パラメータを追加

- `force=False`（デフォルト）: `RuntimeError` を発生
- `force=True`: 既存テーブルを削除してから再初期化

### 3. データベースファイルのパス

**現状**: `data/pmtool.db` 固定

**将来**: Phase 2 以降で環境変数・設定ファイル対応を検討

---

## Phase 1 実装時の注意事項

### 仕様準拠

- **公式仕様書**: `temp/1_プロジェクト管理ツール_ClaudeCode仕様書.md`
- **実装方針**: `temp/3_プロジェクト管理ツール_実装方針確定メモ.md`
- **DB設計**: `temp/8_DB設計書_v2.1_最終版.md`

これらに厳密に準拠すること。

### Phase 1 の範囲外に踏み出す判断が必要な場合

**実装を止めて提示すること**

例:
- 仕様に明記されていない機能の追加
- DB設計の変更
- 実装方針（D1〜D7）の変更

### ChatGPT との連携

- 実装前の議論を重視
- 不明点は推測で進めず、必ず確認を取る
- 複数の実装方法がある場合は提案して選択してもらう

---

## 参考資料

### 公式ドキュメント

1. **仕様書**: `temp/1_プロジェクト管理ツール_ClaudeCode仕様書.md`
2. **実装方針**: `temp/3_プロジェクト管理ツール_実装方針確定メモ.md`
3. **DB設計**: `temp/8_DB設計書_v2.1_最終版.md`

### Phase 0 レポート

4. **実装完了レポート**: `temp/9_Phase0_実装完了レポート.md`
5. **レビュー対応レポート**: `temp/10_Phase0_レビュー対応完了レポート.md`

### コード

6. **database.py**: `src/pmtool/database.py`
7. **init_db.sql**: `scripts/init_db.sql`

---

## データベーススキーマ（Phase 0 対象）

### テーブル一覧

1. `schema_version` - スキーマバージョン管理
2. `projects` - プロジェクト
3. `subprojects` - サブプロジェクト
4. `tasks` - タスク
5. `subtasks` - サブタスク
6. `task_dependencies` - タスク間依存関係
7. `subtask_dependencies` - サブタスク間依存関係

### Phase 3 で追加予定

- `templates` - テンプレート定義
- `template_nodes` - テンプレート内ノード情報
- `template_dependencies` - テンプレート内依存関係

---

## Phase 1 の推奨アプローチ

### 1. モジュール構成案

```
src/pmtool/
├── __init__.py          # パッケージ初期化
├── database.py          # データベース接続（Phase 0 完了）
├── models.py            # データモデル（Phase 1）
├── repository.py        # CRUD操作（Phase 1）
├── dependencies.py      # 依存関係管理（Phase 1）
├── status.py            # ステータス管理（Phase 1）
└── validators.py        # バリデーション（Phase 1）
```

### 2. 実装順序案

1. **データモデル定義** (`models.py`)
   - Project, SubProject, Task, SubTask クラス
   - dataclass または NamedTuple

2. **CRUD操作** (`repository.py`)
   - 基本的な CREATE, READ, UPDATE, DELETE
   - `updated_at` の自動更新

3. **依存関係管理** (`dependencies.py`)
   - 依存関係の追加・削除
   - DAG循環検出
   - レイヤ跨ぎ依存チェック

4. **ステータス管理** (`status.py`)
   - ステータス変更
   - DONE遷移条件チェック

5. **削除制御** (repository.py に統合)
   - 子ノード存在チェック
   - 依存関係の橋渡し処理
   - 連鎖削除（強制フラグ）

### 3. テスト方針

- pytest を使用
- 各モジュールごとにテストファイル作成
- DB操作はトランザクションでロールバック可能にする

---

## Phase 0 完了確認

- [x] プロジェクト構造セットアップ
- [x] DB初期化SQL作成
- [x] SQLite接続・初期化確認
- [x] すべての成果物のレビュー完了
- [x] 引き継ぎドキュメント作成

**Phase 0 は正常に完了しました。Phase 1 に進行可能です。**

---

（以上）
