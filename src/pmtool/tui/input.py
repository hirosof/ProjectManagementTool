"""
TUI 入力処理

prompt_toolkit を使った対話的入力処理を提供します。
"""

from prompt_toolkit import prompt
from prompt_toolkit.validation import ValidationError, Validator


class IntegerValidator(Validator):
    """整数入力のバリデータ"""

    def validate(self, document):
        text = document.text
        if text and not text.isdigit():
            raise ValidationError(message="整数を入力してください。")


def prompt_text(prompt_msg: str, required: bool = True) -> str | None:
    """
    テキスト入力プロンプト

    Args:
        prompt_msg: プロンプトメッセージ
        required: 必須入力かどうか

    Returns:
        入力されたテキスト、またはNone（オプションで未入力の場合）
    """
    while True:
        result = prompt(f"{prompt_msg}: ")
        if result or not required:
            return result if result else None
        print("必須項目です。入力してください。")


def prompt_int(prompt_msg: str, required: bool = True) -> int | None:
    """
    整数入力プロンプト

    Args:
        prompt_msg: プロンプトメッセージ
        required: 必須入力かどうか

    Returns:
        入力された整数、またはNone
    """
    while True:
        result = prompt(
            f"{prompt_msg}: ", validator=IntegerValidator() if required else None
        )
        if result:
            return int(result)
        if not required:
            return None


def confirm(message: str, default: bool = False) -> bool:
    """
    確認プロンプト（Yes/No）

    Args:
        message: 確認メッセージ
        default: デフォルト値（Enterのみの場合）

    Returns:
        True: Yes, False: No
    """
    default_str = "Y/n" if default else "y/N"
    result = prompt(f"{message} ({default_str}): ")

    if not result:
        return default

    return result.lower() in ("y", "yes")
