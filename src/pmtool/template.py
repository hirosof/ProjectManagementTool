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
