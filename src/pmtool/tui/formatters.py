"""
TUI フォーマッター

ステータスの記号・色付けなど、共通のフォーマット処理を提供します。
"""


def get_entity_symbol(entity_type: str, use_emoji: bool = True) -> str:
    """
    エンティティタイプに応じた記号を取得

    Args:
        entity_type: エンティティタイプ（"project", "subproject", "task", "subtask", "tasks_direct"）
        use_emoji: 絵文字を使用するかどうか（デフォルト: True）

    Returns:
        記号文字列

    Examples:
        >>> get_entity_symbol("project")
        '📦'
        >>> get_entity_symbol("project", use_emoji=False)
        '[P]'
    """
    if use_emoji:
        symbol_map = {
            "project": "📦",
            "subproject": "📁",
            "task": "📝",
            "subtask": "✏️",
            "tasks_direct": "📝",
        }
    else:
        symbol_map = {
            "project": "[P]",
            "subproject": "[S]",
            "task": "[T]",
            "subtask": "[ST]",
            "tasks_direct": "[T]",
        }

    return symbol_map.get(entity_type, "[-]")


def format_status(status: str, use_emoji: bool = True) -> str:
    """
    ステータスを記号 + 色で表現

    Args:
        status: ステータス文字列（UNSET, NOT_STARTED, IN_PROGRESS, DONE）
        use_emoji: 絵文字を使用するかどうか（デフォルト: True）

    Returns:
        Richマークアップを含むステータス表示文字列

    Examples:
        >>> format_status("UNSET")
        '[dim][ ] UNSET[/dim]'
        >>> format_status("DONE")
        '[green][✓] DONE[/green]'
        >>> format_status("UNSET", use_emoji=False)
        '[dim][    ] UNSET[/dim]'
        >>> format_status("DONE", use_emoji=False)
        '[green][DONE] DONE[/green]'
    """
    if use_emoji:
        status_map = {
            "UNSET": "[dim][ ] UNSET[/dim]",
            "NOT_STARTED": "[blue][⏸] NOT_STARTED[/blue]",
            "IN_PROGRESS": "[yellow][▶] IN_PROGRESS[/yellow]",
            "DONE": "[green][✓] DONE[/green]",
        }
    else:
        status_map = {
            "UNSET": "[dim][    ] UNSET[/dim]",
            "NOT_STARTED": "[blue][TODO] NOT_STARTED[/blue]",
            "IN_PROGRESS": "[yellow][PROG] IN_PROGRESS[/yellow]",
            "DONE": "[green][DONE] DONE[/green]",
        }

    return status_map.get(status, f"[dim][?] {status}[/dim]")
