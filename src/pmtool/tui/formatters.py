"""
TUI フォーマッター

ステータスの記号・色付けなど、共通のフォーマット処理を提供します。
"""


def format_status(status: str) -> str:
    """
    ステータスを記号 + 色で表現

    Args:
        status: ステータス文字列（UNSET, NOT_STARTED, IN_PROGRESS, DONE）

    Returns:
        Richマークアップを含むステータス表示文字列

    Examples:
        >>> format_status("UNSET")
        '[dim][ ] UNSET[/dim]'
        >>> format_status("DONE")
        '[green][✓] DONE[/green]'
    """
    status_map = {
        "UNSET": "[dim][ ] UNSET[/dim]",
        "NOT_STARTED": "[blue][⏸] NOT_STARTED[/blue]",
        "IN_PROGRESS": "[yellow][▶] IN_PROGRESS[/yellow]",
        "DONE": "[green][✓] DONE[/green]",
    }

    return status_map.get(status, f"[dim][?] {status}[/dim]")
