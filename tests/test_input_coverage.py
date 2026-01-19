"""
input.py カバレッジ向上テスト

ChatGPT Review4フィードバックに基づき、input.pyの各関数をモックでテスト
- prompt_toolkit の入力処理をモック
- 正常入力、空入力、必須チェックの分岐を踏む
"""

from unittest.mock import MagicMock, patch

import pytest
from pmtool.tui.input import prompt_text, prompt_int, confirm, IntegerValidator
from prompt_toolkit.validation import ValidationError as PromptValidationError


# ========================================
# prompt_text のテスト
# ========================================

class TestPromptText:
    """prompt_text関数のテスト"""

    def test_prompt_text_required_with_input(self, monkeypatch):
        """必須入力で値を入力"""
        # promptをモック
        monkeypatch.setattr("pmtool.tui.input.prompt", lambda msg: "TestInput")

        result = prompt_text("Enter name", required=True)
        assert result == "TestInput"

    def test_prompt_text_required_empty_retry(self, monkeypatch):
        """必須入力で空 → リトライ → 入力"""
        call_count = 0

        def mock_prompt(msg):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ""  # 最初は空
            return "TestInput"  # 2回目で入力

        monkeypatch.setattr("pmtool.tui.input.prompt", mock_prompt)

        # printをモック（エラーメッセージ出力確認用）
        mock_print = MagicMock()
        monkeypatch.setattr("builtins.print", mock_print)

        result = prompt_text("Enter name", required=True)
        assert result == "TestInput"
        # エラーメッセージが出力されたことを確認
        assert mock_print.called

    def test_prompt_text_optional_with_input(self, monkeypatch):
        """オプション入力で値を入力"""
        monkeypatch.setattr("pmtool.tui.input.prompt", lambda msg: "TestInput")

        result = prompt_text("Enter description", required=False)
        assert result == "TestInput"

    def test_prompt_text_optional_empty_returns_none(self, monkeypatch):
        """オプション入力で空 → None返却"""
        monkeypatch.setattr("pmtool.tui.input.prompt", lambda msg: "")

        result = prompt_text("Enter description", required=False)
        assert result is None


# ========================================
# prompt_int のテスト
# ========================================

class TestPromptInt:
    """prompt_int関数のテスト"""

    def test_prompt_int_required_with_valid_input(self, monkeypatch):
        """必須入力で正しい整数を入力"""
        monkeypatch.setattr("pmtool.tui.input.prompt", lambda msg, validator=None: "123")

        result = prompt_int("Enter ID", required=True)
        assert result == 123

    def test_prompt_int_optional_with_valid_input(self, monkeypatch):
        """オプション入力で正しい整数を入力"""
        monkeypatch.setattr("pmtool.tui.input.prompt", lambda msg, validator=None: "456")

        result = prompt_int("Enter ID", required=False)
        assert result == 456

    def test_prompt_int_optional_empty_returns_none(self, monkeypatch):
        """オプション入力で空 → None返却"""
        monkeypatch.setattr("pmtool.tui.input.prompt", lambda msg, validator=None: "")

        result = prompt_int("Enter ID", required=False)
        assert result is None


# ========================================
# confirm のテスト
# ========================================

class TestConfirm:
    """confirm関数のテスト"""

    def test_confirm_yes_input(self, monkeypatch):
        """Yes入力"""
        monkeypatch.setattr("pmtool.tui.input.prompt", lambda msg: "y")

        result = confirm("Are you sure?", default=False)
        assert result is True

    def test_confirm_yes_uppercase_input(self, monkeypatch):
        """YES入力（大文字）"""
        monkeypatch.setattr("pmtool.tui.input.prompt", lambda msg: "YES")

        result = confirm("Are you sure?", default=False)
        assert result is True

    def test_confirm_no_input(self, monkeypatch):
        """No入力"""
        monkeypatch.setattr("pmtool.tui.input.prompt", lambda msg: "n")

        result = confirm("Are you sure?", default=True)
        assert result is False

    def test_confirm_empty_default_true(self, monkeypatch):
        """空入力でデフォルトTrue"""
        monkeypatch.setattr("pmtool.tui.input.prompt", lambda msg: "")

        result = confirm("Are you sure?", default=True)
        assert result is True

    def test_confirm_empty_default_false(self, monkeypatch):
        """空入力でデフォルトFalse"""
        monkeypatch.setattr("pmtool.tui.input.prompt", lambda msg: "")

        result = confirm("Are you sure?", default=False)
        assert result is False

    def test_confirm_other_input_returns_false(self, monkeypatch):
        """その他の入力はFalse"""
        monkeypatch.setattr("pmtool.tui.input.prompt", lambda msg: "invalid")

        result = confirm("Are you sure?", default=False)
        assert result is False


# ========================================
# IntegerValidator のテスト
# ========================================

class TestIntegerValidator:
    """IntegerValidator のテスト"""

    def test_integer_validator_valid_input(self):
        """正しい整数入力"""
        validator = IntegerValidator()

        # Documentモック
        class MockDocument:
            def __init__(self, text):
                self.text = text

        doc = MockDocument("123")

        # エラーなし（例外が発生しないことを確認）
        validator.validate(doc)

    def test_integer_validator_invalid_input(self):
        """不正な入力（非整数）"""
        validator = IntegerValidator()

        # Documentモック
        class MockDocument:
            def __init__(self, text):
                self.text = text

        doc = MockDocument("abc")

        # ValidationErrorが発生することを確認
        with pytest.raises(PromptValidationError):
            validator.validate(doc)

    def test_integer_validator_empty_input(self):
        """空入力（エラーなし）"""
        validator = IntegerValidator()

        # Documentモック
        class MockDocument:
            def __init__(self, text):
                self.text = text

        doc = MockDocument("")

        # エラーなし（空文字列はvalidate通過）
        validator.validate(doc)
