"""
ProjectManagementTool のカスタム例外

このモジュールはPMToolアプリケーション全体で使用されるカスタム例外を定義します。
すべての例外はPMToolErrorを継承し、一貫したエラーハンドリングを提供します。
"""

from enum import Enum
from typing import Optional


class PMToolError(Exception):
    """PMTool関連のすべてのエラーの基底例外"""
    pass


class ValidationError(PMToolError):
    """入力バリデーションが失敗した場合に発生 (例: 不正な名前、説明)"""
    pass


class EntityNotFoundError(PMToolError):
    """エンティティが見つからない場合に発生 (例: 存在しないIDへのアクセス)"""
    pass


class ConstraintViolationError(PMToolError):
    """データベースまたはビジネスロジックの制約に違反した場合に発生"""
    pass


class CyclicDependencyError(PMToolError):
    """依存関係の追加によってDAGに循環が生じる場合に発生"""
    pass


class StatusTransitionFailureReason(Enum):
    """ステータス遷移失敗の理由コード"""

    PREREQUISITE_NOT_DONE = "prerequisite_not_done"
    """先行ノード（依存関係のpredecessor）が未完了"""

    CHILD_NOT_DONE = "child_not_done"
    """子ノード（SubTask）が未完了"""

    NODE_NOT_FOUND = "node_not_found"
    """対象ノードが存在しない"""

    INVALID_STATUS = "invalid_status"
    """無効なステータス値"""

    INVALID_NODE_TYPE = "invalid_node_type"
    """無効なノードタイプ"""

    INVALID_TRANSITION = "invalid_transition"
    """無効な遷移（その他の理由）"""


class StatusTransitionError(PMToolError):
    """
    ステータス遷移がビジネスルールに違反する場合に発生

    Phase 3 以降では reason code を持つようになり、エラー理由を構造化して管理します。
    """

    def __init__(
        self,
        message: str,
        reason: Optional[StatusTransitionFailureReason] = None,
        details: Optional[dict] = None,
    ):
        """
        Args:
            message: エラーメッセージ
            reason: 失敗理由コード（Phase 3 以降で使用）
            details: 追加の詳細情報（例: 未完了のノードIDリスト）
        """
        super().__init__(message)
        self.reason = reason
        self.details = details or {}


class DeletionFailureReason(Enum):
    """削除失敗の理由コード"""

    CHILD_EXISTS = "child_exists"
    """子エンティティが存在するため削除不可"""

    DEPENDENCY_EXISTS = "dependency_exists"
    """依存関係が存在するため削除不可"""

    NOT_FOUND = "not_found"
    """削除対象が存在しない"""

    OTHER = "other"
    """その他の理由"""


class DeletionError(PMToolError):
    """
    削除が許可されない場合に発生 (例: 子ノードが存在、依存関係が破壊される)

    Phase 3 以降では reason code を持つようになり、エラー理由を構造化して管理します。
    """

    def __init__(
        self,
        message: str,
        reason: Optional[DeletionFailureReason] = None,
        details: Optional[dict] = None,
    ):
        """
        Args:
            message: エラーメッセージ
            reason: 失敗理由コード（Phase 3 以降で使用）
            details: 追加の詳細情報（例: 子エンティティの件数）
        """
        super().__init__(message)
        self.reason = reason
        self.details = details or {}
