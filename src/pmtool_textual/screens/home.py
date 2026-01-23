"""Home画面（ダミー）"""
from textual.containers import Container
from textual.widgets import Static
from textual.app import ComposeResult
from .base import BaseScreen


class HomeScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield from super().compose()
        yield Container(
            Static("Home Screen (WIP)", id="content"),
            id="main"
        )
