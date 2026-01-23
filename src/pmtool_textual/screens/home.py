"""Home画面 - Project一覧表示"""
from textual.widgets import DataTable
from textual.app import ComposeResult
from textual.binding import Binding
from .base import BaseScreen
from ...pmtool.repository import ProjectRepository


class HomeScreen(BaseScreen):
    """Home画面: Project一覧をDataTableで表示"""

    BINDINGS = [
        Binding("t", "template_hub", "Template Hub"),
        Binding("s", "settings", "Settings"),
        Binding("q", "quit", "Quit"),
    ]

    def compose_main(self) -> ComposeResult:
        """メインコンテンツの構成"""
        yield DataTable(id="project_table")

    def on_mount(self) -> None:
        """画面マウント時の処理"""
        table = self.query_one(DataTable)

        # カラム設定
        table.add_columns("ID", "Name", "Description", "Status", "Updated")
        table.cursor_type = "row"
        table.zebra_stripes = True

        # データ読み込み
        self.load_projects()

    def load_projects(self) -> None:
        """Projectデータを読み込んでテーブルに表示"""
        db = self.app.db_manager.connect()
        repo = ProjectRepository(db)
        projects = repo.list_projects()

        table = self.query_one(DataTable)
        table.clear()

        for project in projects:
            # Status計算（簡易版: SubProject/Task件数から推測）
            # TODO: P5-08でステータス集計ロジックを実装予定
            status = "Active"

            # 行追加
            table.add_row(
                str(project.id),
                project.name,
                project.description or "",
                status,
                project.updated_at[:10],  # YYYY-MM-DD部分のみ
                key=str(project.id),
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """テーブル行選択時: ProjectDetailScreenに遷移"""
        project_id = int(event.row_key.value)
        self.app.push_project_detail(project_id)

    def action_template_hub(self) -> None:
        """Template Hub画面へ遷移"""
        # TODO: P5-10でTemplateHubScreenを実装後、遷移処理を追加
        # self.app.push_screen("template_hub")
        pass

    def action_settings(self) -> None:
        """Settings画面へ遷移"""
        # TODO: P5-13でSettingsScreenを実装後、遷移処理を追加
        # self.app.push_screen("settings")
        pass

    def action_quit(self) -> None:
        """アプリケーション終了"""
        self.app.exit()
