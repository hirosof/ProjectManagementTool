P5-15 Phase5_詳細実装計画書 v1.0.0 レビュー結果：要修正（再レビュー）

Must fix:
1) pmtool_textual の配置が矛盾（2.2は src/pmtool/pmtool_textual、P5-01は src/pmtool_textual）。
   → どちらかに統一して下さい（計画書内で一貫させる）。

2) 「P5-15」が文書IDとタスクIDで二重使用されている。
   → 実装計画書の文書IDを別にするか、タスクID側をリナンバーして衝突を解消して下さい。

3) キーバインド規約がP5-12承認済み設計と矛盾（Bキー復活/ESC説明混在）。
   → P5-12準拠（ESC=Back, H=Home, B廃止）に全コード例・記述を統一して下さい。

4) TemplateRepository の実装場所がP5-9承認済み設計と不整合（repository.pyに追加と記載）。
   → P5-9の構造に合わせてTemplateRepositoryを独立ファイル化する等、設計と計画を統一して下さい。

Should fix:
5) TemplateHubのWidget（ListView vs DataTable）をP5-12と統一。
6) UIから _detect_external_dependencies(private) を呼ぶ方針を計画として明確化
   （暫定許容 or 公開API追加のどちらで行くか明記）。
