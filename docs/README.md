# ProjectManagementTool ドキュメント

このディレクトリには、ProjectManagementToolプロジェクトの各種ドキュメントが格納されています。

---

## ディレクトリ構造

```
docs/
├── README.md                    # このファイル
├── user/                        # ユーザー向けドキュメント
│   ├── USER_GUIDE.md            # ユーザーガイド（基本概念、コマンドリファレンス）
│   ├── TUTORIAL.md              # チュートリアル（実践的なシナリオ）
│   └── FAQ.md                   # よくある質問・トラブルシューティング
├── specifications/              # 実装仕様書
│   ├── 1_プロジェクト管理ツール_ClaudeCode仕様書.md
│   ├── pmtool_統合仕様書_Phase4完了版.md
│   └── テンプレート機能_仕様書.md
├── design/                      # 確定した設計書・計画書
│   ├── 3_プロジェクト管理ツール_実装方針確定メモ.md
│   ├── 8_DB設計書_v2.1_最終版.md
│   ├── 13_Phase0_完了_Phase1_引き継ぎ事項.md
│   ├── Phase2_CLI設計書.md
│   ├── Phase3_拡張機能実装_設計書.md
│   ├── Phase4_品質安定性向上_設計書.md
│   ├── Phase5_テンプレート機能_BL設計書.md
│   ├── Phase5_Textual_UI基本構造設計書.md
│   └── Phase5_詳細実装計画書.md
└── discussions/                 # 議論ログ・レビュー記録
    ├── 01_DB設計書_初期版.md
    ├── 2_ClaudeCodeからの確認事項.md
    ├── 5_DB設計書_Review_by_ChatGPT.md
    ├── 6_DB設計書_v2_修正版.md
    ├── 7_DB設計書_v2_修正版_Review_by_ChatGPT.md
    ├── 9_Phase0_実装完了レポート.md
    ├── 10_Phase0_レビュー対応完了レポート.md
    ├── 11_Phase0_レポート最終確認事項.md
    ├── 12_Phase0_pyproject_requirements_確認用.md
    ├── Phase1_フィードバック対応完了レポート.md
    ├── Phase2_完了レポート.md
    ├── Phase3_P0完了レポート.md
    ├── Phase4_完了レポート.md
    └── Phase5_*.md                # Phase 5議論・レビュー記録（13件）
```

---

## 各ディレクトリの説明

### user/ - ユーザー向けドキュメント

pmtool の使い方を学ぶための詳細なドキュメントを格納します。

- **Git管理**: 対象（コミット・プッシュする）
- **用途**: pmtool の使い方、コマンドリファレンス、トラブルシューティング

**ドキュメント**:
- `USER_GUIDE.md` - ユーザーガイド
  - インストール手順
  - 基本概念（4階層構造、ステータス管理、依存関係管理）
  - コマンドリファレンス（全8コマンドの詳細）
  - 削除操作の詳細（通常削除、橋渡し削除、連鎖削除）
- `TUTORIAL.md` - チュートリアル
  - シナリオ1: 基本的なプロジェクト管理
  - シナリオ2: 依存関係管理
  - 実践的な使い方をステップバイステップで解説
- `FAQ.md` - よくある質問
  - エラー対処法（FK制約違反、サイクル検出、ステータス遷移エラー等）
  - トラブルシューティング（doctor、dry-run の使い方）
  - Tips & Tricks

**初めて使う方は、USER_GUIDE.md から始めることをお勧めします。**

### specifications/ - 実装仕様書

プロジェクトの機能仕様やコンポーネント仕様を記載したドキュメントを格納します。

- **Git管理**: 対象（コミット・プッシュする）
- **用途**: 実装時の参照、機能理解、API仕様の確認

**主要ドキュメント**:
- `1_プロジェクト管理ツール_ClaudeCode仕様書.md` - プロジェクト全体の機能仕様書（Phase 1時点）
- `pmtool_統合仕様書_Phase4完了版.md` - **Phase 0-4統合仕様書（推奨）**
- `テンプレート機能_仕様書.md` - テンプレート機能仕様書（Phase 5実装予定）

**Phase 5実装時の参照順:**
1. `pmtool_統合仕様書_Phase4完了版.md` - 現在の完全な仕様を把握
2. `テンプレート機能_仕様書.md` - テンプレート機能の詳細仕様（Phase 5で実装）

### design/ - 確定した設計書・計画書

確定した設計書、実装計画書、Phase間の引き継ぎ事項を格納します。

- **Git管理**: 対象（コミット・プッシュする）
- **用途**: 実装時の参照、アーキテクチャ理解、Phase計画の確認

**主要ドキュメント**:
- `3_プロジェクト管理ツール_実装方針確定メモ.md` - 実装方針の確定版
- `8_DB設計書_v2.1_最終版.md` - データベース設計の最終確定版
- `13_Phase0_完了_Phase1_引き継ぎ事項.md` - Phase 0からPhase 1への引き継ぎ事項

