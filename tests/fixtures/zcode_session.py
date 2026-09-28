#!/usr/bin/env python3
"""Build a ZCode cli/db/db.sqlite fixture. The sqlite file is the primary store."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


WIDGET_ID = "zcode-session-widget"
GADGET_ID = "zcode-session-gadget"
CHILD_ID = "zcode-session-child"
OTHER_ID = "zcode-session-other"


def _insert_session(
    database: sqlite3.Connection,
    *,
    session_id: str,
    directory: str,
    title: str,
    task_type: str,
    created: int,
    updated: int,
) -> None:
    database.execute(
        """
        INSERT INTO session (
          id, project_id, parent_id, slug, directory, title, version,
          time_created, time_updated, task_type
        ) VALUES (?, ?, NULL, ?, ?, ?, '1', ?, ?, ?)
        """,
        (session_id, "fixture-project", session_id, directory, title, created, updated, task_type),
    )


def _insert_message(
    database: sqlite3.Connection,
    *,
    message_id: str,
    session_id: str,
    created: int,
    payload: dict[str, object],
    parts: list[tuple[str, dict[str, object]]],
) -> None:
    database.execute(
        "INSERT INTO message (id, session_id, time_created, time_updated, data) VALUES (?, ?, ?, ?, ?)",
        (message_id, session_id, created, created, json.dumps(payload)),
    )
    for index, (part_id, part) in enumerate(parts):
        database.execute(
            """
            INSERT INTO part (id, message_id, session_id, time_created, time_updated, data)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (part_id, message_id, session_id, created + index, created + index, json.dumps(part)),
        )


def build(home: Path, cwd: Path, other_cwd: Path) -> Path:
    database_path = home / "cli" / "db" / "db.sqlite"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()
    connection = sqlite3.connect(database_path)
    try:
        connection.executescript(
            """
            CREATE TABLE session (
              id TEXT PRIMARY KEY,
              project_id TEXT,
              parent_id TEXT,
              slug TEXT,
              directory TEXT NOT NULL,
              title TEXT,
              version TEXT,
              time_created INTEGER,
              time_updated INTEGER,
              task_type TEXT
            );
            CREATE TABLE message (
              id TEXT PRIMARY KEY,
              session_id TEXT NOT NULL,
              time_created INTEGER,
              time_updated INTEGER,
              data TEXT NOT NULL
            );
            CREATE TABLE part (
              id TEXT PRIMARY KEY,
              message_id TEXT NOT NULL,
              session_id TEXT NOT NULL,
              time_created INTEGER,
              time_updated INTEGER,
              data TEXT NOT NULL
            );
            """
        )
        cwd_text = str(cwd)
        other_text = str(other_cwd)
        _insert_session(
            connection,
            session_id=WIDGET_ID,
            directory=cwd_text,
            title="Continue the ZCode widget",
            task_type="interactive",
            created=1_755_648_000_000,
            updated=1_755_648_120_000,
        )
        _insert_message(
            connection,
            message_id="widget-user",
            session_id=WIDGET_ID,
            created=1_755_648_000_000,
            payload={"role": "user"},
            parts=[("widget-user-text", {"type": "text", "text": "Continue the ZCode fixture."})],
        )
        _insert_message(
            connection,
            message_id="widget-assistant",
            session_id=WIDGET_ID,
            created=1_755_648_060_000,
            payload={"role": "assistant", "modelID": "glm-4.6", "providerID": "zai"},
            parts=[
                ("widget-reasoning", {"type": "reasoning", "text": "ZCODE_PRIVATE_REASONING"}),
                ("widget-text", {"type": "text", "text": "Prepared the ZCode change."}),
                (
                    "widget-tool",
                    {
                        "type": "tool",
                        "callID": "zcode-call-1",
                        "tool": "bash",
                        "state": {
                            "status": "completed",
                            "input": {"command": "pnpm test"},
                            "output": "zcode focused tests passed",
                        },
                    },
                ),
            ],
        )
        _insert_message(
            connection,
            message_id="widget-summary",
            session_id=WIDGET_ID,
            created=1_755_648_120_000,
            payload={"role": "assistant", "modelID": "glm-4.6"},
            parts=[
                (
                    "widget-compaction",
                    {
                        "type": "compaction",
                        "tail_start_id": "widget-user",
                        "compactBoundary": {"start": "widget-user"},
                        "summary": "Compacted the ZCode fixture.",
                    },
                ),
                ("widget-summary-text", {"type": "text", "text": "Summary after compaction."}),
            ],
        )
        _insert_session(
            connection,
            session_id=GADGET_ID,
            directory=cwd_text,
            title="Continue the ZCode gadget",
            task_type="interactive",
            created=1_755_648_400_000,
            updated=1_755_648_500_000,
        )
        _insert_message(
            connection,
            message_id="gadget-user",
            session_id=GADGET_ID,
            created=1_755_648_400_000,
            payload={"role": "user"},
            parts=[("gadget-user-text", {"type": "text", "text": "Gadget only."})],
        )
        _insert_message(
            connection,
            message_id="gadget-assistant",
            session_id=GADGET_ID,
            created=1_755_648_500_000,
            payload={"role": "assistant", "modelID": "glm-4.6"},
            parts=[("gadget-text", {"type": "text", "text": "Gadget reply."})],
        )
        _insert_session(
            connection,
            session_id=CHILD_ID,
            directory=cwd_text,
            title="ZCode subagent child",
            task_type="subagent_child",
            created=1_755_648_800_000,
            updated=1_755_648_900_000,
        )
        _insert_message(
            connection,
            message_id="child-user",
            session_id=CHILD_ID,
            created=1_755_648_800_000,
            payload={"role": "user"},
            parts=[("child-text", {"type": "text", "text": "ZCODE_SUBAGENT_CHILD"})],
        )
        _insert_session(
            connection,
            session_id=OTHER_ID,
            directory=other_text,
            title="Other workspace",
            task_type="interactive",
            created=1_755_649_000_000,
            updated=1_755_649_500_000,
        )
        _insert_message(
            connection,
            message_id="other-user",
            session_id=OTHER_ID,
            created=1_755_649_000_000,
            payload={"role": "user"},
            parts=[("other-text", {"type": "text", "text": "ZCODE_OTHER_WORKSPACE"})],
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
    other = (args.other_cwd.expanduser().resolve() if args.other_cwd else cwd / "other-workspace")
    cwd.mkdir(parents=True, exist_ok=True)
    other.mkdir(parents=True, exist_ok=True)
    print(build(args.home.expanduser().resolve(), cwd, other))


if __name__ == "__main__":
    main()
