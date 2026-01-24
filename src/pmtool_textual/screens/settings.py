"""Settings画面"""
from pathlib import Path
from textual.widgets import Static
from textual.app import ComposeResult
from .base import BaseScreen


class SettingsScreen(BaseScreen):
    """設定画面

    DBパス表示とバックアップ案内を提供する。
    """

    BINDINGS = [
        ("escape", "back", "Back"),
    ]

    def compose_main(self) -> ComposeResult:
        """メインコンテンツの構成"""
        yield Static("[bold cyan]設定[/bold cyan]", id="title")
        yield Static("", id="db_info")
        yield Static("", id="backup_guide")

    def on_mount(self) -> None:
        """画面表示時の処理"""
        # DBパス表示（絶対パスに変換）
        db_path = Path(self.app.db_manager.db_path).resolve()
        self.query_one("#db_info").update(
            f"\n[bold]データベース:[/bold]\n"
            f"  {db_path}\n"
        )

        # バックアップ案内
        self.query_one("#backup_guide").update(
            "\n[bold]バックアップ:[/bold]\n"
            "上記のデータベースファイルを定期的にコピーして\n"
            "バックアップすることを推奨します。\n\n"
            "[bold]手順:[/bold]\n"
            f"  1. アプリを終了する\n"
            f"  2. 以下のファイルをコピーする\n"
            f"     {db_path}\n"
            f"  3. 安全な場所に保存する\n"
        )

    def action_back(self) -> None:
        """ESCキーで一つ前の画面に戻る"""
        self.app.pop_screen()
