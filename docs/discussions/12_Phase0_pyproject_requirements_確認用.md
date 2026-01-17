# Phase 0: pyproject.toml / requirements.txt 確認用

**作成日**: 2026-01-16
**目的**: Phase 0 で作成した設定ファイルの軽量チェック

---

## 1. pyproject.toml

**ファイルパス**: `pyproject.toml`

```toml
[project]
name = "pmtool"
version = "0.1.0"
description = "Project Management Tool for personal use"
readme = "README.md"
requires-python = ">=3.10"
license = {file = "LICENSE"}

dependencies = [
    "textual>=0.47.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### 設計判断

#### 依存関係
- **textual>=0.47.0**: TUI実装用（Phase 2 で使用予定）
  - Phase 0 では未使用だが、プロジェクト設定として先行定義

#### 開発依存
- **pytest>=7.4.0**: テストフレームワーク（Phase 1 以降で使用予定）
- **pytest-cov>=4.1.0**: カバレッジ測定（Phase 1 以降で使用予定）

#### Python バージョン
- **>=3.10**: 型ヒント `str | Path` を使用するため

#### ビルドシステム
- **setuptools**: Python標準のビルドツール
- パッケージは `src/` ディレクトリ配下

---

## 2. requirements.txt

**ファイルパス**: `requirements.txt`

```txt
# Core dependencies
textual>=0.47.0

# Development dependencies (optional)
pytest>=7.4.0
pytest-cov>=4.1.0
```

### 設計判断

- pyproject.toml との整合性を保つ
- コメント付きで用途を明示
- 開発依存は optional として明記

---

## 3. 確認観点

### ✅ 依存関係の妥当性

1. **textual の追加理由**:
   - Phase 2 でTUI実装に使用予定
   - Phase 0 では未使用だが、プロジェクト全体の依存として定義
   - **確認事項**: Phase 0 時点でtextualを含めることは過剰か？

2. **pytest の追加理由**:
   - Phase 1 以降でテスト実装時に使用予定
   - Phase 0 では未使用
   - **確認事項**: Phase 0 時点でpytestを含めることは過剰か？

### ✅ 実行導線の過剰化

- Phase 0 では実行可能なスクリプトは `scripts/verify_init.py` のみ
- TUIは未実装のため、エントリーポイント未定義
- **確認事項**: エントリーポイント（console_scripts）は Phase 1 以降で追加すべきか？

### ✅ バージョン指定

- すべて `>=` で最低バージョンを指定
- 上限指定なし（依存関係の柔軟性を保つ）
- **確認事項**: バージョン指定は適切か？

---

## 4. 代替案

### 案A: 現状維持（推奨）

- textual, pytest を Phase 0 時点で含める
- メリット: プロジェクト全体の依存が明確
- デメリット: Phase 0 では未使用

### 案B: 最小限の依存（Phase 0 のみ）

```toml
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
]
tui = [
    "textual>=0.47.0",
]
```

- Phase 0 時点では core dependencies を空にする
- textual は optional-dependencies として分離
- メリット: Phase 0 の実装範囲に厳密に合致
- デメリット: Phase 1/2 で追加作業が必要

### 案C: 段階的な追加

- Phase 0: 依存なし
- Phase 1: pytest 追加（テスト実装時）
- Phase 2: textual 追加（TUI実装時）
- メリット: 各フェーズで必要な依存のみ追加
- デメリット: 毎フェーズで設定ファイル更新が必要

---

## 5. Phase 0 での使用状況

### 実際の依存関係（Phase 0）

- **Python標準ライブラリのみ**:
  - `sqlite3`: データベース接続
  - `pathlib`: パス操作
  - `sys`, `io`: 標準入出力

- **外部ライブラリは未使用**:
  - textual: 未使用
  - pytest: 未使用

### verify_init.py の実行

```bash
# 外部ライブラリ不要で実行可能
python scripts/verify_init.py
```

---

## 6. 質問事項

ChatGPT へ確認したい点:

1. **Phase 0 時点で textual を含めることは過剰ですか？**
   - 推奨: 削除して Phase 2 で追加
   - または: プロジェクト全体の依存として現状維持

2. **Phase 0 時点で pytest を含めることは過剰ですか？**
   - 推奨: 削除して Phase 1 で追加
   - または: 開発依存として現状維持

3. **エントリーポイント（console_scripts）は Phase 1 で追加すべきですか？**
   - 例: `pmtool = pmtool.cli:main`
   - Phase 1 でCLI実装時に追加？
   - Phase 2 でTUI実装時に追加？

4. **バージョン指定（>=）は適切ですか？**
   - より厳密な固定（==）が必要？
   - または現状の柔軟な指定で問題なし？

---

## 7. Claude Code の見解

### 現状の設定について

**判断**: 現状維持（案A）を推奨

**理由**:
- プロジェクト全体の依存関係を Phase 0 で定義することは一般的
- 各フェーズで設定ファイルを更新する手間を削減
- textual, pytest は Phase 1/2 で確実に使用する予定
- Phase 0 で未使用でも、インストールに問題はない

### 過剰な依存追加はない

- textual: TUI実装に必要（Phase 2）
- pytest: テスト実装に必要（Phase 1 以降）
- いずれも標準的な開発ツールであり、過剰ではない

### エントリーポイント

- Phase 1: CLI実装なし（CRUD操作はPythonモジュールとして提供）
- Phase 2: TUI実装時にエントリーポイント追加を推奨
  - 例: `pmtool = pmtool.tui:main`

---

## 8. まとめ

**Phase 0 の設定ファイル（pyproject.toml / requirements.txt）は問題なし**

- 依存関係は適切（過剰な追加なし）
- 実行導線は最小限（verify_init.py のみ）
- バージョン指定は柔軟（>=）
- エントリーポイントは Phase 2 で追加予定

**確認待ち事項**:
- ChatGPT 側で軽量チェックを実施
- 問題なければ Phase 1 に進行

---

（以上）
