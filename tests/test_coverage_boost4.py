"""
カバレッジ向上のための追加テスト4

80%達成のための最終プッシュ
- validators.py の未カバー型エラー分岐
- repository.py の未カバー分岐（get_by_parent, SubProject階層）
"""

import pytest
from pmtool.database import Database
from pmtool.repository import (
    ProjectRepository,
    SubProjectRepository,
    TaskRepository,
    SubTaskRepository,
)
from pmtool.validators import (
    validate_description,
    validate_status,
)
from pmtool.exceptions import ValidationError


# ========================================
# validators.py: 型エラー分岐
# ========================================

def test_validate_description_type_error():
    """validate_description: 文字列でない型はエラー"""
    with pytest.raises(ValidationError, match="文字列または None である必要があります"):
        validate_description(123)


def test_validate_status_type_error():
    """validate_status: 文字列でない型はエラー"""
    with pytest.raises(ValidationError, match="文字列である必要があります"):
        validate_status(123)


# ========================================
# repository.py: get_by_parent with subproject_id=None
# ========================================

def test_task_get_by_parent_with_none_subproject(temp_db: Database):
    """Task.get_by_parent: subproject_id=None で直下タスク取得"""
    proj_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)

    proj = proj_repo.create("Project", "Desc")

    # プロジェクト直下のタスク（subproject_id=None）
    task1 = task_repo.create(proj.id, "Task1", subproject_id=None, description="Desc1")
    task2 = task_repo.create(proj.id, "Task2", subproject_id=None, description="Desc2")

    # 取得
    tasks = task_repo.get_by_parent(proj.id, subproject_id=None)

    assert len(tasks) == 2
    assert tasks[0].id == task1.id
    assert tasks[1].id == task2.id


def test_task_get_by_parent_with_subproject_id(temp_db: Database):
    """Task.get_by_parent: subproject_id指定でSubProject配下タスク取得"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)

    proj = proj_repo.create("Project", "Desc")
    subproj = subproj_repo.create(proj.id, "SubProject", description="Desc")

    # SubProject配下のタスク
    task1 = task_repo.create(proj.id, "Task1", subproject_id=subproj.id, description="Desc1")
    task2 = task_repo.create(proj.id, "Task2", subproject_id=subproj.id, description="Desc2")

    # 取得
    tasks = task_repo.get_by_parent(proj.id, subproject_id=subproj.id)

    assert len(tasks) == 2


# ========================================
# repository.py: SubProjectの階層（parent_subproject_id）
# ========================================

def test_subproject_create_with_parent_subproject(temp_db: Database):
    """SubProject作成時にparent_subproject_id指定"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)

    proj = proj_repo.create("Project", "Desc")
    parent_subproj = subproj_repo.create(proj.id, "ParentSubProject", description="Desc")

    # 階層SubProject作成
    child_subproj = subproj_repo.create(
        proj.id, "ChildSubProject", parent_subproject_id=parent_subproj.id, description="Desc"
    )

    assert child_subproj.parent_subproject_id == parent_subproj.id


def test_subproject_get_by_project_with_children(temp_db: Database):
    """SubProject.get_by_project: 階層を含むSubProject取得"""
    proj_repo = ProjectRepository(temp_db)
    subproj_repo = SubProjectRepository(temp_db)

    proj = proj_repo.create("Project", "Desc")
    parent_subproj = subproj_repo.create(proj.id, "ParentSubProject", description="Desc")
    child_subproj = subproj_repo.create(
        proj.id, "ChildSubProject", parent_subproject_id=parent_subproj.id, description="Desc"
    )

    # プロジェクト配下の全SubProject取得
    all_subprojects = subproj_repo.get_by_project(proj.id)

    assert len(all_subprojects) >= 2
