"""
validators層のテスト

入力バリデーションロジックを確認
"""

import pytest

from pmtool.validators import (
    validate_name,
    validate_description,
    validate_order_index,
)
from pmtool.exceptions import ValidationError


def test_validate_name_accepts_valid_name():
    """有効な名前が受け入れられること"""
    # 正常系
    validate_name("Valid Name")
    validate_name("Project 123")
    validate_name("プロジェクト名")  # 日本語
    validate_name("A" * 100)  # 長い名前


def test_validate_name_rejects_empty_string():
    """空文字列が拒否されること"""
    with pytest.raises(ValidationError) as exc_info:
        validate_name("")

    assert "空" in str(exc_info.value) or "empty" in str(exc_info.value).lower()


def test_validate_name_rejects_whitespace_only():
    """空白のみの文字列が拒否されること"""
    with pytest.raises(ValidationError):
        validate_name("   ")


def test_validate_name_rejects_none():
    """Noneが拒否されること"""
    with pytest.raises(ValidationError):
        validate_name(None)


def test_validate_name_rejects_too_long():
    """長すぎる名前が拒否されること（デフォルト256文字制限）"""
    # 257文字（制限を超える）
    long_name = "A" * 257

    with pytest.raises(ValidationError) as exc_info:
        validate_name(long_name)

    assert "最大値" in str(exc_info.value) or "超えています" in str(exc_info.value)


def test_validate_description_accepts_valid_description():
    """有効な説明が受け入れられること"""
    # 正常系
    validate_description("Valid description")
    validate_description("")  # 空文字列は許可（Noneに変換される）
    validate_description(None)  # Noneも許可（オプショナル）
    validate_description("詳細な説明です。\n複数行も可能。")


def test_validate_description_rejects_too_long():
    """長すぎる説明が拒否されること（デフォルト2000文字制限）"""
    # 2001文字（制限を超える）
    long_desc = "A" * 2001

    with pytest.raises(ValidationError):
        validate_description(long_desc)


def test_validate_order_index_accepts_valid_values():
    """有効なorder_indexが受け入れられること"""
    # 正常系
    validate_order_index(0)
    validate_order_index(1)
    validate_order_index(100)
    validate_order_index(999999)


def test_validate_order_index_rejects_negative():
    """負の値が拒否されること"""
    with pytest.raises(ValidationError) as exc_info:
        validate_order_index(-1)

    assert "0 以上" in str(exc_info.value)


def test_validate_order_index_rejects_none():
    """Noneが拒否されること"""
    with pytest.raises(ValidationError):
        validate_order_index(None)


def test_validate_order_index_rejects_non_integer():
    """整数以外が拒否されること"""
    with pytest.raises(ValidationError):
        validate_order_index("not an integer")

    with pytest.raises(ValidationError):
        validate_order_index(3.14)


def test_validate_name_strips_whitespace():
    """名前の前後の空白が除去されること"""
    result = validate_name("  Valid Name  ")
    assert result == "Valid Name"  # 前後の空白が除去される


def test_validate_description_strips_whitespace():
    """説明の前後の空白が除去されること"""
    result = validate_description("  Valid Description  ")
    assert result == "Valid Description"  # 前後の空白が除去される
