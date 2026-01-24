"""初回セットアップ画面"""
from pathlib import Path
from textual.widgets import Static, Button
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from .base import BaseScreen


class SetupScreen(BaseScreen):
    """初回セットアップ画面

    DB未作成時に表示され、データベースの初期化を行う。
    """

    def compose_main(self) -> ComposeResult:
        """メインコンテンツの構成"""
        yield Vertical(
            Static("[bold cyan]初回セットアップ[/bold cyan]", id="title"),
            Static(
                "\nデータベースが見つかりません。\n"
                "初期化しますか？\n\n"
                f"DBパス: {self.app.db_manager.db_path}\n",
                id="message"
            ),
            Horizontal(
                Button("初期化する", id="btn_init", variant="primary"),
                Button("終了", id="btn_quit", variant="default"),
                id="buttons"
            ),
            Static("", id="status"),
            id="setup_container"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """ボタン押下時の処理"""
        if event.button.id == "btn_init":
            self.initialize_database()
        elif event.button.id == "btn_quit":
            self.app.exit()

    def initialize_database(self) -> None:
        """データベース初期化処理"""
        status_widget = self.query_one("#status", Static)
        status_widget.update("[yellow]初期化中...[/yellow]")

        try:
            # init_db.sqlのパスを計算（__file__からの相対パス）
            # src/pmtool_textual/screens/setup.py から scripts/init_db.sql へのパス
            current_file = Path(__file__)  # src/pmtool_textual/screens/setup.py
            project_root = current_file.parent.parent.parent.parent  # ProjectManagementTool/
            init_sql_path = project_root / "scripts" / "init_db.sql"

            if not init_sql_path.exists():
                raise FileNotFoundError(f"初期化SQLファイルが見つかりません: {init_sql_path}")

            # dataディレクトリが存在しない場合は作成
            db_path = Path(self.app.db_manager.db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # データベース初期化
            db = self.app.db_manager.connect()
            db.initialize(init_sql_path, force=False)

            status_widget.update("[green]初期化完了！[/green]")

            # 初期化成功後、Home画面へ遷移
            self.app.call_after_refresh(self.transition_to_home)

        except FileNotFoundError as e:
            status_widget.update(f"[red]エラー: {e}[/red]")
        except Exception as e:
            status_widget.update(f"[red]初期化エラー: {e}[/red]")

    def transition_to_home(self) -> None:
        """Home画面への遷移"""
        # Setup画面をpopしてHome画面をpush
        self.app.pop_screen()
        self.app.push_screen("home")
