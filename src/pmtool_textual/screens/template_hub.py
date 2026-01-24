"""Template Hub画面 - テンプレート一覧・管理"""
from textual.widgets import DataTable, Static
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from .base import BaseScreen
from pmtool.template import TemplateManager


class DeleteConfirmDialog(ModalScreen):
    """テンプレート削除確認ダイアログ"""

    def __init__(self, template_name: str):
        super().__init__()
        self.template_name = template_name
        self.result = False

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(
                f"テンプレート「{self.template_name}」を削除しますか？\n"
                "この操作は取り消せません。",
                id="confirm_message",
            ),
            Horizontal(
                Button("削除する", variant="error", id="confirm_btn"),
                Button("キャンセル", variant="primary", id="cancel_btn"),
                id="button_row",
            ),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """ボタン押下時の処理"""
        if event.button.id == "confirm_btn":
            self.result = True
        else:
            self.result = False
        self.dismiss(self.result)


class TemplateHubScreen(BaseScreen):
    """Template Hub画面: テンプレート一覧・管理"""

    BINDINGS = [
        Binding("a", "apply_wizard", "Apply Template"),
        Binding("d", "delete_template", "Delete Template"),
        Binding("escape", "back", "Back"),
    ]

    def __init__(self):
        super().__init__()
        self.selected_template_id = None

    def compose_main(self) -> ComposeResult:
        """メインコンテンツの構成"""
        yield Vertical(
            Static("[bold]テンプレート一覧[/bold]", id="title"),
            DataTable(id="template_table"),
            Static("", id="template_detail"),
        )

    def on_mount(self) -> None:
        """画面表示時にテンプレート一覧を読み込む"""
        table = self.query_one("#template_table", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Name", "Description", "Tasks", "Created")
        self.load_templates()

    def on_show(self) -> None:
        """画面が表示されるたびに呼ばれる"""
        # 初回マウント時は on_mount で読み込むので、2回目以降のみ再読み込み
        table = self.query_one("#template_table", DataTable)
        has_columns = len(table.columns) > 0
        if table.row_count > 0 or has_columns:
            self.load_templates()

    def on_resume(self) -> None:
        """画面再開時（子画面から戻った時）にテンプレート一覧を再読み込み"""
        self.load_templates()

    def load_templates(self) -> None:
        """テンプレート一覧をDBから取得して表示"""
        db = self.app.db_manager.connect()
        template_manager = TemplateManager(db)
        templates = template_manager.list_templates()

        table = self.query_one("#template_table", DataTable)
        # 行のみをクリア（列定義は保持）
        table.clear(columns=False)

        for tpl in templates:
            table.add_row(
                str(tpl.id),
                tpl.name,
                tpl.description or "",
                "含む" if tpl.include_tasks else "含まない",
                tpl.created_at[:10],
                key=str(tpl.id),
            )

        if not templates:
            detail = self.query_one("#template_detail", Static)
            detail.update("[dim]テンプレートがありません[/dim]")
        else:
            # テーブルにフォーカスを設定し、最初の行を選択状態にする
            table.focus()
            if table.row_count > 0:
                table.move_cursor(row=0)
                # 最初のテンプレートを選択状態にする
                first_key = list(table.rows.keys())[0]
                self.selected_template_id = int(first_key.value)
                template = template_manager.get_template(self.selected_template_id)
                if template:
                    detail_text = f"""
[bold]{template.name}[/bold]
ID: {template.id}
説明: {template.description or "(なし)"}
Task含む: {"はい" if template.include_tasks else "いいえ"}
作成日時: {template.created_at}
更新日時: {template.updated_at}
"""
                    detail = self.query_one("#template_detail", Static)
                    detail.update(detail_text.strip())

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """テンプレート選択時に詳細を表示"""
        row_key = event.row_key.value
        self.selected_template_id = int(row_key)

        db = self.app.db_manager.connect()
        template_manager = TemplateManager(db)
        template = template_manager.get_template(self.selected_template_id)

        if template is None:
            return

        # テンプレート詳細表示
        detail_text = f"""
[bold]{template.name}[/bold]
ID: {template.id}
説明: {template.description or "(なし)"}
Task含む: {"はい" if template.include_tasks else "いいえ"}
作成日時: {template.created_at}
更新日時: {template.updated_at}
"""
        detail = self.query_one("#template_detail", Static)
        detail.update(detail_text.strip())

    def action_apply_wizard(self) -> None:
        """Aキー: Template Apply Wizardへ遷移"""
        if self.selected_template_id is None:
            detail = self.query_one("#template_detail", Static)
            detail.update("[red]テンプレートを選択してください[/red]")
            return

        self.app.push_apply_wizard(template_id=self.selected_template_id)

    def action_delete_template(self) -> None:
        """Dキー: テンプレート削除（確認ダイアログ表示）"""
        if self.selected_template_id is None:
            detail = self.query_one("#template_detail", Static)
            detail.update("[red]テンプレートを選択してください[/red]")
            return

        # workerで削除処理を実行
        self.run_worker(self._delete_template_worker(), exclusive=True)

    async def _delete_template_worker(self) -> None:
        """削除処理のworker"""
        db = self.app.db_manager.connect()
        template_manager = TemplateManager(db)
        template = template_manager.get_template(self.selected_template_id)

        if template is None:
            return

        # 削除確認ダイアログ表示
        dialog = DeleteConfirmDialog(template.name)
        result = await self.app.push_screen_wait(dialog)

        if result:
            # 削除実行
            try:
                template_manager.delete_template(self.selected_template_id)
                detail = self.query_one("#template_detail", Static)
                detail.update(f"[green]テンプレート「{template.name}」を削除しました[/green]")
                self.selected_template_id = None
                self.load_templates()  # 一覧を再読み込み
            except Exception as e:
                detail = self.query_one("#template_detail", Static)
                detail.update(f"[red]削除エラー: {e}[/red]")

    def action_back(self) -> None:
        """ESCキーで一つ前の画面に戻る"""
        self.app.pop_screen()
