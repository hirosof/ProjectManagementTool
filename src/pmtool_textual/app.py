"""Textual UI アプリケーションメインクラス"""
from textual.app import App
from textual.binding import Binding
from .screens.home import HomeScreen
from .screens.project_detail import ProjectDetailScreen
from .screens.subproject_detail import SubProjectDetailScreen
from .screens.template_hub import TemplateHubScreen
from .screens.template_save_wizard import TemplateSaveWizardScreen
from .screens.template_apply_wizard import TemplateApplyWizardScreen
from .screens.settings import SettingsScreen
from .utils.db_manager import DBManager


class PMToolApp(App):
    """Project Management Tool - Textual UI"""

    TITLE = "Project Management Tool"

    BINDINGS = [
        Binding("h", "home", "Home"),
        Binding("q", "quit", "Quit"),
    ]

    SCREENS = {"home": HomeScreen}

    def __init__(self):
        super().__init__()
        self.db_manager = DBManager()

    def on_mount(self) -> None:
        """アプリケーション起動時の処理"""
        self.push_screen("home")

    def push_project_detail(self, project_id: int) -> None:
        """ProjectDetailScreenへ遷移"""
        screen = ProjectDetailScreen(project_id=project_id)
        self.push_screen(screen)

    def push_subproject_detail(self, subproject_id: int) -> None:
        """SubProjectDetailScreenへ遷移"""
        screen = SubProjectDetailScreen(subproject_id=subproject_id)
        self.push_screen(screen)

    def push_template_hub(self) -> None:
        """TemplateHubScreenへ遷移"""
        # 毎回新しいインスタンスを作成して最新データを表示
        screen = TemplateHubScreen()
        self.push_screen(screen)

    def push_save_wizard(self, subproject_id: int = None) -> None:
        """TemplateSaveWizardScreenへ遷移"""
        screen = TemplateSaveWizardScreen(subproject_id=subproject_id)
        self.push_screen(screen)

    def push_apply_wizard(self, template_id: int = None) -> None:
        """TemplateApplyWizardScreenへ遷移"""
        screen = TemplateApplyWizardScreen(template_id=template_id)
        self.push_screen(screen)

    def push_settings(self) -> None:
        """SettingsScreenへ遷移"""
        screen = SettingsScreen()
        self.push_screen(screen)

    def action_quit(self) -> None:
        """Qキーでアプリ終了"""
        self.exit()

    def action_home(self) -> None:
        """HキーでHomeに戻る"""
        # 現在の画面がHomeScreenでない限りpopを繰り返す
        from .screens.home import HomeScreen
        while len(self.screen_stack) > 1 and not isinstance(self.screen, HomeScreen):
            self.pop_screen()


def main() -> None:
    """エントリーポイント"""
    app = PMToolApp()
    app.run()


if __name__ == "__main__":
    main()