### discussions/ - 議論ログ・レビュー記録

設計・仕様策定のプロセス、議論過程、レビュー記録を保管します。

- **Git管理**: 対象（コミット・プッシュする）
- **用途**: 設計の経緯確認、レビュー内容の参照、問題解決の履歴確認

**主要ドキュメント**:
- DB設計の変遷: `01_DB設計書_初期版.md` → `6_DB設計書_v2_修正版.md` → 最終版
- ChatGPTレビュー記録: `5_DB設計書_Review_by_ChatGPT.md`, `7_DB設計書_v2_修正版_Review_by_ChatGPT.md`
- Phase完了レポート: `9_Phase0_実装完了レポート.md`, `Phase1_フィードバック対応完了レポート.md`, `Phase2_完了レポート.md`, `Phase3_P0完了レポート.md`, `Phase4_完了レポート.md`

---

## 開発フェーズ別ドキュメント

### Phase 0: 基盤構築 (完了)

**設計書**:
- `design/8_DB設計書_v2.1_最終版.md`
- `design/3_プロジェクト管理ツール_実装方針確定メモ.md`

**完了レポート**:
- `discussions/9_Phase0_実装完了レポート.md`
- `discussions/10_Phase0_レビュー対応完了レポート.md`

**引き継ぎ**:
- `design/13_Phase0_完了_Phase1_引き継ぎ事項.md`

### Phase 1: コア機能実装 (フィードバック対応完了)

**仕様書**:
- `specifications/1_プロジェクト管理ツール_ClaudeCode仕様書.md`

**完了レポート**:
- `discussions/Phase1_フィードバック対応完了レポート.md`

**検証スクリプト**:
- `../scripts/verify_phase1.py`

### Phase 2: CLIインターフェース (完了)

**設計書**:
- `design/Phase2_CLI設計書.md`

**完了レポート**:
- `discussions/Phase2_完了レポート.md`

**検証スクリプト**:
- `../scripts/verify_phase2.py`

### Phase 3: 拡張機能 (P0完了)

**設計書**:
- `design/Phase3_拡張機能実装_設計書.md`

**完了レポート**:
- `discussions/Phase3_P0完了レポート.md`

### Phase 4: 品質・安定性向上 (完了)

**設計書**:
- `design/Phase4_品質安定性向上_設計書.md`

**完了レポート**:
- `discussions/Phase4_完了レポート.md`

**成果物**:
- **P4-01**: テストカバレッジ80.08%達成（2319 stmt / 462 miss）
  - テストコード: `../tests/`（~1,850行）
- **P4-07**: ユーザードキュメント整備（~1,600行）
  - `user/USER_GUIDE.md` - ユーザーガイド
  - `user/TUTORIAL.md` - チュートリアル
  - `user/FAQ.md` - よくある質問
- **P4-08**: テンプレート機能仕様書（~780行）
  - `specifications/テンプレート機能_仕様書.md` - Phase 5実装予定

### Phase 5: Textual UI + テンプレート機能 (設計完了、実装着手可能)

**仕様書**:
- `specifications/テンプレート機能_仕様書.md` - テンプレート機能仕様書（Phase 4で作成）

**設計書（3件、すべて承認済み）**:
- `design/Phase5_テンプレート機能_BL設計書.md` (47KB)
  - P5-9 v1.1.1（承認済み）
  - TemplateManager、TemplateRepository設計
  - SaveTemplateResult、ExternalDependencyWarning設計
  - own_connパターンによるトランザクション設計
- `design/Phase5_Textual_UI基本構造設計書.md` (26KB)
  - P5-12 v1.0.2（承認済み）
  - 7画面構成（Home, Project Detail, SubProject Detail, Template Hub, Save/Apply Wizard, Settings）
  - Widget設計、キーバインド統一（ESC=Back, H=Home）
  - Textual 7.3.0バージョン固定
- `design/Phase5_詳細実装計画書.md` (38KB)
  - P5-17 v1.0.1（承認済み）
  - 全16タスク（P5-01～P5-16）の詳細実装手順
  - 実装順序・マイルストーン（推定34時間）
  - 品質目標（テストカバレッジ80%）

