# Phase 4 品質・安定性向上 設計書

**作成日:** 2026-01-19
**対象フェーズ:** Phase 4（品質・安定性向上）
**前提:** Phase 3（P0）完了・承認済み
**ステータス:** 確定版（ChatGPT承認済み）

---

## 目次

1. [概要](#1-概要)
2. [Phase 4 の目的と方針](#2-phase-4-の目的と方針)
3. [スコープ定義](#3-スコープ定義)
4. [実装順序](#4-実装順序)
5. [完了条件](#5-完了条件)
6. [個別機能設計](#6-個別機能設計)
7. [技術方針](#7-技術方針)
8. [リスクと制約](#8-リスクと制約)
9. [Phase 5 との境界](#9-phase-5-との境界)

---

## 1. 概要

### 1.1 Phase 4 の位置づけ

Phase 4 は、**CLI版（Rich/prompt_toolkit ベース）を完成状態にする最終フェーズ**です。

**Phase 1（完了）:**
- 4階層構造（Project → SubProject → Task → SubTask）
- CRUD操作、DAG依存関係管理、ステータス管理
- 削除制御（子チェック、橋渡し削除）

**Phase 2（完了）:**
- Rich + prompt_toolkit + argparse によるコマンド中心TUI（CLI）
- 基本操作コマンド（list, show, add, delete, status, deps）

**Phase 3（P0完了）:**
- Project直下Task区画化、deps list、削除確認、親文脈表示
- --bridge、ステータスエラーヒント、橋渡し説明、理由タイプ表示

**Phase 4（本フェーズ）:**
- **品質・安定性・安全性向上**が重心
- **CLI版を完成状態**にする
- **Phase 5（Textual版）には機能・品質タスクを持ち込まない**

### 1.2 Phase 4 の重心

- **テストカバレッジの拡充**: pytest-cov 導入、80%以上、TUI最低限含む
- **P1-01: 依存関係の可視化強化**: direct graph、dependency chain、影響範囲可視化
- **P1-02: dry-run の拡張**: status DONE、必要範囲での拡張
- **doctor/check の拡充**: 整合性チェック（DAG/FK/status/order_index）、Error/Warning分類
- **cascade_delete の正式実装**: --cascade --force 必須、--dry-run 前提、--bridge との排他維持
- **エラーハンドリング改善**: 原因＋解決ヒント、トランザクション安全性強化
- **ユーザードキュメント整備**: user guide、tutorial、FAQ

---

## 2. Phase 4 の目的と方針

### 2.1 目的

1. **品質保証の確立**: テストカバレッジ80%以上、エッジケース・境界値テスト完備
2. **安全性の強化**: dry-run、doctor/check、cascade_delete により誤操作・データ破損を防止
3. **使いやすさの向上**: 依存関係可視化、エラーメッセージ改善により運用負担を軽減
4. **CLI版の完成**: Phase 5（Textual版）に機能・品質タスクを持ち込まない

### 2.2 UI 方針（重要）

**Phase 4 は現行の Rich/prompt_toolkit 版を完成状態にする**

- Textual 等の全画面TUIは、**Phase 5 で別プログラム/別系統として扱う**
- Phase 4 では、コマンド中心TUIの枠組みを維持しつつ、品質・安全性に集中する
- **Phase 5 は Textual UI を中心とするフェーズ**
  - **例外として、テンプレート機能（P1-03）だけは Phase 5 で実装する**
  - それ以外の品質・保守タスクは持ち込まない

### 2.3 P1-03（テンプレート機能）の扱い（重要）

**Phase 4 では「仕様のみ確定」し、実装は行わない**

- **仕様確定**: テンプレート機能の要件・設計を文書化
- **実装しない**: CLI版には搭載しない
- **Phase 5 で実装**: Textual版（予定）にのみ実装する前提

### 2.4 対象外項目（Phase 4 / Phase 5 のどちらにも含めない）

以下の項目は、**Phase 4 / Phase 5 のどちらにも含めず**、将来のバックログとして扱います:

- **パフォーマンス最適化**（現状で十分な性能があると判断）
- **開発者ドキュメント整備**（将来のメンテナンスフェーズで検討）

---

## 3. スコープ定義

Phase 4 は **すべて必須項目**とし、完了条件に含めます。

### 3.1 必須項目（Phase 4 完了条件に含める）

| No | 項目 | 概要 | 実装難易度 |
|----|------|------|-----------|
| P4-01 | テストカバレッジ拡充 | pytest-cov 導入、80%以上、エッジケース・境界値・TUI最低限 | ★★★★☆ |
| P4-02 | P1-01：依存関係の可視化強化 | direct graph / chain 表示、影響範囲可視化 | ★★★☆☆ |
| P4-03 | P1-02：dry-run の拡張 | status DONE、必要範囲での拡張 | ★★☆☆☆ |
| P4-04 | doctor/check の拡充 | 整合性チェック拡充（DAG/FK/status/order_index）、Error/Warning分類 | ★★★☆☆ |
| P4-05 | cascade_delete の正式実装 | --cascade --force 必須、--dry-run 前提、--bridge との排他 | ★★★☆☆ |
| P4-06 | エラーハンドリング改善 | 原因＋解決ヒント、トランザクション安全性強化 | ★★☆☆☆ |
| P4-07 | ユーザードキュメント整備 | user guide、tutorial、FAQ | ★★☆☆☆ |
| P4-08 | P1-03：テンプレート機能（仕様のみ） | テンプレート機能の要件・設計を文書化（実装しない） | ★☆☆☆☆ |

---

## 4. 実装順序

品質基盤 → UX改善 → 安全性強化 → ドキュメント → 仕様確定 の順で進める。

1. **テスト基盤強化（P4-01）** - pytest-cov、エッジケース・境界値・TUI最低限
2. **依存関係可視化（P4-02）** - UX改善の要
3. **dry-run 拡張（P4-03）** - 安全性向上
4. **doctor/check（P4-04）** - データ整合性保証
5. **cascade_delete（P4-05）** - 破壊的操作の安全化
6. **エラーハンドリング改善（P4-06）** - ユーザビリティ向上
7. **ユーザードキュメント整備（P4-07）** - 利用促進
8. **テンプレート機能仕様確定（P4-08）** - Phase 5 への引き継ぎ準備

**理由:**
- テスト基盤を最初に整備し、以降の実装をテストで担保
- UX改善（依存可視化、dry-run）を早期に提供し、運用品質を向上
- 破壊的操作（cascade_delete）は、テスト基盤が整ってから実装
- ドキュメント整備は、機能実装が安定してから着手
- テンプレート仕様確定は、Phase 5 への引き継ぎ資料として最後に作成

---

## 5. 完了条件

### 5.1 品質

- **テストカバレッジ 80% 以上**（pytest-cov による測定）
- **エッジケース・境界値テスト完備**
- **TUI層の最低限の統合テスト完備**
- **Phase 3 までの主要機能を壊していない**（後方互換）

### 5.2 安全性

- **破壊的操作は dry-run により影響範囲を確認できる**
- **cascade_delete は --force 必須**で誤削除リスクを下げる
- **doctor/check で異常を検出できる**（Error/Warning分類明確）

### 5.3 使いやすさ

- **依存関係の可視化が充実**（direct graph、chain、影響範囲）
- **エラーメッセージが原因＋解決ヒント付き**
- **ユーザードキュメントが最低限整備されている**

### 5.4 ドキュメント

- 実装仕様書が更新されている
- ユーザードキュメント（user guide、tutorial、FAQ）が整備されている
- テンプレート機能仕様書が確定している（実装はしない）
- Phase 4 完了レポートが作成されている
- CLAUDE.md が最新状態に更新されている

### 5.5 Phase 5 への準備

- **CLI版が完成状態**になっている
- **Phase 5 に機能・品質タスクを持ち込まない**状態になっている
- **テンプレート機能仕様書**が Phase 5 への引き継ぎ資料として確定している

---

## 6. 個別機能設計

### 6.1 P4-01: テストカバレッジ拡充

#### 目的
- pytest-cov を導入し、カバレッジ 80% 以上を達成
- エッジケース・境界値テストを追加
- TUI層の最低限の統合テストを追加

#### 実装内容

**1. pytest-cov 導入**
```bash
pip install pytest-cov
pytest --cov=src/pmtool --cov-report=html
```

**2. カバレッジターゲット**
- **全体カバレッジ: 80% 以上**
- **コア層（repository, dependencies, status）: 90% 以上**
- **TUI層: 50% 以上**（最低限の統合テスト）

**カバレッジ計測範囲:**
- 計測対象: `src/pmtool` 配下のみ
- 除外対象: `tests/` ディレクトリ、`__init__.py`（空または import のみの場合）
- 設定: `pyproject.toml` または `.coveragerc` で明示

**3. テスト追加対象**

**エッジケース・境界値:**
- 空文字、NULL、巨大な値
- 境界値（0, 1, MAX）
- 同時実行、トランザクション競合（可能な範囲で）

**コア層（Phase 3 から継続）:**
- repository 層: CRUD操作、FK制約違反、トランザクション整合性
- dependencies 層: サイクル検出、レイヤー制約、橋渡し処理
- status 層: DONE遷移（成功/失敗）、reason code
- doctor 層: 代表的な異常検出、正常データでError=0
- validators 層: バリデーションエラー検出

**TUI層（Phase 4 で追加）:**
- CLIコマンドの統合テスト（最低限）
  - list projects
  - show project <id>
  - add/delete/status/deps の代表ケース
- 表示ロジックのテスト（可能な範囲で）

**TUI統合テストの実施方式:**
- 基本方針: **CLI引数パース → コマンドハンドラ呼び出し → 出力文字列確認**（擬似統合テスト）
- prompt_toolkit の完全E2Eは不安定になりがちなため、コマンドハンドラレベルでのテストを中心とする
- 必要に応じて subprocess での `pmtool` 実行も検討（CI環境次第）

#### 受け入れ条件（AC）
- pytest-cov が動作し、カバレッジ 80% 以上を達成
- エッジケース・境界値テストが追加されている
- TUI層の統合テストが最低限追加されている
- すべてのテストが安定してパスする

#### 影響範囲
- 新規ファイル: `tests/test_*_edgecases.py`（エッジケース・境界値テスト）
- 新規ファイル: `tests/test_tui_integration.py`（TUI統合テスト）
- 更新ファイル: `requirements.txt`（pytest-cov追加）
- 更新ファイル: `pyproject.toml`（カバレッジ設定追加）

---

### 6.2 P4-02: P1-01：依存関係の可視化強化

#### 目的
- 依存関係をより視覚的に理解しやすくする
- 複雑な依存関係の理解を支援する

#### 実装内容

**機能1: direct graph 表示**
- 直接先行ノード（direct predecessors）と直接後続ノード（direct successors）を表示

**機能2: dependency chain 表示**
- A → B → C → D のようなチェーン表示

**機能3: 影響範囲の可視化**
- あるTaskがDONEになると何が解放されるか（後続ノード一覧）

**コマンドI/F（案）:**
```bash
# direct graph
pmtool deps graph task 5

# dependency chain（from → to の経路）
pmtool deps chain task --from 3 --to 7

# 影響範囲（task 5 が DONE になると解放されるノード）
pmtool deps impact task 5
```

**表示例:**
```
$ pmtool deps graph task 5

=== Dependency Graph: Task 5 ===

Direct Predecessors (must be DONE first):
  → Task 3 (in Project 1 > SubProject 2) [DONE]
  → Task 4 (in Project 1 > SubProject 2) [IN_PROGRESS]

Direct Successors (waiting for this task):
  → Task 6 (in Project 1 > SubProject 2) [NOT_STARTED]
  → Task 8 (in Project 1 > SubProject 3) [NOT_STARTED]
```

#### 受け入れ条件（AC）
- direct graph が出力できる
- chain の有無を判定し、経路を表示できる
- impact の影響範囲を表示できる

#### 影響範囲
- 更新ファイル: `src/pmtool/dependencies.py`（パス探索ロジック追加）
- 更新ファイル: `src/pmtool/tui/display.py`（グラフ表示追加）
- 更新ファイル: `src/pmtool/tui/commands.py`（コマンドハンドラ追加）
- 更新ファイル: `src/pmtool/tui/cli.py`（サブコマンド追加）

---

### 6.3 P4-03: P1-02：dry-run の拡張

#### 目的
- ステータス変更の影響範囲を事前確認できるようにする
- 必要範囲で dry-run を拡張する

#### 実装内容

**機能1: status DONE の dry-run**
```bash
pmtool status task 5 DONE --dry-run
# 可否 + reason code を表示
```

**表示例:**
```
$ pmtool status task 5 DONE --dry-run

=== Dry-run: Set Task 5 to DONE ===

Result: ✗ Cannot transition to DONE

Reason:
  [PREREQUISITE_NOT_DONE] Task 4 (predecessor) is not DONE yet

Hint:
  First complete Task 4, then retry.

※ これは dry-run です。実際にはステータスは変更されません。
```

#### 受け入れ条件（AC）
- status DONE の dry-run で可否 + reason code が出る
- dry-run でDBが変化しない

**注記:**
- update操作のdry-runは、Phase 4では対象外とします（スコープ過剰を避けるため）

#### 影響範囲
- 更新ファイル: `src/pmtool/tui/commands.py`（dry-run ロジック拡張）
- 更新ファイル: `src/pmtool/tui/cli.py`（--dry-run フラグ追加）

---

### 6.4 P4-04: doctor/check の拡充

#### 目的
- データ整合性チェックを拡充し、異常を早期検出する
- Error/Warning 分類を明確化する

#### 背景
- Phase 3 では doctor/check の基盤が実装済み
- Phase 4 では、チェック項目を拡充し、Error/Warning 分類を明確化

#### 実装内容

**チェック項目（Phase 4 で拡充）:**

1. **親欠損 / 参照欠損（FK破綻相当）** - Phase 3 から継続
   - SubProject の project_id が存在しない
   - Task の subproject_id が存在しない
   - SubTask の task_id が存在しない
   - 依存関係の predecessor_id / successor_id が存在しない

2. **DAG サイクル検出** - Phase 3 から継続
   - Task間依存、SubTask間依存でサイクルが存在する

3. **禁止依存（レイヤ制約違反）** - Phase 3 から継続
   - cross-layer 依存（Task → SubTask など）が存在する

4. **ステータス不整合** - Phase 4 で拡充
   - 子SubTaskが未完了なのに親TaskがDONE
   - 先行Taskが未完了なのに後続TaskがDONE
   - **Phase 4 で追加（防御的検査）**: ステータス値の不正（UNSET/NOT_STARTED/IN_PROGRESS/DONE 以外）
     - 注記: DB設計上CHECK制約があり、通常経路では不正値は入らないが、DB破損・外部改変を想定した防御的検査として実装

5. **order_index 異常** - Phase 4 で拡充
   - 同一親内で重複している
   - **Phase 4 で追加**: 負の値が存在する
   - **Phase 4 で追加**: 欠番が存在する（0, 1, 3, 4... のように2が欠けている） → Warning

6. **SubProject 入れ子存在（Warning）** - Phase 3 から継続
   - parent_subproject_id が NULL でない SubProject を検出
   - Phase 4 でも機能対応しないため、Warning として報告

**Error/Warning 分類（Phase 4 で明確化）:**

**Error（データ整合性が破綻）:**
- FK破綻、DAGサイクル、レイヤー制約違反
- ステータス値不正、order_index負値、order_index重複

**Warning（運用上の注意喚起）:**
- order_index欠番
- SubProject入れ子存在

**出力形式（Phase 4 で改善）:**
```
=== Doctor Check Report ===

Summary:
  Errors:   3
  Warnings: 2

Errors:
  [E001] FK破綻: Task 5 の parent SubProject 3 が存在しません
  [E002] DAGサイクル: Task 7 → Task 8 → Task 7
  [E003] ステータス不整合: Task 10 は DONE だが、子SubTask 25 が IN_PROGRESS

Warnings:
  [W001] SubProject入れ子: SubProject 10 が parent_subproject_id=9 を持っています
  [W002] order_index欠番: Project 1 の SubProject で order_index 2 が欠けています

正常データ: ✗ (Errors: 3, Warnings: 2)
```

#### 受け入れ条件（AC）
- 意図的に異常データを作った場合に、該当項目が Error/Warning として検出される
- Error/Warning 分類が明確になっている
- 正常データでは Error が 0 件になる

#### 影響範囲
- 更新ファイル: `src/pmtool/doctor.py`（チェック項目拡充、分類明確化）
- 更新ファイル: `src/pmtool/tui/commands.py`（出力形式改善）

---

### 6.5 P4-05: cascade_delete の正式実装

#### 目的
- 子ノードを含めたサブツリー一括削除を可能にする
- 安全性を確保しつつ、運用効率を向上させる

#### 背景
- Phase 1 で `NotImplementedError` として無効化されていた機能
- Phase 3 でも未実装のまま
- プロジェクト全体の削除や、不要なサブツリーの効率的な削除に必要

#### 実装内容

**コマンドI/F:**
```bash
# dry-run で影響確認
pmtool delete project 1 --cascade --dry-run

# 実削除（--force 必須）
pmtool delete project 1 --cascade --force

# エラー（--force なし）
pmtool delete project 1 --cascade
# Error: cascade delete requires --force flag

# エラー（--bridge と排他）
pmtool delete task 5 --cascade --bridge
# Error: --cascade and --bridge are mutually exclusive
```

**安全設計（確定）:**
1. **実削除は --force 必須**
   - `--cascade` のみでは実行せず、エラーメッセージを表示
   - `--cascade --force` で初めて実削除される
2. **--bridge と排他**
   - 同時指定はエラー
3. **dry-run 前提**
   - `--cascade --dry-run` で削除対象の概要を表示
4. **トランザクションで一括実行**
   - 失敗時は rollback により、部分削除を防ぐ

**削除順序:**
- 子→親の順で再帰的に削除
- 依存関係は `ON DELETE CASCADE` により自動削除

**dry-run 表示例:**
```
$ pmtool delete project 1 --cascade --dry-run

=== Dry-run: Cascade Delete Project 1 ===

削除対象:
  Project: 1件
  SubProject: 3件
  Task: 12件
  SubTask: 25件

削除される依存関係:
  Task依存: 8件
  SubTask依存: 15件

※ これは dry-run です。実際には削除されません。
実行する場合は --cascade --force を指定してください。
```

#### 受け入れ条件（AC）
- `--cascade --dry-run` が動作し、DB が変化しない
- `--cascade --force` でサブツリーが削除される
- `--force` なしでエラーになる
- `--bridge` と同時指定でエラーになる
- 削除後に参照破綻が起きない（依存エッジが適切に消える）

#### 影響範囲
- 更新ファイル: `src/pmtool/repository.py`（cascade_delete 実装）
- 更新ファイル: `src/pmtool/tui/commands.py`（--cascade --force フラグ処理）
- 更新ファイル: `src/pmtool/tui/cli.py`（フラグ追加）

---

### 6.6 P4-06: エラーハンドリング改善

#### 目的
- エラーメッセージを改善し、ユーザーフレンドリーにする
- トランザクション安全性を整理・強化する

#### 実装内容

**1. エラーメッセージ改善**

**現状:**
```
Error: Cannot transition to DONE
```

**改善後:**
```
Error: Cannot transition Task 5 to DONE

Reason:
  [PREREQUISITE_NOT_DONE] Task 4 (predecessor) is not DONE yet

Hint:
  First complete Task 4, then retry.
```

**改善ポイント:**
- **原因の明示**: reason code により、エラーの原因を構造的に提示
- **解決ヒント**: 次に何をすべきかを具体的に提示
- **対象の明示**: どのエンティティで発生したエラーかを明示

**2. トランザクション安全性の整理・強化**

**レビュー対象:**
- own_conn パターンの一貫性確認
- ロールバック処理の漏れチェック
- トランザクション境界の明確化

**強化内容:**
- トランザクション境界のドキュメント化
- エラー時のロールバック保証
- 必要に応じてトランザクション分離レベルの調整（検討）

#### 受け入れ条件（AC）
- 主要なエラーメッセージが原因＋解決ヒント付きになっている
- トランザクション安全性のレビューが完了している
- エラー時のロールバックが保証されている

#### 影響範囲
- 更新ファイル: `src/pmtool/exceptions.py`（エラーメッセージ改善）
- 更新ファイル: `src/pmtool/tui/commands.py`（エラー表示改善）
- レビュー対象: `src/pmtool/repository.py`, `src/pmtool/dependencies.py`, `src/pmtool/status.py`

---

### 6.7 P4-07: ユーザードキュメント整備

#### 目的
- ユーザーガイド、チュートリアル、FAQを整備し、利用促進を図る

#### 実装内容

**1. ユーザーガイド（user guide）**

**内容:**
- インストール手順
- 基本的な使い方（コマンド一覧、オプション一覧）
- 4階層構造の説明
- ステータス管理の説明
- 依存関係管理の説明
- 削除操作の説明（通常削除、橋渡し削除、連鎖削除）

**ファイル:**
- `docs/user_guide.md`

**2. チュートリアル（tutorial）**

**内容:**
- 簡単なプロジェクト管理の例
  - プロジェクト作成
  - サブプロジェクト・タスク・サブタスク作成
  - ステータス更新
  - 削除
- 依存関係を使った例
  - 依存関係追加
  - DONE遷移条件の確認
  - 依存関係の可視化

**ファイル:**
- `docs/tutorial.md`

**3. FAQ、トラブルシューティング**

**内容:**
- よくある質問
  - FK制約違反の対処法
  - サイクル検出エラーの対処法
  - ステータス遷移エラーの対処法
- トラブルシューティング
  - データ整合性チェック（doctor）の実行方法
  - dry-runの使い方

**ファイル:**
- `docs/faq.md`

#### 受け入れ条件（AC）
- user guide、tutorial、FAQ が整備されている
- 最低限の内容が記載されている
- 実装と整合性が取れている

#### 影響範囲
- 新規ファイル: `docs/user_guide.md`
- 新規ファイル: `docs/tutorial.md`
- 新規ファイル: `docs/faq.md`

---

### 6.8 P4-08: P1-03：テンプレート機能（仕様のみ確定）

#### 目的
- テンプレート機能の要件・設計を文書化する
- **Phase 4 では実装しない**
- Phase 5（Textual版）への引き継ぎ資料として確定する

#### 実装内容

**文書化する内容:**

1. **要件定義**
   - よく使う SubProject 構造を再利用可能にする
   - テンプレート保存・一覧・適用の機能

2. **設計方針**
   - **SubProject テンプレート限定**（Project全体は扱わない）
   - **外部依存禁止**（テンプレート内部の依存のみ再現）
   - **適用時ステータスは原則 UNSET**（安全側）
   - **適用は破壊的操作扱い**として dry-run を提供

3. **コマンドI/F（案）**
   ```bash
   # テンプレート保存
   pmtool template save subproject 5 --name "開発タスク標準"

   # テンプレート一覧
   pmtool template list

   # テンプレート適用（dry-run）
   pmtool template apply "開発タスク標準" --to project 2 --dry-run

   # テンプレート適用（実行）
   pmtool template apply "開発タスク標準" --to project 2
   ```

4. **保存形式（案）**
   - **DB内テーブル** または **JSON/YAML**
   - テーブル設計（案）:
     - `templates` テーブル: id, name, created_at
     - `template_tasks` テーブル: template_id, task_order, name, description
     - `template_subtasks` テーブル: template_id, task_order, subtask_order, name, description
     - `template_dependencies` テーブル: template_id, from_order, to_order, dep_type

5. **適用時の処理（案）**
   - テンプレート内の Task/SubTask構造を複製
   - 内部依存関係を再現
   - 外部依存が存在する場合はエラー
   - ステータスは UNSET に初期化

6. **Phase 5 での実装方針**
   - Textual版でのUI設計
   - テンプレート管理画面の設計

**ファイル:**
- `docs/specifications/テンプレート機能_仕様書.md`

#### 受け入れ条件（AC）
- テンプレート機能仕様書が作成されている
- Phase 5 への引き継ぎ資料として十分な内容が記載されている
- **実装は行わない**ことが明記されている

#### 影響範囲
- 新規ファイル: `docs/specifications/テンプレート機能_仕様書.md`

---

## 7. 技術方針

### 7.1 コーディング規約

Phase 1/2/3 と同様の規約を維持：

- **命名規則**: 関数・変数は snake_case、クラスは PascalCase、定数は UPPER_SNAKE_CASE
- **型ヒント**: 積極的に使用
- **docstring**: 公開APIには必須
- **コメント**: 複雑なロジックには日本語コメント

### 7.2 トランザクション管理

Phase 1 で確立した own_conn パターンを継続：

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

### 7.3 dry-run の実装パターン

トランザクション + rollback により実現：

```python
def delete_with_dryrun(self, entity_id: int, dry_run: bool = False, conn=None):
    own_conn = False
    if conn is None:
        conn = self.db.connect()
        own_conn = True

    try:
        # 影響範囲の収集
        affected = self._collect_affected_entities(entity_id, conn)

        if dry_run:
            # dry-run: 影響範囲を表示して終了
            if own_conn:
                conn.rollback()  # dry-runでは必ずrollback
            return affected

        # 実削除
        self._perform_delete(entity_id, conn)

        if own_conn:
            conn.commit()
    except Exception as e:
        if own_conn:
            conn.rollback()
        raise
```

### 7.4 reason code の活用

Phase 3 で導入した reason code を活用：

```python
from enum import Enum

class StatusTransitionFailureReason(Enum):
    PREREQUISITE_NOT_DONE = "prerequisite_not_done"
    CHILD_NOT_DONE = "child_not_done"
    DEPENDENCY_CYCLE = "dependency_cycle"
    INVALID_TRANSITION = "invalid_transition"

class StatusTransitionError(Exception):
    def __init__(self, message: str, reason: StatusTransitionFailureReason):
        super().__init__(message)
        self.reason = reason
```

### 7.5 テスト方針

**カバレッジターゲット:**
- 全体: 80% 以上
- コア層（repository, dependencies, status）: 90% 以上
- TUI層: 50% 以上

**テスト戦略:**
- ユニットテスト中心（repository, dependencies, status, validators）
- インテグレーションテスト（doctor, cascade_delete、TUI統合）
- エッジケース・境界値テスト完備

**テストDB:**
- 各テストで独立したDBを使用（fixture活用）
- テスト間の相互影響を排除

---

## 8. リスクと制約

### 8.1 リスク

| リスク | 影響 | 対策 |
|--------|------|------|
| cascade_delete でのデータ喪失 | 高 | --force 必須、dry-run 提供、テスト充実 |
| テストカバレッジ80%達成の工数増 | 中 | 段階的にカバレッジを上げる、優先度設定 |
| doctor/check の誤検出 | 中 | テストでチェック項目の精度を担保 |
| エラーメッセージ改善による既存コード影響 | 低 | 段階的移行、既存動作を維持 |

### 8.2 制約

- **Phase 4 では Textual 化は行わない**（Phase 5 で別プログラム/別系統として扱う）
- **P1-03（テンプレート機能）は仕様のみ確定、実装しない**
- **--bridge と --cascade は排他**（同時指定は禁止）
- **パフォーマンス最適化・開発者ドキュメント整備は対象外**

---

## 9. Phase 5 との境界

### 9.1 Phase 4 の責務

- **CLI版を完成状態にする**
- **品質・安定性・安全性を確保する**
- **ユーザードキュメントを整備する**
- **テンプレート機能の仕様を確定する**

### 9.2 Phase 5 の責務

- **Textual 等の全画面TUIを別プログラム/別系統として開発**（Textual UI を中心とするフェーズ）
- **例外として、テンプレート機能（P1-03）のみを実装する**（Textual版のみ）
- **それ以外の品質・保守タスクは持ち込まない**

### 9.3 Phase 5 への引き継ぎ資料

- **Phase 4 完了レポート**
- **テンプレート機能仕様書**
- **CLAUDE.md（最新状態）**
- **ユーザードキュメント一式**

---

## 10. 補足事項

### 10.1 実装の柔軟性

本設計書は実装の指針を示すものであり、実装時に技術的により良い方法が見つかった場合は、方針を維持しつつ実装詳細を調整することを推奨します。

### 10.2 完了条件の明確化

Phase 4 は「CLI版の完成」を目指すため、完了条件を明確にし、Phase 5 に機能・品質タスクを持ち込まないことを重視します。

### 10.3 ChatGPT とのレビュー

本設計書は、作成後に ChatGPT によるレビューを受け、承認後に実装に移ります。

---

## 変更履歴

| 日付 | 変更内容 | 担当 |
|------|----------|------|
| 2026-01-19 | 初版作成（Phase 4 方針確定を基に設計書ドラフト作成） | Claude Code |
| 2026-01-19 | レビュー反映（要修正3点+推奨修正2点を反映） | Claude Code |
| 2026-01-19 | ChatGPT承認・確定版として配置 | Claude Code |

---

**以上**
