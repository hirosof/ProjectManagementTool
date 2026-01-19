"""
commands.pyの簡易カバレッジテスト

最も簡単にカバーできるhandler関数を集中的にテスト
- handle_list
- handle_doctor
"""

from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest
from pmtool.database import Database
from pmtool.repository import ProjectRepository
from pmtool.tui import commands


class TestHandleList:
    """handle_list関数のテスト"""

    def test_handle_list_projects_empty(self, temp_db, monkeypatch):
        """プロジェクト一覧（空）"""
        # displayをモック
        mock_display = MagicMock()
        monkeypatch.setattr("pmtool.tui.commands.display.show_project_list", mock_display)

        args = Namespace(entity="projects", no_emoji=False)

        commands.handle_list(temp_db, args)

        # show_project_listが呼ばれたことを確認
        mock_display.assert_called_once()

    def test_handle_list_projects_with_data(self, temp_db, monkeypatch):
        """プロジェクト一覧（データあり）"""
        # テストデータ作成
        proj_repo = ProjectRepository(temp_db)
        proj_repo.create("Project1", "Desc1")
        proj_repo.create("Project2", "Desc2")

        # displayをモック
        mock_display = MagicMock()
        monkeypatch.setattr("pmtool.tui.commands.display.show_project_list", mock_display)

        args = Namespace(entity="projects", no_emoji=False)

        commands.handle_list(temp_db, args)

        # show_project_listが呼ばれたことを確認
        mock_display.assert_called_once()
        # 引数として2つのProjectが渡されたことを確認
        call_args = mock_display.call_args[0][0]
        assert len(call_args) == 2


class TestHandleDoctor:
    """handle_doctor関数のテスト"""

    def test_handle_doctor_empty_db(self, temp_db, monkeypatch):
        """doctor check（空DB）"""
        # displayをモック
        mock_display = MagicMock()
        monkeypatch.setattr("pmtool.tui.commands.display.show_doctor_report", mock_display)

        args = Namespace()

        commands.handle_doctor(temp_db, args)

        # show_doctor_reportが呼ばれたことを確認
        mock_display.assert_called_once()

    def test_handle_doctor_with_data(self, temp_db, monkeypatch):
        """doctor check（データあり）"""
        # テストデータ作成
        proj_repo = ProjectRepository(temp_db)
        proj_repo.create("Project1", "Desc1")

        # displayをモック
        mock_display = MagicMock()
        monkeypatch.setattr("pmtool.tui.commands.display.show_doctor_report", mock_display)

        args = Namespace()

        commands.handle_doctor(temp_db, args)

        # show_doctor_reportが呼ばれたことを確認
        mock_display.assert_called_once()
