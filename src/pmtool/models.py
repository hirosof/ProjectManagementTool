"""
ProjectManagementTool のデータモデル

このモジュールはPMToolシステムのすべてのエンティティ型を表すデータクラスを定義します。
これらのモデルはデータベースレコードの型安全な表現を提供します。
"""

from dataclasses import dataclass


@dataclass
class Project:
    """
    トップレベルのProjectを表す

    Attributes:
        id: 一意識別子 (DB挿入前の新規エンティティではNone)
        name: プロジェクト名 (グローバルで一意)
        description: プロジェクトの説明 (オプション)
        order_index: 表示順序 (0始まり、>= 0)
        created_at: 作成タイムスタンプ (ISO 8601 UTC)
        updated_at: 最終更新タイムスタンプ (ISO 8601 UTC)
    """
    id: int | None
    name: str
    description: str | None
    order_index: int
    created_at: str
    updated_at: str


@dataclass
class SubProject:
    """
    Project内のSubProjectを表す

    Attributes:
        id: 一意識別子 (新規エンティティではNone)
        project_id: 親プロジェクトID (projectsへのFK)
        parent_subproject_id: 親サブプロジェクトID (subprojectsへのFK、MVPでは常にNone)
        name: SubProject名 (親コンテキスト内で一意)
        description: 説明 (オプション)
        order_index: 親内での表示順序 (0始まり、>= 0)
        created_at: 作成タイムスタンプ (ISO 8601 UTC)
        updated_at: 最終更新タイムスタンプ (ISO 8601 UTC)
    """
    id: int | None
    project_id: int
    parent_subproject_id: int | None
    name: str
    description: str | None
    order_index: int
    created_at: str
    updated_at: str


@dataclass
class Task:
    """
    ProjectまたはSubProject内のTaskを表す

    Attributes:
        id: 一意識別子 (新規エンティティではNone)
        project_id: 親プロジェクトID (projectsへのFK)
        subproject_id: 親サブプロジェクトID (subprojectsへのFK、プロジェクト直下のタスクではNone)
        name: Task名 (親コンテキスト内で一意)
        description: 説明 (オプション)
        status: タスクステータス (UNSET, NOT_STARTED, IN_PROGRESS, DONE)
        order_index: 親内での表示順序 (0始まり、>= 0)
        created_at: 作成タイムスタンプ (ISO 8601 UTC)
        updated_at: 最終更新タイムスタンプ (ISO 8601 UTC)
    """
    id: int | None
    project_id: int
    subproject_id: int | None
    name: str
    description: str | None
    status: str
    order_index: int
    created_at: str
    updated_at: str


@dataclass
class SubTask:
    """
    Task内のSubTaskを表す

    Attributes:
        id: 一意識別子 (新規エンティティではNone)
        task_id: 親タスクID (tasksへのFK)
        name: SubTask名 (タスク内で一意)
        description: 説明 (オプション)
        status: サブタスクステータス (UNSET, NOT_STARTED, IN_PROGRESS, DONE)
        order_index: タスク内での表示順序 (0始まり、>= 0)
        created_at: 作成タイムスタンプ (ISO 8601 UTC)
        updated_at: 最終更新タイムスタンプ (ISO 8601 UTC)
    """
    id: int | None
    task_id: int
    name: str
    description: str | None
    status: str
    order_index: int
    created_at: str
    updated_at: str


@dataclass
class Dependency:
    """
    2つのノード間の依存関係を表す (TasksまたはSubTasks)

    これは終了-開始依存関係: 後続ノードは先行ノードがDONEになった後でのみ開始可能。
    task_dependenciesとsubtask_dependenciesは別テーブルとして存在します。

    Attributes:
        id: 一意識別子 (新規エンティティではNone)
        predecessor_id: 先行ノードのID
        successor_id: 後続ノードのID
        created_at: 作成タイムスタンプ (ISO 8601 UTC)
    """
    id: int | None
    predecessor_id: int
    successor_id: int
    created_at: str
