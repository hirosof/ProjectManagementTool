P5-12 Textual UI基本構造設計書 v1.0.0 レビュー結果：条件付き承認（軽微修正あり）

Must fix:
1) Save Wizard の警告フローがBL設計(P5-9)と矛盾：
   - P5-12の例だと save_template() 後に has_warnings を見て「キャンセルなら保存中止」になっているが、
     P5-9では save_template() は commit して結果を返すため、後から中止できない。
   - 対応案（推奨）：外部依存警告などは Step4（確認画面）で事前に検出API（preview/detect）で表示し、
     ユーザー同意後に save_template() を実行するフローに修正して下さい。

2) 戻るキー規約の不整合：
   - 4.2/6.1ではESC=Home、画面別ではESC=Backが混在。
   - ESCはBack（キャンセル/一つ前）に統一し、Homeへ戻る専用キー（例：H）等を設けるなど、規約を一本化して下さい。

Should fix（推奨）:
3) Project直下TaskのTree表示上の配置方針を明記（Project直下/表示のみの区画として分離）。
4) 「3クリック以内」→「3操作以内」等、キーボード中心UIに合わせた指標へ調整。
5) Textualバージョンの固定方針（例：~=0.50）を注記（再現性向上）。
