"""
フィールドバリデーション関数

このモジュールはPMToolエンティティのフィールド検証を行う関数を提供します。
すべてのCRUD操作で使用され、データの整合性を保証します。
"""

from .exceptions import ValidationError


def validate_name(name: str, max_length: int = 256) -> str:
    """
    name フィールドのバリデーションと正規化

    Args:
        name: 検証する名前
        max_length: 最大文字数 (デフォルト: 256)

    Returns:
        str: 正規化された名前 (前後の空白を削除)

    Raises:
        ValidationError: 名前が空、または最大長を超える場合
    """
    if not isinstance(name, str):
        raise ValidationError(f"name は文字列である必要があります: {type(name)}")

    # 前後の空白を削除
    normalized = name.strip()

    if not normalized:
        raise ValidationError("name は空であってはいけません")

    if len(normalized) > max_length:
        raise ValidationError(
            f"name の長さが最大値 {max_length} を超えています: {len(normalized)} 文字"
        )

    return normalized


def validate_description(description: str | None, max_length: int = 2000) -> str | None:
    """
    description フィールドのバリデーション

    Args:
        description: 検証する説明 (Noneも許可)
        max_length: 最大文字数 (デフォルト: 2000)

    Returns:
        str | None: 正規化された説明、またはNone

    Raises:
        ValidationError: 最大長を超える場合
    """
    if description is None:
        return None

    if not isinstance(description, str):
        raise ValidationError(f"description は文字列または None である必要があります: {type(description)}")

    # 前後の空白を削除 (空文字列の場合は None に変換)
    normalized = description.strip()
    if not normalized:
        return None

    if len(normalized) > max_length:
        raise ValidationError(
            f"description の長さが最大値 {max_length} を超えています: {len(normalized)} 文字"
        )

    return normalized


def validate_status(status: str) -> str:
    """
    status フィールドのバリデーション

    Args:
        status: 検証するステータス

    Returns:
        str: 検証済みステータス

    Raises:
        ValidationError: 不正なステータス値の場合
    """
    VALID_STATUSES = {"UNSET", "NOT_STARTED", "IN_PROGRESS", "DONE"}

    if not isinstance(status, str):
        raise ValidationError(f"status は文字列である必要があります: {type(status)}")

    if status not in VALID_STATUSES:
        raise ValidationError(
            f"不正な status 値: {status}. 有効な値: {', '.join(sorted(VALID_STATUSES))}"
        )

    return status


def validate_order_index(order_index: int) -> int:
    """
    order_index フィールドのバリデーション

    Args:
        order_index: 検証する順序インデックス

    Returns:
        int: 検証済み順序インデックス

    Raises:
        ValidationError: 負の値の場合
    """
    if not isinstance(order_index, int):
        raise ValidationError(f"order_index は整数である必要があります: {type(order_index)}")

    if order_index < 0:
        raise ValidationError(f"order_index は 0 以上である必要があります: {order_index}")

    return order_index
