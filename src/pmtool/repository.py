"""
CRUD操作リポジトリ

このモジュールはすべてのエンティティ(Project, SubProject, Task, SubTask)に対する
データベースCRUD操作を提供します。
"""

import sqlite3
from datetime import datetime
from typing import Optional

from .database import Database
from .exceptions import ConstraintViolationError, DeletionError, ValidationError
from .models import Project, SubProject, Task, SubTask
from .validators import (
    validate_description,
    validate_name,
    validate_order_index,
    validate_status,
)


def _now() -> str:
    """
    現在のUTCタイムスタンプをISO 8601形式で返す

    Returns:
        str: ISO 8601形式のUTCタイムスタンプ
    """
    return datetime.utcnow().isoformat()


class ProjectRepository:
    """
    Projectエンティティのリポジトリ

    Projectの作成、読み取り、更新、削除操作を提供します。
    """

    def __init__(self, db: Database):
        """
        Args:
            db: Database インスタンス
        """
        self.db = db

    def create(self, name: str, description: Optional[str] = None) -> Project:
        """
        新しいProjectを作成

        Args:
            name: プロジェクト名 (グローバルで一意)
            description: プロジェクトの説明 (オプション)

        Returns:
            Project: 作成されたProject

        Raises:
            ValidationError: 入力値が不正な場合
            ConstraintViolationError: 名前が既に存在する場合
        """
        # バリデーション
        name = validate_name(name)
        description = validate_description(description)

        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # 名前の重複チェック
            cursor.execute("SELECT id FROM projects WHERE name = ?", (name,))
            if cursor.fetchone():
                raise ConstraintViolationError(f"プロジェクト名 '{name}' は既に存在します")

            # 次の order_index を計算
            cursor.execute("SELECT COALESCE(MAX(order_index), -1) + 1 FROM projects")
            next_order_index = cursor.fetchone()[0]

            # INSERT
            now = _now()
            cursor.execute(
                """
                INSERT INTO projects (name, description, order_index, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, description, next_order_index, now, now),
            )
            project_id = cursor.lastrowid
            conn.commit()

            return Project(
                id=project_id,
                name=name,
                description=description,
                order_index=next_order_index,
                created_at=now,
                updated_at=now,
            )

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"プロジェクトの作成に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def get_by_id(self, project_id: int) -> Optional[Project]:
        """
        IDでProjectを取得

        Args:
            project_id: プロジェクトID

        Returns:
            Project | None: 見つかったProject、または None
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return Project(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            order_index=row["order_index"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_all(self) -> list[Project]:
        """
        すべてのProjectを取得

        Returns:
            list[Project]: order_index順に並べられたProject一覧
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY order_index")
        rows = cursor.fetchall()

        return [
            Project(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                order_index=row["order_index"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def update(
        self,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Project:
        """
        Projectを更新

        Args:
            project_id: プロジェクトID
            name: 新しい名前 (Noneの場合は変更しない)
            description: 新しい説明 (Noneの場合は変更しない)

        Returns:
            Project: 更新されたProject

        Raises:
            ValidationError: 入力値が不正な場合
            ConstraintViolationError: 名前が既に存在する場合、またはプロジェクトが存在しない場合
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # プロジェクトの存在確認
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            if not row:
                raise ConstraintViolationError(f"プロジェクトID {project_id} は存在しません")

            # 更新する値を決定
            new_name = validate_name(name) if name is not None else row["name"]
            new_description = (
                validate_description(description)
                if description is not None
                else row["description"]
            )

            # 名前が変更される場合、重複チェック
            if new_name != row["name"]:
                cursor.execute(
                    "SELECT id FROM projects WHERE name = ? AND id != ?",
                    (new_name, project_id),
                )
                if cursor.fetchone():
                    raise ConstraintViolationError(f"プロジェクト名 '{new_name}' は既に存在します")

            # UPDATE
            now = _now()
            cursor.execute(
                """
                UPDATE projects
                SET name = ?, description = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_name, new_description, now, project_id),
            )
            conn.commit()

            return Project(
                id=project_id,
                name=new_name,
                description=new_description,
                order_index=row["order_index"],
                created_at=row["created_at"],
                updated_at=now,
            )

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"プロジェクトの更新に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def delete(self, project_id: int) -> None:
        """
        Projectを削除

        Args:
            project_id: プロジェクトID

        Raises:
            ConstraintViolationError: 子SubProjectが存在する場合、またはプロジェクトが存在しない場合
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # プロジェクトの存在確認
            cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
            if not cursor.fetchone():
                raise ConstraintViolationError(f"プロジェクトID {project_id} は存在しません")

            # 子SubProjectの存在確認
            cursor.execute(
                "SELECT COUNT(*) FROM subprojects WHERE project_id = ?", (project_id,)
            )
            child_count = cursor.fetchone()[0]
            if child_count > 0:
                raise ConstraintViolationError(
                    f"プロジェクトID {project_id} には {child_count} 個の子SubProjectが存在するため削除できません"
                )

            # DELETE (FK RESTRICTで保護されているが、念のため明示的にチェック済み)
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"プロジェクトの削除に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def cascade_delete(
        self, project_id: int, dry_run: bool = False, conn: Optional[sqlite3.Connection] = None
    ) -> dict:
        """
        Projectを子要素も含めて連鎖削除（Phase 4 実装）

        子SubProject、Task、SubTaskを再帰的に削除します。
        依存関係はON DELETE CASCADEにより自動削除されます。

        Args:
            project_id: プロジェクトID
            dry_run: True の場合、削除対象を収集するのみで実際には削除しない
            conn: 既存のコネクション（トランザクション共有用）

        Returns:
            dict: 削除結果 {
                'projects': 削除されるProject数,
                'subprojects': 削除されるSubProject数,
                'tasks': 削除されるTask数,
                'subtasks': 削除されるSubTask数,
                'task_dependencies': 削除されるTask依存関係数,
                'subtask_dependencies': 削除されるSubTask依存関係数
            }

        Raises:
            ConstraintViolationError: Projectが存在しない場合
        """
        own_conn = False
        if conn is None:
            conn = self.db.connect()
            own_conn = True

        try:
            cursor = conn.cursor()

            # Projectの存在確認
            cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
            if not cursor.fetchone():
                raise ConstraintViolationError(f"プロジェクトID {project_id} は存在しません")

            # 削除対象の収集
            # SubProject配下のTaskを取得
            cursor.execute(
                """
                SELECT t.id FROM tasks t
                INNER JOIN subprojects sp ON t.subproject_id = sp.id
                WHERE sp.project_id = ?
                """,
                (project_id,),
            )
            task_ids_from_subprojects = [row[0] for row in cursor.fetchall()]

            # Project直下のTaskを取得
            cursor.execute(
                "SELECT id FROM tasks WHERE project_id = ? AND subproject_id IS NULL",
                (project_id,),
            )
            task_ids_direct = [row[0] for row in cursor.fetchall()]

            all_task_ids = task_ids_from_subprojects + task_ids_direct

            # SubTaskを取得
            if all_task_ids:
                placeholders = ",".join("?" * len(all_task_ids))
                cursor.execute(
                    f"SELECT id FROM subtasks WHERE task_id IN ({placeholders})",
                    all_task_ids,
                )
                subtask_ids = [row[0] for row in cursor.fetchall()]
            else:
                subtask_ids = []

            # SubProjectを取得
            cursor.execute("SELECT id FROM subprojects WHERE project_id = ?", (project_id,))
            subproject_ids = [row[0] for row in cursor.fetchall()]

            # 依存関係数を取得
            if all_task_ids:
                placeholders = ",".join("?" * len(all_task_ids))
                cursor.execute(
                    f"""
                    SELECT COUNT(*) FROM task_dependencies
                    WHERE predecessor_id IN ({placeholders}) OR successor_id IN ({placeholders})
                    """,
                    all_task_ids + all_task_ids,
                )
                task_dep_count = cursor.fetchone()[0]
            else:
                task_dep_count = 0

            if subtask_ids:
                placeholders = ",".join("?" * len(subtask_ids))
                cursor.execute(
                    f"""
                    SELECT COUNT(*) FROM subtask_dependencies
                    WHERE predecessor_id IN ({placeholders}) OR successor_id IN ({placeholders})
                    """,
                    subtask_ids + subtask_ids,
                )
                subtask_dep_count = cursor.fetchone()[0]
            else:
                subtask_dep_count = 0

            result = {
                "projects": 1,
                "subprojects": len(subproject_ids),
                "tasks": len(all_task_ids),
                "subtasks": len(subtask_ids),
                "task_dependencies": task_dep_count,
                "subtask_dependencies": subtask_dep_count,
            }

            if dry_run:
                # dry-runモード: rollback して結果を返す
                if own_conn:
                    conn.rollback()
                return result

            # 実削除: 子→親の順で削除
            # SubTask削除（依存関係は ON DELETE CASCADE で自動削除）
            if subtask_ids:
                placeholders = ",".join("?" * len(subtask_ids))
                cursor.execute(f"DELETE FROM subtasks WHERE id IN ({placeholders})", subtask_ids)

            # Task削除（依存関係は ON DELETE CASCADE で自動削除）
            if all_task_ids:
                placeholders = ",".join("?" * len(all_task_ids))
                cursor.execute(f"DELETE FROM tasks WHERE id IN ({placeholders})", all_task_ids)

            # SubProject削除
            if subproject_ids:
                placeholders = ",".join("?" * len(subproject_ids))
                cursor.execute(f"DELETE FROM subprojects WHERE id IN ({placeholders})", subproject_ids)

            # Project削除
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))

            if own_conn:
                conn.commit()

            return result

        except Exception as e:
            if own_conn:
                conn.rollback()
            raise


class SubProjectRepository:
    """
    SubProjectエンティティのリポジトリ

    SubProjectの作成、読み取り、更新、削除操作を提供します。
    """

    def __init__(self, db: Database):
        """
        Args:
            db: Database インスタンス
        """
        self.db = db

    def create(
        self,
        project_id: int,
        name: str,
        parent_subproject_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> SubProject:
        """
        新しいSubProjectを作成

        Args:
            project_id: 親プロジェクトID
            name: SubProject名 (親コンテキスト内で一意)
            parent_subproject_id: 親SubProjectID (MVP では常に None)
            description: 説明 (オプション)

        Returns:
            SubProject: 作成されたSubProject

        Raises:
            ValidationError: 入力値が不正な場合
            ConstraintViolationError: 親が存在しない、または名前が重複している場合
        """
        # バリデーション
        name = validate_name(name)
        description = validate_description(description)

        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # 親プロジェクトの存在確認
            cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
            if not cursor.fetchone():
                raise ConstraintViolationError(f"プロジェクトID {project_id} は存在しません")

            # 親SubProjectの存在確認 (指定されている場合)
            if parent_subproject_id is not None:
                cursor.execute(
                    "SELECT id FROM subprojects WHERE id = ?", (parent_subproject_id,)
                )
                if not cursor.fetchone():
                    raise ConstraintViolationError(
                        f"親SubProjectID {parent_subproject_id} は存在しません"
                    )

            # 名前の重複チェック (部分UNIQUEインデックスが保護)
            if parent_subproject_id is None:
                cursor.execute(
                    """
                    SELECT id FROM subprojects
                    WHERE project_id = ? AND name = ? AND parent_subproject_id IS NULL
                    """,
                    (project_id, name),
                )
            else:
                cursor.execute(
                    """
                    SELECT id FROM subprojects
                    WHERE project_id = ? AND parent_subproject_id = ? AND name = ?
                    """,
                    (project_id, parent_subproject_id, name),
                )

            if cursor.fetchone():
                raise ConstraintViolationError(f"SubProject名 '{name}' は既に存在します")

            # 次の order_index を計算
            cursor.execute(
                """
                SELECT COALESCE(MAX(order_index), -1) + 1
                FROM subprojects
                WHERE project_id = ? AND parent_subproject_id IS ?
                """,
                (project_id, parent_subproject_id),
            )
            next_order_index = cursor.fetchone()[0]

            # INSERT
            now = _now()
            cursor.execute(
                """
                INSERT INTO subprojects
                (project_id, parent_subproject_id, name, description, order_index, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    parent_subproject_id,
                    name,
                    description,
                    next_order_index,
                    now,
                    now,
                ),
            )
            subproject_id = cursor.lastrowid

            # 親プロジェクトの updated_at を更新
            cursor.execute(
                "UPDATE projects SET updated_at = ? WHERE id = ?", (now, project_id)
            )

            conn.commit()

            return SubProject(
                id=subproject_id,
                project_id=project_id,
                parent_subproject_id=parent_subproject_id,
                name=name,
                description=description,
                order_index=next_order_index,
                created_at=now,
                updated_at=now,
            )

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"SubProjectの作成に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def get_by_id(self, subproject_id: int) -> Optional[SubProject]:
        """
        IDでSubProjectを取得

        Args:
            subproject_id: SubProjectID

        Returns:
            SubProject | None: 見つかったSubProject、または None
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM subprojects WHERE id = ?", (subproject_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return SubProject(
            id=row["id"],
            project_id=row["project_id"],
            parent_subproject_id=row["parent_subproject_id"],
            name=row["name"],
            description=row["description"],
            order_index=row["order_index"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_by_project(self, project_id: int) -> list[SubProject]:
        """
        プロジェクトIDですべてのSubProjectを取得

        Args:
            project_id: プロジェクトID

        Returns:
            list[SubProject]: order_index順に並べられたSubProject一覧
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM subprojects WHERE project_id = ? ORDER BY order_index",
            (project_id,),
        )
        rows = cursor.fetchall()

        return [
            SubProject(
                id=row["id"],
                project_id=row["project_id"],
                parent_subproject_id=row["parent_subproject_id"],
                name=row["name"],
                description=row["description"],
                order_index=row["order_index"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def update(
        self,
        subproject_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> SubProject:
        """
        SubProjectを更新

        Args:
            subproject_id: SubProjectID
            name: 新しい名前 (Noneの場合は変更しない)
            description: 新しい説明 (Noneの場合は変更しない)

        Returns:
            SubProject: 更新されたSubProject

        Raises:
            ValidationError: 入力値が不正な場合
            ConstraintViolationError: 名前が既に存在する場合、またはSubProjectが存在しない場合
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # SubProjectの存在確認
            cursor.execute("SELECT * FROM subprojects WHERE id = ?", (subproject_id,))
            row = cursor.fetchone()
            if not row:
                raise ConstraintViolationError(f"SubProjectID {subproject_id} は存在しません")

            # 更新する値を決定
            new_name = validate_name(name) if name is not None else row["name"]
            new_description = (
                validate_description(description)
                if description is not None
                else row["description"]
            )

            # 名前が変更される場合、重複チェック
            if new_name != row["name"]:
                if row["parent_subproject_id"] is None:
                    cursor.execute(
                        """
                        SELECT id FROM subprojects
                        WHERE project_id = ? AND name = ? AND parent_subproject_id IS NULL AND id != ?
                        """,
                        (row["project_id"], new_name, subproject_id),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id FROM subprojects
                        WHERE project_id = ? AND parent_subproject_id = ? AND name = ? AND id != ?
                        """,
                        (
                            row["project_id"],
                            row["parent_subproject_id"],
                            new_name,
                            subproject_id,
                        ),
                    )

                if cursor.fetchone():
                    raise ConstraintViolationError(f"SubProject名 '{new_name}' は既に存在します")

            # UPDATE
            now = _now()
            cursor.execute(
                """
                UPDATE subprojects
                SET name = ?, description = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_name, new_description, now, subproject_id),
            )

            # 親プロジェクトの updated_at を更新
            cursor.execute(
                "UPDATE projects SET updated_at = ? WHERE id = ?",
                (now, row["project_id"]),
            )

            conn.commit()

            return SubProject(
                id=subproject_id,
                project_id=row["project_id"],
                parent_subproject_id=row["parent_subproject_id"],
                name=new_name,
                description=new_description,
                order_index=row["order_index"],
                created_at=row["created_at"],
                updated_at=now,
            )

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"SubProjectの更新に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def delete(self, subproject_id: int) -> None:
        """
        SubProjectを削除

        Args:
            subproject_id: SubProjectID

        Raises:
            ConstraintViolationError: 子Taskが存在する場合、またはSubProjectが存在しない場合
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # SubProjectの存在確認
            cursor.execute("SELECT * FROM subprojects WHERE id = ?", (subproject_id,))
            row = cursor.fetchone()
            if not row:
                raise ConstraintViolationError(f"SubProjectID {subproject_id} は存在しません")

            # 子Taskの存在確認
            cursor.execute(
                "SELECT COUNT(*) FROM tasks WHERE subproject_id = ?", (subproject_id,)
            )
            child_count = cursor.fetchone()[0]
            if child_count > 0:
                raise ConstraintViolationError(
                    f"SubProjectID {subproject_id} には {child_count} 個の子Taskが存在するため削除できません"
                )

            # DELETE
            cursor.execute("DELETE FROM subprojects WHERE id = ?", (subproject_id,))

            # 親プロジェクトの updated_at を更新
            now = _now()
            cursor.execute(
                "UPDATE projects SET updated_at = ? WHERE id = ?",
                (now, row["project_id"]),
            )

            conn.commit()

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"SubProjectの削除に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def cascade_delete(
        self, subproject_id: int, dry_run: bool = False, conn: Optional[sqlite3.Connection] = None
    ) -> dict:
        """
        SubProjectを子要素も含めて連鎖削除（Phase 4 実装）

        子Task、SubTaskを再帰的に削除します。
        依存関係はON DELETE CASCADEにより自動削除されます。

        Args:
            subproject_id: SubProjectID
            dry_run: True の場合、削除対象を収集するのみで実際には削除しない
            conn: 既存のコネクション（トランザクション共有用）

        Returns:
            dict: 削除結果 {
                'subprojects': 削除されるSubProject数,
                'tasks': 削除されるTask数,
                'subtasks': 削除されるSubTask数,
                'task_dependencies': 削除されるTask依存関係数,
                'subtask_dependencies': 削除されるSubTask依存関係数
            }

        Raises:
            ConstraintViolationError: SubProjectが存在しない場合
        """
        own_conn = False
        if conn is None:
            conn = self.db.connect()
            own_conn = True

        try:
            cursor = conn.cursor()

            # SubProjectの存在確認
            cursor.execute("SELECT project_id FROM subprojects WHERE id = ?", (subproject_id,))
            row = cursor.fetchone()
            if not row:
                raise ConstraintViolationError(f"SubProjectID {subproject_id} は存在しません")

            project_id = row[0]

            # 削除対象の収集
            # Taskを取得
            cursor.execute("SELECT id FROM tasks WHERE subproject_id = ?", (subproject_id,))
            task_ids = [row[0] for row in cursor.fetchall()]

            # SubTaskを取得
            if task_ids:
                placeholders = ",".join("?" * len(task_ids))
                cursor.execute(
                    f"SELECT id FROM subtasks WHERE task_id IN ({placeholders})",
                    task_ids,
                )
                subtask_ids = [row[0] for row in cursor.fetchall()]
            else:
                subtask_ids = []

            # 依存関係数を取得
            if task_ids:
                placeholders = ",".join("?" * len(task_ids))
                cursor.execute(
                    f"""
                    SELECT COUNT(*) FROM task_dependencies
                    WHERE predecessor_id IN ({placeholders}) OR successor_id IN ({placeholders})
                    """,
                    task_ids + task_ids,
                )
                task_dep_count = cursor.fetchone()[0]
            else:
                task_dep_count = 0

            if subtask_ids:
                placeholders = ",".join("?" * len(subtask_ids))
                cursor.execute(
                    f"""
                    SELECT COUNT(*) FROM subtask_dependencies
                    WHERE predecessor_id IN ({placeholders}) OR successor_id IN ({placeholders})
                    """,
                    subtask_ids + subtask_ids,
                )
                subtask_dep_count = cursor.fetchone()[0]
            else:
                subtask_dep_count = 0

            result = {
                "subprojects": 1,
                "tasks": len(task_ids),
                "subtasks": len(subtask_ids),
                "task_dependencies": task_dep_count,
                "subtask_dependencies": subtask_dep_count,
            }

            if dry_run:
                # dry-runモード: rollback して結果を返す
                if own_conn:
                    conn.rollback()
                return result

            # 実削除: 子→親の順で削除
            # SubTask削除（依存関係は ON DELETE CASCADE で自動削除）
            if subtask_ids:
                placeholders = ",".join("?" * len(subtask_ids))
                cursor.execute(f"DELETE FROM subtasks WHERE id IN ({placeholders})", subtask_ids)

            # Task削除（依存関係は ON DELETE CASCADE で自動削除）
            if task_ids:
                placeholders = ",".join("?" * len(task_ids))
                cursor.execute(f"DELETE FROM tasks WHERE id IN ({placeholders})", task_ids)

            # SubProject削除
            cursor.execute("DELETE FROM subprojects WHERE id = ?", (subproject_id,))

            # 親プロジェクトの updated_at を更新
            now = _now()
            cursor.execute("UPDATE projects SET updated_at = ? WHERE id = ?", (now, project_id))

            if own_conn:
                conn.commit()

            return result

        except Exception as e:
            if own_conn:
                conn.rollback()
            raise


class TaskRepository:
    """
    Taskエンティティのリポジトリ

    Taskの作成、読み取り、更新、削除操作を提供します。
    """

    def __init__(self, db: Database):
        """
        Args:
            db: Database インスタンス
        """
        self.db = db

    def create(
        self,
        project_id: int,
        name: str,
        subproject_id: Optional[int] = None,
        description: Optional[str] = None,
        status: str = "UNSET",
    ) -> Task:
        """
        新しいTaskを作成

        Args:
            project_id: 親プロジェクトID
            name: Task名 (親コンテキスト内で一意)
            subproject_id: 親SubProjectID (None の場合はプロジェクト直下)
            description: 説明 (オプション)
            status: ステータス (デフォルト: UNSET)

        Returns:
            Task: 作成されたTask

        Raises:
            ValidationError: 入力値が不正な場合
            ConstraintViolationError: 親が存在しない、または名前が重複している場合
        """
        # バリデーション
        name = validate_name(name)
        description = validate_description(description)
        status = validate_status(status)

        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # 親プロジェクトの存在確認
            cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
            if not cursor.fetchone():
                raise ConstraintViolationError(f"プロジェクトID {project_id} は存在しません")

            # 親SubProjectの存在確認 (指定されている場合)
            if subproject_id is not None:
                cursor.execute(
                    "SELECT id FROM subprojects WHERE id = ?", (subproject_id,)
                )
                if not cursor.fetchone():
                    raise ConstraintViolationError(
                        f"SubProjectID {subproject_id} は存在しません"
                    )

            # 名前の重複チェック (部分UNIQUEインデックスが保護)
            if subproject_id is None:
                cursor.execute(
                    """
                    SELECT id FROM tasks
                    WHERE project_id = ? AND name = ? AND subproject_id IS NULL
                    """,
                    (project_id, name),
                )
            else:
                cursor.execute(
                    """
                    SELECT id FROM tasks
                    WHERE project_id = ? AND subproject_id = ? AND name = ?
                    """,
                    (project_id, subproject_id, name),
                )

            if cursor.fetchone():
                raise ConstraintViolationError(f"Task名 '{name}' は既に存在します")

            # 次の order_index を計算
            cursor.execute(
                """
                SELECT COALESCE(MAX(order_index), -1) + 1
                FROM tasks
                WHERE project_id = ? AND subproject_id IS ?
                """,
                (project_id, subproject_id),
            )
            next_order_index = cursor.fetchone()[0]

            # INSERT
            now = _now()
            cursor.execute(
                """
                INSERT INTO tasks
                (project_id, subproject_id, name, description, status, order_index, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    subproject_id,
                    name,
                    description,
                    status,
                    next_order_index,
                    now,
                    now,
                ),
            )
            task_id = cursor.lastrowid

            # 親の updated_at を更新
            if subproject_id is not None:
                cursor.execute(
                    "UPDATE subprojects SET updated_at = ? WHERE id = ?",
                    (now, subproject_id),
                )
            else:
                cursor.execute(
                    "UPDATE projects SET updated_at = ? WHERE id = ?", (now, project_id)
                )

            conn.commit()

            return Task(
                id=task_id,
                project_id=project_id,
                subproject_id=subproject_id,
                name=name,
                description=description,
                status=status,
                order_index=next_order_index,
                created_at=now,
                updated_at=now,
            )

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"Taskの作成に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def get_by_id(self, task_id: int) -> Optional[Task]:
        """
        IDでTaskを取得

        Args:
            task_id: TaskID

        Returns:
            Task | None: 見つかったTask、または None
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return Task(
            id=row["id"],
            project_id=row["project_id"],
            subproject_id=row["subproject_id"],
            name=row["name"],
            description=row["description"],
            status=row["status"],
            order_index=row["order_index"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_by_parent(
        self, project_id: int, subproject_id: Optional[int] = None
    ) -> list[Task]:
        """
        親IDですべてのTaskを取得

        Args:
            project_id: プロジェクトID
            subproject_id: SubProjectID (Noneの場合はプロジェクト直下)

        Returns:
            list[Task]: order_index順に並べられたTask一覧
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        if subproject_id is None:
            cursor.execute(
                """
                SELECT * FROM tasks
                WHERE project_id = ? AND subproject_id IS NULL
                ORDER BY order_index
                """,
                (project_id,),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM tasks
                WHERE project_id = ? AND subproject_id = ?
                ORDER BY order_index
                """,
                (project_id, subproject_id),
            )

        rows = cursor.fetchall()

        return [
            Task(
                id=row["id"],
                project_id=row["project_id"],
                subproject_id=row["subproject_id"],
                name=row["name"],
                description=row["description"],
                status=row["status"],
                order_index=row["order_index"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def get_by_status(self, status: str) -> list[Task]:
        """
        ステータスでTaskを取得

        Args:
            status: ステータス

        Returns:
            list[Task]: 指定されたステータスのTask一覧
        """
        status = validate_status(status)

        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tasks WHERE status = ? ORDER BY order_index", (status,)
        )
        rows = cursor.fetchall()

        return [
            Task(
                id=row["id"],
                project_id=row["project_id"],
                subproject_id=row["subproject_id"],
                name=row["name"],
                description=row["description"],
                status=row["status"],
                order_index=row["order_index"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def update(
        self,
        task_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Task:
        """
        Taskを更新

        Args:
            task_id: TaskID
            name: 新しい名前 (Noneの場合は変更しない)
            description: 新しい説明 (Noneの場合は変更しない)

        Returns:
            Task: 更新されたTask

        Raises:
            ValidationError: 入力値が不正な場合
            ConstraintViolationError: 名前が既に存在する場合、またはTaskが存在しない場合
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # Taskの存在確認
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                raise ConstraintViolationError(f"TaskID {task_id} は存在しません")

            # 更新する値を決定
            new_name = validate_name(name) if name is not None else row["name"]
            new_description = (
                validate_description(description)
                if description is not None
                else row["description"]
            )

            # 名前が変更される場合、重複チェック
            if new_name != row["name"]:
                if row["subproject_id"] is None:
                    cursor.execute(
                        """
                        SELECT id FROM tasks
                        WHERE project_id = ? AND name = ? AND subproject_id IS NULL AND id != ?
                        """,
                        (row["project_id"], new_name, task_id),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id FROM tasks
                        WHERE project_id = ? AND subproject_id = ? AND name = ? AND id != ?
                        """,
                        (row["project_id"], row["subproject_id"], new_name, task_id),
                    )

                if cursor.fetchone():
                    raise ConstraintViolationError(f"Task名 '{new_name}' は既に存在します")

            # UPDATE
            now = _now()
            cursor.execute(
                """
                UPDATE tasks
                SET name = ?, description = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_name, new_description, now, task_id),
            )

            # 親の updated_at を更新
            if row["subproject_id"] is not None:
                cursor.execute(
                    "UPDATE subprojects SET updated_at = ? WHERE id = ?",
                    (now, row["subproject_id"]),
                )
            else:
                cursor.execute(
                    "UPDATE projects SET updated_at = ? WHERE id = ?",
                    (now, row["project_id"]),
                )

            conn.commit()

            return Task(
                id=task_id,
                project_id=row["project_id"],
                subproject_id=row["subproject_id"],
                name=new_name,
                description=new_description,
                status=row["status"],
                order_index=row["order_index"],
                created_at=row["created_at"],
                updated_at=now,
            )

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"Taskの更新に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def delete(self, task_id: int) -> None:
        """
        Taskを削除

        Args:
            task_id: TaskID

        Raises:
            ConstraintViolationError: 子SubTaskが存在する場合、またはTaskが存在しない場合
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # Taskの存在確認
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                raise ConstraintViolationError(f"TaskID {task_id} は存在しません")

            # 子SubTaskの存在確認
            cursor.execute(
                "SELECT COUNT(*) FROM subtasks WHERE task_id = ?", (task_id,)
            )
            child_count = cursor.fetchone()[0]
            if child_count > 0:
                raise ConstraintViolationError(
                    f"TaskID {task_id} には {child_count} 個の子SubTaskが存在するため削除できません"
                )

            # DELETE
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

            # 親の updated_at を更新
            now = _now()
            if row["subproject_id"] is not None:
                cursor.execute(
                    "UPDATE subprojects SET updated_at = ? WHERE id = ?",
                    (now, row["subproject_id"]),
                )
            else:
                cursor.execute(
                    "UPDATE projects SET updated_at = ? WHERE id = ?",
                    (now, row["project_id"]),
                )

            conn.commit()

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"Taskの削除に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def delete_with_bridge(self, task_id: int) -> list[tuple[int, int]]:
        """
        依存関係を橋渡ししてからTaskを削除 (D6)

        このメソッドは、Taskの先行・後続依存関係を橋渡ししてから削除します。
        子SubTaskが存在する場合はエラーになります。

        Args:
            task_id: TaskID

        Returns:
            list[tuple[int, int]]: 橋渡しされた依存関係のリスト [(pred_id, succ_id), ...]

        Raises:
            DeletionError: 子SubTaskが存在する場合
            ConstraintViolationError: Taskが存在しない場合
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # Taskの存在確認
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                raise ConstraintViolationError(f"TaskID {task_id} は存在しません")

            # 子SubTaskの存在確認
            cursor.execute(
                "SELECT COUNT(*) FROM subtasks WHERE task_id = ?", (task_id,)
            )
            child_count = cursor.fetchone()[0]
            if child_count > 0:
                raise DeletionError(
                    f"TaskID {task_id} には {child_count} 個の子SubTaskが存在するため削除できません"
                )

            # 依存関係の橋渡しを実行 (DependencyManagerを使用)
            # 注: 循環インポートを避けるため、ここで遅延インポート
            from .dependencies import DependencyManager

            dep_manager = DependencyManager(self.db)
            # 同一トランザクション内で橋渡しを実行
            bridged = dep_manager.bridge_dependencies(task_id, "task", conn=conn)

            # DELETE (依存関係はCASCADEで自動削除)
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

            # 親の updated_at を更新
            now = _now()
            if row["subproject_id"] is not None:
                cursor.execute(
                    "UPDATE subprojects SET updated_at = ? WHERE id = ?",
                    (now, row["subproject_id"]),
                )
            else:
                cursor.execute(
                    "UPDATE projects SET updated_at = ? WHERE id = ?",
                    (now, row["project_id"]),
                )

            conn.commit()
            return bridged

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"Taskの削除に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def cascade_delete(
        self, task_id: int, dry_run: bool = False, conn: Optional[sqlite3.Connection] = None
    ) -> dict:
        """
        Taskを子SubTaskも含めて連鎖削除（Phase 4 実装）

        子SubTaskを再帰的に削除します。
        依存関係はON DELETE CASCADEにより自動削除されます。

        Args:
            task_id: TaskID
            dry_run: True の場合、削除対象を収集するのみで実際には削除しない
            conn: 既存のコネクション（トランザクション共有用）

        Returns:
            dict: 削除結果 {
                'tasks': 削除されるTask数,
                'subtasks': 削除されるSubTask数,
                'task_dependencies': 削除されるTask依存関係数,
                'subtask_dependencies': 削除されるSubTask依存関係数
            }

        Raises:
            ConstraintViolationError: Taskが存在しない場合
        """
        own_conn = False
        if conn is None:
            conn = self.db.connect()
            own_conn = True

        try:
            cursor = conn.cursor()

            # Taskの存在確認
            cursor.execute("SELECT project_id, subproject_id FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                raise ConstraintViolationError(f"TaskID {task_id} は存在しません")

            project_id = row[0]
            subproject_id = row[1]

            # 削除対象の収集
            # SubTaskを取得
            cursor.execute("SELECT id FROM subtasks WHERE task_id = ?", (task_id,))
            subtask_ids = [row[0] for row in cursor.fetchall()]

            # 依存関係数を取得
            cursor.execute(
                """
                SELECT COUNT(*) FROM task_dependencies
                WHERE predecessor_id = ? OR successor_id = ?
                """,
                (task_id, task_id),
            )
            task_dep_count = cursor.fetchone()[0]

            if subtask_ids:
                placeholders = ",".join("?" * len(subtask_ids))
                cursor.execute(
                    f"""
                    SELECT COUNT(*) FROM subtask_dependencies
                    WHERE predecessor_id IN ({placeholders}) OR successor_id IN ({placeholders})
                    """,
                    subtask_ids + subtask_ids,
                )
                subtask_dep_count = cursor.fetchone()[0]
            else:
                subtask_dep_count = 0

            result = {
                "tasks": 1,
                "subtasks": len(subtask_ids),
                "task_dependencies": task_dep_count,
                "subtask_dependencies": subtask_dep_count,
            }

            if dry_run:
                # dry-runモード: rollback して結果を返す
                if own_conn:
                    conn.rollback()
                return result

            # 実削除: 子→親の順で削除
            # SubTask削除（依存関係は ON DELETE CASCADE で自動削除）
            if subtask_ids:
                placeholders = ",".join("?" * len(subtask_ids))
                cursor.execute(f"DELETE FROM subtasks WHERE id IN ({placeholders})", subtask_ids)

            # Task削除（依存関係は ON DELETE CASCADE で自動削除）
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

            # 親の updated_at を更新
            now = _now()
            if subproject_id is not None:
                cursor.execute("UPDATE subprojects SET updated_at = ? WHERE id = ?", (now, subproject_id))
            else:
                cursor.execute("UPDATE projects SET updated_at = ? WHERE id = ?", (now, project_id))

            if own_conn:
                conn.commit()

            return result

        except Exception as e:
            if own_conn:
                conn.rollback()
            raise


class SubTaskRepository:
    """
    SubTaskエンティティのリポジトリ

    SubTaskの作成、読み取り、更新、削除操作を提供します。
    """

    def __init__(self, db: Database):
        """
        Args:
            db: Database インスタンス
        """
        self.db = db

    def create(
        self,
        task_id: int,
        name: str,
        description: Optional[str] = None,
        status: str = "UNSET",
    ) -> SubTask:
        """
        新しいSubTaskを作成

        Args:
            task_id: 親TaskID
            name: SubTask名 (Task内で一意)
            description: 説明 (オプション)
            status: ステータス (デフォルト: UNSET)

        Returns:
            SubTask: 作成されたSubTask

        Raises:
            ValidationError: 入力値が不正な場合
            ConstraintViolationError: 親Taskが存在しない、または名前が重複している場合
        """
        # バリデーション
        name = validate_name(name)
        description = validate_description(description)
        status = validate_status(status)

        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # 親Taskの存在確認
            cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
            if not cursor.fetchone():
                raise ConstraintViolationError(f"TaskID {task_id} は存在しません")

            # 名前の重複チェック (UNIQUEインデックスが保護)
            cursor.execute(
                "SELECT id FROM subtasks WHERE task_id = ? AND name = ?",
                (task_id, name),
            )
            if cursor.fetchone():
                raise ConstraintViolationError(f"SubTask名 '{name}' は既に存在します")

            # 次の order_index を計算
            cursor.execute(
                "SELECT COALESCE(MAX(order_index), -1) + 1 FROM subtasks WHERE task_id = ?",
                (task_id,),
            )
            next_order_index = cursor.fetchone()[0]

            # INSERT
            now = _now()
            cursor.execute(
                """
                INSERT INTO subtasks
                (task_id, name, description, status, order_index, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (task_id, name, description, status, next_order_index, now, now),
            )
            subtask_id = cursor.lastrowid

            # 親Taskの updated_at を更新
            cursor.execute("UPDATE tasks SET updated_at = ? WHERE id = ?", (now, task_id))

            conn.commit()

            return SubTask(
                id=subtask_id,
                task_id=task_id,
                name=name,
                description=description,
                status=status,
                order_index=next_order_index,
                created_at=now,
                updated_at=now,
            )

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"SubTaskの作成に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def get_by_id(self, subtask_id: int) -> Optional[SubTask]:
        """
        IDでSubTaskを取得

        Args:
            subtask_id: SubTaskID

        Returns:
            SubTask | None: 見つかったSubTask、または None
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM subtasks WHERE id = ?", (subtask_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return SubTask(
            id=row["id"],
            task_id=row["task_id"],
            name=row["name"],
            description=row["description"],
            status=row["status"],
            order_index=row["order_index"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_by_task(self, task_id: int) -> list[SubTask]:
        """
        TaskIDですべてのSubTaskを取得

        Args:
            task_id: TaskID

        Returns:
            list[SubTask]: order_index順に並べられたSubTask一覧
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM subtasks WHERE task_id = ? ORDER BY order_index",
            (task_id,),
        )
        rows = cursor.fetchall()

        return [
            SubTask(
                id=row["id"],
                task_id=row["task_id"],
                name=row["name"],
                description=row["description"],
                status=row["status"],
                order_index=row["order_index"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def update(
        self,
        subtask_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> SubTask:
        """
        SubTaskを更新

        Args:
            subtask_id: SubTaskID
            name: 新しい名前 (Noneの場合は変更しない)
            description: 新しい説明 (Noneの場合は変更しない)

        Returns:
            SubTask: 更新されたSubTask

        Raises:
            ValidationError: 入力値が不正な場合
            ConstraintViolationError: 名前が既に存在する場合、またはSubTaskが存在しない場合
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # SubTaskの存在確認
            cursor.execute("SELECT * FROM subtasks WHERE id = ?", (subtask_id,))
            row = cursor.fetchone()
            if not row:
                raise ConstraintViolationError(f"SubTaskID {subtask_id} は存在しません")

            # 更新する値を決定
            new_name = validate_name(name) if name is not None else row["name"]
            new_description = (
                validate_description(description)
                if description is not None
                else row["description"]
            )

            # 名前が変更される場合、重複チェック
            if new_name != row["name"]:
                cursor.execute(
                    """
                    SELECT id FROM subtasks
                    WHERE task_id = ? AND name = ? AND id != ?
                    """,
                    (row["task_id"], new_name, subtask_id),
                )
                if cursor.fetchone():
                    raise ConstraintViolationError(f"SubTask名 '{new_name}' は既に存在します")

            # UPDATE
            now = _now()
            cursor.execute(
                """
                UPDATE subtasks
                SET name = ?, description = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_name, new_description, now, subtask_id),
            )

            # 親Taskの updated_at を更新
            cursor.execute(
                "UPDATE tasks SET updated_at = ? WHERE id = ?",
                (now, row["task_id"]),
            )

            conn.commit()

            return SubTask(
                id=subtask_id,
                task_id=row["task_id"],
                name=new_name,
                description=new_description,
                status=row["status"],
                order_index=row["order_index"],
                created_at=row["created_at"],
                updated_at=now,
            )

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"SubTaskの更新に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def delete(self, subtask_id: int) -> None:
        """
        SubTaskを削除

        Args:
            subtask_id: SubTaskID

        Raises:
            ConstraintViolationError: SubTaskが存在しない場合
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # SubTaskの存在確認
            cursor.execute("SELECT * FROM subtasks WHERE id = ?", (subtask_id,))
            row = cursor.fetchone()
            if not row:
                raise ConstraintViolationError(f"SubTaskID {subtask_id} は存在しません")

            # 依存関係の存在確認 (FK CASCADEで自動削除されるが、ここでは警告のみ)
            cursor.execute(
                "SELECT COUNT(*) FROM subtask_dependencies WHERE predecessor_id = ? OR successor_id = ?",
                (subtask_id, subtask_id),
            )
            dep_count = cursor.fetchone()[0]
            # 注: 依存関係は ON DELETE CASCADE で自動削除される

            # DELETE
            cursor.execute("DELETE FROM subtasks WHERE id = ?", (subtask_id,))

            # 親Taskの updated_at を更新
            now = _now()
            cursor.execute(
                "UPDATE tasks SET updated_at = ? WHERE id = ?", (now, row["task_id"])
            )

            conn.commit()

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"SubTaskの削除に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def cascade_delete(
        self, subtask_id: int, dry_run: bool = False, conn: Optional[sqlite3.Connection] = None
    ) -> dict:
        """
        SubTaskを連鎖削除（Phase 4 実装）

        SubTaskには子エンティティがないため、単純な削除と同じ動作になります。
        依存関係はON DELETE CASCADEにより自動削除されます。

        Args:
            subtask_id: SubTaskID
            dry_run: True の場合、削除対象を収集するのみで実際には削除しない
            conn: 既存のコネクション（トランザクション共有用）

        Returns:
            dict: 削除結果 {
                'subtasks': 削除されるSubTask数,
                'subtask_dependencies': 削除されるSubTask依存関係数
            }

        Raises:
            ConstraintViolationError: SubTaskが存在しない場合
        """
        own_conn = False
        if conn is None:
            conn = self.db.connect()
            own_conn = True

        try:
            cursor = conn.cursor()

            # SubTaskの存在確認
            cursor.execute("SELECT task_id FROM subtasks WHERE id = ?", (subtask_id,))
            row = cursor.fetchone()
            if not row:
                raise ConstraintViolationError(f"SubTaskID {subtask_id} は存在しません")

            task_id = row[0]

            # 依存関係数を取得
            cursor.execute(
                """
                SELECT COUNT(*) FROM subtask_dependencies
                WHERE predecessor_id = ? OR successor_id = ?
                """,
                (subtask_id, subtask_id),
            )
            subtask_dep_count = cursor.fetchone()[0]

            result = {
                "subtasks": 1,
                "subtask_dependencies": subtask_dep_count,
            }

            if dry_run:
                # dry-runモード: rollback して結果を返す
                if own_conn:
                    conn.rollback()
                return result

            # 実削除
            # SubTask削除（依存関係は ON DELETE CASCADE で自動削除）
            cursor.execute("DELETE FROM subtasks WHERE id = ?", (subtask_id,))

            # 親Taskの updated_at を更新
            now = _now()
            cursor.execute("UPDATE tasks SET updated_at = ? WHERE id = ?", (now, task_id))

            if own_conn:
                conn.commit()

            return result

        except Exception as e:
            if own_conn:
                conn.rollback()
            raise

    def delete_with_bridge(self, subtask_id: int) -> list[tuple[int, int]]:
        """
        依存関係を橋渡ししてからSubTaskを削除 (D6)

        このメソッドは、SubTaskの先行・後続依存関係を橋渡ししてから削除します。

        Args:
            subtask_id: SubTaskID

        Returns:
            list[tuple[int, int]]: 橋渡しされた依存関係のリスト [(pred_id, succ_id), ...]

        Raises:
            ConstraintViolationError: SubTaskが存在しない場合
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # SubTaskの存在確認
            cursor.execute("SELECT * FROM subtasks WHERE id = ?", (subtask_id,))
            row = cursor.fetchone()
            if not row:
                raise ConstraintViolationError(f"SubTaskID {subtask_id} は存在しません")

            # 依存関係の橋渡しを実行 (DependencyManagerを使用)
            # 注: 循環インポートを避けるため、ここで遅延インポート
            from .dependencies import DependencyManager

            dep_manager = DependencyManager(self.db)
            # 同一トランザクション内で橋渡しを実行
            bridged = dep_manager.bridge_dependencies(subtask_id, "subtask", conn=conn)

            # DELETE (依存関係はCASCADEで自動削除)
            cursor.execute("DELETE FROM subtasks WHERE id = ?", (subtask_id,))

            # 親Taskの updated_at を更新
            now = _now()
            cursor.execute(
                "UPDATE tasks SET updated_at = ? WHERE id = ?", (now, row["task_id"])
            )

            conn.commit()
            return bridged

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"SubTaskの削除に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise
