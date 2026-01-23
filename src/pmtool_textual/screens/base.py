"""基底Screen クラス"""
from textual.screen import Screen
from textual.widgets import Header, Footer
from textual.containers import Container
from textual.app import ComposeResult


class BaseScreen(Screen):
    """全画面の基底クラス

    Header / Main Container / Footer の3層構造を提供。
    派生クラスは compose_main() をオーバーライドして
    メインコンテンツを実装する。
    """

    def compose(self) -> ComposeResult:
        """画面構成: Header / Main / Footer"""
        yield Header()
        yield Container(*self.compose_main(), id="main")
        yield Footer()

    def compose_main(self) -> ComposeResult:
        """メインコンテンツの構成（派生クラスでオーバーライド）"""
        yield

    def on_mount(self) -> None:
        """画面表示時の処理"""
        pass
