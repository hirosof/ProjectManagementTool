受領しました。DB設計書（4_DB設計書.md）を、確定方針（D1〜D7）＋公式仕様の観点でレビューします。  

---

## 総評

**かなり良いです。MVP実装に入れる水準**にあります。
特に以下は、確定事項にきれいに一致しています。

* Python / SQLite / `PRAGMA foreign_keys=ON` 前提 ✅ 
* `parent_subproject_id` を用意（D3）✅ 
* 依存を2テーブルに分離（D7）✅ 
* ステータスに UNSET を含める（D5）✅ 
* order整数（`order_index`）採用（D2）✅ 

---

## ✅ OK（このまま実装に入って良い点）

### 1) 名前重複禁止（同一階層）を UNIQUE で担保

* `subprojects`: `UNIQUE(project_id, parent_subproject_id, name)` ✅ 
* `tasks`: `UNIQUE(project_id, subproject_id, name)` ✅ 
* `subtasks`: `UNIQUE(task_id, name)` ✅ 

→ 「同一階層内で名前重複禁止」の要件に合致です。 

### 2) 依存テーブルの最小制約

* 自己参照禁止（`CHECK(predecessor_id != successor_id)`） ✅ 
* UNIQUE（重複辺の禁止） ✅ 

→ DAG循環はアプリ検査、という責務分離も妥当です（D4）。 

---

## ⚠️ 要調整（実装で詰まりやすい / D6 と衝突しやすい）

ここだけ直すと、事故が大きく減ります。

### A) FK の `ON DELETE CASCADE` が D6（子持ち削除デフォルト禁止）と相性が悪い

現状、多くの FK が CASCADE です。例：

* `subprojects.project_id -> projects(id) ON DELETE CASCADE`
* `tasks.project_id -> projects(id) ON DELETE CASCADE`
* `tasks.subproject_id -> subprojects(id) ON DELETE CASCADE`
* `subtasks.task_id -> tasks(id) ON DELETE CASCADE`
* 依存テーブルも CASCADE 

**問題点**

* “通常削除では子持ち削除禁止” をアプリで守るつもりでも、
  **誤って親を削除した瞬間に配下がDB側で連鎖削除**されます（特に `projects` / `subprojects` / `tasks`）。
* D6 は「連鎖削除は明示フラグ付きの別操作」なので、DBが勝手に連鎖削除できる状態はリスクが高いです。 

**修正案（推奨）**

* 少なくとも “通常運用で削除し得る親子” は **RESTRICT 相当**にするのが安全です。

  * SQLiteは `ON DELETE RESTRICT` / 省略（デフォルトNO ACTION）で実質同様にできます。
* 方針としてはこの2択になります：

  1. **FKは基本 RESTRICT（推奨）**：アプリが明示的に連鎖削除を実行する
  2. CASCADE維持：ただし “通常削除コマンドでは絶対に親を消さない” を徹底（事故ったら一撃で全消し）

D6の意図からすると **(1)が自然**です。

---

### B) `parent_subproject_id` の `ON DELETE CASCADE` は将来の入れ子で破壊力が大きい

入れ子を将来解禁した際、親subproject削除で配下subprojectがDBで全消しになります。 
D6の思想（明示的連鎖削除）と合わせるなら、ここも **RESTRICT推奨**です。

---

## 🔶 要検討（今決めなくても進められるが、決めると手戻りが減る）

DB設計書の「議論点」にあるものへ、こちらの推奨だけ出します。

### 1) テンプレート依存関係テーブル `template_dependencies`

設計書では「Phase 3で必要・今は含めない」とあります。 
**推奨：今は入れなくてOK（Phase 3で追加）**
理由：テンプレ機能自体が後段なら、スキーマ凍結を先にした方がPhase 0/1が速い。

### 2) `order_index` の初期値（0 or 1）

**推奨：0始まり**（配列的で扱いやすい）
ただし仕様要件ではないので、どちらでもOK。重要なのは「一貫性」です。

### 3) タイムスタンプ（UTC vs ローカル）

`datetime('now')` はSQLiteではUTC扱いになることが多いです（環境差が出る可能性あり）。 
**推奨：DBはUTCで固定**（表示はアプリでローカル変換）
※ここは実装での取り扱いルールを書くだけで足ります。

### 4) 論理削除

**推奨：MVPは物理削除のみ**
理由：D6でdry-run＋安全削除を厚くしているので、まずは物理で十分。将来 `deleted_at` を足せます。

---

## 「D4 doctor/check」観点での適合

* Error対象（循環・欠損参照・レイヤ跨ぎ）は、DB設計に明示されていて良いです。 
* ただし上記のCASCADE問題が残ると、doctor/check以前に「事故が起きたらデータが消える」ので、**FK方針の調整が最優先**です。

---

## 結論（レビュー判定）

* ✅ **概ねOK**（構造・制約・インデックス方針は良い）
* ⚠️ **要調整：FKの `ON DELETE` 方針（特にCASCADE）をD6に合わせて見直し推奨** 

---

## 補完・仮定一覧（厳密構成モード）

* D6「連鎖削除は明示フラグの別操作」を“安全要件”として強めに解釈し、DB側CASCADEは事故リスクとして指摘しました（仕様と確定方針に基づく）。 
* SQLiteのFK運用は `PRAGMA foreign_keys=ON` を前提にしています（設計書に明記あり）。 

## 暗黙の前提

* 「通常削除」と「連鎖削除（強制削除）」はコマンド体系として分かれており、DBが勝手に連鎖削除しないことが安全性の前提になっている（D6の思想）。 

---

必要なら、**「CASCADEをRESTRICT寄りに直した版の差分（修正案SQL）」**もこちらで即作れます。
