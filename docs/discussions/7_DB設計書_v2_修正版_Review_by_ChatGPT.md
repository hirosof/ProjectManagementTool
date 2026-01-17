受領しました。DB設計書 v2、全体として **かなり良くなっていて、方針（D2/D3/D4/D5/D6/D7）にも整合**しています。 

ただし、**SQLite 特有の “UNIQUE + NULL” 落とし穴**が 2 箇所あり、ここだけは **要修正（重要）**です。

---

## ✅ OK（このままで良い）

* 親子FKを **RESTRICT**、依存FKを **CASCADE**：D6と整合して安全。 
* `parent_subproject_id` を用意し、MVPはNULL固定（入れ子は将来）：D3整合。 
* 依存2テーブル（task/subtask）：D7整合。 
* `order_index` 0始まり・インデックス方針も妥当：D2整合。 
* UTC固定の明記、論理削除MVPなし：OK。 
* doctor/check の責務分離（DAG等はアプリ）：D4整合。 

---

## ❗要修正（重要）：SQLiteの UNIQUE と NULL の扱い

SQLite では **UNIQUE 制約に含まれる列が NULL だと、重複とみなされず同名を複数入れられてしまう**ことがあります。

### 1) `tasks` の重複防止が “Project直下” で効かない

現状：`UNIQUE(project_id, subproject_id, name)` 
`subproject_id` が NULL（Project直下）の場合、同一 `project_id` + 同一 `name` を複数登録できてしまう可能性があります。

**修正案（どれか1つ採用でOK）**

* A: **部分UNIQUEインデックス**で NULL ケースを別途縛る（おすすめ）

  * `subproject_id IS NULL` 用の UNIQUE
  * `subproject_id IS NOT NULL` 用の UNIQUE
* B: `subproject_id` を NULL で持たず、Project直下用の “擬似SubProject” を作って必ず埋める（設計が変わるので非推奨）

### 2) `subprojects` の重複防止が “Project直下” で効かない

現状：`UNIQUE(project_id, parent_subproject_id, name)` 
`parent_subproject_id` が NULL（Project直下）の場合、同名SubProjectが複数入る可能性があります。

→ 上と同じく、**NULLケース用の部分UNIQUEインデックス**が堅いです。

この2点は「同一階層内で名前重複禁止」という公式仕様に直撃するので、**v2のまま実装に入るのは危険**です。 

---

## ⚠️ 軽微（任意だが入れると良い）

* `order_index` に `CHECK(order_index >= 0)` を付ける（0始まりをDB側でも明確化）
* `updated_at` は自動更新されないので、**アプリで必ず更新する**（またはトリガー追加。MVPはアプリ更新でOK）
  ※設計書上は “アプリ側で更新する” と一言書けば十分です。

---

## 判定

* ✅ 方針は合格（D6のRESTRICT化など、狙い通り）
* ❗ただし **tasks/subprojects の UNIQUE + NULL 問題だけ修正必須**

  * ここを直した版を「v2.1」などで出せば、**DB設計としてクローズ**でOKです。

---

必要なら、こちらで「部分UNIQUEインデックス案（SQL断片）」をそのまま貼れる形で作って返します（Claude Codeに渡す用）。
