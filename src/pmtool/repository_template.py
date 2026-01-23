"""
Template機能のRepository層

Phase 5で追加されたテンプレート機能のCRUD操作を提供します。
"""

import sqlite3
from datetime import datetime
from typing import Optional

from .database import Database
from .models import (
    Template,
    TemplateTask,
    TemplateSubTask,
    TemplateDependency,
)


def _now() -> str:
    """現在時刻をISO 8601形式で返す"""
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class TemplateRepository:
    """テンプレート系テーブルのCRUD操作を担当 (Phase 5)"""

    def __init__(self, db: Database):
        self.db = db

    # ============================================================
    # templates テーブル操作
    # ============================================================

    def add_template(
        self,
        name: str,
        description: Optional[str],
        include_tasks: bool,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Template:
        """テンプレートを追加

        name重複時はsqlite3.IntegrityError（UNIQUE制約違反）が発生する。
        呼び出し側でTemplateNameConflictErrorに変換すること。

        Args:
            name: テンプレート名（UNIQUE制約）
            description: テンプレート説明（オプション）
            include_tasks: Task/SubTask/依存関係を含むか
            conn: トランザクション用接続（オプション）

        Returns:
            作成されたTemplateオブジェクト

        Raises:
            sqlite3.IntegrityError: 名前が重複している場合
        """
        own_conn = False
        if conn is None:
            conn = self.db.connect()
            own_conn = True

        try:
            cursor = conn.cursor()
            now = _now()

            cursor.execute(
                """
                INSERT INTO templates (name, description, include_tasks, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, description, 1 if include_tasks else 0, now, now),
            )

            template_id = cursor.lastrowid

            if own_conn:
                conn.commit()

            return Template(
                id=template_id,
                name=name,
                description=description,
                include_tasks=include_tasks,
                created_at=now,
                updated_at=now,
            )

        except Exception as e:
            if own_conn:
                conn.rollback()
            raise

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
        if conn is None:
            conn = self.db.connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, description, include_tasks, created_at, updated_at
            FROM templates
            WHERE id = ?
            """,
            (template_id,),
        )

        row = cursor.fetchone()
        if row is None:
            return None

        return Template(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            include_tasks=bool(row["include_tasks"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

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
        if conn is None:
            conn = self.db.connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, description, include_tasks, created_at, updated_at
            FROM templates
            WHERE name = ?
            """,
            (name,),
        )

        row = cursor.fetchone()
        if row is None:
            return None

        return Template(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            include_tasks=bool(row["include_tasks"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_templates(
        self,
        conn: Optional[sqlite3.Connection] = None,
    ) -> list[Template]:
        """テンプレート一覧を取得

        Args:
            conn: トランザクション用接続（オプション）

        Returns:
            Templateオブジェクトのリスト（created_at降順）
        """
        if conn is None:
            conn = self.db.connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, description, include_tasks, created_at, updated_at
            FROM templates
            ORDER BY created_at DESC
            """
        )

        rows = cursor.fetchall()
        return [
            Template(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                include_tasks=bool(row["include_tasks"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

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
        """
        own_conn = False
        if conn is None:
            conn = self.db.connect()
            own_conn = True

        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))

            if own_conn:
                conn.commit()

        except Exception as e:
            if own_conn:
                conn.rollback()
            raise

    # ============================================================
    # template_tasks テーブル操作
    # ============================================================

    def add_template_task(
        self,
        template_id: int,
        task_order: int,
        name: str,
        description: Optional[str],
        conn: Optional[sqlite3.Connection] = None,
    ) -> TemplateTask:
        """テンプレートTaskを追加

        Args:
            template_id: テンプレートID
            task_order: テンプレート内での順序（0始まり）
            name: Task名
            description: 説明（オプション）
            conn: トランザクション用接続（オプション）

        Returns:
            作成されたTemplateTaskオブジェクト
        """
        own_conn = False
        if conn is None:
            conn = self.db.connect()
            own_conn = True

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO template_tasks (template_id, task_order, name, description)
                VALUES (?, ?, ?, ?)
                """,
                (template_id, task_order, name, description),
            )

            template_task_id = cursor.lastrowid

            if own_conn:
                conn.commit()

            return TemplateTask(
                id=template_task_id,
                template_id=template_id,
                task_order=task_order,
                name=name,
                description=description,
            )

        except Exception as e:
            if own_conn:
                conn.rollback()
            raise

    def get_template_tasks(
        self,
        template_id: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> list[TemplateTask]:
        """テンプレートTask一覧を取得

        Args:
            template_id: テンプレートID
            conn: トランザクション用接続（オプション）

        Returns:
            TemplateTaskオブジェクトのリスト（task_order昇順）
        """
        if conn is None:
            conn = self.db.connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, template_id, task_order, name, description
            FROM template_tasks
            WHERE template_id = ?
            ORDER BY task_order ASC
            """,
            (template_id,),
        )

        rows = cursor.fetchall()
        return [
            TemplateTask(
                id=row["id"],
                template_id=row["template_id"],
                task_order=row["task_order"],
                name=row["name"],
                description=row["description"],
            )
            for row in rows
        ]

    # ============================================================
    # template_subtasks テーブル操作
    # ============================================================

    def add_template_subtask(
        self,
        template_task_id: int,
        subtask_order: int,
        name: str,
        description: Optional[str],
        conn: Optional[sqlite3.Connection] = None,
    ) -> TemplateSubTask:
        """テンプレートSubTaskを追加

        Args:
            template_task_id: 親TemplateTaskID
            subtask_order: Task内での順序（0始まり）
            name: SubTask名
            description: 説明（オプション）
            conn: トランザクション用接続（オプション）

        Returns:
            作成されたTemplateSubTaskオブジェクト
        """
        own_conn = False
        if conn is None:
            conn = self.db.connect()
            own_conn = True

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO template_subtasks (template_task_id, subtask_order, name, description)
                VALUES (?, ?, ?, ?)
                """,
                (template_task_id, subtask_order, name, description),
            )

            template_subtask_id = cursor.lastrowid

            if own_conn:
                conn.commit()

            return TemplateSubTask(
                id=template_subtask_id,
                template_task_id=template_task_id,
                subtask_order=subtask_order,
                name=name,
                description=description,
            )

        except Exception as e:
            if own_conn:
                conn.rollback()
            raise

    def get_template_subtasks(
        self,
        template_id: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> list[TemplateSubTask]:
        """テンプレートSubTask一覧を取得

        Args:
            template_id: テンプレートID
            conn: トランザクション用接続（オプション）

        Returns:
            TemplateSubTaskオブジェクトのリスト（task_order, subtask_order昇順）
        """
        if conn is None:
            conn = self.db.connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ts.id, ts.template_task_id, ts.subtask_order, ts.name, ts.description
            FROM template_subtasks ts
            JOIN template_tasks tt ON ts.template_task_id = tt.id
            WHERE tt.template_id = ?
            ORDER BY tt.task_order ASC, ts.subtask_order ASC
            """,
            (template_id,),
        )

        rows = cursor.fetchall()
        return [
            TemplateSubTask(
                id=row["id"],
                template_task_id=row["template_task_id"],
                subtask_order=row["subtask_order"],
                name=row["name"],
                description=row["description"],
            )
            for row in rows
        ]

    # ============================================================
    # template_dependencies テーブル操作
    # ============================================================

    def add_template_dependency(
        self,
        template_id: int,
        predecessor_order: int,
        successor_order: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> TemplateDependency:
        """テンプレート依存関係を追加

        Args:
            template_id: テンプレートID
            predecessor_order: 先行Taskのtask_order
            successor_order: 後続Taskのtask_order
            conn: トランザクション用接続（オプション）

        Returns:
            作成されたTemplateDependencyオブジェクト
        """
        own_conn = False
        if conn is None:
            conn = self.db.connect()
            own_conn = True

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO template_dependencies (template_id, predecessor_order, successor_order)
                VALUES (?, ?, ?)
                """,
                (template_id, predecessor_order, successor_order),
            )

            template_dep_id = cursor.lastrowid

            if own_conn:
                conn.commit()

            return TemplateDependency(
                id=template_dep_id,
                template_id=template_id,
                predecessor_order=predecessor_order,
                successor_order=successor_order,
            )

        except Exception as e:
            if own_conn:
                conn.rollback()
            raise

    def get_template_dependencies(
        self,
        template_id: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> list[TemplateDependency]:
        """テンプレート依存関係一覧を取得

        Args:
            template_id: テンプレートID
            conn: トランザクション用接続（オプション）

        Returns:
            TemplateDependencyオブジェクトのリスト
        """
        if conn is None:
            conn = self.db.connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, template_id, predecessor_order, successor_order
            FROM template_dependencies
            WHERE template_id = ?
            """,
            (template_id,),
        )

        rows = cursor.fetchall()
        return [
            TemplateDependency(
                id=row["id"],
                template_id=row["template_id"],
                predecessor_order=row["predecessor_order"],
                successor_order=row["successor_order"],
            )
            for row in rows
        ]
