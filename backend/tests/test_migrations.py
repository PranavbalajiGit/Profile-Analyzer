from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_alembic_offline_upgrade_renders_sql() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "alembic.ini",
            "upgrade",
            "head",
            "--sql",
        ],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        env={
            **os.environ,
            "ENVIRONMENT": "test",
            "LOG_JSON": "false",
            "LOG_LEVEL": "WARNING",
        },
    )

    assert result.returncode == 0, result.stderr
    assert "CREATE EXTENSION IF NOT EXISTS pgcrypto" in result.stdout
