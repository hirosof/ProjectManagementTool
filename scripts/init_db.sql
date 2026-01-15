-- プロジェクト管理ツール DB初期化スクリプト
-- Phase 0: 基盤構築
-- DB設計書 v2.1 準拠

-- 外部キー制約を有効化
PRAGMA foreign_keys = ON;

-- ============================================================
-- スキーマバージョン管理
-- ============================================================

CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 初期バージョン挿入
INSERT INTO schema_version (version) VALUES (1);

-- ============================================================
-- projects テーブル
-- ============================================================

CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    order_index INTEGER NOT NULL CHECK(order_index >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_projects_order ON projects(order_index);

-- ============================================================
-- subprojects テーブル
-- ============================================================

CREATE TABLE subprojects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    parent_subproject_id INTEGER DEFAULT NULL,
    name TEXT NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL CHECK(order_index >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    FOREIGN KEY (parent_subproject_id) REFERENCES subprojects(id) ON DELETE RESTRICT
);

-- 部分UNIQUEインデックス（UNIQUE + NULL 問題対応）
-- Project直下のSubProject（parent_subproject_id = NULL）
CREATE UNIQUE INDEX idx_subprojects_unique_project_direct
    ON subprojects(project_id, name)
    WHERE parent_subproject_id IS NULL;

-- 入れ子SubProject（parent_subproject_id IS NOT NULL）
CREATE UNIQUE INDEX idx_subprojects_unique_nested
    ON subprojects(project_id, parent_subproject_id, name)
    WHERE parent_subproject_id IS NOT NULL;

CREATE INDEX idx_subprojects_project ON subprojects(project_id);
CREATE INDEX idx_subprojects_parent ON subprojects(parent_subproject_id);
CREATE INDEX idx_subprojects_order ON subprojects(project_id, parent_subproject_id, order_index);

-- ============================================================
-- tasks テーブル
-- ============================================================

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    subproject_id INTEGER DEFAULT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'UNSET',
    order_index INTEGER NOT NULL CHECK(order_index >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    FOREIGN KEY (subproject_id) REFERENCES subprojects(id) ON DELETE RESTRICT,
    CHECK(status IN ('UNSET', 'NOT_STARTED', 'IN_PROGRESS', 'DONE'))
);

-- 部分UNIQUEインデックス（UNIQUE + NULL 問題対応）
-- Project直下のTask（subproject_id = NULL）
CREATE UNIQUE INDEX idx_tasks_unique_project_direct
    ON tasks(project_id, name)
    WHERE subproject_id IS NULL;

-- SubProject配下のTask（subproject_id IS NOT NULL）
CREATE UNIQUE INDEX idx_tasks_unique_subproject
    ON tasks(project_id, subproject_id, name)
    WHERE subproject_id IS NOT NULL;

CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_subproject ON tasks(subproject_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_order ON tasks(project_id, subproject_id, order_index);

-- ============================================================
-- subtasks テーブル
-- ============================================================

CREATE TABLE subtasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'UNSET',
    order_index INTEGER NOT NULL CHECK(order_index >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE RESTRICT,
    UNIQUE(task_id, name),
    CHECK(status IN ('UNSET', 'NOT_STARTED', 'IN_PROGRESS', 'DONE'))
);

CREATE INDEX idx_subtasks_task ON subtasks(task_id);
CREATE INDEX idx_subtasks_status ON subtasks(status);
CREATE INDEX idx_subtasks_order ON subtasks(task_id, order_index);

-- ============================================================
-- task_dependencies テーブル
-- ============================================================

CREATE TABLE task_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    predecessor_id INTEGER NOT NULL,
    successor_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (predecessor_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (successor_id) REFERENCES tasks(id) ON DELETE CASCADE,
    UNIQUE(predecessor_id, successor_id),
    CHECK(predecessor_id != successor_id)
);

CREATE INDEX idx_task_deps_predecessor ON task_dependencies(predecessor_id);
CREATE INDEX idx_task_deps_successor ON task_dependencies(successor_id);

-- ============================================================
-- subtask_dependencies テーブル
-- ============================================================

CREATE TABLE subtask_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    predecessor_id INTEGER NOT NULL,
    successor_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (predecessor_id) REFERENCES subtasks(id) ON DELETE CASCADE,
    FOREIGN KEY (successor_id) REFERENCES subtasks(id) ON DELETE CASCADE,
    UNIQUE(predecessor_id, successor_id),
    CHECK(predecessor_id != successor_id)
);

CREATE INDEX idx_subtask_deps_predecessor ON subtask_dependencies(predecessor_id);
CREATE INDEX idx_subtask_deps_successor ON subtask_dependencies(successor_id);

-- ============================================================
-- 初期化完了
-- ============================================================
