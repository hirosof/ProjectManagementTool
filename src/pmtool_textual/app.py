"""Textual UI アプリケーションメインクラス"""
from textual.app import App
from textual.binding import Binding
from .screens.home import HomeScreen


class PMToolApp(App):
    """Project Management Tool - Textual UI"""

    TITLE = "Project Management Tool"

    BINDINGS = [
        Binding("h", "home", "Home"),
        Binding("q", "quit", "Quit"),
    ]

    SCREENS = {"home": HomeScreen}

    def on_mount(self) -> None:
        """アプリケーション起動時の処理"""
        self.push_screen("home")

    def action_quit(self) -> None:
        """Qキーでアプリ終了"""
        self.exit()

    def action_home(self) -> None:
        """HキーでHomeに戻る"""
        # 画面スタックをクリアしてHomeに戻る
        while len(self.screen_stack) > 1:
            self.pop_screen()


def main() -> None:
    """エントリーポイント"""
    app = PMToolApp()
    app.run()


if __name__ == "__main__":
    main()
