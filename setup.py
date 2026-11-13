from setuptools import setup, find_packages

setup(
    name="saltice-agent",
    version="1.0.0",
    description="Saltice Autonomous Terminal Coding Assistant",
    packages=find_packages(),
    py_modules=[
        "main",
        "engine",
        "tools",
        "skills",
        "session_manager",
        "ui_validator",
        "providers",
        "caveman",
        "subagents",
        "context_manager",
        "artifacts",
        "hooks",
        "mcp_catalog",
        "cloudflare_platform",
        "token_monitor",
        "workflow"
    ],
    entry_points={
        "console_scripts": [
            "saltice=main:main",
        ],
    },
)