**議論・レビュー記録（13件）**:
- `discussions/Phase5_P5-1_搭載機能洗い出し_議論スレッド.md` - 搭載機能の初期議論
- `discussions/Phase5_P5-3_搭載機能洗い出し結果.md` - 搭載機能の洗い出し結果
- `discussions/Phase5_P5-4-1_フェーズ分解結果.md` - Phase 5/Phase 6以降のフェーズ分解
- `discussions/Phase5_P5-4-2_フェーズ分解結果_ChatGPT用.md` - ChatGPT用フェーズ分解
- `discussions/Phase5_P5-5_設計整理スレッド初投稿文.md` - 設計整理スレッド初投稿
- `discussions/Phase5_P5-6_設計整理結果.md` - 設計整理結果
- `discussions/Phase5_P5-7_論点隔離スレッド初投稿文.md` - 論点隔離スレッド初投稿
- `discussions/Phase5_P5-8_設計中論点_ClaudeCode検出分.md` - Claude検出の設計論点（5件）
- `discussions/Phase5_P5-9_BL設計書レビュー結果1.md` - BL設計書レビュー結果1
- `discussions/Phase5_P5-9_BL設計書レビュー結果2.md` - BL設計書レビュー結果2（承認）
- `discussions/Phase5_P5-12_UI設計書レビュー結果1.md` - UI設計書レビュー結果1
- `discussions/Phase5_P5-12_UI設計書レビュー結果2.md` - UI設計書レビュー結果2（承認）
- `discussions/Phase5_P5-17_実装計画書レビュー結果1.md` - 実装計画書レビュー結果（承認）

**実装タスク**:
- **P5-01～P5-03**: 基盤整備（プロジェクト構造、Textual骨格、DB接続）
- **P5-04～P5-06**: テンプレート機能BL層（TemplateRepository、TemplateManager）
- **P5-07～P5-09**: 基本UI（Home、Project Detail、SubProject Detail）
- **P5-10～P5-12**: テンプレート機能UI（Template Hub、Save/Apply Wizard）
- **P5-13～P5-16**: 補助機能・品質向上（Settings、初回セットアップ、テスト整備、完了レポート）

**推定工数**: 約34時間

---

## ドキュメント作成・更新のガイドライン

### 新規ドキュメントの配置先

1. **実装仕様書**: `specifications/` に配置
   - コンポーネント仕様書
   - API仕様書
   - 機能仕様書

2. **確定した設計書・計画書**: `design/` に配置
   - Phase計画書
   - アーキテクチャ設計書
   - データベース設計書

3. **議論ログ・レビュー記録**: `discussions/` に配置
   - 設計レビュー記録
   - ChatGPT/Claude Codeとの議論過程
   - Phase完了レポート

### ワークフロー

1. **議論段階**: 一時的に `../temp/` に配置してChatGPTとファイル受け渡し
2. **議論確定後**: `docs/discussions/` に移動（copyコマンド使用）
3. **設計確定後**: `docs/design/` に配置
4. **仕様確定後**: `docs/specifications/` に配置

**重要**:
- `temp/` フォルダはGit管理対象外（.gitignoreに登録済み）
- 仕様書やドキュメントから `temp/` 配下のパスを参照しないこと
- 確定後は必ず `docs/` 配下に移動すること

---

## 参照時の注意事項

### 実装時に参照すべきドキュメント

**Phase 1実装時**:
1. `specifications/1_プロジェクト管理ツール_ClaudeCode仕様書.md` - 機能仕様
2. `design/3_プロジェクト管理ツール_実装方針確定メモ.md` - 実装方針
3. `design/8_DB設計書_v2.1_最終版.md` - DB設計
4. `design/13_Phase0_完了_Phase1_引き継ぎ事項.md` - 引き継ぎ事項

**Phase 2実装時**:
- Phase 1の完了レポートを参照
- CLI仕様書（作成予定）

**Phase 5実装時**:
1. `specifications/pmtool_統合仕様書_Phase4完了版.md` - Phase 0-4の統合仕様
2. `specifications/テンプレート機能_仕様書.md` - テンプレート機能仕様
3. `design/Phase5_詳細実装計画書.md` - 全16タスクの詳細実装手順（最優先）
4. `design/Phase5_テンプレート機能_BL設計書.md` - ビジネスロジック層設計
5. `design/Phase5_Textual_UI基本構造設計書.md` - UI層設計

### バージョン管理

- 設計書のバージョン変遷は `discussions/` に保管
- 最新の確定版のみ `design/` に配置
- 過去バージョンが必要な場合は `discussions/` を参照

---

## 更新履歴

- **2026-01-22**: Phase 5設計完了（設計書3件、議論・レビュー記録13件を追加）
  - `design/Phase5_テンプレート機能_BL設計書.md`（承認済み）
  - `design/Phase5_Textual_UI基本構造設計書.md`（承認済み）
  - `design/Phase5_詳細実装計画書.md`（承認済み）
  - `discussions/Phase5_*.md`（13件の議論・レビュー記録）
- **2026-01-20**: Phase 4完了（P4-01〜P4-08全タスク完了、完了レポート追加）
- **2026-01-18**: Phase 3 P0完了レポート追加
- **2026-01-17**: Phase 2完了レポート追加、Phase2_CLI設計書追加
- **2026-01-16**: docsフォルダ構造作成、Phase 0ドキュメント整理、Phase 1フィードバック対応完了レポート追加

---

**注意**: このドキュメント構造は `CLAUDE.md` の「ファイル配置とフォルダ管理」セクションに準拠しています。
