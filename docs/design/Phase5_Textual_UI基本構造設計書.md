# Textual UI 基本構造設計書

**バージョン:** 1.0.2
**作成日:** 2026-01-21
**更新日:** 2026-01-22
**対象フェーズ:** Phase 5（Textual版）
**ステータス:** 承認済み（実装可能）

---

## 目次

1. [概要](#1-概要)
2. [設計方針](#2-設計方針)
3. [画面構成](#3-画面構成)
4. [画面遷移](#4-画面遷移)
5. [Widget構成](#5-widget構成)
6. [キーバインド](#6-キーバインド)
7. [ビジネスロジック層との接続](#7-ビジネスロジック層との接続)
8. [エラーハンドリング](#8-エラーハンドリング)

---

## 1. 概要

### 1.1 目的

本設計書は、Phase 5で実装する**Textual UIの基本構造**を定義します。

### 1.2 スコープ

**対象:**
- 全画面TUIアプリケーションの基本構造
- 画面構成と遷移フロー
- Widget構成とレイアウト
- キーバインド設計

**対象外（Phase 6以降）:**
- 検索・絞り込み機能
- メモ機能
- 複数DB管理

### 1.3 前提条件

**Phase 5設計整理結果より:**
- Project直下Taskは**表示のみ**（操作はCLI版）
- テンプレート適用先は**新SubProject固定**
- テンプレート名リネームは**不可**（削除→再作成）
- 設計思想: **「安全に増やすUI」**

---

## 2. 設計方針

### 2.1 基本方針

#### 方針1: シンプルな画面構成
- 画面数を最小限に抑える（迷路化しない）
- 主要な操作は3操作以内で完了（キーボード操作を想定）
- 階層は深くても2階層まで

#### 方針2: キーボード中心の操作
- すべての操作をキーボードのみで完結
- マウス操作は補助的（使えるが必須ではない）
- ショートカットキーを一貫して配置

#### 方針3: 閲覧と作成の分離
- 閲覧画面: Project一覧、詳細表示
- 作成画面: Template保存・適用
- 編集は最小限（CLI版に委譲）

#### 方針4: 確認・dry-runの徹底
- 破壊的操作の前には必ず確認
- テンプレート適用時はdry-runを必須表示
- キャンセル可能なフロー

---

## 3. 画面構成

### 3.1 画面一覧

Phase 5では以下の7画面を実装します：

| 画面名 | 役割 | 主な操作 |
|--------|------|----------|
| **Home** | Project一覧表示 | Project選択、Template Hubへ遷移 |
| **Project Detail** | Project詳細（4階層ツリー） | 閲覧、SubProject選択 |
| **SubProject Detail** | SubProject詳細 | 閲覧、Template保存へ遷移 |
| **Template Hub** | Template一覧・管理 | Template選択、適用・削除 |
| **Template Save Wizard** | Template保存ウィザード | SubProject選択、名前入力、保存 |
| **Template Apply Wizard** | Template適用ウィザード | Project選択、dry-run確認、適用 |
| **Settings** | 設定画面（最小） | DBファイルパス表示、バックアップ案内 |

### 3.2 各画面の詳細

#### 3.2.1 Home（Project一覧）

**役割:**
- アプリケーションのエントリーポイント
- Project一覧を表示

**主な操作:**
- Project選択 → Project Detail へ遷移
- `T` キー → Template Hub へ遷移
- `S` キー → Settings へ遷移
- `Q` キー → アプリケーション終了

**表示内容:**
- Project一覧（Tableウィジェット）
  - ID、名前、説明、ステータス、更新日時
- ヘッダー: アプリケーション名、現在のDB名
- フッター: キーバインドヒント

**遷移元:** -（起動時の初期画面）
**遷移先:** Project Detail, Template Hub, Settings

---

#### 3.2.2 Project Detail（Project詳細）

**役割:**
- 選択したProjectの4階層構造を表示
- SubProject選択の起点

**主な操作:**
- SubProject選択 → SubProject Detail へ遷移
- `B` キー → Home へ戻る
- `ESC` キー → Home へ戻る

**表示内容:**
- Project情報（上部パネル）
  - ID、名前、説明、ステータス
- 4階層ツリー（中央パネル）
  - SubProject（選択可能）
  - **「Project直下のTask」区画**（表示のみ、選択不可）
    - Task（Project直下）← **グレーアウト表示**
  - SubProject配下（選択可能）
    - Task
      - SubTask
- ステータス記号: `[ ]` UNSET, `[⏸]` NOT_STARTED, `[▶]` IN_PROGRESS, `[✓]` DONE

**注意事項:**
- **Project直下Taskの表示方針**:
  - 「Project直下のTask」という区画として分離表示
  - グレーアウト表示（操作不可を視覚的に示す）
  - 選択不可、操作はCLI版に委譲
  - この区画はUX改善のための表示のみ（Phase 3 P0-01で導入済み）
- SubProject選択のみ可能

**遷移元:** Home
**遷移先:** SubProject Detail, Home

---

#### 3.2.3 SubProject Detail（SubProject詳細）

**役割:**
- SubProject配下のTask/SubTask構造を表示
- Template保存の起点

**主な操作:**
- `S` キー → Template Save Wizard へ遷移（このSubProjectを保存）
- `B` キー → Project Detail へ戻る
- `ESC` キー → Project Detail へ戻る

**表示内容:**
- SubProject情報（上部パネル）
  - ID、名前、説明、ステータス、親Project名
- Task/SubTaskツリー（中央パネル）
  - Task
    - SubTask
- ステータス記号表示

**遷移元:** Project Detail
**遷移先:** Template Save Wizard, Project Detail

---

#### 3.2.4 Template Hub（Template一覧・管理）

**役割:**
- 保存済みTemplate一覧の表示
- Template適用・削除の起点

**主な操作:**
- Template選択 + `A` キー → Template Apply Wizard へ遷移
- Template選択 + `D` キー → 削除確認ダイアログ表示
- `B` キー → Home へ戻る
- `ESC` キー → Home へ戻る

**表示内容:**
- Template一覧（Tableウィジェット）
  - ID、名前、説明、include_tasks、作成日時
- Template詳細プレビュー（右側パネル）
  - 選択中Templateの構造サマリ（件数表示）
  - Task名一覧（include_tasks=Trueの場合）

**遷移元:** Home
**遷移先:** Template Apply Wizard, Home

---

#### 3.2.5 Template Save Wizard（Template保存）

**役割:**
- SubProjectをTemplateとして保存

**主な操作:**
- ステップ1: SubProject確認（既に選択済み）
- ステップ2: include_tasks ON/OFF選択
- ステップ3: Template名・説明入力
- ステップ4: 確認画面
  - テンプレート名重複チェック
  - 外部依存警告表示（ある場合）
  - 続行/キャンセル
- `C` キー → キャンセル、SubProject Detail へ戻る

**表示内容:**
- ステップインジケーター（上部）
- 各ステップの入力フォーム
- 確認画面:
  - 保存内容サマリ
  - 外部依存警告（赤字で表示）
  - 「この内容で保存しますか？」

**フロー:**
```
SubProject Detail
  ↓ `S` キー
Step 1: SubProject確認（名前・説明表示）
  ↓ Enter
Step 2: include_tasks選択（デフォルト: OFF）
  ↓ Enter
Step 3: Template名・説明入力
  ↓ Enter
Step 4: 確認画面（保存実行前のプレビュー）
  - テンプレート名重複チェック（get_template_by_name）
    → 重複時は警告、Step 3へ戻る
  - 外部依存検出・表示（_detect_external_dependencies呼び出し）
    → 警告がある場合は表示、続行確認
  - 保存内容サマリ表示
  ↓ Enter（続行） or C（キャンセル）
保存実行（save_template） → 完了メッセージ → SubProject Detail へ戻る
```

**重要な設計判断:**
- Step 4では`save_template()`を呼ばず、事前チェックのみ実施
  - テンプレート名重複: `get_template_by_name()`で確認
  - 外部依存検出: `_detect_external_dependencies()`で警告取得
- ユーザーが「続行」を選択した場合のみ、`save_template()`を実行
- これにより、ユーザーがキャンセルした場合でもDB操作は発生しない

**遷移元:** SubProject Detail
**遷移先:** SubProject Detail（保存完了 or キャンセル）

---

#### 3.2.6 Template Apply Wizard（Template適用）

**役割:**
- Templateを適用し、新SubProjectを作成

**主な操作:**
- ステップ1: Template確認（既に選択済み）
- ステップ2: 適用先Project選択
- ステップ3: dry-run結果表示
  - 件数サマリ（SubProject: 1, Task: X, SubTask: Y）
  - 1階層ツリー（SubProject名 + 直下Task名）
- ステップ4: 実行確認
- `C` キー → キャンセル、Template Hub へ戻る

**表示内容:**
- ステップインジケーター（上部）
- dry-run結果（ステップ3）:
  ```
  作成内容:
  - SubProject: 1
  - Task: 5
  - SubTask: 12
  - 依存関係: 3

  [新SubProject] 開発フロー
  ├── [Task] 要件定義
  ├── [Task] 設計 (SubTasks: 3)
  ├── [Task] 実装 (SubTasks: 5)
  ├── [Task] テスト (SubTasks: 4)
  └── [Task] リリース
  ```
- 実行確認（ステップ4）:
  - 「この内容で適用しますか？」
  - 「すべてのステータスはUNSETで初期化されます」

**フロー:**
```
Template Hub
  ↓ Template選択 + `A` キー
Step 1: Template確認（名前・説明表示）
  ↓ Enter
Step 2: 適用先Project選択（一覧から選択）
  ↓ Enter
Step 3: dry-run結果表示
  ↓ Enter
Step 4: 実行確認
  ↓ Enter（実行） or C（キャンセル）
適用実行 → 完了メッセージ → 作成されたSubProject Detailへ遷移
```

**遷移元:** Template Hub
**遷移先:** SubProject Detail（適用完了）, Template Hub（キャンセル）

---

#### 3.2.7 Settings（設定）

**役割:**
- DBファイルパス表示
- バックアップ案内（最小）

**主な操作:**
- `B` キー → Home へ戻る
- `ESC` キー → Home へ戻る

**表示内容:**
- DBファイルパス
- バックアップ手順案内（静的テキスト）
  ```
  バックアップ方法:
  1. 以下のファイルをコピーしてください:
     D:\...\data\pmtool.db

  2. 安全な場所に保存してください

  注意:
  - アプリケーション終了時にバックアップすることを推奨
  - 定期的なバックアップを心がけてください
  ```

**遷移元:** Home
**遷移先:** Home

---

## 4. 画面遷移

### 4.1 遷移図

```
┌──────────────────────────────────────────────────┐
│                                                  │
│                  [Home]                          │
│              Project一覧                          │
│                                                  │
│  Project選択 │   T キー    │   S キー           │
└──────┬───────┴────┬────────┴────┬────────────────┘
       │             │              │
       ↓             ↓              ↓
┌─────────────┐ ┌──────────┐ ┌──────────┐
│ Project     │ │ Template │ │ Settings │
│ Detail      │ │ Hub      │ └────┬─────┘
│             │ │          │      │
│ SubProject  │ │ Template │      │ B/ESC
│ 選択        │ │ 選択     │      ↓
└──────┬──────┘ └────┬─────┘    (Home)
       │             │
       │ SubProject  │ A キー
       │ 選択        │
       ↓             ↓
┌─────────────┐ ┌──────────────┐
│ SubProject  │ │ Template     │
│ Detail      │ │ Apply Wizard │
│             │ │              │
│ S キー      │ │              │
└──────┬──────┘ └──────┬───────┘
       │                │
       │                │ 適用完了
       ↓                ↓
┌─────────────┐ ┌──────────────┐
│ Template    │ │ SubProject   │
│ Save Wizard │ │ Detail       │
│             │ │ (新規作成)    │
└─────────────┘ └──────────────┘
```

### 4.2 遷移ルール

**基本ルール:**
- `ESC` キー: 1つ前の画面に戻る / ダイアログをキャンセル（Back）
- `H` キー: Home に戻る（どの画面からでも）
- `Q` キー: アプリケーション終了（Homeのみ）

**Wizard画面のルール:**
- `C` キー: キャンセル、元の画面に戻る（明示的なキャンセル）
- `Enter` キー: 次のステップへ進む（または実行）
- `ESC` キー: キャンセル、元の画面に戻る（Cキーと同じ）

**キーバインド統一方針:**
- `ESC`は常に「戻る / キャンセル」を意味する
- Homeへの直接遷移は`H`キーを使用（グローバル）
- この統一により、ユーザーの迷いを最小化

---

## 5. Widget構成

### 5.1 共通レイアウト

すべての画面は以下の共通レイアウトを持ちます：

```
┌────────────────────────────────────────────────┐
│ Header (アプリ名、DB名、現在画面名)              │
├────────────────────────────────────────────────┤
│                                                │
│                                                │
│             Main Content Area                  │
│                                                │
│                                                │
├────────────────────────────────────────────────┤
│ Footer (キーバインドヒント)                     │
└────────────────────────────────────────────────┘
```

### 5.2 使用するTextual Widgetリスト

| Widget | 用途 | 画面 |
|--------|------|------|
| **Header** | ヘッダー表示 | 全画面 |
| **Footer** | フッター表示 | 全画面 |
| **DataTable** | Project一覧、Template一覧 | Home, Template Hub |
| **Tree** | 4階層ツリー表示 | Project Detail |
| **ListView** | Task/SubTaskリスト | SubProject Detail |
| **Static** | 静的テキスト表示 | Settings, 確認画面 |
| **Input** | テキスト入力 | Template Save Wizard |
| **Select** | 選択肢（ON/OFF） | Template Save Wizard |
| **Button** | 実行・キャンセルボタン | Wizard画面 |
| **Label** | ラベル表示 | 全画面 |
| **Container** | レイアウトコンテナ | 全画面 |
| **ScrollView** | スクロール可能領域 | 長いリスト表示 |

### 5.3 画面別Widget構成

#### Home
```python
class HomeScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="project_table")  # Project一覧
        yield Footer()
```

#### Project Detail
```python
class ProjectDetailScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Project情報", id="project_info")  # 上部パネル
        yield Tree("Project階層", id="project_tree")    # 4階層ツリー
        yield Footer()
```

#### Template Save Wizard
```python
class TemplateSaveWizardScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("ステップインジケーター", id="step_indicator")
        yield Container(
            # ステップごとに切り替わるコンテンツ
            id="wizard_content"
        )
        yield Footer()
```

---

## 6. キーバインド

### 6.1 グローバルキーバインド

すべての画面で有効なキー：

| キー | 動作 | 補足 |
|------|------|------|
| `ESC` | 1つ前の画面に戻る / ダイアログキャンセル | 常に「戻る」を意味 |
| `H` | Homeに戻る | どの画面からでも |
| `?` | ヘルプ表示 | キーバインド一覧をモーダル表示 |

### 6.2 画面別キーバインド

#### Home
| キー | 動作 |
|------|------|
| `↑` / `↓` | Project選択 |
| `Enter` | Project Detail へ遷移 |
| `T` | Template Hub へ遷移 |
| `S` | Settings へ遷移 |
| `Q` | アプリケーション終了 |

#### Project Detail
| キー | 動作 |
|------|------|
| `↑` / `↓` | SubProject選択 |
| `Enter` | SubProject Detail へ遷移 |
| `ESC` | Home へ戻る |

#### SubProject Detail
| キー | 動作 |
|------|------|
| `S` | Template Save Wizard へ遷移 |
| `ESC` | Project Detail へ戻る |

#### Template Hub
| キー | 動作 |
|------|------|
| `↑` / `↓` | Template選択 |
| `A` | Template Apply Wizard へ遷移 |
| `D` | Template削除（確認ダイアログ） |
| `ESC` | Home へ戻る |

#### Template Save Wizard
| キー | 動作 |
|------|------|
| `Enter` | 次のステップへ（または保存実行） |
| `C` | キャンセル、SubProject Detail へ戻る |
| `ESC` | キャンセル、SubProject Detail へ戻る |

#### Template Apply Wizard
| キー | 動作 |
|------|------|
| `Enter` | 次のステップへ（または適用実行） |
| `C` | キャンセル、Template Hub へ戻る |
| `ESC` | キャンセル、Template Hub へ戻る |

#### Settings
| キー | 動作 |
|------|------|
| `ESC` | Home へ戻る |

---

## 7. ビジネスロジック層との接続

### 7.1 接続方針

**Textual UI → TemplateManager/Repository の呼び出し:**
- 同一プロセス内でimport
- subprocessによるCLI呼び出しは使用しない

### 7.2 各画面での呼び出し

#### Home
```python
# Project一覧取得
from src.pmtool.repository import Repository
from src.pmtool.database import Database

db = Database('data/pmtool.db')
repo = Repository(db)
projects = repo.list_projects()
```

#### Project Detail
```python
# Project詳細取得（4階層）
project = repo.get_project(project_id)
subprojects = repo.list_subprojects(project_id=project_id)
# ... Task/SubTask取得
```

#### Template Save Wizard
```python
from src.pmtool.template import TemplateManager

template_manager = TemplateManager(db)

# ステップ4: 確認画面での事前チェック

# 1. テンプレート名重複チェック
existing = template_manager.get_template_by_name(name)
if existing:
    # 警告表示、ステップ3へ戻る
    return

# 2. 外部依存検出（保存前にプレビュー）
external_warnings = template_manager._detect_external_dependencies(
    subproject_id=subproject_id
)

if external_warnings:
    # 外部依存警告を表示
    # 「続行しますか？」確認ダイアログ
    if user_cancelled:
        # Step 3へ戻る、または SubProject Detail へ戻る
        return

# 3. 保存内容サマリ表示
# - SubProject名、include_tasks、Task/SubTask件数など

# ユーザーが「保存する」を選択した場合のみ実行
if user_confirmed:
    result = template_manager.save_template(
        subproject_id=subproject_id,
        name=name,
        description=description,
        include_tasks=include_tasks
    )
    # result.has_warningsは空であるはず（事前検出済み）
    # 完了メッセージ表示 → SubProject Detail へ戻る
```

**注意:**
- `_detect_external_dependencies()`はprivateメソッドだが、UI側から直接呼び出す
- これは事前プレビューのために必要（保存前に警告を表示するため）
- 将来的には`preview_template()`のような公開APIを用意することも検討

#### Template Apply Wizard
```python
# ステップ3: dry-run
dry_run_result = template_manager.dry_run(
    template_id=template_id,
    project_id=project_id
)

# dry_run_result.tree_preview を表示

# ステップ4: 適用実行
new_subproject_id = template_manager.apply_template(
    template_id=template_id,
    project_id=project_id
)

# 作成されたSubProject Detailへ遷移
```

---

## 8. エラーハンドリング

### 8.1 例外処理方針

**UI層での処理:**
- すべての例外をキャッチ
- ユーザーフレンドリーなエラーメッセージを表示
- モーダルダイアログで表示（Textual標準の`ModalScreen`を用いて実装）

### 8.2 エラーメッセージ例

#### TemplateNameConflictError
```
エラー: テンプレート名が既に存在します

テンプレート名 "開発フロー" は既に使用されています。
別の名前を入力してください。

[OK]
```

#### SubProjectNotFoundError
```
エラー: SubProjectが見つかりません

指定されたSubProject (ID: 123) が存在しません。
削除された可能性があります。

[OK]
```

#### CycleDetectedError（適用時）
```
エラー: 依存関係にサイクルが検出されました

このテンプレートは破損している可能性があります。
適用を中止しました。

詳細: Task A → Task B → Task A

[OK]
```

### 8.3 確認ダイアログ例

#### Template削除確認
```
確認: テンプレートを削除しますか？

テンプレート: "開発フロー"

この操作は取り消せません。

[削除する] [キャンセル]
```

#### 外部依存警告（保存時）
```
警告: このSubProjectは外部依存を持っています

以下の依存関係はテンプレートに保存されません:

- Task "要件定義" は SubProject外のTask "プロジェクト計画" に依存しています

テンプレート適用時、これらの依存関係は再現されません。

続行しますか？

[続行する] [キャンセル]
```

---

## 9. 実装の優先順位

### Phase 5 での実装順序

#### 順序1: 基盤整備（P5-01, P5-02, P5-03）
1. プロジェクト構造整備（`src/pmtool_textual/`）
2. Textual基本アプリケーション骨格
3. DB接続管理

#### 順序2: 基本UI（P5-04, P5-05, P5-06）
4. Home（Project一覧）
5. Project Detail（4階層ツリー）
6. SubProject Detail

#### 順序3: テンプレート機能UI（P5-10, P5-11, P5-12）
7. Template Hub
8. Template Save Wizard
9. Template Apply Wizard

#### 順序4: 補助機能（P5-13）
10. Settings（バックアップ案内）

**注意:**
- テンプレート機能のビジネスロジック層（P5-07, P5-08, P5-09）は、UI実装前に完成していること

---

## 10. 補足事項

### 10.1 Textualバージョン

Phase 5では **Textual 7.3.0** を使用します（バージョン固定）。

**理由:**
- 安定性が高い
- DataTable、Tree等の主要Widgetが充実
- ドキュメントが整備されている

**バージョン固定方針:**
- `pyproject.toml`に`textual==7.3.0`と記載（厳密にバージョン固定）
- Phase 5実装期間中の再現性確保のため、検証済みバージョンに固定
- 予期しないAPI変更や破壊的変更を防ぐ

### 10.2 スタイリング

**カラースキーム:**
- ダークテーマを基本とする
- ステータス記号の色分け:
  - UNSET: グレー
  - NOT_STARTED: 黄色
  - IN_PROGRESS: 青
  - DONE: 緑

**フォント:**
- 等幅フォント前提（TUI）
- 記号は Unicode対応

### 10.3 将来拡張の考慮

**Phase 6以降で検討する機能:**
- 検索・絞り込み機能（Home、Template Hubに追加）
- メモ機能（各詳細画面にメモ欄追加）
- 複数DB切替（Settings画面を拡張）

---

## 変更履歴

### v1.0.2 (2026-01-22)
ChatGPTレビュー結果2（P5-14）を反映:

1. Textualバージョン修正（10.1節、変更履歴v1.0.1-5項目）
   - 修正前: `textual~=0.50.0`（古すぎる）
   - 修正後: `textual==7.3.0`（Phase 5実装期間中の再現性確保のため検証済みバージョンに固定）

2. ModalScreen抽象化（8.1節）
   - 修正前: 「Textualの`MessageBox`」と具体実装記述
   - 修正後: 「Textual標準の`ModalScreen`を用いて実装」に抽象化（バージョン間の流儀変化に対応）

### v1.0.1 (2026-01-22)
ChatGPTレビュー結果（P5-13）を反映:

**Must fix:**
1. Save Wizard の警告フロー修正（6.5.2節）
   - 修正前: save_template() 実行後に has_warnings を確認（保存後キャンセル不可の矛盾）
   - 修正後: Step4 確認画面で事前に外部依存を検出・警告表示し、ユーザー同意後に save_template() を実行

2. 戻るキー規約の統一（4.2節、6.x節全体）
   - ESC: Back（キャンセル/一つ前）に統一
   - H: Home（ホームへ戻る）を追加
   - B（Back）キーを廃止

**Should fix:**
3. Project直下Task の Tree表示方針を明記（6.2.1節、3.1.1節）
   - "Project直下Task"区画として分離表示、グレーアウト、選択不可

4. 「3クリック以内」→「3操作以内」に用語修正（2.2節、各画面操作性記述）
   - キーボード中心UIに合わせた指標へ調整

5. Textual バージョン固定方針を明記（10.1節）
   - 推奨バージョン: `textual==7.3.0`（Phase 5実装期間中の再現性確保のため）

### v1.0.0 (2026-01-21)
- 初版作成
- 7画面の基本構造、ウィジェット構成、画面遷移、キーバインド定義

---

**以上**
