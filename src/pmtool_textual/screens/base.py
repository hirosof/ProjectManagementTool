"""基底Screen クラス"""
from textual.screen import Screen
from textual.widgets import Header, Footer
from textual.app import ComposeResult


class BaseScreen(Screen):
    """全画面の基底クラス"""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """画面表示時の処理"""
        pass
