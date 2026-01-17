"""
ProjectManagementTool セットアップスクリプト
"""

from setuptools import find_packages, setup

setup(
    name="pmtool",
    version="0.2.0",  # Phase 2
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "rich>=13.0.0",
        "prompt_toolkit>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "pmtool=pmtool.tui.cli:main",
        ],
    },
    python_requires=">=3.10",
    author="Claude Code",
    description="階層型プロジェクト管理ツール - DAG依存関係管理とステータス制御を備えたプロジェクト・タスク管理システム",
    keywords="project management task dependency dag",
)
