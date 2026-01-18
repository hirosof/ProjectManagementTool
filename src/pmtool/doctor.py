"""
doctor/check モジュール

データベースの整合性をチェックし、異常を検出・報告する機能を提供します。
"""

from dataclasses import dataclass
from enum import Enum
from typing import List

from .database import Database
from .dependencies import DependencyManager
from .repository import (
    ProjectRepository,
    SubProjectRepository,
    SubTaskRepository,
    TaskRepository,
)


class IssueLevel(Enum):
    """問題のレベル"""

    ERROR = "error"
    """エラー（データ整合性の破綻）"""

    WARNING = "warning"
    """警告（推奨されない状態だが、動作は可能）"""


@dataclass
class Issue:
    """検出された問題"""

    level: IssueLevel
    """問題のレベル（ERROR/WARNING）"""

    code: str
    """問題コード（例: FK001, DAG001）"""

    message: str
    """問題の説明"""

    details: dict
    """詳細情報"""


@dataclass
class DoctorReport:
    """doctor/check の実行結果レポート"""

    errors: List[Issue]
    """エラーのリスト"""

    warnings: List[Issue]
    """警告のリスト"""

    @property
    def error_count(self) -> int:
        """エラー件数"""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """警告件数"""
        return len(self.warnings)

    @property
    def is_healthy(self) -> bool:
        """データベースが健全か（エラーが0件）"""
        return self.error_count == 0


