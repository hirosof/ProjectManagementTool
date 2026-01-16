"""
ステータス管理モジュール

このモジュールはTaskとSubTaskのステータス遷移を管理します。
DONE遷移時の前提条件チェック(D3)を含みます。
"""

import sqlite3
from datetime import datetime

from .database import Database
from .dependencies import DependencyManager
from .exceptions import StatusTransitionError
from .models import SubTask, Task
from .repository import SubTaskRepository, TaskRepository
from .validators import validate_status


def _now() -> str:
    """
    現在のUTCタイムスタンプをISO 8601形式で返す

    Returns:
        str: ISO 8601形式のUTCタイムスタンプ
    """
    return datetime.utcnow().isoformat()


class StatusManager:
    """
    ステータス遷移を管理するクラス

    TaskとSubTaskのステータス更新、およびDONE遷移の前提条件チェックを提供します。
    """

    def __init__(self, db: Database, dep_manager: DependencyManager):
        """
        Args:
            db: Database インスタンス
            dep_manager: DependencyManager インスタンス
        """
        self.db = db
        self.dep_manager = dep_manager
        self.task_repo = TaskRepository(db)
        self.subtask_repo = SubTaskRepository(db)

    def update_task_status(self, task_id: int, new_status: str) -> Task:
        """
        Taskのステータスを更新

        Args:
            task_id: TaskID
            new_status: 新しいステータス

        Returns:
            Task: 更新されたTask

        Raises:
            StatusTransitionError: DONE遷移の条件を満たしていない場合
        """
        # ステータスのバリデーション
        new_status = validate_status(new_status)

        # Taskの存在確認
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise StatusTransitionError(f"TaskID {task_id} は存在しません")

        # DONE遷移の場合、前提条件をチェック
        if new_status == "DONE":
            is_valid, error_message = self.validate_done_transition(task_id, "task")
            if not is_valid:
                raise StatusTransitionError(error_message)

        # ステータス更新
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            now = _now()
            cursor.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (new_status, now, task_id),
            )
            conn.commit()

            # 更新されたTaskを返す
            task.status = new_status
            task.updated_at = now
            return task

        except sqlite3.Error as e:
            conn.rollback()
            raise StatusTransitionError(f"Taskステータスの更新に失敗しました: {e}")

    def update_subtask_status(self, subtask_id: int, new_status: str) -> SubTask:
        """
        SubTaskのステータスを更新

        Args:
            subtask_id: SubTaskID
            new_status: 新しいステータス

        Returns:
            SubTask: 更新されたSubTask

        Raises:
            StatusTransitionError: DONE遷移の条件を満たしていない場合
        """
        # ステータスのバリデーション
        new_status = validate_status(new_status)

        # SubTaskの存在確認
        subtask = self.subtask_repo.get_by_id(subtask_id)
        if not subtask:
            raise StatusTransitionError(f"SubTaskID {subtask_id} は存在しません")

        # DONE遷移の場合、前提条件をチェック
        if new_status == "DONE":
            is_valid, error_message = self.validate_done_transition(
                subtask_id, "subtask"
            )
            if not is_valid:
                raise StatusTransitionError(error_message)

        # ステータス更新
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            now = _now()
            cursor.execute(
                "UPDATE subtasks SET status = ?, updated_at = ? WHERE id = ?",
                (new_status, now, subtask_id),
            )
            conn.commit()

            # 更新されたSubTaskを返す
            subtask.status = new_status
            subtask.updated_at = now
            return subtask

        except sqlite3.Error as e:
            conn.rollback()
            raise StatusTransitionError(f"SubTaskステータスの更新に失敗しました: {e}")

    def validate_done_transition(
        self, node_id: int, node_type: str
    ) -> tuple[bool, str]:
        """
        DONE遷移の前提条件を検証 (D3)

        Args:
            node_id: ノードID (TaskIDまたはSubTaskID)
            node_type: ノードタイプ ('task' または 'subtask')

        Returns:
            tuple[bool, str]: (検証結果, エラーメッセージ)
                - True, "" : 遷移可能
                - False, "理由" : 遷移不可能
        """
        # すべての先行ノードがDONEであることを確認
        if not self._all_predecessors_done(node_id, node_type):
            return (
                False,
                f"すべての先行{node_type}がDONEでないため、DONEに遷移できません",
            )

        # Taskの場合、すべての子SubTaskがDONEであることを確認
        if node_type == "task":
            if not self._all_child_subtasks_done(node_id):
                return (
                    False,
                    "すべての子SubTaskがDONEでないため、TaskをDONEに遷移できません",
                )

        return (True, "")

    def _all_predecessors_done(self, node_id: int, node_type: str) -> bool:
        """
        すべての先行ノードがDONEかチェック

        Args:
            node_id: ノードID
            node_type: ノードタイプ ('task' または 'subtask')

        Returns:
            bool: すべての先行ノードがDONEの場合True
        """
        if node_type == "task":
            deps = self.dep_manager.get_task_dependencies(node_id)
            predecessors = deps["predecessors"]

            for pred_id in predecessors:
                pred_task = self.task_repo.get_by_id(pred_id)
                if pred_task and pred_task.status != "DONE":
                    return False

        elif node_type == "subtask":
            deps = self.dep_manager.get_subtask_dependencies(node_id)
            predecessors = deps["predecessors"]

            for pred_id in predecessors:
                pred_subtask = self.subtask_repo.get_by_id(pred_id)
                if pred_subtask and pred_subtask.status != "DONE":
                    return False

        return True

    def _all_child_subtasks_done(self, task_id: int) -> bool:
        """
        Taskのすべての子SubTaskがDONEかチェック

        Args:
            task_id: TaskID

        Returns:
            bool: すべての子SubTaskがDONEの場合True (子がいない場合もTrue)
        """
        subtasks = self.subtask_repo.get_by_task(task_id)

        # 子SubTaskがいない場合はTrue
        if not subtasks:
            return True

        # すべてDONEかチェック
        for subtask in subtasks:
            if subtask.status != "DONE":
                return False

        return True
