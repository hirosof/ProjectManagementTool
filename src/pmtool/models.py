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


# ============================================================
# Phase 5: テンプレート機能関連モデル
# ============================================================


@dataclass
class Template:
    """
    SubProjectテンプレートを表す (Phase 5)

    Attributes:
        id: 一意識別子 (新規エンティティではNone)
        name: テンプレート名 (グローバルで一意)
        description: テンプレートの説明 (オプション)
        include_tasks: Task/SubTask/依存関係を含むか (bool)
        created_at: 作成タイムスタンプ (ISO 8601 UTC)
        updated_at: 最終更新タイムスタンプ (ISO 8601 UTC)
    """
    id: int | None
    name: str
    description: str | None
    include_tasks: bool
    created_at: str
    updated_at: str


@dataclass
class TemplateTask:
    """
    テンプレート内のTaskを表す (Phase 5)

    Attributes:
        id: 一意識別子 (新規エンティティではNone)
        template_id: 親テンプレートID (templatesへのFK)
        task_order: テンプレート内での順序 (0始まり)
        name: Task名
        description: 説明 (オプション)
    """
    id: int | None
    template_id: int
    task_order: int
    name: str
    description: str | None


@dataclass
class TemplateSubTask:
    """
    テンプレート内のSubTaskを表す (Phase 5)

    Attributes:
        id: 一意識別子 (新規エンティティではNone)
        template_task_id: 親TemplateTaskID (template_tasksへのFK)
        subtask_order: Task内での順序 (0始まり)
        name: SubTask名
        description: 説明 (オプション)
    """
    id: int | None
    template_task_id: int
    subtask_order: int
    name: str
    description: str | None


@dataclass
class TemplateDependency:
    """
    テンプレート内のTask依存関係を表す (Phase 5)

    Attributes:
        id: 一意識別子 (新規エンティティではNone)
        template_id: 親テンプレートID (templatesへのFK)
        predecessor_order: 先行Taskのtask_order
        successor_order: 後続Taskのtask_order
    """
    id: int | None
    template_id: int
    predecessor_order: int
    successor_order: int


@dataclass
class ExternalDependencyWarning:
    """
    外部依存警告情報 (Phase 5)

    SubProject配下のTaskが、SubProject外のTaskに依存している場合の警告情報。

    Attributes:
        from_task_id: 依存元TaskのID
        to_task_id: 依存先TaskのID
        from_task_name: 依存元Task名
        to_task_name: 依存先Task名
        direction: 依存方向 ('outgoing': 外部への依存, 'incoming': 外部からの依存)
    """
    from_task_id: int
    to_task_id: int
    from_task_name: str
    to_task_name: str
    direction: str  # 'outgoing' or 'incoming'


@dataclass
class SaveTemplateResult:
    """
    save_template() の戻り値 (Phase 5)

    Attributes:
        template: 保存されたTemplateエンティティ
        external_dependencies: 外部依存警告のリスト
    """
    template: Template
    external_dependencies: list[ExternalDependencyWarning]

    @property
    def has_warnings(self) -> bool:
        """外部依存警告が存在するか"""
        return len(self.external_dependencies) > 0
