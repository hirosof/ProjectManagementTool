"""Home画面（ダミー）"""
from textual.widgets import Static
from textual.app import ComposeResult
from .base import BaseScreen


class HomeScreen(BaseScreen):
    def compose_main(self) -> ComposeResult:
        """メインコンテンツの構成"""
        yield Static("Home Screen (WIP)", id="content")
