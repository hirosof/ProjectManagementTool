"""
絵文字なし表示機能のテスト

--no-emoji オプションが正しく動作することを確認
"""

from pmtool.tui import formatters


def test_format_status_with_emoji():
    """デフォルト（絵文字あり）でformat_status()が正しく動作すること"""
    # UNSET
    result = formatters.format_status("UNSET")
    assert "[ ]" in result
    assert "UNSET" in result

    # NOT_STARTED
    result = formatters.format_status("NOT_STARTED")
    assert "⏸" in result
    assert "NOT_STARTED" in result

    # IN_PROGRESS
    result = formatters.format_status("IN_PROGRESS")
    assert "▶" in result
    assert "IN_PROGRESS" in result

    # DONE
    result = formatters.format_status("DONE")
    assert "✓" in result
    assert "DONE" in result


def test_format_status_without_emoji():
    """絵文字なし（use_emoji=False）でformat_status()が正しく動作すること"""
    # UNSET
    result = formatters.format_status("UNSET", use_emoji=False)
    assert "[    ]" in result
    assert "UNSET" in result
    # 絵文字が含まれていないこと
    assert "⏸" not in result
    assert "▶" not in result
    assert "✓" not in result

    # NOT_STARTED
    result = formatters.format_status("NOT_STARTED", use_emoji=False)
    assert "[TODO]" in result
    assert "NOT_STARTED" in result
    # 絵文字が含まれていないこと
    assert "⏸" not in result

    # IN_PROGRESS
    result = formatters.format_status("IN_PROGRESS", use_emoji=False)
    assert "[PROG]" in result
    assert "IN_PROGRESS" in result
    # 絵文字が含まれていないこと
    assert "▶" not in result

    # DONE
    result = formatters.format_status("DONE", use_emoji=False)
    assert "[DONE]" in result
    assert "DONE" in result
    # 絵文字が含まれていないこと
    assert "✓" not in result


def test_get_entity_symbol_with_emoji():
    """デフォルト（絵文字あり）でget_entity_symbol()が正しく動作すること"""
    assert formatters.get_entity_symbol("project") == "📦"
    assert formatters.get_entity_symbol("subproject") == "📁"
    assert formatters.get_entity_symbol("task") == "📝"
    assert formatters.get_entity_symbol("subtask") == "✏️"
    assert formatters.get_entity_symbol("tasks_direct") == "📝"


def test_get_entity_symbol_without_emoji():
    """絵文字なし（use_emoji=False）でget_entity_symbol()が正しく動作すること"""
    assert formatters.get_entity_symbol("project", use_emoji=False) == "[P]"
    assert formatters.get_entity_symbol("subproject", use_emoji=False) == "[S]"
    assert formatters.get_entity_symbol("task", use_emoji=False) == "[T]"
    assert formatters.get_entity_symbol("subtask", use_emoji=False) == "[ST]"
    assert formatters.get_entity_symbol("tasks_direct", use_emoji=False) == "[T]"


def test_get_entity_symbol_unknown_type():
    """未定義のエンティティタイプでも正しくデフォルト記号を返すこと"""
    assert formatters.get_entity_symbol("unknown") == "[-]"
    assert formatters.get_entity_symbol("unknown", use_emoji=False) == "[-]"
