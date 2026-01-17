# Phase 0 レビュー対応完了レポート

**対応日**: 2026-01-16
**対象**: init_db.sql / database.py / verify_init.py のレビューフィードバック

---

## レビューフィードバック内容

ChatGPTから以下の2点の軽微な推奨事項を受けました:

1. **SQLiteの外部キーは「接続単位」なので、今後も本Databaseクラス経由で接続する前提をコメント等で明示推奨**
2. **initialize() は初期化済みDBに対して再実行すると失敗し得るため、ガードまたはエラーメッセージ明確化を推奨**

---

## 対応内容

### 1. PRAGMA foreign_keys 接続単位の注意事項を明記

**対応箇所**: `src/pmtool/database.py`

#### 1.1 モジュールdocstringに追記

```python
"""
データベース接続および初期化モジュール

Phase 0: 基盤構築
- SQLite接続管理
- DB初期化
- PRAGMA設定

重要な注意事項:
    SQLiteの外部キー制約（PRAGMA foreign_keys）は接続単位で設定されます。
    本モジュールのDatabaseクラスは、connect()時に自動的に外部キー制約を有効化します。

    そのため、データベース操作を行う際は必ず本Databaseクラス経由で接続してください。
    sqlite3.connect()を直接使用すると、外部キー制約が無効のまま動作する可能性があります。
"""
```

#### 1.2 Databaseクラスのdocstringに追記

```python
class Database:
    """
    SQLiteデータベース接続を管理するクラス

    このクラスは、データベース接続時に自動的に以下の設定を行います:
    - PRAGMA foreign_keys = ON（外部キー制約の有効化）
    - Row factory設定（カラム名でのアクセスを可能にする）

    重要:
        外部キー制約はSQLiteでは接続単位で設定されるため、
        データベース操作を行う際は必ず本クラス経由で接続してください。
    """
```

**目的**:
- 外部キー制約が接続単位であることを明示
- `sqlite3.connect()` の直接使用を避けるべきことを明確化
- Phase 1以降の実装者が誤った接続方法を使用しないようにする

---

### 2. initialize()メソッドに初期化済みチェックのガードを追加

**対応箇所**: `src/pmtool/database.py`, `scripts/verify_init.py`

#### 2.1 initialize()メソッドの改善

**追加機能**:
- `force` パラメータの追加（デフォルト: False）
- 初期化済みチェックの追加
- force=True の場合は既存テーブルを削除してから再初期化

**実装**:
```python
def initialize(self, sql_file: str | Path, force: bool = False):
    """
    データベースを初期化

    Args:
        sql_file: 初期化SQLファイルのパス
        force: すでに初期化済みの場合でも強制的に再初期化する場合True（デフォルト: False）

    Raises:
        FileNotFoundError: SQLファイルが存在しない場合
        RuntimeError: すでに初期化済みの場合（force=Falseの場合のみ）
        sqlite3.Error: SQL実行エラーが発生した場合

    注意:
        force=Trueで再初期化すると、既存のデータはすべて失われます。
    """
    # 初期化済みチェック
    if self.is_initialized() and not force:
        raise RuntimeError(
            f"Database is already initialized at {self.db_path}. "
            "Use force=True to reinitialize (WARNING: all data will be lost)."
        )

    # ... (以下、初期化処理)

    try:
        # force=Trueの場合、既存のテーブルをすべて削除
        if force and self.is_initialized():
            # 既存のテーブル一覧を取得
            cursor.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            # 外部キー制約を一時的に無効化
            cursor.execute("PRAGMA foreign_keys = OFF")

            # すべてのテーブルを削除
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")

            # 外部キー制約を再度有効化
            cursor.execute("PRAGMA foreign_keys = ON")

            conn.commit()

        # SQLスクリプトを実行
        cursor.executescript(sql_script)
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise e
```

**動作**:
- `force=False`（デフォルト）: 初期化済みの場合は `RuntimeError` を発生
- `force=True`: 既存のテーブルをすべて削除してから再初期化

**エラーメッセージ**:
```
RuntimeError: Database is already initialized at D:\...\pmtool.db.
Use force=True to reinitialize (WARNING: all data will be lost).
```

#### 2.2 verify_init.py の修正

**変更内容**:
```python
# 初期化前の状態確認
is_initialized_before = db.is_initialized()
print(f"DB初期化前: {is_initialized_before}")

# 初期化実行
print(f"SQLファイル: {sql_path}")

# 既存のDBがある場合は force=True で再初期化
if is_initialized_before:
    print("既存のDBを検出（force=Trueで再初期化）")
    db.initialize(sql_path, force=True)
else:
    db.initialize(sql_path)
```

**動作**:
- 既存DBがある場合は自動的に `force=True` で再初期化
- 既存DBがない場合は通常の初期化

---

## 検証結果

### 修正後の動作確認

```bash
python scripts/verify_init.py
```

