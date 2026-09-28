#!/usr/bin/env python3
"""Build a plaintext Trae ModularData/ai-agent/database.db fixture."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


WIDGET_ID = "trae-session-widget"
GADGET_ID = "trae-session-gadget"
CHILD_ID = "trae-session-child"
OTHER_ID = "trae-session-other"


def _exec(database: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> None:
    database.execute(sql, params)


def build(home: Path, cwd: Path, other_cwd: Path) -> Path:
    database_path = home / "ModularData" / "ai-agent" / "database.db"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()
    connection = sqlite3.connect(database_path)
    try:
        connection.executescript(
            """
            CREATE TABLE project (
              id INTEGER PRIMARY KEY,
              project_id TEXT NOT NULL,
              name TEXT,
              absolute_path TEXT,
              created_at INTEGER,
              updated_at INTEGER,
              deleted_at INTEGER
            );
            CREATE TABLE session_project (
              id INTEGER PRIMARY KEY,
              project_id TEXT NOT NULL,
              session_id TEXT NOT NULL,
              created_at INTEGER
            );
            CREATE TABLE chat_session (
              id INTEGER PRIMARY KEY,
              session_id TEXT NOT NULL,
              project_id TEXT,
              created_at INTEGER,
              updated_at INTEGER,
              deleted_at INTEGER,
              session_type TEXT,
              session_title TEXT,
              hidden_status TEXT,
              work_mode TEXT
            );
            CREATE TABLE chat_message (
              id INTEGER PRIMARY KEY,
              session_id TEXT NOT NULL,
              message_id TEXT NOT NULL,
              message_type TEXT,
              message_role TEXT,
              message_index INTEGER,
              is_archived INTEGER,
              created_at INTEGER,
              updated_at INTEGER,
              deleted_at INTEGER
            );
            CREATE TABLE chat_message_chat (
              id INTEGER PRIMARY KEY,
              message_id TEXT NOT NULL,
              content TEXT,
              created_at INTEGER,
              updated_at INTEGER,
              deleted_at INTEGER
            );
            CREATE TABLE agent_run (
              id INTEGER PRIMARY KEY,
              agent_run_id TEXT NOT NULL,
              parent_run_id TEXT,
              session_id TEXT,
              created_at INTEGER,
              updated_at INTEGER
            );
            CREATE TABLE toolcall (
              id INTEGER PRIMARY KEY,
              toolcall_id TEXT NOT NULL,
              name TEXT,
              status TEXT,
              params TEXT,
              result TEXT,
              created_at INTEGER,
              updated_at INTEGER,
              agent_run_id TEXT
            );
            CREATE TABLE history_v2 (
              id INTEGER PRIMARY KEY,
              history_v2_id TEXT,
              session_id TEXT,
              message_id TEXT,
              messages TEXT,
              summary TEXT,
              micro_compacted INTEGER,
              summarized_above INTEGER,
              created_at INTEGER,
              updated_at INTEGER
            );
            """
        )
        cwd_text = str(cwd)
        other_text = str(other_cwd)
        _exec(
            connection,
            "INSERT INTO project (project_id, name, absolute_path, created_at, updated_at) VALUES (?,?,?,?,?)",
            ("proj-cwd", "fixture", cwd_text, 1_755_648_000_000, 1_755_648_500_000),
        )
        _exec(
            connection,
            "INSERT INTO project (project_id, name, absolute_path, created_at, updated_at) VALUES (?,?,?,?,?)",
            ("proj-other", "other", other_text, 1_755_649_000_000, 1_755_649_500_000),
        )

        def add_session(
            session_id: str,
            project_id: str,
            title: str,
            session_type: str,
            created: int,
            updated: int,
        ) -> None:
            _exec(
                connection,
                """
                INSERT INTO chat_session (
                  session_id, project_id, created_at, updated_at, session_type, session_title, hidden_status
                ) VALUES (?, ?, ?, ?, ?, ?, NULL)
                """,
                (session_id, project_id, created, updated, session_type, title),
            )
            _exec(
                connection,
                "INSERT INTO session_project (project_id, session_id, created_at) VALUES (?, ?, ?)",
                (project_id, session_id, created),
            )

        add_session(WIDGET_ID, "proj-cwd", "Continue the Trae widget", "interactive", 1_755_648_000_000, 1_755_648_120_000)
        add_session(GADGET_ID, "proj-cwd", "Continue the Trae gadget", "interactive", 1_755_648_400_000, 1_755_648_500_000)
        add_session(CHILD_ID, "proj-cwd", "Trae subagent child", "subagent_child", 1_755_648_800_000, 1_755_648_900_000)
        add_session(OTHER_ID, "proj-other", "Other workspace", "interactive", 1_755_649_000_000, 1_755_649_500_000)

        _exec(
            connection,
            """
            INSERT INTO chat_message (session_id, message_id, message_type, message_role, message_index, is_archived, created_at, updated_at)
            VALUES (?, ?, 'chat', 'user', 0, 0, ?, ?)
            """,
            (WIDGET_ID, "widget-user", 1_755_648_000_000, 1_755_648_000_000),
        )
        _exec(
            connection,
            "INSERT INTO chat_message_chat (message_id, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ("widget-user", "Continue the Trae fixture.", 1_755_648_000_000, 1_755_648_000_000),
        )
        _exec(
            connection,
            """
            INSERT INTO chat_message (session_id, message_id, message_type, message_role, message_index, is_archived, created_at, updated_at)
            VALUES (?, ?, 'chat', 'assistant', 1, 0, ?, ?)
            """,
            (WIDGET_ID, "widget-assistant", 1_755_648_060_000, 1_755_648_060_000),
        )
        _exec(
            connection,
            "INSERT INTO chat_message_chat (message_id, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (
                "widget-assistant",
                json.dumps(
                    [
                        {"type": "reasoning", "text": "TRAE_PRIVATE_REASONING"},
                        {"type": "text", "text": "Prepared the Trae change."},
                    ]
                ),
                1_755_648_060_000,
                1_755_648_060_000,
            ),
        )
        _exec(
            connection,
            "INSERT INTO agent_run (agent_run_id, parent_run_id, session_id, created_at, updated_at) VALUES (?, NULL, ?, ?, ?)",
            ("run-widget", WIDGET_ID, 1_755_648_070_000, 1_755_648_080_000),
        )
        _exec(
            connection,
            """
            INSERT INTO toolcall (toolcall_id, name, status, params, result, created_at, updated_at, agent_run_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "trae-call-1",
                "bash",
                "completed",
                json.dumps({"command": "pnpm test"}),
                "trae focused tests passed",
                1_755_648_080_000,
                1_755_648_080_000,
                "run-widget",
            ),
        )
        _exec(
            connection,
            """
            INSERT INTO history_v2 (history_v2_id, session_id, message_id, summary, micro_compacted, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            """,
            ("hist-widget", WIDGET_ID, "widget-assistant", "Compacted the Trae fixture.", 1_755_648_120_000, 1_755_648_120_000),
        )

        _exec(
            connection,
            """
            INSERT INTO chat_message (session_id, message_id, message_type, message_role, message_index, is_archived, created_at, updated_at)
            VALUES (?, ?, 'chat', 'user', 0, 0, ?, ?)
            """,
            (GADGET_ID, "gadget-user", 1_755_648_400_000, 1_755_648_400_000),
        )
        _exec(
            connection,
            "INSERT INTO chat_message_chat (message_id, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ("gadget-user", "Gadget only.", 1_755_648_400_000, 1_755_648_400_000),
        )
        _exec(
            connection,
            """
            INSERT INTO chat_message (session_id, message_id, message_type, message_role, message_index, is_archived, created_at, updated_at)
            VALUES (?, ?, 'chat', 'assistant', 1, 0, ?, ?)
            """,
            (GADGET_ID, "gadget-assistant", 1_755_648_500_000, 1_755_648_500_000),
        )
        _exec(
            connection,
            "INSERT INTO chat_message_chat (message_id, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ("gadget-assistant", "Gadget reply.", 1_755_648_500_000, 1_755_648_500_000),
        )

        _exec(
            connection,
            """
            INSERT INTO chat_message (session_id, message_id, message_type, message_role, message_index, is_archived, created_at, updated_at)
            VALUES (?, ?, 'chat', 'user', 0, 0, ?, ?)
            """,
            (CHILD_ID, "child-user", 1_755_648_800_000, 1_755_648_800_000),
        )
        _exec(
            connection,
            "INSERT INTO chat_message_chat (message_id, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ("child-user", "TRAE_SUBAGENT_CHILD", 1_755_648_800_000, 1_755_648_800_000),
        )

        _exec(
            connection,
            """
            INSERT INTO chat_message (session_id, message_id, message_type, message_role, message_index, is_archived, created_at, updated_at)
            VALUES (?, ?, 'chat', 'user', 0, 0, ?, ?)
            """,
            (OTHER_ID, "other-user", 1_755_649_000_000, 1_755_649_000_000),
        )
        _exec(
            connection,
            "INSERT INTO chat_message_chat (message_id, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ("other-user", "TRAE_OTHER_WORKSPACE", 1_755_649_000_000, 1_755_649_000_000),
        )
        connection.commit()
    finally:
        connection.close()
    return database_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", required=True, type=Path)
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--other-cwd", type=Path)
    args = parser.parse_args()
    cwd = args.cwd.expanduser().resolve()
    other = args.other_cwd.expanduser().resolve() if args.other_cwd else cwd / "other-workspace"
    cwd.mkdir(parents=True, exist_ok=True)
    other.mkdir(parents=True, exist_ok=True)
    print(build(args.home.expanduser().resolve(), cwd, other))


if __name__ == "__main__":
    main()
