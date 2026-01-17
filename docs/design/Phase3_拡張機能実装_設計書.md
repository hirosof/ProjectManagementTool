# Phase 3 拡張機能実装 設計書

**作成日:** 2026-01-18
**対象フェーズ:** Phase 3（拡張機能実装）
**前提:** Phase 2 完了・ChatGPTレビュー承認済み
**ステータス:** 設計確定

---

## 目次

1. [概要](#1-概要)
2. [Phase 3 の目的と方針](#2-phase-3-の目的と方針)
3. [スコープ定義](#3-スコープ定義)
4. [実装順序](#4-実装順序)
5. [完了条件](#5-完了条件)
6. [個別機能設計](#6-個別機能設計)
7. [技術方針](#7-技術方針)
8. [リスクと制約](#8-リスクと制約)
9. [Phase 4 以降への展望](#9-phase-4-以降への展望)

---

## 1. 概要

### 1.1 Phase 3 の位置づけ

Phase 3 は、Phase 1（ビジネスロジック層）・Phase 2（TUI層）で構築した基盤の上に、**運用支援・安全性・編集性**を中心とした拡張機能を追加するフェーズです。

**Phase 1（完了）:**
- 4階層構造（Project → SubProject → Task → SubTask）
- CRUD操作、DAG依存関係管理、ステータス管理
- 削除制御（子チェック、橋渡し削除）

**Phase 2（完了）:**
- Rich + prompt_toolkit + argparse によるコマンド中心TUI（CLI）
- 基本操作コマンド（list, show, add, delete, status, deps）

**Phase 3（本フェーズ）:**
- 編集機能（update）、データ検査（doctor/check）、プレビュー（dry-run）
- 連鎖削除（cascade_delete）、理由構造化（reason code）
- 表示改善（絵文字なし）、自動テスト（pytest）

### 1.2 Phase 3 の重心

- **編集（update）**: 削除→再作成に頼らず、名前・説明・表示順を安全に更新
- **検査（doctor/check）**: データ整合性の異常を早期検出し、運用事故を防ぐ
- **プレビュー（dry-run）**: 破壊的操作の影響範囲を事前確認し、誤操作を減らす
- **品質（pytest）**: 拡張に伴うリグレッションを抑え、今後の改修コストを下げる

---

## 2. Phase 3 の目的と方針

### 2.1 目的

1. **実用性の向上**: 編集機能により、実運用での操作効率を大幅に改善
2. **安全性の強化**: dry-run、doctor/check、reason codeにより誤操作・データ破損を防止
3. **保守性の向上**: pytestによる自動テストで、今後の機能追加時のリグレッションを抑制
4. **UI柔軟性**: 絵文字なし表示により、端末環境の多様性に対応

### 2.2 UI 方針（重要）

**Phase 3 は現行の Rich/prompt_toolkit 版を維持・拡張する（置換しない）**

- Textual 等の全画面TUIは、**将来フェーズで「別プログラムとして移植」**する
  - 失敗時も現行CLIが残る（フォールバック確保）
  - 置換による破壊リスクを避ける
- Phase 3 では、コマンド中心TUIの枠組みを維持しつつ、機能拡張に集中する

### 2.3 SubProject 入れ子の扱い（重要）

Phase 3 では、SubProject の入れ子（parent_subproject_id を活用した階層構造）について、以下の方針とする：

- **機能対応はしない**（表示・操作の実装は行わない）
- **doctor/check で存在検出し、Warning を出すのみ**
- 将来フェーズで対応を検討する

---

## 3. スコープ定義

Phase 3 は **P0（MVP）を完了したら Phase 3 完了**とし、P1 は余力で実施する。

### 3.1 P0（MVP：Phase 3 完了条件に含める）

| No | 機能 | 概要 | 実装難易度 |
|----|------|------|-----------|
| P0-01 | pytest 導入（枠組み） | pytest環境整備、スモークテスト実行 | ★☆☆☆☆ |
| P0-02 | reason code 基盤 | ステータス遷移理由の構造化（Enum化） | ★★☆☆☆ |
| P0-03 | doctor/check | データ整合性チェック（Error/Warning分類） | ★★★☆☆ |
| P0-04 | dry-run 基盤 | 削除操作のプレビュー表示 | ★★☆☆☆ |
| P0-05 | cascade_delete | サブツリー一括削除（--force必須、--bridge排他） | ★★☆☆☆ |
| P0-06 | update 系コマンド | name/description/order_index 更新 | ★☆☆☆☆ |
| P0-07 | 絵文字なし表示 | --no-emoji オプション追加 | ★☆☆☆☆ |
| P0-08 | pytest（テスト実装） | コア層の代表的テストケース追加 | ★★★☆☆ |

### 3.2 P1（拡張：余力で実施）

| No | 機能 | 概要 | 実装難易度 |
|----|------|------|-----------|
| P1-01 | 依存関係の可視化強化 | direct graph、依存パス表示 | ★★★☆☆ |
| P1-02 | dry-run の拡張 | status DONE、update操作のプレビュー | ★★☆☆☆ |
| P1-03 | テンプレート機能（最小仕様） | SubProjectテンプレ保存・適用 | ★★★★☆ |

### 3.3 P2（見送り：Phase 4 以降で検討）

- 検索・フィルタ・ソート
- SubProject 入れ子の表示・操作
- Textual 等の全画面TUI（別プログラム移植）

---

## 4. 実装順序

安全網 → 破壊操作 → 編集 → 表示 → 拡張 の順で進める。

1. **pytest導入（枠組み整備）** - テスト環境の構築
2. **reason code 基盤** - 理由構造化の基盤整備
3. **doctor/check** - データ整合性チェック（Warning/Error分類、入れ子Warning含む）
4. **dry-run 基盤** - プレビュー表示の枠組み
5. **cascade_delete** - サブツリー削除（dry-run + force + 排他）
6. **update系** - 編集機能（name/description/order_index）
7. **絵文字なし表示** - 表示オプション追加
8. **pytest（テスト実装）** - P0 テストケース追加
9. **（P1）依存可視化強化** - グラフ表示・パス表示
10. **（P1）テンプレ（最小仕様）** - SubProject限定

**理由:**
- pytest を最初に導入し、以降の実装をテストで担保しながら進める
- reason code は doctor/dry-run/status で共通利用するため、早期に基盤整備
- 破壊的操作（cascade_delete）は、dry-run 基盤が整ってから実装
- update系は比較的シンプルなため、後半に配置
- テスト実装は、P0機能がすべて揃ってから実施

---

## 5. 完了条件

### 5.1 機能完了

- **P0 項目がすべて実装されている**
- TUI上で以下の運用フローが成立する：
  - 作成 → 編集（update）→ 依存設定 → ステータス更新 → doctor/check → 削除（dry-run + 実行）

### 5.2 安全性

- **破壊的操作は dry-run により影響範囲を確認できる**
- **cascade_delete は --force 必須**で誤削除リスクを下げる
- **doctor/check で異常を検出できる**

### 5.3 品質

- **pytest（P0テスト）が安定してパスする**
- **Phase 2 までの主要機能を壊していない**（後方互換）

### 5.4 ドキュメント

- 実装仕様書が更新されている
- Phase 3 完了レポートが作成されている
- CLAUDE.md が最新状態に更新されている

---

## 6. 個別機能設計

### 6.1 P0-01: pytest 導入（枠組み）

#### 目的
- 自動テスト環境を整備し、以降の実装をテストで担保する基盤を作る

#### 実装内容
- pytest をプロジェクトに導入
- `tests/` ディレクトリを作成
- 最初のスモークテストが実行できる状態にする
- `pyproject.toml` に pytest 設定を追加

#### 受け入れ条件（AC）
- `pytest` 実行でテスト収集が成功する
- 1件以上のテストが実行される
- CI/CDで実行可能な状態になる

#### 影響範囲
- 新規ディレクトリ: `tests/`
- 更新ファイル: `pyproject.toml`, `requirements.txt`

---

### 6.2 P0-02: reason code 基盤

#### 目的
- ステータス遷移不可の理由を、メッセージ文字列依存から脱却し、構造化する

#### 背景
- Phase 2 では、例外メッセージの文字列パターンマッチングで原因を判定している
- この方法は脆弱で、メッセージ変更で判定ロジックが壊れるリスクがある

#### 実装内容
- ステータス遷移関連の例外に reason code（Enum）を付与
- 既存の「メッセージ文字列で原因判定」ロジックを段階的に除去
- reason code の種類（案）：
  - `PREREQUISITE_NOT_DONE` - 先行タスクが未完了
  - `CHILD_NOT_DONE` - 子SubTaskが未完了
  - `DEPENDENCY_CYCLE` - 依存関係にサイクルが存在
  - `INVALID_TRANSITION` - 無効な遷移
  - 他、必要に応じて追加

#### 受け入れ条件（AC）
- DONE遷移不可の代表ケースで reason code が安定して取得できる
- dry-run/doctor の出力で reason code を表示できる（最低1箇所）

#### 影響範囲
- 更新ファイル: `src/pmtool/exceptions.py`（reason code Enum追加）
- 更新ファイル: `src/pmtool/status.py`（例外に reason code 付与）
- 更新ファイル: `src/pmtool/tui/commands.py`（reason code 表示）

---

### 6.3 P0-03: doctor/check

#### 目的
- データベースの整合性をチェックし、異常を早期検出する

#### 実装内容

**コマンドI/F（案）:**
```bash
pmtool doctor
# または
pmtool check
```

**出力形式:**
```
=== Doctor Check Report ===

Summary:
  Errors:   2
  Warnings: 1

Errors:
  [E001] FK破綻: Task 5 の parent SubProject 3 が存在しません
  [E002] DAGサイクル: Task 7 → Task 8 → Task 7

Warnings:
  [W001] SubProject入れ子: SubProject 10 が parent_subproject_id=9 を持っています

正常データ: OK (Errors: 0)
```

**チェック項目（最低限）:**

1. **親欠損 / 参照欠損（FK破綻相当）**
   - SubProject の project_id が存在しない
   - Task の subproject_id が存在しない
   - SubTask の task_id が存在しない
   - 依存関係の predecessor_id / successor_id が存在しない

2. **DAG サイクル検出**
   - Task間依存、SubTask間依存でサイクルが存在する

3. **禁止依存（レイヤ制約違反）**
   - cross-layer 依存（Task → SubTask など）が存在する

4. **ステータス不整合**
   - 子SubTaskが未完了なのに親TaskがDONE
   - 先行Taskが未完了なのに後続TaskがDONE

5. **order_index 異常**
   - 同一親内で重複している
   - 欠番が存在する（0, 1, 3, 4... のように2が欠けている）

6. **SubProject 入れ子存在（Warning）**
   - parent_subproject_id が NULL でない SubProject を検出
   - Phase 3 では機能対応しないため、Warning として報告

#### 受け入れ条件（AC）
- 意図的に異常データを作った場合に、該当項目が Error/Warning として検出される
- 正常データでは Error が 0 件になる

#### 影響範囲
- 新規ファイル: `src/pmtool/doctor.py`（チェックロジック）
- 更新ファイル: `src/pmtool/tui/commands.py`（コマンドハンドラ追加）
- 更新ファイル: `src/pmtool/tui/cli.py`（サブコマンド追加）

---

### 6.4 P0-04: dry-run 基盤

#### 目的
- 破壊的操作の影響範囲を事前に確認し、誤操作を防ぐ

#### 実装内容

**対象操作（P0）:**
- `delete project <id> --dry-run`
- `delete subproject <id> --dry-run`
- `delete task <id> --dry-run`
- `delete subtask <id> --dry-run`
- `delete ... --bridge --dry-run`
- `delete ... --cascade --dry-run`（P0-05で実装）

**表示内容（最低限）:**
- 削除対象件数（階層別でも可）
- 削除対象のツリー（可能なら）
- 消える dependency edge 数（入/出）（可能なら）

**例:**
```bash
$ pmtool delete project 1 --dry-run

=== Dry-run: Delete Project 1 ===

削除対象:
  Project: 1件
  SubProject: 3件
  Task: 12件
  SubTask: 25件

削除される依存関係:
  Task依存: 8件
  SubTask依存: 15件

※ これは dry-run です。実際には削除されません。
実行する場合は --dry-run を外してください。
```

#### 技術方針
- トランザクション内で削除処理を実行し、最後に rollback することで実現
- `--dry-run` フラグが指定された場合、削除前に影響範囲を収集し、表示後に rollback

#### 受け入れ条件（AC）
- `--dry-run` で DB が変化しない（同一操作が繰り返し可能）
- dry-run 出力に「削除対象件数」または「削除対象ツリー」のいずれかが含まれる

#### 影響範囲
- 更新ファイル: `src/pmtool/tui/commands.py`（dry-run ロジック追加）
- 更新ファイル: `src/pmtool/tui/cli.py`（--dry-run フラグ追加）

---

### 6.5 P0-05: cascade_delete

#### 目的
- 子ノードを含めたサブツリー一括削除を可能にする

#### 背景
- Phase 1 で `NotImplementedError` として無効化されていた機能
- 現在は子が存在する場合は削除不可（ChildExistsError）
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
3. **dry-run 表示**
   - `--cascade --dry-run` で削除対象の概要を表示
4. **トランザクションで一括実行**
   - 失敗時は rollback により、部分削除を防ぐ

**削除順序:**
- 子→親の順で再帰的に削除
- 依存関係は `ON DELETE CASCADE` により自動削除

#### 受け入れ条件（AC）
- `--cascade --dry-run` が動作し、DB が変化しない
- `--cascade --force` でサブツリーが削除される
- `--bridge` と同時指定でエラーになる
- 削除後に参照破綻が起きない（依存エッジが適切に消える）

#### 影響範囲
- 更新ファイル: `src/pmtool/repository.py`（cascade_delete 実装）
- 更新ファイル: `src/pmtool/tui/commands.py`（--cascade --force フラグ処理）
- 更新ファイル: `src/pmtool/tui/cli.py`（フラグ追加）

---

### 6.6 P0-06: update 系コマンド

#### 目的
- 削除→再作成に頼らず、名前・説明・表示順を直接更新できるようにする

#### 背景
- Phase 2 では追加・削除のみ可能で、修正には削除→再作成が必要
- 実用上、タスク名や説明の修正は頻繁に発生する
- 削除→再作成は、ID変更・依存関係再設定が必要で非効率

#### 実装内容

**コマンドI/F（案）:**
```bash
# 名前更新
pmtool update project <id> --name "新しい名前"

# 説明更新
pmtool update task <id> --description "新しい説明"

# 表示順更新
pmtool update subtask <id> --order 5

# 複数項目同時更新
pmtool update project <id> --name "新名前" --description "新説明"
```

**対象エンティティ:**
- project
- subproject
- task
- subtask

**更新可能項目:**
- name
- description
- order_index

**注意点:**
- order_index 更新時は、Phase 3 では自動調整せず、単純更新のみ
  - 重複が発生する場合はエラーとする（UNIQUE制約違反）
  - 自動調整機能は Phase 4 以降で検討

#### 受け入れ条件（AC）
- 主要エンティティで name/description/order_index が更新できる
- 更新後に一覧/ツリー表示へ反映される
- 不正入力で適切にエラーになる
- Phase 2 の既存コマンド体系を壊さない

#### 影響範囲
- 更新ファイル: `src/pmtool/tui/commands.py`（update コマンドハンドラ追加）
- 更新ファイル: `src/pmtool/tui/cli.py`（update サブコマンド追加）
- repository.py には既に update_project, update_subproject, update_task, update_subtask が実装済み

---

### 6.7 P0-07: 絵文字なし表示

#### 目的
- 端末環境の多様性に対応し、絵文字が表示できない環境でも使えるようにする

#### 背景
- Phase 2 では、ステータス記号に絵文字を使用（`[⏸]`, `[▶]`, `[✓]`）
- Windows環境など、一部の端末で絵文字が正しく表示されない場合がある

#### 実装内容

**コマンドI/F（案）:**
```bash
# 絵文字なし表示
pmtool list projects --no-emoji
pmtool show project 1 --no-emoji

# デフォルト（絵文字あり）
pmtool list projects
```

**表示例:**
```
# 絵文字あり（デフォルト）
[✓] Task 1: 完了したタスク
[▶] Task 2: 進行中のタスク
[⏸] Task 3: 未着手のタスク
[ ] Task 4: 未設定のタスク

# 絵文字なし（--no-emoji）
[DONE] Task 1: 完了したタスク
[PROG] Task 2: 進行中のタスク
[TODO] Task 3: 未着手のタスク
[    ] Task 4: 未設定のタスク
```

**技術方針:**
- `src/pmtool/tui/formatters.py` に既にある `format_status_symbol()` を拡張
- グローバルフラグまたは関数引数で絵文字表示を切り替え

#### 受け入れ条件（AC）
- オプション指定時に絵文字が表示されない
- デフォルトで現行表示が維持される

#### 影響範囲
- 更新ファイル: `src/pmtool/tui/formatters.py`（絵文字なし表示ロジック）
- 更新ファイル: `src/pmtool/tui/cli.py`（--no-emoji フラグ追加）
- 更新ファイル: `src/pmtool/tui/commands.py`（フラグ処理）

---

### 6.8 P0-08: pytest（テスト実装）

#### 目的
- コア層の代表的なテストケースを追加し、リグレッションを防ぐ

#### 実装内容

**テスト対象（最低限）:**

1. **repository 層**
   - 作成/更新/削除（通常/bridge/cascade）の代表ケース
   - FK制約違反の検出
   - トランザクション整合性

2. **dependencies 層**
   - サイクル検出
   - 禁止依存（レイヤー制約）
   - 橋渡し処理

3. **status 層**
   - DONE遷移（成功ケース）
   - DONE遷移（失敗ケース：先行タスク未完了、子SubTask未完了）
   - reason code の取得

4. **doctor**
   - 代表的な異常の検出（FK破綻、サイクル、ステータス不整合）
   - 正常データで Error が 0 件

5. **validators 層**
   - バリデーションエラーの検出

**テスト戦略:**
- ユニットテスト中心（repository, dependencies, status, validators）
- インテグレーションテスト（doctor, cascade_delete）
- TUI層は優先度低（P1以降で検討）

**実行環境:**
- **Phase 3 では ローカル実行を必須条件とする**
- CI/CD（GitHub Actions等）での自動実行は Phase 4 以降で検討
- 開発者は実装完了前に `pytest` をローカルで実行し、パスを確認する

#### 受け入れ条件（AC）
- `pytest` がローカル環境で安定してパスする
- P0 対象の代表テストが実装されている

#### 影響範囲
- 新規ファイル: `tests/test_repository.py`
- 新規ファイル: `tests/test_dependencies.py`
- 新規ファイル: `tests/test_status.py`
- 新規ファイル: `tests/test_doctor.py`
- 新規ファイル: `tests/test_validators.py`

---

### 6.9 P1-01: 依存関係の可視化強化

#### 目的
- 複雑な依存関係の理解を支援する

#### 実装内容

**機能1: direct graph 表示**
- 直接先行ノード（direct predecessors）と直接後続ノード（direct successors）を表示

**機能2: 依存パス表示**
- from → to の到達パスが存在するかを判定し、経路を表示

**コマンドI/F（案）:**
```bash
# direct graph
pmtool deps graph task 5

# 依存パス
pmtool deps path task --from 3 --to 7
```

#### 受け入れ条件（AC）
- direct graph が出力できる
- path の有無を判定し、結果を表示できる

#### 影響範囲
- 更新ファイル: `src/pmtool/dependencies.py`（パス探索ロジック）
- 更新ファイル: `src/pmtool/tui/display.py`（グラフ表示）
- 更新ファイル: `src/pmtool/tui/commands.py`（コマンドハンドラ追加）

---

### 6.10 P1-02: dry-run の拡張

#### 目的
- ステータス変更やupdate操作のプレビューを可能にする

#### 実装内容

**機能1: status DONE の dry-run**
```bash
pmtool status task 5 DONE --dry-run
# 可否 + reason code を表示
```

**機能2: update操作の差分プレビュー（任意）**
```bash
pmtool update project 1 --name "新名前" --dry-run
# 変更前後の差分を表示
```

#### 受け入れ条件（AC）
- DONE dry-run で可否 + reason code が出る

#### 影響範囲
- 更新ファイル: `src/pmtool/tui/commands.py`（dry-run ロジック拡張）

---

### 6.11 P1-03: テンプレート機能（最小仕様）

#### 目的
- よく使う SubProject 構造を再利用可能にする

#### 制約（Phase 3）
- **SubProject テンプレート限定**（Project全体は扱わない）
- **外部依存禁止**（テンプレート内部の依存のみ再現）
- **適用時ステータスは原則 UNSET**（安全側）
- **適用は破壊的操作扱い**として dry-run を必須提供

#### 実装内容

**コマンドI/F（案）:**
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

**保存形式:**
- **Phase 3 では DB内テーブルに固定**
  - ファイル保存（JSON/YAML）は Phase 4 以降で検討
- テーブル設計（案）:
  - `templates` テーブル: id, name, created_at
  - `template_tasks` テーブル: template_id, task_order, name, description
  - `template_subtasks` テーブル: template_id, task_order, subtask_order, name, description
  - `template_dependencies` テーブル: template_id, from_order, to_order, dep_type

**適用時の処理:**
1. テンプレート内の Task/SubTask構造を複製
2. 内部依存関係を再現
3. 外部依存が存在する場合はエラー
4. ステータスは UNSET に初期化

#### 受け入れ条件（AC）
- 保存→適用で SubProject ツリーが複製される
- 外部依存がある場合にエラーとなる

#### 影響範囲
- 新規ファイル: `src/pmtool/template.py`
- 新規ディレクトリ: `data/templates/`（またはDB拡張）
- 更新ファイル: `src/pmtool/tui/commands.py`（コマンドハンドラ追加）

---

## 7. 技術方針

### 7.1 コーディング規約

Phase 1/2 と同様の規約を維持：

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

### 7.4 reason code の設計

Enum により構造化：

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

- **ユニットテスト**: repository, dependencies, status, validators 層
- **インテグレーションテスト**: doctor, cascade_delete
- **テストDB**: 各テストで独立したDBを使用（fixture活用）
- **カバレッジ**: P0では代表ケースのみ、P1以降で拡充

---

## 8. リスクと制約

### 8.1 リスク

| リスク | 影響 | 対策 |
|--------|------|------|
| cascade_delete でのデータ喪失 | 高 | --force 必須、dry-run 提供 |
| reason code 導入による既存コード影響 | 中 | 段階的移行、既存動作を維持 |
| pytest 導入による開発コスト増 | 中 | P0では代表ケースのみ実装 |
| doctor/check の誤検出 | 中 | 最低限のチェック項目に絞る |

### 8.2 制約

- **Phase 3 では Textual 化は行わない**（将来フェーズで別プログラムとして移植）
- **SubProject 入れ子は機能対応しない**（doctor Warning のみ）
- **テンプレート機能は SubProject 限定**（Project全体は扱わない）
- **--bridge と --cascade は排他**（同時指定は禁止）

---

## 9. Phase 4 以降への展望

### 9.1 Phase 4 候補機能

- **検索・フィルタ・ソート**: 大規模プロジェクトでの操作性向上
- **SubProject 入れ子の表示・操作**: 階層構造の完全サポート
- **doctor/check の拡張**: より詳細なチェック項目追加
- **テンプレート機能の拡張**: Project全体のテンプレート化
- **全画面TUI（Textual）**: 別プログラムとして移植

### 9.2 保守性向上

- **テストカバレッジの拡充**: TUI層のテスト追加
- **CI/CD環境の構築**: GitHub Actions 等による自動テスト
- **ドキュメントの充実**: ユーザーガイド、開発者ガイド

---

## 10. 補足事項

### 10.1 コマンド名・オプション名の調整

本設計書では仮のコマンド名・オプション名を使用している箇所があります（例: `--no-emoji`, `pmtool doctor`）。実装時には、既存のCLI体系に合わせて最終決定してください。

### 10.2 doctor/check の網羅性

P0 では「代表的なチェック項目」を重視し、網羅性は Phase 4 以降で拡張する方針です。

### 10.3 実装の柔軟性

本設計書は実装の指針を示すものであり、実装時に技術的により良い方法が見つかった場合は、方針を維持しつつ実装詳細を調整することを推奨します。

---

## 変更履歴

| 日付 | 変更内容 | 担当 |
|------|----------|------|
| 2026-01-18 | 初版作成（ChatGPT議論結果を基に設計書確定） | Claude Code |

---

**以上**
