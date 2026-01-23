"""
テンプレート機能ビジネスロジック層

Phase 5で追加されたテンプレート機能の管理クラスを提供します。
"""

import sqlite3
from typing import Optional

from .database import Database
from .repository import SubProjectRepository, TaskRepository, SubTaskRepository
from .repository_template import TemplateRepository
from .dependencies import DependencyManager
from .models import (
    Template,
    TemplateTask,
    TemplateSubTask,
    TemplateDependency,
    ExternalDependencyWarning,
    SaveTemplateResult,
)
from .exceptions import EntityNotFoundError


class TemplateManager:
    """テンプレート機能の管理クラス (Phase 5)

    SubProjectテンプレートの保存・一覧・詳細・適用・削除機能を提供します。
    """

    def __init__(self, db: Database):
        self.db = db
        self.template_repo = TemplateRepository(db)
        self.subproject_repo = SubProjectRepository(db)
        self.task_repo = TaskRepository(db)
        self.subtask_repo = SubTaskRepository(db)
        self.dep_manager = DependencyManager(db)

    # ============================================================
    # 基本メソッド (P5-05)
    # ============================================================

    def list_templates(
        self,
        conn: Optional[sqlite3.Connection] = None,
    ) -> list[Template]:
        """テンプレート一覧を取得

        Args:
            conn: トランザクション用接続（オプション）

        Returns:
            Templateオブジェクトのリスト（作成日時降順）
        """
        return self.template_repo.list_templates(conn)

    def get_template(
        self,
        template_id: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[Template]:
        """テンプレートを取得

        Args:
            template_id: テンプレートID
            conn: トランザクション用接続（オプション）

        Returns:
            Templateオブジェクト、存在しない場合はNone
        """
        return self.template_repo.get_template(template_id, conn)

    def get_template_by_name(
        self,
        name: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[Template]:
        """名前でテンプレートを取得

        Args:
            name: テンプレート名
            conn: トランザクション用接続（オプション）

        Returns:
            Templateオブジェクト、存在しない場合はNone
        """
        return self.template_repo.get_template_by_name(name, conn)

    def delete_template(
        self,
        template_id: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        """テンプレートを削除

        CASCADE設定により関連レコードも自動削除される。

        Args:
            template_id: テンプレートID
            conn: トランザクション用接続（オプション）

        Raises:
            EntityNotFoundError: テンプレートが存在しない場合
        """
        # 存在確認
        template = self.template_repo.get_template(template_id, conn)
        if template is None:
            raise EntityNotFoundError(f"テンプレートID {template_id} が見つかりません")

        self.template_repo.delete_template(template_id, conn)

    # ============================================================
    # 高度なメソッド (P5-06)
    # ============================================================

    def save_template(
        self,
        subproject_id: int,
        name: str,
        description: Optional[str] = None,
        include_tasks: bool = False,
        conn: Optional[sqlite3.Connection] = None,
    ) -> SaveTemplateResult:
        """SubProjectをテンプレートとして保存

        外部依存が検出された場合は警告情報を返すが、エラーにはしない。
        UI側で警告を表示し、ユーザーの続行判断を求めること。

        Args:
            subproject_id: 保存対象のSubProject ID
            name: テンプレート名（UNIQUE制約）
            description: テンプレート説明（オプション）
            include_tasks: Task/SubTask/依存関係を含むか（デフォルト: False）
            conn: トランザクション用接続（オプション）

        Returns:
            SaveTemplateResultオブジェクト（template + 外部依存警告リスト）

        Raises:
            EntityNotFoundError: SubProjectが存在しない
            sqlite3.IntegrityError: テンプレート名が重複している
        """
        own_conn = False
        if conn is None:
            conn = self.db.connect()
            own_conn = True

        try:
            # 1. SubProjectの存在確認
            subproject = self.subproject_repo.get_subproject(subproject_id, conn)
            if subproject is None:
                raise EntityNotFoundError(f"SubProject ID {subproject_id} が見つかりません")

            # 2. 外部依存の検出
            external_warnings = self._detect_external_dependencies(subproject_id, conn)

            # 3. templatesレコード作成
            template = self.template_repo.add_template(
                name=name,
                description=description,
                include_tasks=include_tasks,
                conn=conn,
            )

            # 4. include_tasks=Trueの場合、Task/SubTask/依存関係を保存
            if include_tasks:
                # Task一覧取得（order_index昇順）
                tasks = self.task_repo.list_tasks(
                    project_id=subproject.project_id,
                    subproject_id=subproject_id,
                    conn=conn,
                )

                # Task IDからtask_orderへのマッピング構築
                task_id_to_order = {task.id: idx for idx, task in enumerate(tasks)}

                # Task保存
                for idx, task in enumerate(tasks):
                    self.template_repo.add_template_task(
                        template_id=template.id,
                        task_order=idx,
                        name=task.name,
                        description=task.description,
                        conn=conn,
                    )

                # SubTask保存
                for task_order, task in enumerate(tasks):
                    subtasks = self.subtask_repo.list_subtasks(task.id, conn)
                    for subtask_order, subtask in enumerate(subtasks):
                        # template_task_idを取得（template_idとtask_orderから）
                        template_tasks = self.template_repo.get_template_tasks(
                            template.id, conn
                        )
                        template_task = template_tasks[task_order]

                        self.template_repo.add_template_subtask(
                            template_task_id=template_task.id,
                            subtask_order=subtask_order,
                            name=subtask.name,
                            description=subtask.description,
                            conn=conn,
                        )

                # 内部依存関係保存
                internal_deps = self._get_internal_dependencies(
                    subproject_id, task_id_to_order, conn
                )

                for pred_order, succ_order in internal_deps:
                    self.template_repo.add_template_dependency(
                        template_id=template.id,
                        predecessor_order=pred_order,
                        successor_order=succ_order,
                        conn=conn,
                    )

            if own_conn:
                conn.commit()

            return SaveTemplateResult(
                template=template, external_dependencies=external_warnings
            )

        except Exception as e:
            if own_conn:
                conn.rollback()
            raise

    def apply_template(
        self,
        template_id: int,
        project_id: int,
        new_subproject_name: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> int:
        """テンプレートを適用（新SubProjectを作成）

        Args:
            template_id: テンプレートID
            project_id: 適用先ProjectID
            new_subproject_name: 新SubProject名（省略時はテンプレート名を使用）
            conn: トランザクション用接続（オプション）

        Returns:
            作成されたSubProject ID

        Raises:
            EntityNotFoundError: テンプレートまたはProjectが存在しない
        """
        own_conn = False
        if conn is None:
            conn = self.db.connect()
            own_conn = True

        try:
            # 1. テンプレート存在確認
            template = self.template_repo.get_template(template_id, conn)
            if template is None:
                raise EntityNotFoundError(f"テンプレートID {template_id} が見つかりません")

            # 2. Project存在確認
            from .repository import ProjectRepository

            project_repo = ProjectRepository(self.db)
            project = project_repo.get_project(project_id, conn)
            if project is None:
                raise EntityNotFoundError(f"Project ID {project_id} が見つかりません")

            # 3. 新SubProject作成（ステータスはUNSET固定）
            if new_subproject_name is None:
                new_subproject_name = template.name

            # order_indexを自動計算
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COALESCE(MAX(order_index), -1) + 1
                FROM subprojects
                WHERE project_id = ? AND parent_subproject_id IS NULL
                """,
                (project_id,),
            )
            order_index = cursor.fetchone()[0]

            new_subproject = self.subproject_repo.add_subproject(
                project_id=project_id,
                name=new_subproject_name,
                description=template.description,
                parent_subproject_id=None,
                order_index=order_index,
                conn=conn,
            )

            # 4. include_tasks=Trueの場合、Task/SubTask/依存関係を複製
            if template.include_tasks:
                # Task複製
                template_tasks = self.template_repo.get_template_tasks(template_id, conn)
                task_order_to_id = {}  # task_order -> 新Task ID のマッピング

                for template_task in template_tasks:
                    new_task = self.task_repo.add_task(
                        project_id=project_id,
                        subproject_id=new_subproject.id,
                        name=template_task.name,
                        description=template_task.description,
                        status="UNSET",
                        order_index=template_task.task_order,
                        conn=conn,
                    )
                    task_order_to_id[template_task.task_order] = new_task.id

                # SubTask複製
                template_subtasks = self.template_repo.get_template_subtasks(
                    template_id, conn
                )

                # template_task_idごとにグループ化
                subtasks_by_template_task = {}
                for ts in template_subtasks:
                    if ts.template_task_id not in subtasks_by_template_task:
                        subtasks_by_template_task[ts.template_task_id] = []
                    subtasks_by_template_task[ts.template_task_id].append(ts)

                for template_task in template_tasks:
                    new_task_id = task_order_to_id[template_task.task_order]
                    subtasks = subtasks_by_template_task.get(template_task.id, [])

                    for template_subtask in subtasks:
                        self.subtask_repo.add_subtask(
                            task_id=new_task_id,
                            name=template_subtask.name,
                            description=template_subtask.description,
                            status="UNSET",
                            order_index=template_subtask.subtask_order,
                            conn=conn,
                        )

                # 内部依存関係再接続
                template_deps = self.template_repo.get_template_dependencies(
                    template_id, conn
                )

                for dep in template_deps:
                    pred_task_id = task_order_to_id[dep.predecessor_order]
                    succ_task_id = task_order_to_id[dep.successor_order]

                    self.dep_manager.add_dependency(
                        pred_task_id, succ_task_id, "task", conn=conn
                    )

            if own_conn:
                conn.commit()

            return new_subproject.id

        except Exception as e:
            if own_conn:
                conn.rollback()
            raise

    def dry_run(
        self,
        template_id: int,
        project_id: int,
        new_subproject_name: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> dict:
        """テンプレート適用のdry-run（プレビュー）

        Args:
            template_id: テンプレートID
            project_id: 適用先ProjectID
            new_subproject_name: 新SubProject名（省略時はテンプレート名を使用）
            conn: トランザクション用接続（オプション）

        Returns:
            dry-run結果の辞書（件数サマリ + 1階層ツリー）

        Raises:
            EntityNotFoundError: テンプレートまたはProjectが存在しない
        """
        if conn is None:
            conn = self.db.connect()

        # 1. テンプレート存在確認
        template = self.template_repo.get_template(template_id, conn)
        if template is None:
            raise EntityNotFoundError(f"テンプレートID {template_id} が見つかりません")

        # 2. Project存在確認
        from .repository import ProjectRepository

        project_repo = ProjectRepository(self.db)
        project = project_repo.get_project(project_id, conn)
        if project is None:
            raise EntityNotFoundError(f"Project ID {project_id} が見つかりません")

        # 3. テンプレート内容取得
        template_tasks = self.template_repo.get_template_tasks(template_id, conn)
        template_subtasks = self.template_repo.get_template_subtasks(template_id, conn)
        template_deps = self.template_repo.get_template_dependencies(template_id, conn)

        # 4. 件数サマリ計算
        task_count = len(template_tasks)
        subtask_count = len(template_subtasks)
        dependency_count = len(template_deps)

        # 5. 1階層ツリー生成
        if new_subproject_name is None:
            new_subproject_name = template.name

        task_names = []
        # template_task_idごとのSubTask数をカウント
        subtask_counts = {}
        for ts in template_subtasks:
            subtask_counts[ts.template_task_id] = (
                subtask_counts.get(ts.template_task_id, 0) + 1
            )

        for tt in template_tasks:
            st_count = subtask_counts.get(tt.id, 0)
            if st_count > 0:
                task_names.append(f"{tt.name} (SubTasks: {st_count})")
            else:
                task_names.append(tt.name)

        return {
            "subproject_name": new_subproject_name,
            "task_count": task_count,
            "subtask_count": subtask_count,
            "dependency_count": dependency_count,
            "task_names": task_names,
        }

    # ============================================================
    # 内部メソッド (P5-06)
    # ============================================================

    def _detect_external_dependencies(
        self,
        subproject_id: int,
        conn: sqlite3.Connection,
    ) -> list[ExternalDependencyWarning]:
        """外部依存を検出（警告情報として返す）

        SubProject配下のTaskが、SubProject外のTaskに依存している場合を検出。

        Args:
            subproject_id: SubProject ID
            conn: DB接続

        Returns:
            外部依存警告のリスト
        """
        warnings = []

        # SubProject配下のTask一覧取得
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name FROM tasks WHERE subproject_id = ?", (subproject_id,)
        )
        internal_tasks = {row["id"]: row["name"] for row in cursor.fetchall()}

        if not internal_tasks:
            return warnings

        # 各Taskの依存関係をチェック
        for task_id, task_name in internal_tasks.items():
            # 先行Task（このTaskが依存しているTask）
            cursor.execute(
                """
                SELECT t.id, t.name
                FROM tasks t
                JOIN task_dependencies td ON t.id = td.predecessor_id
                WHERE td.successor_id = ?
                """,
                (task_id,),
            )
            for row in cursor.fetchall():
                pred_id = row["id"]
                if pred_id not in internal_tasks:
                    # 外部への依存（outgoing）
                    warnings.append(
                        ExternalDependencyWarning(
                            from_task_id=task_id,
                            to_task_id=pred_id,
                            from_task_name=task_name,
                            to_task_name=row["name"],
                            direction="outgoing",
                        )
                    )

            # 後続Task（このTaskに依存しているTask）
            cursor.execute(
                """
                SELECT t.id, t.name
                FROM tasks t
                JOIN task_dependencies td ON t.id = td.successor_id
                WHERE td.predecessor_id = ?
                """,
                (task_id,),
            )
            for row in cursor.fetchall():
                succ_id = row["id"]
                if succ_id not in internal_tasks:
                    # 外部からの依存（incoming）
                    warnings.append(
                        ExternalDependencyWarning(
                            from_task_id=succ_id,
                            to_task_id=task_id,
                            from_task_name=row["name"],
                            to_task_name=task_name,
                            direction="incoming",
                        )
                    )

        return warnings

    def _get_internal_dependencies(
        self,
        subproject_id: int,
        task_id_to_order: dict[int, int],
        conn: sqlite3.Connection,
    ) -> list[tuple[int, int]]:
        """内部依存関係を取得

        SubProject配下のTask間の依存関係のみを取得。

        Args:
            subproject_id: SubProject ID
            task_id_to_order: Task IDからtask_orderへのマッピング
            conn: DB接続

        Returns:
            (predecessor_order, successor_order) のタプルのリスト
        """
        internal_deps = []

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT td.predecessor_id, td.successor_id
            FROM task_dependencies td
            WHERE td.predecessor_id IN (SELECT id FROM tasks WHERE subproject_id = ?)
              AND td.successor_id IN (SELECT id FROM tasks WHERE subproject_id = ?)
            """,
            (subproject_id, subproject_id),
        )

        for row in cursor.fetchall():
            pred_id = row["predecessor_id"]
            succ_id = row["successor_id"]
            pred_order = task_id_to_order[pred_id]
            succ_order = task_id_to_order[succ_id]
            internal_deps.append((pred_order, succ_order))

        return internal_deps
