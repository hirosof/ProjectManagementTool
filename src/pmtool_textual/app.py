"""Textual UI アプリケーションメインクラス"""
from textual.app import App


class PMToolApp(App):
    """Project Management Tool - Textual UI"""

    TITLE = "Project Management Tool"

    def on_mount(self) -> None:
        """アプリケーション起動時の処理"""
        pass


def main() -> None:
    """エントリーポイント"""
    app = PMToolApp()
    app.run()


if __name__ == "__main__":
    main()
