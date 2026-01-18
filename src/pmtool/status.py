"""
ステータス管理モジュール

このモジュールはTaskとSubTaskのステータス遷移を管理します。
DONE遷移時の前提条件チェック(D3)を含みます。
"""

import sqlite3
from datetime import datetime

from .database import Database
from .dependencies import DependencyManager
from .exceptions import StatusTransitionError, StatusTransitionFailureReason
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
            raise StatusTransitionError(
                f"TaskID {task_id} は存在しません",
                reason=StatusTransitionFailureReason.NODE_NOT_FOUND,
                details={"node_id": task_id, "node_type": "task"},
            )

        # DONE遷移の場合、前提条件をチェック
        if new_status == "DONE":
            is_valid, error_message, reason, details = self.validate_done_transition(
                task_id, "task"
            )
            if not is_valid:
                raise StatusTransitionError(error_message, reason=reason, details=details)

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
            raise StatusTransitionError(
                f"SubTaskID {subtask_id} は存在しません",
                reason=StatusTransitionFailureReason.NODE_NOT_FOUND,
                details={"node_id": subtask_id, "node_type": "subtask"},
            )

        # DONE遷移の場合、前提条件をチェック
        if new_status == "DONE":
            is_valid, error_message, reason, details = self.validate_done_transition(
                subtask_id, "subtask"
            )
            if not is_valid:
                raise StatusTransitionError(error_message, reason=reason, details=details)

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
    ) -> tuple[bool, str, StatusTransitionFailureReason | None, dict]:
        """
        DONE遷移の前提条件を検証 (D3)

        Args:
            node_id: ノードID (TaskIDまたはSubTaskID)
            node_type: ノードタイプ ('task' または 'subtask')

        Returns:
            tuple[bool, str, StatusTransitionFailureReason | None, dict]:
                (検証結果, エラーメッセージ, reason code, 詳細情報)
                - True, "", None, {} : 遷移可能
                - False, "理由", reason, details : 遷移不可能
        """
        # すべての先行ノードがDONEであることを確認
        incomplete_predecessors = self._get_incomplete_predecessors(node_id, node_type)
        if incomplete_predecessors:
            return (
                False,
                f"すべての先行{node_type}がDONEでないため、DONEに遷移できません",
                StatusTransitionFailureReason.PREREQUISITE_NOT_DONE,
                {
                    "node_id": node_id,
                    "node_type": node_type,
                    "incomplete_predecessors": incomplete_predecessors,
                },
            )

        # Taskの場合、すべての子SubTaskがDONEであることを確認
        if node_type == "task":
            incomplete_children = self._get_incomplete_child_subtasks(node_id)
            if incomplete_children:
                return (
                    False,
                    "すべての子SubTaskがDONEでないため、TaskをDONEに遷移できません",
                    StatusTransitionFailureReason.CHILD_NOT_DONE,
                    {
                        "node_id": node_id,
                        "node_type": node_type,
                        "incomplete_children": incomplete_children,
                    },
                )

        return (True, "", None, {})

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

    def _get_incomplete_predecessors(
        self, node_id: int, node_type: str
    ) -> list[dict]:
        """
        未完了の先行ノードのリストを取得

        Args:
            node_id: ノードID
            node_type: ノードタイプ ('task' または 'subtask')

        Returns:
            list[dict]: 未完了の先行ノード情報のリスト
                例: [{"id": 3, "name": "先行タスク", "status": "IN_PROGRESS"}, ...]
        """
        incomplete = []

        if node_type == "task":
            deps = self.dep_manager.get_task_dependencies(node_id)
            predecessors = deps["predecessors"]

            for pred_id in predecessors:
                pred_task = self.task_repo.get_by_id(pred_id)
                if pred_task and pred_task.status != "DONE":
                    incomplete.append(
                        {
                            "id": pred_task.id,
                            "name": pred_task.name,
                            "status": pred_task.status,
                        }
                    )

        elif node_type == "subtask":
            deps = self.dep_manager.get_subtask_dependencies(node_id)
            predecessors = deps["predecessors"]

            for pred_id in predecessors:
                pred_subtask = self.subtask_repo.get_by_id(pred_id)
                if pred_subtask and pred_subtask.status != "DONE":
                    incomplete.append(
                        {
                            "id": pred_subtask.id,
                            "name": pred_subtask.name,
                            "status": pred_subtask.status,
                        }
                    )

        return incomplete

    def _get_incomplete_child_subtasks(self, task_id: int) -> list[dict]:
        """
        未完了の子SubTaskのリストを取得

        Args:
            task_id: TaskID

        Returns:
            list[dict]: 未完了の子SubTask情報のリスト
                例: [{"id": 5, "name": "子SubTask", "status": "NOT_STARTED"}, ...]
        """
        incomplete = []
        subtasks = self.subtask_repo.get_by_task(task_id)

        for subtask in subtasks:
            if subtask.status != "DONE":
                incomplete.append(
                    {
                        "id": subtask.id,
                        "name": subtask.name,
                        "status": subtask.status,
                    }
                )

        return incomplete

    def dry_run_status_update(
        self, node_id: int, node_type: str, new_status: str
    ) -> tuple[bool, str, StatusTransitionFailureReason | None, dict]:
        """
        ステータス更新のdry-run（DBを変更せず、可否のみチェック）

        Args:
            node_id: ノードID (TaskIDまたはSubTaskID)
            node_type: ノードタイプ ('task' または 'subtask')
            new_status: 新しいステータス

        Returns:
            tuple[bool, str, StatusTransitionFailureReason | None, dict]:
                (可否, エラーメッセージ, reason code, 詳細情報)
                - True, "", None, {} : 遷移可能
                - False, "理由", reason, details : 遷移不可能
        """
        from .validators import validate_status

        # 1. ステータス値のバリデーション
        if not validate_status(new_status, node_type):
            return (
                False,
                f"無効なステータス値: {new_status}",
                StatusTransitionFailureReason.INVALID_STATUS,
                {"node_id": node_id, "node_type": node_type, "new_status": new_status},
            )

        # 2. ノードの存在確認
        if node_type == "task":
            task_repo = TaskRepository(self.db)
            node = task_repo.get_by_id(node_id)
            if not node:
                return (
                    False,
                    f"Task {node_id} が見つかりません",
                    StatusTransitionFailureReason.NODE_NOT_FOUND,
                    {"node_id": node_id, "node_type": node_type},
                )
        elif node_type == "subtask":
            subtask_repo = SubTaskRepository(self.db)
            node = subtask_repo.get_by_id(node_id)
            if not node:
                return (
                    False,
                    f"SubTask {node_id} が見つかりません",
                    StatusTransitionFailureReason.NODE_NOT_FOUND,
                    {"node_id": node_id, "node_type": node_type},
                )
        else:
            return (
                False,
                f"無効なノードタイプ: {node_type}",
                StatusTransitionFailureReason.INVALID_NODE_TYPE,
                {"node_id": node_id, "node_type": node_type},
            )

        # 3. DONEへの遷移の場合は前提条件を検証
        if new_status == "DONE":
            return self.validate_done_transition(node_id, node_type)

        # 4. DONE以外への遷移は常に許可（現在の仕様）
        return (True, "", None, {})
