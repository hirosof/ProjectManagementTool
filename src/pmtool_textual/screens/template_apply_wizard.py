"""Template Apply Wizard - テンプレート適用ウィザード"""
from textual.widgets import Static, Input, Button, DataTable
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from textual.binding import Binding
from .base import BaseScreen
from pmtool.template import TemplateManager
from pmtool.repository import ProjectRepository


class TemplateApplyWizardScreen(BaseScreen):
    """Template Apply Wizard: 4ステップでテンプレート適用"""

    BINDINGS = [
        Binding("escape", "back", "Back"),
    ]

    def __init__(self, template_id: int = None):
        super().__init__()
        # ウィザードの状態
        self.current_step = 1
        self.selected_template_id = template_id
        self.selected_project_id = None
        self.new_subproject_name = ""
        self.dry_run_result = None

    def compose_main(self) -> ComposeResult:
        """メインコンテンツの構成"""
        yield Vertical(
            Static("[bold]Template Apply Wizard[/bold]", id="title"),
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
        next_btn.label = "適用" if self.current_step == 4 else "次へ"

        # 各ステップの適切なウィジェットにフォーカスを設定
        if self.current_step == 1:
            table = self.query_one("#template_table", DataTable)
            table.focus()
        elif self.current_step == 2:
            table = self.query_one("#project_table", DataTable)
            table.focus()
        elif self.current_step == 4:
            name_input = self.query_one("#new_name_input", Input)
            name_input.focus()

    def render_step1(self, container: Vertical) -> None:
        """Step 1: Template選択"""
        container.mount(
            Static("適用するテンプレートを選択してください:", id="step1_label"),
            DataTable(id="template_table"),
        )

        # Template一覧を取得
        db = self.app.db_manager.connect()
        template_manager = TemplateManager(db)
        templates = template_manager.list_templates()

        table = self.query_one("#template_table", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Name", "Description", "Tasks", "Created")

        for tpl in templates:
            table.add_row(
                str(tpl.id),
                tpl.name,
                tpl.description or "",
                "含む" if tpl.include_tasks else "含まない",
                tpl.created_at[:10],
                key=str(tpl.id),
            )

        # 初期選択（template_idが指定されている場合、または最初の行を選択）
        if table.row_count > 0:
            if self.selected_template_id is not None:
                try:
                    row_index = self._find_row_index(table, str(self.selected_template_id))
                    table.move_cursor(row=row_index)
                except:
                    table.move_cursor(row=0)
                    first_key = list(table.rows.keys())[0]
                    self.selected_template_id = int(first_key.value)
            else:
                # 最初の行を選択
                table.move_cursor(row=0)
                first_key = list(table.rows.keys())[0]
                self.selected_template_id = int(first_key.value)

    def _find_row_index(self, table: DataTable, row_key: str) -> int:
        """DataTableから指定したkeyの行インデックスを取得"""
        for idx, key in enumerate(table.rows):
            if key.value == row_key:
                return idx
        return 0

    def render_step2(self, container: Vertical) -> None:
        """Step 2: 適用先Project選択"""
        container.mount(
            Static("適用先のProjectを選択してください:", id="step2_label"),
            DataTable(id="project_table"),
        )

        # Project一覧を取得
        db = self.app.db_manager.connect()
        proj_repo = ProjectRepository(db)
        projects = proj_repo.get_all()

        table = self.query_one("#project_table", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Name", "Description", "Updated")

        for proj in projects:
            table.add_row(
                str(proj.id),
                proj.name,
                proj.description or "",
                proj.updated_at[:10],
                key=str(proj.id),
            )

        # 最初の行を選択
        if table.row_count > 0:
            table.move_cursor(row=0)
            first_key = list(table.rows.keys())[0]
            self.selected_project_id = int(first_key.value)

    def render_step3(self, container: Vertical) -> None:
        """Step 3: dry-runプレビュー"""
        if self.dry_run_result is None:
            # dry-run実行
            db = self.app.db_manager.connect()
            template_manager = TemplateManager(db)
            self.dry_run_result = template_manager.dry_run(
                template_id=self.selected_template_id,
                project_id=self.selected_project_id,
            )

        # プレビュー表示
        preview_text = f"""
[bold]適用プレビュー[/bold]

作成されるSubProject名: {self.dry_run_result['subproject_name']}

作成されるノード数:
  SubProject: 1
  Task: {self.dry_run_result['task_count']}
  SubTask: {self.dry_run_result['subtask_count']}
  依存関係: {self.dry_run_result['dependency_count']}

Task一覧:
"""
        for task_name in self.dry_run_result['tasks']:
            preview_text += f"  📋 {task_name}\n"

        container.mount(Static(preview_text.strip(), id="step3_preview"))

    def render_step4(self, container: Vertical) -> None:
        """Step 4: 新SubProject名入力・適用実行"""
        container.mount(
            Static("新しく作成されるSubProjectの名前を入力してください:", id="step4_label"),
            Input(
                placeholder="例: Webアプリ開発_2024-01",
                id="new_name_input",
                value=self.new_subproject_name or self.dry_run_result['subproject_name'],
            ),
            Static(
                "\n[dim]「適用」ボタンを押すと、テンプレートが適用されます。[/dim]",
                id="step4_hint"
            ),
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """行選択時の処理"""
        if self.current_step == 1:
            self.selected_template_id = int(event.row_key.value)
        elif self.current_step == 2:
            self.selected_project_id = int(event.row_key.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """ボタン押下時の処理"""
        if event.button.id == "prev_btn":
            self.action_prev_step()
        elif event.button.id == "next_btn":
            self.action_next_step()
        elif event.button.id == "cancel_btn":
            self.action_back()

    def action_prev_step(self) -> None:
        """前のステップへ戻る"""
        if self.current_step > 1:
            self.current_step -= 1
            # Step 3から戻る場合、dry-run結果をクリア
            if self.current_step == 2:
                self.dry_run_result = None
            self.update_step()

    def action_next_step(self) -> None:
        """次のステップへ進む（または適用実行）"""
        # 入力値の保存・検証
        if self.current_step == 1:
            if self.selected_template_id is None:
                # エラー表示
                return
        elif self.current_step == 2:
            if self.selected_project_id is None:
                # エラー表示
                return

        # 最終ステップなら適用実行
        if self.current_step == 4:
            self.apply_template()
            return

        # 次のステップへ
        self.current_step += 1
        self.update_step()

    def apply_template(self) -> None:
        """テンプレート適用処理"""
        db = self.app.db_manager.connect()
        template_manager = TemplateManager(db)

        try:
            # 新SubProject名を取得
            name_input = self.query_one("#new_name_input", Input)
            self.new_subproject_name = name_input.value

            if not self.new_subproject_name.strip():
                # エラー表示
                content = self.query_one("#step_content", Vertical)
                content.mount(Static("[red]SubProject名を入力してください[/red]", id="error_msg"))
                return

            # 適用実行
            new_subproject_id = template_manager.apply_template(
                template_id=self.selected_template_id,
                project_id=self.selected_project_id,
                new_subproject_name=self.new_subproject_name,
            )

            # 成功メッセージ表示後、SubProject Detail画面へ遷移
            content = self.query_one("#step_content", Vertical)
            content.remove_children()
            content.mount(
                Static(
                    f"[green]テンプレートを適用しました\n新SubProject ID: {new_subproject_id}[/green]",
                    id="success_msg"
                )
            )

            # 1秒後に画面を閉じてSubProject Detail画面へ遷移
            self.set_timer(1.0, lambda: self.navigate_to_subproject(new_subproject_id))

        except Exception as e:
            # エラー表示
            content = self.query_one("#step_content", Vertical)
            content.remove_children()
            content.mount(Static(f"[red]適用エラー: {e}[/red]", id="error_msg"))

    def navigate_to_subproject(self, subproject_id: int) -> None:
        """SubProject Detail画面へ遷移"""
        self.app.pop_screen()
        self.app.push_subproject_detail(subproject_id=subproject_id)

    def action_back(self) -> None:
        """ESCキーまたはキャンセルボタンで元の画面に戻る"""
        self.app.pop_screen()
