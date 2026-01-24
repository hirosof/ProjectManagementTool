"""Template Save Wizard - テンプレート保存ウィザード"""
from textual.widgets import Static, Input, Button, Label, DataTable, Checkbox
from textual.containers import Vertical, Horizontal, Grid
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from .base import BaseScreen
from pmtool.template import TemplateManager
from pmtool.repository import SubProjectRepository, ProjectRepository


class ExternalDependencyWarningDialog(ModalScreen):
    """外部依存警告ダイアログ"""

    def __init__(self, warnings: list):
        super().__init__()
        self.warnings = warnings
        self.result = False

    def compose(self) -> ComposeResult:
        # 警告メッセージ生成
        warning_text = "以下の外部依存が検出されました:\n\n"
        for w in self.warnings:
            if w.direction == "outgoing":
                warning_text += f"  • {w.from_task_name} → {w.to_task_name} (SubProject外への依存)\n"
            else:
                warning_text += f"  • {w.to_task_name} ← {w.from_task_name} (SubProject外からの依存)\n"
        warning_text += "\nこれらの依存関係はテンプレートに保存されません。続行しますか?"

        yield Vertical(
            Label(warning_text, id="warning_message"),
            Horizontal(
                Button("続行する", variant="warning", id="continue_btn"),
                Button("キャンセル", variant="primary", id="cancel_btn"),
                id="button_row",
            ),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """ボタン押下時の処理"""
        if event.button.id == "continue_btn":
            self.result = True
        else:
            self.result = False
        self.dismiss(self.result)


class TemplateSaveWizardScreen(BaseScreen):
    """Template Save Wizard: 4ステップでテンプレート保存"""

    BINDINGS = [
        Binding("escape", "back", "Back"),
    ]

    def __init__(self, subproject_id: int = None):
        super().__init__()
        # ウィザードの状態
        self.current_step = 1
        self.selected_subproject_id = subproject_id
        self.template_name = ""
        self.template_description = ""
        self.include_tasks = False

    def compose_main(self) -> ComposeResult:
        """メインコンテンツの構成"""
        yield Vertical(
            Static("[bold]Template Save Wizard[/bold]", id="title"),
            Static("", id="step_indicator"),
            Vertical(id="step_content"),
            Horizontal(
                Button("戻る", id="prev_btn", variant="default"),
                Button("次へ", id="next_btn", variant="primary"),
                Button("キャンセル", id="cancel_btn", variant="default"),
                id="button_row",
            ),
        )

    def on_mount(self) -> None:
        """画面マウント時の処理"""
        self.update_step()

    def update_step(self) -> None:
        """現在のステップに応じて画面を更新"""
        # ステップインジケータ更新
        indicator = self.query_one("#step_indicator", Static)
        indicator.update(f"Step {self.current_step} / 4")

        # ステップコンテンツ更新
        content = self.query_one("#step_content", Vertical)
        content.remove_children()

        if self.current_step == 1:
            self.render_step1(content)
        elif self.current_step == 2:
            self.render_step2(content)
        elif self.current_step == 3:
            self.render_step3(content)
        elif self.current_step == 4:
            self.render_step4(content)

        # ボタン状態更新
        prev_btn = self.query_one("#prev_btn", Button)
        next_btn = self.query_one("#next_btn", Button)
        prev_btn.disabled = (self.current_step == 1)
        next_btn.label = "保存" if self.current_step == 4 else "次へ"

        # 各ステップの適切なウィジェットにフォーカスを設定
        if self.current_step == 1:
            table = self.query_one("#subproject_table", DataTable)
            table.focus()
        elif self.current_step == 2:
            name_input = self.query_one("#name_input", Input)
            name_input.focus()
        elif self.current_step == 3:
            checkbox = self.query_one("#include_tasks_checkbox", Checkbox)
            checkbox.focus()

    def render_step1(self, container: Vertical) -> None:
        """Step 1: SubProject選択"""
        container.mount(
            Static("保存するSubProjectを選択してください:", id="step1_label"),
            DataTable(id="subproject_table"),
        )

        # SubProject一覧を取得
        db = self.app.db_manager.connect()
        sp_repo = SubProjectRepository(db)
        proj_repo = ProjectRepository(db)

        table = self.query_one("#subproject_table", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Project", "SubProject Name", "Updated")

        # 全SubProjectを取得
        projects = proj_repo.get_all()
        for project in projects:
            subprojects = sp_repo.get_by_project(project.id)
            for sp in subprojects:
                table.add_row(
                    str(sp.id),
                    project.name,
                    sp.name,
                    sp.updated_at[:10],
                    key=str(sp.id),
                )

        # 初期選択（subproject_idが指定されている場合、または最初の行を選択）
        if table.row_count > 0:
            if self.selected_subproject_id is not None:
                try:
                    row_index = self._find_row_index(table, str(self.selected_subproject_id))
                    table.move_cursor(row=row_index)
                except:
                    table.move_cursor(row=0)
                    first_key = list(table.rows.keys())[0]
                    self.selected_subproject_id = int(first_key.value)
            else:
                # 最初の行を選択
                table.move_cursor(row=0)
                first_key = list(table.rows.keys())[0]
                self.selected_subproject_id = int(first_key.value)

    def _find_row_index(self, table: DataTable, row_key: str) -> int:
        """DataTableから指定したkeyの行インデックスを取得"""
        for idx, key in enumerate(table.rows):
            if key.value == row_key:
                return idx
        return 0

    def render_step2(self, container: Vertical) -> None:
        """Step 2: テンプレート名入力"""
        container.mount(
            Static("テンプレート名:", id="step2_label"),
            Input(placeholder="例: Webアプリ開発テンプレート", id="name_input", value=self.template_name),
            Static("説明（オプション）:", id="step2_desc_label"),
            Input(placeholder="このテンプレートの説明を入力", id="desc_input", value=self.template_description),
        )

    def render_step3(self, container: Vertical) -> None:
        """Step 3: include_tasks選択"""
        container.mount(
            Static("テンプレートに含む内容を選択してください:", id="step3_label"),
            Checkbox("Task/SubTask/依存関係を含む", id="include_tasks_checkbox", value=self.include_tasks),
            Static(
                "\n[dim]チェックなし: SubProjectのメタデータのみ保存\n"
                "チェックあり: Task/SubTask/依存関係も保存[/dim]",
                id="step3_hint"
            ),
        )

    def render_step4(self, container: Vertical) -> None:
        """Step 4: 確認・保存"""
        db = self.app.db_manager.connect()
        sp_repo = SubProjectRepository(db)
        subproject = sp_repo.get_by_id(self.selected_subproject_id)

        summary = f"""
[bold]保存内容の確認[/bold]

SubProject: {subproject.name} (ID: {subproject.id})
テンプレート名: {self.template_name}
説明: {self.template_description or "(なし)"}
Task含む: {"はい" if self.include_tasks else "いいえ"}

「保存」ボタンを押すとテンプレートが作成されます。
"""
        container.mount(Static(summary.strip(), id="step4_summary"))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """SubProject選択時"""
        self.selected_subproject_id = int(event.row_key.value)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """ボタン押下時の処理"""
        if event.button.id == "prev_btn":
            self.action_prev_step()
        elif event.button.id == "next_btn":
            await self.action_next_step()
        elif event.button.id == "cancel_btn":
            self.action_back()

    def action_prev_step(self) -> None:
        """前のステップへ戻る"""
        if self.current_step > 1:
            self.current_step -= 1
            self.update_step()

    async def action_next_step(self) -> None:
        """次のステップへ進む（または保存実行）"""
        # 入力値の保存
        if self.current_step == 1:
            if self.selected_subproject_id is None:
                # エラー表示
                return
        elif self.current_step == 2:
            name_input = self.query_one("#name_input", Input)
            desc_input = self.query_one("#desc_input", Input)
            self.template_name = name_input.value
            self.template_description = desc_input.value

            # 名前チェック
            if not self.template_name.strip():
                # エラー表示
                return
        elif self.current_step == 3:
            checkbox = self.query_one("#include_tasks_checkbox", Checkbox)
            self.include_tasks = checkbox.value

        # 最終ステップなら保存実行
        if self.current_step == 4:
            await self.save_template()
            return

        # 次のステップへ
        self.current_step += 1
        self.update_step()

    async def save_template(self) -> None:
        """テンプレート保存処理"""
        db = self.app.db_manager.connect()
        template_manager = TemplateManager(db)

        try:
            # 1. テンプレート名重複チェック
            existing = template_manager.get_template_by_name(self.template_name)
            if existing:
                # エラー表示
                content = self.query_one("#step_content", Vertical)
                content.mount(Static("[red]テンプレート名が既に存在します[/red]", id="error_msg"))
                return

            # 2. 外部依存事前検出
            external_warnings = template_manager.detect_external_dependencies(
                subproject_id=self.selected_subproject_id,
            )

            # 3. 警告表示・確認
            if external_warnings:
                dialog = ExternalDependencyWarningDialog(external_warnings)
                result = await self.app.push_screen_wait(dialog)
                if not result:
                    return  # キャンセル

            # 4. 保存実行
            result = template_manager.save_template(
                subproject_id=self.selected_subproject_id,
                name=self.template_name,
                description=self.template_description,
                include_tasks=self.include_tasks,
            )

            # 成功メッセージ表示後、元の画面に戻る
            content = self.query_one("#step_content", Vertical)
            content.remove_children()
            content.mount(
                Static(
                    f"[green]テンプレート「{result.template.name}」を保存しました[/green]",
                    id="success_msg"
                )
            )

            # 1秒後に画面を閉じる
            self.set_timer(1.0, self.action_back)

        except Exception as e:
            # エラー表示
            content = self.query_one("#step_content", Vertical)
            content.remove_children()
            content.mount(Static(f"[red]保存エラー: {e}[/red]", id="error_msg"))

    def action_back(self) -> None:
        """ESCキーまたはキャンセルボタンで元の画面に戻る"""
        self.app.pop_screen()