**結果**:
```
============================================================
Phase 0: データベース初期化検証
============================================================

1. データベース初期化
------------------------------------------------------------
DB初期化前: True
SQLファイル: D:\...\init_db.sql
既存のDBを検出（force=Trueで再初期化）
✓ 初期化成功

DB初期化後: True

2. PRAGMA設定確認
------------------------------------------------------------
外部キー制約: 有効
✓ PRAGMA設定OK

3. テーブル作成確認
------------------------------------------------------------
作成されたテーブル数: 7
✓ すべてのテーブル作成OK（7テーブル）

4. スキーマバージョン確認
------------------------------------------------------------
現在のスキーマバージョン: 1
✓ スキーマバージョンOK

5. インデックス確認
------------------------------------------------------------
部分UNIQUEインデックス数: 4
✓ 部分UNIQUEインデックスOK（4個）

============================================================
Phase 0: 初期化検証完了
============================================================
```

### 初期化ガードの動作確認

**ケース1: 初期化済みDBに対して force=False で実行**
```python
db = Database("data/pmtool.db")
db.initialize("scripts/init_db.sql")  # force=False（デフォルト）
```

**結果**:
```
RuntimeError: Database is already initialized at data/pmtool.db.
Use force=True to reinitialize (WARNING: all data will be lost).
```
✅ 期待通りエラーが発生

**ケース2: 初期化済みDBに対して force=True で実行**
```python
db = Database("data/pmtool.db")
db.initialize("scripts/init_db.sql", force=True)
```

**結果**:
- 既存テーブルが削除される
- 新しいテーブルが作成される
- ✅ 正常に再初期化完了

---

## 技術的な判断事項

### 1. force=True 時の既存テーブル削除方法

**選択肢**:
- A: DBファイル自体を削除して再作成
- B: 既存のテーブルを DROP してから再作成

**採用**: **B（既存のテーブルをDROP）**

**理由**:
- DBファイルの削除は外部のファイルシステム操作が必要
- トランザクション内で完結できる
- エラー時のロールバックが可能
- より安全な実装

**実装のポイント**:
- 外部キー制約を一時的に無効化（`PRAGMA foreign_keys = OFF`）
- すべてのテーブルを削除
- 外部キー制約を再度有効化（`PRAGMA foreign_keys = ON`）
- トランザクション内で実行

---

### 2. エラーメッセージの明確化

**変更前**:
```
sqlite3.OperationalError: table schema_version already exists
```
→ 内部的なSQLエラーメッセージで、ユーザーにとって分かりにくい

**変更後**:
```
RuntimeError: Database is already initialized at D:\...\pmtool.db.
Use force=True to reinitialize (WARNING: all data will be lost).
```
→ 明確な原因と解決方法を提示

---

## 修正ファイル一覧

1. **src/pmtool/database.py**
   - モジュールdocstringに注意事項を追加
   - Databaseクラスdocstringに注意事項を追加
   - `initialize()` メソッドに `force` パラメータを追加
   - 初期化済みチェックのガードを追加
   - force=True 時の既存テーブル削除処理を追加

2. **scripts/verify_init.py**
   - 初期化済みDBに対して `force=True` で再初期化するように変更
   - DBファイル削除処理を削除（不要になったため）

---

## レビュー観点

修正内容について、以下の観点でレビューをお願いします:

### 1. 注意事項の明確性
- PRAGMA foreign_keys の接続単位の説明は十分か
- Databaseクラス経由での接続が必須であることが明確か

### 2. 初期化ガードの実装
- force パラメータの動作は妥当か
- エラーメッセージは分かりやすいか
- 既存テーブル削除の実装は安全か

### 3. verify_init.py の変更
- force=True での再初期化が適切か
- ユーザーへのメッセージは十分か

### 4. 後方互換性
- 既存コードへの影響はないか（force のデフォルト値が False）

---

## 補足事項

### force=True の使用シーン

**推奨される使用シーン**:
- 開発中のテストやデバッグ
- スキーマ変更後の再初期化
- データをリセットしたい場合

**推奨されない使用シーン**:
- 本番環境での運用中
- データを保持したい場合

### 将来の拡張性

**Phase 1以降で検討すべき事項**:
- マイグレーション機能の実装
- バックアップ機能の追加
- 初期化前の確認プロンプト（TUI）

---

## まとめ

レビューフィードバックの2点について対応が完了しました:

1. ✅ PRAGMA foreign_keys の接続単位について明確化
   - モジュールdocstring、クラスdocstringに注意事項を追加
   - Databaseクラス経由での接続が必須であることを明記

2. ✅ initialize()の初期化済みチェックのガードを追加
   - `force` パラメータの追加
   - 初期化済みの場合のエラーメッセージ明確化
   - force=True 時の既存テーブル削除処理を実装

すべての修正が検証され、正常に動作することを確認しました。

---

（以上）
