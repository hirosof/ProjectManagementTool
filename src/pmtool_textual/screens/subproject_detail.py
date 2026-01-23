"""SubProject Detail画面 - Task/SubTaskツリー表示"""
from textual.widgets import Tree, Static
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.binding import Binding
from .base import BaseScreen
from pmtool.repository import SubProjectRepository, TaskRepository, SubTaskRepository


class SubProjectDetailScreen(BaseScreen):
    """SubProject Detail画面: Task/SubTaskツリー + Template保存機能"""

    BINDINGS = [
        Binding("s", "save_template", "Save Template"),
        Binding("escape", "back", "Back"),
    ]

    def __init__(self, subproject_id: int):
        super().__init__()
        self.subproject_id = subproject_id

    def compose_main(self) -> ComposeResult:
        """メインコンテンツの構成"""
        yield Vertical(
            Static("", id="subproject_info"),
            Tree("SubProject", id="subproject_tree"),
        )

    def on_mount(self) -> None:
        """SubProject情報とツリーを読み込む"""
        db = self.app.db_manager.connect()
        sp_repo = SubProjectRepository(db)
        subproject = sp_repo.get_by_id(self.subproject_id)

        if subproject is None:
            self.app.pop_screen()
            return

        # SubProject情報表示
        info = self.query_one("#subproject_info", Static)
        info.update(
            f"[bold]{subproject.name}[/bold]\n"
            f"ID: {subproject.id} | Updated: {subproject.updated_at[:10]}\n"
            f"{subproject.description or ''}"
        )

        # Task/SubTaskツリー構築
        self.build_tree(subproject)

    def build_tree(self, subproject) -> None:
        """Task/SubTaskツリーを構築"""
        tree = self.query_one("#subproject_tree", Tree)
        tree.clear()

        db = self.app.db_manager.connect()
        task_repo = TaskRepository(db)
        st_repo = SubTaskRepository(db)

        # Task一覧取得
        tasks = task_repo.get_by_parent(subproject.project_id, subproject.id)

        for task in tasks:
            task_node = tree.root.add(
                f"📋 {task.name} [{task.status}]",
                data={"type": "task", "id": task.id},
            )

            # SubTask一覧取得
            subtasks = st_repo.get_by_task(task.id)
            for st in subtasks:
                task_node.add(
                    f"✓ {st.name} [{st.status}]",
                    data={"type": "subtask", "id": st.id},
                )

        tree.root.expand()

    def action_save_template(self) -> None:
        """Sキー: Template Save Wizardへ遷移"""
        # TODO: P5-11でTemplateSaveWizardを実装後、遷移処理を追加
        # self.app.push_save_wizard(subproject_id=self.subproject_id)
        pass

    def action_back(self) -> None:
        """ESCキーで一つ前の画面に戻る"""
        self.app.pop_screen()