class Doctor:
    """
    データベースの整合性チェッククラス

    各種制約違反や異常を検出し、レポートを生成します。
    """

    def __init__(self, db: Database):
        """
        Args:
            db: Database インスタンス
        """
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.subproject_repo = SubProjectRepository(db)
        self.task_repo = TaskRepository(db)
        self.subtask_repo = SubTaskRepository(db)
        self.dep_manager = DependencyManager(db)

    def check_all(self) -> DoctorReport:
        """
        すべてのチェックを実行

        Returns:
            DoctorReport: チェック結果レポート
        """
        issues: List[Issue] = []

        # 各チェックを実行
        issues.extend(self._check_fk_integrity())
        issues.extend(self._check_dag_integrity())
        issues.extend(self._check_status_consistency())
        issues.extend(self._check_order_index())
        issues.extend(self._check_subproject_nesting())

        # Error/Warning に分類
        errors = [issue for issue in issues if issue.level == IssueLevel.ERROR]
        warnings = [issue for issue in issues if issue.level == IssueLevel.WARNING]

        return DoctorReport(errors=errors, warnings=warnings)

    def _check_fk_integrity(self) -> List[Issue]:
        """
        外部キー整合性チェック

        Returns:
            List[Issue]: 検出された問題のリスト
        """
        issues = []
        conn = self.db.connect()
        cursor = conn.cursor()

        # SubProject の project_id チェック
        cursor.execute("""
            SELECT sp.id, sp.name, sp.project_id
            FROM subprojects sp
            LEFT JOIN projects p ON sp.project_id = p.id
            WHERE p.id IS NULL
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="FK001",
                    message=f"SubProject {row[0]} の親Project {row[2]} が存在しません",
                    details={
                        "subproject_id": row[0],
                        "subproject_name": row[1],
                        "missing_project_id": row[2],
                    },
                )
            )

        # Task の project_id チェック
        cursor.execute("""
            SELECT t.id, t.name, t.project_id
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE p.id IS NULL
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="FK002",
                    message=f"Task {row[0]} の親Project {row[2]} が存在しません",
                    details={
                        "task_id": row[0],
                        "task_name": row[1],
                        "missing_project_id": row[2],
                    },
                )
            )

        # Task の subproject_id チェック
        cursor.execute("""
            SELECT t.id, t.name, t.subproject_id
            FROM tasks t
            WHERE t.subproject_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM subprojects sp WHERE sp.id = t.subproject_id
            )
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="FK003",
                    message=f"Task {row[0]} の親SubProject {row[2]} が存在しません",
                    details={
                        "task_id": row[0],
                        "task_name": row[1],
                        "missing_subproject_id": row[2],
                    },
                )
            )

        # SubTask の task_id チェック
        cursor.execute("""
            SELECT st.id, st.name, st.task_id
            FROM subtasks st
            LEFT JOIN tasks t ON st.task_id = t.id
            WHERE t.id IS NULL
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="FK004",
                    message=f"SubTask {row[0]} の親Task {row[2]} が存在しません",
                    details={
                        "subtask_id": row[0],
                        "subtask_name": row[1],
                        "missing_task_id": row[2],
                    },
                )
            )

        # Task依存関係の参照整合性チェック
        cursor.execute("""
            SELECT td.predecessor_id, td.successor_id
            FROM task_dependencies td
            LEFT JOIN tasks t1 ON td.predecessor_id = t1.id
            WHERE t1.id IS NULL
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="FK005",
                    message=f"Task依存関係の predecessor {row[0]} が存在しません",
                    details={
                        "predecessor_id": row[0],
                        "successor_id": row[1],
                    },
                )
            )

        cursor.execute("""
            SELECT td.predecessor_id, td.successor_id
            FROM task_dependencies td
            LEFT JOIN tasks t2 ON td.successor_id = t2.id
            WHERE t2.id IS NULL
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="FK006",
                    message=f"Task依存関係の successor {row[1]} が存在しません",
                    details={
                        "predecessor_id": row[0],
                        "successor_id": row[1],
                    },
                )
            )

        # SubTask依存関係の参照整合性チェック
        cursor.execute("""
            SELECT std.predecessor_id, std.successor_id
            FROM subtask_dependencies std
            LEFT JOIN subtasks st1 ON std.predecessor_id = st1.id
            WHERE st1.id IS NULL
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="FK007",
                    message=f"SubTask依存関係の predecessor {row[0]} が存在しません",
                    details={
                        "predecessor_id": row[0],
                        "successor_id": row[1],
                    },
                )
            )

        cursor.execute("""
            SELECT std.predecessor_id, std.successor_id
            FROM subtask_dependencies std
            LEFT JOIN subtasks st2 ON std.successor_id = st2.id
            WHERE st2.id IS NULL
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="FK008",
                    message=f"SubTask依存関係の successor {row[1]} が存在しません",
                    details={
                        "predecessor_id": row[0],
                        "successor_id": row[1],
                    },
                )
            )
        return issues

    def _check_dag_integrity(self) -> List[Issue]:
        """
        DAG整合性チェック（サイクル検出、禁止依存）

        Returns:
            List[Issue]: 検出された問題のリスト
        """
        issues = []

        # Task依存のサイクル検出
        try:
            cycles = self._detect_cycles_task()
            for cycle in cycles:
                issues.append(
                    Issue(
                        level=IssueLevel.ERROR,
                        code="DAG001",
                        message=f"Task依存関係にサイクルが存在します: {' → '.join(map(str, cycle))}",
                        details={"cycle": cycle},
                    )
                )
        except Exception:
            # サイクル検出で例外が発生した場合はスキップ
            pass

        # SubTask依存のサイクル検出
        try:
            cycles = self._detect_cycles_subtask()
            for cycle in cycles:
                issues.append(
                    Issue(
                        level=IssueLevel.ERROR,
                        code="DAG002",
                        message=f"SubTask依存関係にサイクルが存在します: {' → '.join(map(str, cycle))}",
                        details={"cycle": cycle},
                    )
                )
        except Exception:
            # サイクル検出で例外が発生した場合はスキップ
            pass

        return issues

    def _detect_cycles_task(self) -> List[List[int]]:
        """
        Task依存関係のサイクルを検出

        Returns:
            List[List[int]]: 検出されたサイクルのリスト
        """
        # DFSでサイクル検出（簡易実装）
        conn = self.db.connect()
        cursor = conn.cursor()
        cycles = []

        # すべてのTaskを取得
        cursor.execute("SELECT id FROM tasks")
        task_ids = [row[0] for row in cursor.fetchall()]

        for task_id in task_ids:
            visited = set()
            rec_stack = set()
            path = []

            if self._dfs_task(task_id, visited, rec_stack, path, cursor):
                # サイクル検出（pathから抽出）
                if path:
                    cycles.append(path.copy())

        return cycles

    def _dfs_task(
        self, node_id: int, visited: set, rec_stack: set, path: list, cursor
    ) -> bool:
        """Task依存のDFS（簡易版・サイクル検出用）"""
        visited.add(node_id)
        rec_stack.add(node_id)
        path.append(node_id)

        # 後続ノードを取得
        cursor.execute(
            "SELECT successor_id FROM task_dependencies WHERE predecessor_id = ?",
            (node_id,),
        )
        successors = [row[0] for row in cursor.fetchall()]

        for successor_id in successors:
            if successor_id not in visited:
                if self._dfs_task(successor_id, visited, rec_stack, path, cursor):
                    return True
            elif successor_id in rec_stack:
                # サイクル検出
                return True

        rec_stack.remove(node_id)
        path.pop()
        return False

    def _detect_cycles_subtask(self) -> List[List[int]]:
        """
        SubTask依存関係のサイクルを検出

        Returns:
            List[List[int]]: 検出されたサイクルのリスト
        """
        # Task版と同様の実装（SubTask用）
        conn = self.db.connect()
        cursor = conn.cursor()
        cycles = []

        cursor.execute("SELECT id FROM subtasks")
        subtask_ids = [row[0] for row in cursor.fetchall()]

        for subtask_id in subtask_ids:
            visited = set()
            rec_stack = set()
            path = []

            if self._dfs_subtask(subtask_id, visited, rec_stack, path, cursor):
                if path:
                    cycles.append(path.copy())

        return cycles

    def _dfs_subtask(
        self, node_id: int, visited: set, rec_stack: set, path: list, cursor
    ) -> bool:
        """SubTask依存のDFS（簡易版・サイクル検出用）"""
        visited.add(node_id)
        rec_stack.add(node_id)
        path.append(node_id)

        cursor.execute(
            "SELECT successor_id FROM subtask_dependencies WHERE predecessor_id = ?",
            (node_id,),
        )
        successors = [row[0] for row in cursor.fetchall()]

        for successor_id in successors:
            if successor_id not in visited:
                if self._dfs_subtask(successor_id, visited, rec_stack, path, cursor):
                    return True
            elif successor_id in rec_stack:
                return True

        rec_stack.remove(node_id)
        path.pop()
        return False

    def _check_status_consistency(self) -> List[Issue]:
        """
        ステータス整合性チェック

        Returns:
            List[Issue]: 検出された問題のリスト
        """
        issues = []
        conn = self.db.connect()
        cursor = conn.cursor()

        # ステータス値の不正チェック（Phase 4 で追加）
        # Task の不正なステータス値
        cursor.execute("""
            SELECT id, name, status
            FROM tasks
            WHERE status NOT IN ('UNSET', 'NOT_STARTED', 'IN_PROGRESS', 'DONE')
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="STATUS_INVALID001",
                    message=f"Task {row[0]} のステータスが不正です: '{row[2]}'",
                    details={
                        "task_id": row[0],
                        "task_name": row[1],
                        "invalid_status": row[2],
                    },
                )
            )

        # SubTask の不正なステータス値
        cursor.execute("""
            SELECT id, name, status
            FROM subtasks
            WHERE status NOT IN ('UNSET', 'NOT_STARTED', 'IN_PROGRESS', 'DONE')
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="STATUS_INVALID002",
                    message=f"SubTask {row[0]} のステータスが不正です: '{row[2]}'",
                    details={
                        "subtask_id": row[0],
                        "subtask_name": row[1],
                        "invalid_status": row[2],
                    },
                )
            )

        # 子SubTaskが未完了なのに親TaskがDONEの場合
        cursor.execute("""
            SELECT t.id, t.name, COUNT(st.id) as incomplete_count
            FROM tasks t
            INNER JOIN subtasks st ON st.task_id = t.id
            WHERE t.status = 'DONE'
            AND st.status != 'DONE'
            GROUP BY t.id, t.name
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="STATUS001",
                    message=f"Task {row[0]} がDONEですが、{row[2]}件の子SubTaskが未完了です",
                    details={
                        "task_id": row[0],
                        "task_name": row[1],
                        "incomplete_subtask_count": row[2],
                    },
                )
            )

        # 先行Taskが未完了なのに後続TaskがDONEの場合
        cursor.execute("""
            SELECT t2.id, t2.name, t1.id as pred_id, t1.name as pred_name
            FROM tasks t2
            INNER JOIN task_dependencies td ON td.successor_id = t2.id
            INNER JOIN tasks t1 ON td.predecessor_id = t1.id
            WHERE t2.status = 'DONE'
            AND t1.status != 'DONE'
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="STATUS002",
                    message=f"Task {row[0]} がDONEですが、先行Task {row[2]} が未完了です",
                    details={
                        "task_id": row[0],
                        "task_name": row[1],
                        "predecessor_id": row[2],
                        "predecessor_name": row[3],
                    },
                )
            )

        # 先行SubTaskが未完了なのに後続SubTaskがDONEの場合
        cursor.execute("""
            SELECT st2.id, st2.name, st1.id as pred_id, st1.name as pred_name
            FROM subtasks st2
            INNER JOIN subtask_dependencies std ON std.successor_id = st2.id
            INNER JOIN subtasks st1 ON std.predecessor_id = st1.id
            WHERE st2.status = 'DONE'
            AND st1.status != 'DONE'
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="STATUS003",
                    message=f"SubTask {row[0]} がDONEですが、先行SubTask {row[2]} が未完了です",
                    details={
                        "subtask_id": row[0],
                        "subtask_name": row[1],
                        "predecessor_id": row[2],
                        "predecessor_name": row[3],
                    },
                )
            )
        return issues

    def _check_order_index(self) -> List[Issue]:
        """
        order_index 異常チェック（重複・負値・欠番）

        Returns:
            List[Issue]: 検出された問題のリスト
        """
        issues = []
        conn = self.db.connect()
        cursor = conn.cursor()

        # --- 負値チェック（Phase 4 で追加） ---

        # SubProject の order_index 負値チェック
        cursor.execute("""
            SELECT id, name, order_index
            FROM subprojects
            WHERE order_index < 0
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="ORDER_NEG001",
                    message=f"SubProject {row[0]} の order_index が負の値です: {row[2]}",
                    details={
                        "subproject_id": row[0],
                        "subproject_name": row[1],
                        "order_index": row[2],
                    },
                )
            )

        # Task の order_index 負値チェック
        cursor.execute("""
            SELECT id, name, order_index
            FROM tasks
            WHERE order_index < 0
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="ORDER_NEG002",
                    message=f"Task {row[0]} の order_index が負の値です: {row[2]}",
                    details={
                        "task_id": row[0],
                        "task_name": row[1],
                        "order_index": row[2],
                    },
                )
            )

        # SubTask の order_index 負値チェック
        cursor.execute("""
            SELECT id, name, order_index
            FROM subtasks
            WHERE order_index < 0
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="ORDER_NEG003",
                    message=f"SubTask {row[0]} の order_index が負の値です: {row[2]}",
                    details={
                        "subtask_id": row[0],
                        "subtask_name": row[1],
                        "order_index": row[2],
                    },
                )
            )

        # --- 重複チェック ---

        # SubProject の order_index 重複チェック
        # 注: parent_subproject_id も考慮する必要がある（親が異なれば別の文脈）
        cursor.execute("""
            SELECT project_id, COALESCE(parent_subproject_id, -1) as parent_id, order_index, COUNT(*) as dup_count
            FROM subprojects
            GROUP BY project_id, parent_subproject_id, order_index
            HAVING dup_count > 1
        """)
        for row in cursor.fetchall():
            parent_info = f"parent_subproject_id={row[1]}" if row[1] != -1 else "parent_subproject_id=NULL"
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="ORDER001",
                    message=f"Project {row[0]} ({parent_info}) 内で order_index {row[2]} が重複しています（{row[3]}件）",
                    details={
                        "project_id": row[0],
                        "parent_subproject_id": row[1] if row[1] != -1 else None,
                        "order_index": row[2],
                        "duplicate_count": row[3],
                    },
                )
            )

        # Task の order_index 重複チェック
        # 注: project_id と subproject_id の両方を考慮（subproject_id=NULL の場合もある）
        cursor.execute("""
            SELECT project_id, COALESCE(subproject_id, -1) as sp_id, order_index, COUNT(*) as dup_count
            FROM tasks
            GROUP BY project_id, subproject_id, order_index
            HAVING dup_count > 1
        """)
        for row in cursor.fetchall():
            context_info = f"SubProject {row[1]}" if row[1] != -1 else f"Project {row[0]} 直下"
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="ORDER002",
                    message=f"{context_info} 内で order_index {row[2]} が重複しています（{row[3]}件）",
                    details={
                        "project_id": row[0],
                        "subproject_id": row[1] if row[1] != -1 else None,
                        "order_index": row[2],
                        "duplicate_count": row[3],
                    },
                )
            )

        # SubTask の order_index 重複チェック
        cursor.execute("""
            SELECT task_id, order_index, COUNT(*) as dup_count
            FROM subtasks
            GROUP BY task_id, order_index
            HAVING dup_count > 1
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    code="ORDER003",
                    message=f"Task {row[0]} 内で order_index {row[1]} が重複しています（{row[2]}件）",
                    details={
                        "task_id": row[0],
                        "order_index": row[1],
                        "duplicate_count": row[2],
                    },
                )
            )

        # --- 欠番検出（WARNING） ---

        # SubProject の order_index 欠番チェック
        cursor.execute("""
            SELECT project_id, COALESCE(parent_subproject_id, -1) as parent_id,
                   COUNT(*) as total_count, MAX(order_index) as max_index
            FROM subprojects
            GROUP BY project_id, parent_subproject_id
            HAVING max_index > (total_count - 1)
        """)
        for row in cursor.fetchall():
            parent_info = f"parent_subproject_id={row[1]}" if row[1] != -1 else "parent_subproject_id=NULL"
            issues.append(
                Issue(
                    level=IssueLevel.WARNING,
                    code="ORDER_W001",
                    message=f"Project {row[0]} ({parent_info}) 内で order_index に欠番があります（件数={row[2]}, 最大={row[3]}）",
                    details={
                        "project_id": row[0],
                        "parent_subproject_id": row[1] if row[1] != -1 else None,
                        "total_count": row[2],
                        "max_index": row[3],
                    },
                )
            )

        # Task の order_index 欠番チェック
        cursor.execute("""
            SELECT project_id, COALESCE(subproject_id, -1) as sp_id,
                   COUNT(*) as total_count, MAX(order_index) as max_index
            FROM tasks
            GROUP BY project_id, subproject_id
            HAVING max_index > (total_count - 1)
        """)
        for row in cursor.fetchall():
            context_info = f"SubProject {row[1]}" if row[1] != -1 else f"Project {row[0]} 直下"
            issues.append(
                Issue(
                    level=IssueLevel.WARNING,
                    code="ORDER_W002",
                    message=f"{context_info} 内で order_index に欠番があります（件数={row[2]}, 最大={row[3]}）",
                    details={
                        "project_id": row[0],
                        "subproject_id": row[1] if row[1] != -1 else None,
                        "total_count": row[2],
                        "max_index": row[3],
                    },
                )
            )

        # SubTask の order_index 欠番チェック
        cursor.execute("""
            SELECT task_id, COUNT(*) as total_count, MAX(order_index) as max_index
            FROM subtasks
            GROUP BY task_id
            HAVING max_index > (total_count - 1)
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.WARNING,
                    code="ORDER_W003",
                    message=f"Task {row[0]} 内で order_index に欠番があります（件数={row[1]}, 最大={row[2]}）",
                    details={
                        "task_id": row[0],
                        "total_count": row[1],
                        "max_index": row[2],
                    },
                )
            )

        return issues

    def _check_subproject_nesting(self) -> List[Issue]:
        """
        SubProject 入れ子存在チェック

        Phase 3 では SubProject 入れ子（parent_subproject_id != NULL）を
        機能対応しないため、存在する場合は WARNING を出す。

        Returns:
            List[Issue]: 検出された問題のリスト
        """
        issues = []
        conn = self.db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, parent_subproject_id
            FROM subprojects
            WHERE parent_subproject_id IS NOT NULL
        """)
        for row in cursor.fetchall():
            issues.append(
                Issue(
                    level=IssueLevel.WARNING,
                    code="NEST001",
                    message=f"SubProject {row[0]} が入れ子構造を持っています（parent_subproject_id={row[2]}）",
                    details={
                        "subproject_id": row[0],
                        "subproject_name": row[1],
                        "parent_subproject_id": row[2],
                    },
                )
            )

        return issues
