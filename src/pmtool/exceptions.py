"""
ProjectManagementTool のカスタム例外

このモジュールはPMToolアプリケーション全体で使用されるカスタム例外を定義します。
すべての例外はPMToolErrorを継承し、一貫したエラーハンドリングを提供します。
"""


class PMToolError(Exception):
    """PMTool関連のすべてのエラーの基底例外"""
    pass


class ValidationError(PMToolError):
    """入力バリデーションが失敗した場合に発生 (例: 不正な名前、説明)"""
    pass


class ConstraintViolationError(PMToolError):
    """データベースまたはビジネスロジックの制約に違反した場合に発生"""
    pass


class CyclicDependencyError(PMToolError):
    """依存関係の追加によってDAGに循環が生じる場合に発生"""
    pass


class StatusTransitionError(PMToolError):
    """ステータス遷移がビジネスルールに違反する場合に発生 (例: 前提条件なしのDONE遷移)"""
    pass


class DeletionError(PMToolError):
    """削除が許可されない場合に発生 (例: 子ノードが存在、依存関係が破壊される)"""
    pass
