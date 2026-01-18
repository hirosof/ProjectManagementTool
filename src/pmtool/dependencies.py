"""
依存関係管理モジュール

このモジュールはTask間およびSubTask間の依存関係を管理します。
DAG (有向非巡回グラフ) の検証と循環検出を行います。
"""

import sqlite3
from collections import deque
from datetime import datetime
from typing import Optional

from .database import Database
from .exceptions import ConstraintViolationError, CyclicDependencyError
from .models import Dependency


def _now() -> str:
    """
    現在のUTCタイムスタンプをISO 8601形式で返す

    Returns:
        str: ISO 8601形式のUTCタイムスタンプ
    """
    return datetime.utcnow().isoformat()


class DependencyManager:
    """
    依存関係を管理するクラス

    TaskとSubTaskの依存関係の追加・削除・取得、およびDAG循環検出を提供します。
    """

    def __init__(self, db: Database):
        """
        Args:
            db: Database インスタンス
        """
        self.db = db

    def add_task_dependency(
        self, predecessor_id: int, successor_id: int
    ) -> Dependency:
        """
        Task間の依存関係を追加

        Args:
            predecessor_id: 先行TaskID
            successor_id: 後続TaskID

        Returns:
            Dependency: 作成された依存関係

        Raises:
            ConstraintViolationError: タスクが存在しない、または同じプロジェクトに属していない場合
            CyclicDependencyError: 循環依存が発生する場合
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # 両方のTaskの存在確認とproject_idの取得
            cursor.execute(
                "SELECT id, project_id FROM tasks WHERE id = ?", (predecessor_id,)
            )
            pred_row = cursor.fetchone()
            if not pred_row:
                raise ConstraintViolationError(f"TaskID {predecessor_id} は存在しません")

            cursor.execute(
                "SELECT id, project_id FROM tasks WHERE id = ?", (successor_id,)
            )
            succ_row = cursor.fetchone()
            if not succ_row:
                raise ConstraintViolationError(f"TaskID {successor_id} は存在しません")

            # 同じプロジェクトに属しているか確認 (D1制約)
            if pred_row["project_id"] != succ_row["project_id"]:
                raise ConstraintViolationError(
                    f"Task {predecessor_id} と Task {successor_id} は異なるプロジェクトに属しているため、"
                    f"依存関係を作成できません"
                )

            # 自己参照チェック (DB CHECK制約でも保護されているが念のため)
            if predecessor_id == successor_id:
                raise ConstraintViolationError("TaskIDは自分自身に依存できません")

            # 既存の依存関係チェック (DB UNIQUE制約でも保護されているが念のため)
            cursor.execute(
                """
                SELECT id FROM task_dependencies
                WHERE predecessor_id = ? AND successor_id = ?
                """,
                (predecessor_id, successor_id),
            )
            if cursor.fetchone():
                raise ConstraintViolationError(
                    f"Task {predecessor_id} → {successor_id} の依存関係は既に存在します"
                )

            # 循環検出 (DAG検証)
            self.validate_no_cycle(predecessor_id, successor_id, "task", conn=conn)

            # INSERT
            now = _now()
            cursor.execute(
                """
                INSERT INTO task_dependencies (predecessor_id, successor_id, created_at)
                VALUES (?, ?, ?)
                """,
                (predecessor_id, successor_id, now),
            )
            dep_id = cursor.lastrowid
            conn.commit()

            return Dependency(
                id=dep_id,
                predecessor_id=predecessor_id,
                successor_id=successor_id,
                created_at=now,
            )

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"Task依存関係の作成に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def add_subtask_dependency(
        self, predecessor_id: int, successor_id: int
    ) -> Dependency:
        """
        SubTask間の依存関係を追加

        Args:
            predecessor_id: 先行SubTaskID
            successor_id: 後続SubTaskID

        Returns:
            Dependency: 作成された依存関係

        Raises:
            ConstraintViolationError: SubTaskが存在しない、または同じTaskに属していない場合
            CyclicDependencyError: 循環依存が発生する場合
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # 両方のSubTaskの存在確認とtask_idの取得
            cursor.execute(
                "SELECT id, task_id FROM subtasks WHERE id = ?", (predecessor_id,)
            )
            pred_row = cursor.fetchone()
            if not pred_row:
                raise ConstraintViolationError(f"SubTaskID {predecessor_id} は存在しません")

            cursor.execute(
                "SELECT id, task_id FROM subtasks WHERE id = ?", (successor_id,)
            )
            succ_row = cursor.fetchone()
            if not succ_row:
                raise ConstraintViolationError(f"SubTaskID {successor_id} は存在しません")

            # 同じTaskに属しているか確認 (D1制約)
            if pred_row["task_id"] != succ_row["task_id"]:
                raise ConstraintViolationError(
                    f"SubTask {predecessor_id} と SubTask {successor_id} は異なるTaskに属しているため、"
                    f"依存関係を作成できません"
                )

            # 自己参照チェック
            if predecessor_id == successor_id:
                raise ConstraintViolationError("SubTaskIDは自分自身に依存できません")

            # 既存の依存関係チェック
            cursor.execute(
                """
                SELECT id FROM subtask_dependencies
                WHERE predecessor_id = ? AND successor_id = ?
                """,
                (predecessor_id, successor_id),
            )
            if cursor.fetchone():
                raise ConstraintViolationError(
                    f"SubTask {predecessor_id} → {successor_id} の依存関係は既に存在します"
                )

            # 循環検出 (DAG検証)
            self.validate_no_cycle(predecessor_id, successor_id, "subtask", conn=conn)

            # INSERT
            now = _now()
            cursor.execute(
                """
                INSERT INTO subtask_dependencies (predecessor_id, successor_id, created_at)
                VALUES (?, ?, ?)
                """,
                (predecessor_id, successor_id, now),
            )
            dep_id = cursor.lastrowid
            conn.commit()

            return Dependency(
                id=dep_id,
                predecessor_id=predecessor_id,
                successor_id=successor_id,
                created_at=now,
            )

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"SubTask依存関係の作成に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def remove_task_dependency(
        self, predecessor_id: int, successor_id: int
    ) -> None:
        """
        Task間の依存関係を削除

        Args:
            predecessor_id: 先行TaskID
            successor_id: 後続TaskID

        Raises:
            ConstraintViolationError: 依存関係が存在しない場合
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # 依存関係の存在確認
            cursor.execute(
                """
                SELECT id FROM task_dependencies
                WHERE predecessor_id = ? AND successor_id = ?
                """,
                (predecessor_id, successor_id),
            )
            if not cursor.fetchone():
                raise ConstraintViolationError(
                    f"Task {predecessor_id} → {successor_id} の依存関係は存在しません"
                )

            # DELETE
            cursor.execute(
                """
                DELETE FROM task_dependencies
                WHERE predecessor_id = ? AND successor_id = ?
                """,
                (predecessor_id, successor_id),
            )
            conn.commit()

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"Task依存関係の削除に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def remove_subtask_dependency(
        self, predecessor_id: int, successor_id: int
    ) -> None:
        """
        SubTask間の依存関係を削除

        Args:
            predecessor_id: 先行SubTaskID
            successor_id: 後続SubTaskID

        Raises:
            ConstraintViolationError: 依存関係が存在しない場合
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # 依存関係の存在確認
            cursor.execute(
                """
                SELECT id FROM subtask_dependencies
                WHERE predecessor_id = ? AND successor_id = ?
                """,
                (predecessor_id, successor_id),
            )
            if not cursor.fetchone():
                raise ConstraintViolationError(
                    f"SubTask {predecessor_id} → {successor_id} の依存関係は存在しません"
                )

            # DELETE
            cursor.execute(
                """
                DELETE FROM subtask_dependencies
                WHERE predecessor_id = ? AND successor_id = ?
                """,
                (predecessor_id, successor_id),
            )
            conn.commit()

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ConstraintViolationError(f"SubTask依存関係の削除に失敗しました: {e}")
        except Exception as e:
            conn.rollback()
            raise

    def get_task_dependencies(self, task_id: int) -> dict[str, list[int]]:
        """
        指定されたTaskの依存関係を取得

        Args:
            task_id: TaskID

        Returns:
            dict: {
                'predecessors': [先行TaskIDリスト],
                'successors': [後続TaskIDリスト]
            }
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        # 先行Task取得
        cursor.execute(
            """
            SELECT predecessor_id FROM task_dependencies
            WHERE successor_id = ?
            """,
            (task_id,),
        )
        predecessors = [row["predecessor_id"] for row in cursor.fetchall()]

        # 後続Task取得
        cursor.execute(
            """
            SELECT successor_id FROM task_dependencies
            WHERE predecessor_id = ?
            """,
            (task_id,),
        )
        successors = [row["successor_id"] for row in cursor.fetchall()]

        return {"predecessors": predecessors, "successors": successors}

    def get_subtask_dependencies(self, subtask_id: int) -> dict[str, list[int]]:
        """
        指定されたSubTaskの依存関係を取得

        Args:
            subtask_id: SubTaskID

        Returns:
            dict: {
                'predecessors': [先行SubTaskIDリスト],
                'successors': [後続SubTaskIDリスト]
            }
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        # 先行SubTask取得
        cursor.execute(
            """
            SELECT predecessor_id FROM subtask_dependencies
            WHERE successor_id = ?
            """,
            (subtask_id,),
        )
        predecessors = [row["predecessor_id"] for row in cursor.fetchall()]

        # 後続SubTask取得
        cursor.execute(
            """
            SELECT successor_id FROM subtask_dependencies
            WHERE predecessor_id = ?
            """,
            (subtask_id,),
        )
        successors = [row["successor_id"] for row in cursor.fetchall()]

        return {"predecessors": predecessors, "successors": successors}

    def validate_no_cycle(
        self,
        predecessor_id: int,
        successor_id: int,
        dep_type: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        """
        新しい依存関係が循環を作らないことを検証

        Args:
            predecessor_id: 先行ノードID
            successor_id: 後続ノードID
            dep_type: 依存関係タイプ ('task' または 'subtask')
            conn: 既存のコネクション (Noneの場合は新規作成)

        Raises:
            CyclicDependencyError: 循環依存が発生する場合
        """
        # グラフを構築 (同一connを渡す)
        graph = self._build_dependency_graph(dep_type, conn=conn)

        # 新しいエッジ (predecessor → successor) を追加した場合に
        # successor → predecessor へのパスが存在するかチェック
        # もし存在すれば、新しいエッジで循環が形成される
        if self._has_path(graph, successor_id, predecessor_id):
            raise CyclicDependencyError(
                f"依存関係 {predecessor_id} → {successor_id} を追加すると循環依存が発生します"
            )

    def _build_dependency_graph(
        self,
        dep_type: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> dict[int, list[int]]:
        """
        依存関係グラフを構築

        Args:
            dep_type: 依存関係タイプ ('task' または 'subtask')
            conn: 既存のコネクション (Noneの場合は新規作成)

        Returns:
            dict: 隣接リスト表現のグラフ {node_id: [successor_ids]}
        """
        if conn is None:
            conn = self.db.connect()

        cursor = conn.cursor()

        if dep_type == "task":
            cursor.execute(
                "SELECT predecessor_id, successor_id FROM task_dependencies"
            )
        elif dep_type == "subtask":
            cursor.execute(
                "SELECT predecessor_id, successor_id FROM subtask_dependencies"
            )
        else:
            raise ValueError(f"不正な dep_type: {dep_type}")

        graph: dict[int, list[int]] = {}
        for row in cursor.fetchall():
            pred = row["predecessor_id"]
            succ = row["successor_id"]

            if pred not in graph:
                graph[pred] = []
            graph[pred].append(succ)

            # 後続ノードがグラフに存在することを保証
            if succ not in graph:
                graph[succ] = []

        return graph

    def _has_path(self, graph: dict[int, list[int]], start: int, end: int) -> bool:
        """
        グラフ内にstartからendへのパスが存在するかBFSで判定

        Args:
            graph: 隣接リスト表現のグラフ
            start: 開始ノード
            end: 終了ノード

        Returns:
            bool: パスが存在する場合True
        """
        if start == end:
            return True

        if start not in graph:
            return False

        visited = set()
        queue = deque([start])
        visited.add(start)

        while queue:
            current = queue.popleft()

            for neighbor in graph.get(current, []):
                if neighbor == end:
                    return True
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return False

    def bridge_dependencies(
        self,
        node_id: int,
        dep_type: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> list[tuple[int, int]]:
        """
        ノード削除時に依存関係を橋渡しする

        指定されたノードのすべての先行ノードと後続ノードを直接接続します。
        循環を作る組み合わせはスキップします。

        Args:
            node_id: 削除対象ノードID
            dep_type: 依存関係タイプ ('task' または 'subtask')
            conn: 既存のコネクション (Noneの場合は新規作成)

        Returns:
            list[tuple[int, int]]: 作成された橋渡し依存関係のリスト [(pred_id, succ_id), ...]

        Raises:
            CyclicDependencyError: 橋渡しによって循環が発生する場合
        """
        # connが渡されていればそれを使用、なければ新規取得
        own_conn = False
        if conn is None:
            conn = self.db.connect()
            own_conn = True

        cursor = conn.cursor()

        table_name = (
            "task_dependencies" if dep_type == "task" else "subtask_dependencies"
        )

        # 先行ノードを取得
        cursor.execute(
            f"SELECT predecessor_id FROM {table_name} WHERE successor_id = ?",
            (node_id,),
        )
        predecessors = [row["predecessor_id"] for row in cursor.fetchall()]

        # 後続ノードを取得
        cursor.execute(
            f"SELECT successor_id FROM {table_name} WHERE predecessor_id = ?",
            (node_id,),
        )
        successors = [row["successor_id"] for row in cursor.fetchall()]

        bridged = []

        try:
            # 各組み合わせで橋渡し
            for pred in predecessors:
                for succ in successors:
                    # 既に存在する依存関係はスキップ
                    cursor.execute(
                        f"""
                        SELECT id FROM {table_name}
                        WHERE predecessor_id = ? AND successor_id = ?
                        """,
                        (pred, succ),
                    )
                    if cursor.fetchone():
                        continue

                    # 循環検出 (橋渡し後のグラフで循環が発生しないかチェック)
                    try:
                        self.validate_no_cycle(pred, succ, dep_type, conn=conn)
                    except CyclicDependencyError:
                        # この組み合わせは循環を作るのでスキップ
                        continue

                    # 橋渡し依存関係を作成
                    now = _now()
                    cursor.execute(
                        f"""
                        INSERT INTO {table_name} (predecessor_id, successor_id, created_at)
                        VALUES (?, ?, ?)
                        """,
                        (pred, succ, now),
                    )
                    bridged.append((pred, succ))

            # 自分でコネクションを作成した場合のみcommit
            if own_conn:
                conn.commit()

            return bridged

        except Exception as e:
            if own_conn:
                conn.rollback()
            raise

    def find_path_between_tasks(
        self, from_task_id: int, to_task_id: int
    ) -> Optional[list[int]]:
        """
        2つのTask間の依存経路を探索（BFS）

        Args:
            from_task_id: 開始TaskID
            to_task_id: 終了TaskID

        Returns:
            Optional[list[int]]: 経路が存在する場合、TaskIDのリスト [from, ..., to]
                                 経路が存在しない場合、None
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        # BFSで経路探索
        queue = deque([(from_task_id, [from_task_id])])
        visited = {from_task_id}

        while queue:
            current_id, path = queue.popleft()

            # 目的地に到達した
            if current_id == to_task_id:
                return path

            # 後続ノードを探索
            cursor.execute(
                """
                SELECT successor_id FROM task_dependencies
                WHERE predecessor_id = ?
                """,
                (current_id,),
            )
            successors = [row["successor_id"] for row in cursor.fetchall()]

            for succ_id in successors:
                if succ_id not in visited:
                    visited.add(succ_id)
                    queue.append((succ_id, path + [succ_id]))

        # 経路が見つからなかった
        return None

    def find_path_between_subtasks(
        self, from_subtask_id: int, to_subtask_id: int
    ) -> Optional[list[int]]:
        """
        2つのSubTask間の依存経路を探索（BFS）

        Args:
            from_subtask_id: 開始SubTaskID
            to_subtask_id: 終了SubTaskID

        Returns:
            Optional[list[int]]: 経路が存在する場合、SubTaskIDのリスト [from, ..., to]
                                 経路が存在しない場合、None
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        # BFSで経路探索
        queue = deque([(from_subtask_id, [from_subtask_id])])
        visited = {from_subtask_id}

        while queue:
            current_id, path = queue.popleft()

            # 目的地に到達した
            if current_id == to_subtask_id:
                return path

            # 後続ノードを探索
            cursor.execute(
                """
                SELECT successor_id FROM subtask_dependencies
                WHERE predecessor_id = ?
                """,
                (current_id,),
            )
            successors = [row["successor_id"] for row in cursor.fetchall()]

            for succ_id in successors:
                if succ_id not in visited:
                    visited.add(succ_id)
                    queue.append((succ_id, path + [succ_id]))

        # 経路が見つからなかった
        return None

    def get_all_task_successors_recursive(self, task_id: int) -> list[int]:
        """
        指定されたTaskの全後続ノード（間接的な後続も含む）を取得

        Args:
            task_id: TaskID

        Returns:
            list[int]: 後続TaskIDのリスト（重複なし、順不同）
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        all_successors = set()
        queue = deque([task_id])
        visited = {task_id}

        while queue:
            current_id = queue.popleft()

            # 直接の後続ノードを取得
            cursor.execute(
                """
                SELECT successor_id FROM task_dependencies
                WHERE predecessor_id = ?
                """,
                (current_id,),
            )
            successors = [row["successor_id"] for row in cursor.fetchall()]

            for succ_id in successors:
                all_successors.add(succ_id)
                if succ_id not in visited:
                    visited.add(succ_id)
                    queue.append(succ_id)

        return list(all_successors)

    def get_all_subtask_successors_recursive(self, subtask_id: int) -> list[int]:
        """
        指定されたSubTaskの全後続ノード（間接的な後続も含む）を取得

        Args:
            subtask_id: SubTaskID

        Returns:
            list[int]: 後続SubTaskIDのリスト（重複なし、順不同）
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        all_successors = set()
        queue = deque([subtask_id])
        visited = {subtask_id}

        while queue:
            current_id = queue.popleft()

            # 直接の後続ノードを取得
            cursor.execute(
                """
                SELECT successor_id FROM subtask_dependencies
                WHERE predecessor_id = ?
                """,
                (current_id,),
            )
            successors = [row["successor_id"] for row in cursor.fetchall()]

            for succ_id in successors:
                all_successors.add(succ_id)
                if succ_id not in visited:
                    visited.add(succ_id)
                    queue.append(succ_id)

        return list(all_successors)
