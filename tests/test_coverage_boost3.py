"""
カバレッジ向上のための追加テスト3

80%達成のための集中カバレッジ向上
- repository.py の get_all (Projectのみ)
- repository.py の update正常系
"""

import pytest
from pmtool.database import Database
from pmtool.repository import (
    ProjectRepository,
    SubProjectRepository,
    TaskRepository,
    SubTaskRepository,
)


# ========================================
# repository.py: get_all系テスト
# ========================================

def test_project_get_all(temp_db: Database):
    """Project.get_all - 全プロジェクト取得"""
    repo = ProjectRepository(temp_db)

    # プロジェクトを複数作成
    proj1 = repo.create("Project1", "Desc1")
    proj2 = repo.create("Project2", "Desc2")
    proj3 = repo.create("Project3", "Desc3")

    # 全取得
    all_projects = repo.get_all()

    assert len(all_projects) == 3
    assert all_projects[0].id == proj1.id
    assert all_projects[1].id == proj2.id
    assert all_projects[2].id == proj3.id


# ========================================
# repository.py: update系正常ケース
# ========================================

def test_project_update_name_only(temp_db: Database):
    """Project名のみ更新"""
    repo = ProjectRepository(temp_db)

    proj = repo.create("Project", "Desc")

    updated = repo.update(proj.id, name="New Name")

    assert updated.name == "New Name"
    assert updated.description == "Desc"


def test_project_update_description_only(temp_db: Database):
    """Project説明のみ更新"""
    repo = ProjectRepository(temp_db)

    proj = repo.create("Project", "Desc")

    updated = repo.update(proj.id, description="New Desc")

    assert updated.name == "Project"
    assert updated.description == "New Desc"


def test_subproject_update_name_and_description(temp_db: Database):
    """SubProject名と説明を更新"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)

    proj = proj_repo.create("Project", "Desc")
    subproj = subproj_repo.create(proj.id, "SubProject", description="Desc")

    updated = subproj_repo.update(subproj.id, name="New Name", description="New Desc")

    assert updated.name == "New Name"
    assert updated.description == "New Desc"


def test_task_update_name_and_description(temp_db: Database):
    """Task名と説明を更新"""
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)

    proj = proj_repo.create("Project", "Desc")
    task = task_repo.create(proj.id, "Task", description="Desc")

    updated = task_repo.update(task.id, name="New Name", description="New Desc")

    assert updated.name == "New Name"
    assert updated.description == "New Desc"


def test_subtask_update_name_and_description(temp_db: Database):
    """SubTask名と説明を更新"""
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    subtask_repo = SubTaskRepository(temp_db)

    proj = proj_repo.create("Project", "Desc")
    task = task_repo.create(proj.id, "Task", description="Desc")
    subtask = subtask_repo.create(task.id, "SubTask", "Desc")

    updated = subtask_repo.update(subtask.id, name="New Name", description="New Desc")

    assert updated.name == "New Name"
    assert updated.description == "New Desc"
