P5-9 テンプレート機能BL設計書レビュー結果：要修正（再レビュー）

Must fix:
1) テンプレ名重複チェックの責務が矛盾：
   - 「確認画面で実施」としつつ save_template() で get_template_by_name→例外、にもなっている。
   - UI事前チェック＋ロジック最終防衛（UNIQUE違反→TemplateNameConflictError変換）等、責務分離を明文化して統一して下さい。

2) 外部依存の扱い（警告継続）の仕様化が不足：
   - 外部依存は保存しない/適用でも再現されない、を保証として明文化。
   - UI側で必ず表示し、続行条件（明示同意など）を設計に反映して下さい。
   - そのための戻り値設計が必要（現状は「警告を戻り値に含める」と書きつつ戻り値がTemplateのみで矛盾）。

3) save_template() の戻り値型を修正：
   - SaveTemplateResult(template, warnings) 等の結果型を導入するか、
   - 警告取得を別APIに分離して save_template() は保存だけにするか、
   いずれかに統一して下さい。

4) template系テーブル操作の責務を明確化：
   - TemplateManagerがSQL直書きにならないよう、TemplateRepositoryを新設するか、既存Repositoryにtemplate操作を追加するかを明記して下さい。

Should fix:
5) SQLiteのBOOLEAN表現（0/1）を設計書上で統一（注記含む）。
6) apply時のCycleDetected等の扱いを「理論上起きない」ではなく、起きた場合のロールバック＋例外変換方針として明記。
