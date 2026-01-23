"""Project Detail画面 - 4階層ツリー表示"""
from textual.widgets import Tree, Static
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.binding import Binding
from .base import BaseScreen
from pmtool.repository import ProjectRepository, SubProjectRepository, TaskRepository, SubTaskRepository


class ProjectDetailScreen(BaseScreen):
    """Project Detail画面: 4階層ツリー（Project→SubProject→Task→SubTask）"""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("h", "home", "Home"),
    ]

    def __init__(self, project_id: int):
        super().__init__()
        self.project_id = project_id

    def compose_main(self) -> ComposeResult:
        """メインコンテンツの構成"""
        yield Vertical(
            Static("", id="project_info"),
            Tree("Project", id="project_tree"),
        )

    def on_mount(self) -> None:
        """Project情報とツリーを読み込む"""
        db = self.app.db_manager.connect()
        repo = ProjectRepository(db)
        project = repo.get_by_id(self.project_id)

        if project is None:
            self.app.pop_screen()
            return

        # Project情報表示
        info = self.query_one("#project_info", Static)
        info.update(
            f"[bold]{project.name}[/bold]\n"
            f"ID: {project.id} | Updated: {project.updated_at[:10]}\n"
            f"{project.description or ''}"
        )

        # 4階層ツリー構築
        self.build_tree(project)

    def build_tree(self, project) -> None:
        """4階層ツリーを構築"""
        tree = self.query_one("#project_tree", Tree)
        tree.clear()

        db = self.app.db_manager.connect()
        sp_repo = SubProjectRepository(db)
        task_repo = TaskRepository(db)
        st_repo = SubTaskRepository(db)

        # SubProject一覧取得
        subprojects = sp_repo.get_by_project(project.id)

        for sp in subprojects:
            sp_node = tree.root.add(
                f"📁 {sp.name} [UNSET]",  # SubProjectにはstatusフィールドがない
                data={"type": "subproject", "id": sp.id},
            )

            # Task一覧取得
            tasks = task_repo.get_by_parent(project.id, sp.id)
            for task in tasks:
                task_node = sp_node.add(
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

        # Project直下Task区画（グレーアウト）
        direct_tasks = task_repo.get_by_parent(project.id, None)
        if direct_tasks:
            direct_node = tree.root.add(
                "[dim]Project直下のTask（操作不可）[/dim]",
                data={"type": "section"},
            )
            for task in direct_tasks:
                direct_node.add(
                    f"[dim]📋 {task.name}[/dim]",
                    data={"type": "readonly"},
                )

        tree.root.expand()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """ツリーノード選択時の処理"""
        node_data = event.node.data
        if node_data and node_data.get("type") == "subproject":
            subproject_id = node_data["id"]
            self.app.push_subproject_detail(subproject_id)

    def action_back(self) -> None:
        """ESCキーで一つ前の画面に戻る"""
        self.app.pop_screen()

    def action_home(self) -> None:
        """HキーでHomeに戻る（画面スタックをクリア）"""
        while len(self.app.screen_stack) > 1:
            self.app.pop_screen()
