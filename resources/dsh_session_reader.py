#!/usr/bin/env python3
"""Extend Grok's foreign-session reader with inert Grok and Pi adapters."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

import session_reader as core

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


EXTENDED_TOOLS = ("grok", "pi")
TOOLS = (*core.TOOLS, *EXTENDED_TOOLS)


def _canonical_cwd(value: str) -> str:
    return str(Path(value).expanduser().resolve(strict=False))


def _absolute_cwd(value: str) -> str:
    return os.path.abspath(os.path.expanduser(value))


def _same_cwd(left: Any, right: str) -> bool:
    if not isinstance(left, str):
        return False
    return (
        _absolute_cwd(left) == _absolute_cwd(right)
        or _canonical_cwd(left) == _canonical_cwd(right)
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError) as exc:
        raise core.ReaderError(f"failed to read session metadata {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise core.ReaderError(f"session metadata is not a JSON object: {path}")
    return value


def _read_json_optional(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _as_iso(value: Any) -> str | None:
    return core._iso_from_millis(core._timestamp_to_millis(value))


def _max_mtime(paths: Iterable[Path]) -> int:
    return max((core._mtime_millis(path) for path in paths), default=0)


def _bounded_text(value: Any, limit: int) -> str:
    text = core._safe_text(value)
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _append_text_turn(turns: list[dict[str, Any]], role: str, value: Any) -> None:
    text = core._safe_text(value)
    if not text:
        return
    if (
        turns
        and turns[-1].get("role") == role
        and not turns[-1].get("tool_calls")
        and not turns[-1].get("tool_results")
    ):
        existing = core._safe_text(turns[-1].get("text"))
        turns[-1]["text"] = existing + text
        return
    turns.append(core._turn(role, text=text))


class ProviderAdapter:
    tool: str

    def discover(self, cwd: str, within_min: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    def candidate_from_path(self, raw_path: str, cwd: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def find_id(self, session_id: str, cwd: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def read(self, candidate: dict[str, Any], max_tool_chars: int) -> dict[str, Any]:
        raise NotImplementedError


class GrokAdapter(ProviderAdapter):
    tool = "grok"

    @staticmethod
    def _home() -> Path:
        configured = os.environ.get("GROK_HOME")
        return Path(configured).expanduser() if configured else Path.home() / ".grok"

    @classmethod
    def _root(cls) -> Path:
        return cls._home() / "sessions"

    @staticmethod
    def _workspace_names(cwd: str) -> list[str]:
        raw = str(Path(cwd).expanduser())
        absolute = _absolute_cwd(cwd)
        canonical = _canonical_cwd(cwd)
        return list(
            dict.fromkeys(quote(value, safe="") for value in (raw, absolute, canonical))
        )

    @classmethod
    def _session_dirs_for_cwd(cls, cwd: str) -> Iterable[Path]:
        root = cls._root()
        seen: set[Path] = set()
        for name in cls._workspace_names(cwd):
            workspace = root / name
            if not workspace.is_dir() or workspace.is_symlink():
                continue
            for session_dir in sorted(workspace.iterdir(), key=lambda path: path.name):
                if session_dir.is_dir() and not session_dir.is_symlink() and session_dir not in seen:
                    seen.add(session_dir)
                    yield session_dir

        # Older or alternate Grok builds may encode a non-canonical spelling.
        # Metadata remains the authority and keeps fallback discovery cwd-scoped.
        if seen or not root.is_dir() or root.is_symlink():
            return
        for workspace in sorted(root.iterdir(), key=lambda path: path.name):
            if not workspace.is_dir() or workspace.is_symlink():
                continue
            for session_dir in sorted(workspace.iterdir(), key=lambda path: path.name):
                if not session_dir.is_dir() or session_dir.is_symlink():
                    continue
                candidate = cls._candidate_from_dir(session_dir, cwd, require_cwd=True)
                if candidate is not None:
                    yield session_dir

    @classmethod
    def _all_session_dirs(cls) -> Iterable[Path]:
        root = cls._root()
        if not root.is_dir() or root.is_symlink():
            return
        for workspace in sorted(root.iterdir(), key=lambda path: path.name):
            if not workspace.is_dir() or workspace.is_symlink():
                continue
            for session_dir in sorted(workspace.iterdir(), key=lambda path: path.name):
                if session_dir.is_dir() and not session_dir.is_symlink():
                    yield session_dir

    @classmethod
    def _candidate_from_dir(
        cls,
        session_dir: Path,
        cwd: str,
        *,
        require_cwd: bool,
    ) -> dict[str, Any] | None:
        summary_path = session_dir / "summary.json"
        updates_path = session_dir / "updates.jsonl"
        if (
            not summary_path.is_file()
            or summary_path.is_symlink()
            or not updates_path.is_file()
            or updates_path.is_symlink()
        ):
            return None
        summary = _read_json_optional(summary_path)
        if summary is None:
            return None
        info = summary.get("info") if isinstance(summary.get("info"), dict) else {}
        actual_cwd = info.get("cwd") if isinstance(info.get("cwd"), str) else None
        if require_cwd and not _same_cwd(actual_cwd, cwd):
            return None
        session_id = info.get("id") if isinstance(info.get("id"), str) else session_dir.name
        updated_ms = (
            core._timestamp_to_millis(summary.get("last_active_at"))
            or core._timestamp_to_millis(summary.get("updated_at"))
            or _max_mtime((updates_path, summary_path, session_dir))
        )
        created_ms = core._timestamp_to_millis(summary.get("created_at"))
        title = summary.get("generated_title") or summary.get("session_summary")
        return {
            "tool": "grok",
            "source": "grok",
            "session_id": core._safe_text(session_id),
            "path": str(session_dir),
            "title": core._safe_text(title) if title else None,
            "cwd": core._safe_text(actual_cwd) if actual_cwd else None,
            "branch": None,
            "created_at": core._iso_from_millis(created_ms),
            "updated_at_ms": updated_ms,
            "updated_at": core._iso_from_millis(updated_ms),
            "source_repo_root_path": (
                core._safe_text(summary.get("git_root_dir"))
                if isinstance(summary.get("git_root_dir"), str)
                else None
            ),
            "model": (
                core._safe_text(summary.get("current_model_id"))
                if isinstance(summary.get("current_model_id"), str)
                else None
            ),
            "head_commit": (
                core._safe_text(summary.get("head_commit"))
                if isinstance(summary.get("head_commit"), str)
                else None
            ),
            "chat_format_version": summary.get("chat_format_version"),
        }

    def discover(self, cwd: str, within_min: int) -> list[dict[str, Any]]:
        sessions: list[dict[str, Any]] = []
        for session_dir in self._session_dirs_for_cwd(cwd):
            candidate = self._candidate_from_dir(session_dir, cwd, require_cwd=True)
            if candidate is None:
                continue
            if core._within(int(candidate.get("updated_at_ms") or 0), within_min):
                sessions.append(candidate)
        return core._sort_and_dedupe(sessions)

    def candidate_from_path(self, raw_path: str, cwd: str) -> dict[str, Any] | None:
        path = Path(raw_path).expanduser()
        if not path.exists() or path.is_symlink():
            return None
        session_dir = path.parent if path.is_file() and path.name in {"summary.json", "updates.jsonl"} else path
        if not session_dir.is_dir() or session_dir.is_symlink():
            return None
        return self._candidate_from_dir(session_dir, cwd, require_cwd=False)

    def find_id(self, session_id: str, cwd: str) -> dict[str, Any] | None:
        for session_dir in self._session_dirs_for_cwd(cwd):
            if session_dir.name.casefold() == session_id.casefold():
                return self._candidate_from_dir(session_dir, cwd, require_cwd=False)
        for session_dir in self._all_session_dirs():
            if session_dir.name.casefold() != session_id.casefold():
                continue
            return self._candidate_from_dir(session_dir, cwd, require_cwd=False)
        return None

    @staticmethod
    def _tool_details(update: dict[str, Any]) -> tuple[str, Any]:
        metadata = update.get("_meta") if isinstance(update.get("_meta"), dict) else {}
        tool_metadata = (
            metadata.get("x.ai/tool")
            if isinstance(metadata.get("x.ai/tool"), dict)
            else {}
        )
        name = (
            tool_metadata.get("name")
            or tool_metadata.get("label")
            or update.get("title")
            or update.get("kind")
            or "grok_tool"
        )
        raw_input = update.get("rawInput")
        if raw_input is None:
            raw_input = tool_metadata.get("input", {})
        return core._safe_text(name), raw_input

    @staticmethod
    def _tool_output(
        update: dict[str, Any],
        max_tool_chars: int,
        warnings: list[dict[str, str]],
    ) -> str:
        parts: list[str] = []
        content = update.get("content")
        blocks = content if isinstance(content, list) else [content]
        for block in blocks:
            if isinstance(block, str):
                parts.append(block)
                continue
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "content":
                nested = block.get("content")
                if isinstance(nested, dict) and nested.get("type") == "text":
                    text = nested.get("text")
                    if isinstance(text, str):
                        parts.append(text)
                elif isinstance(nested, str):
                    parts.append(nested)
            elif block_type == "text" and isinstance(block.get("text"), str):
                parts.append(block["text"])
            elif block_type == "diff":
                path = core._one_line(block.get("path") or "unknown path", 160)
                parts.append(f"[diff body unavailable for {path}]")
                core._add_warning(
                    warnings,
                    "diff_content_unavailable",
                    "Grok diff bodies were excluded; only their paths were retained.",
                )
        output: Any = "\n".join(parts)
        if not output:
            output = update.get("rawOutput")
        return core._json_preview(output, max_tool_chars)

    def read(self, candidate: dict[str, Any], max_tool_chars: int) -> dict[str, Any]:
        session_dir = Path(str(candidate["path"]))
        summary = _read_json(session_dir / "summary.json")
        records, malformed = core._read_plain_jsonl(session_dir / "updates.jsonl")
        warnings: list[dict[str, str]] = []
        turns: list[dict[str, Any]] = []
        plan: list[dict[str, Any]] = []
        emitted_calls: set[str] = set()
        emitted_results: set[str] = set()
        hidden_thoughts = 0
        hook_records = 0
        unknown_records = 0

        for index, record in enumerate(records):
            params = record.get("params") if isinstance(record.get("params"), dict) else {}
            update = params.get("update") if isinstance(params.get("update"), dict) else None
            # Accept the inner update directly in fixtures and exported streams.
            if update is None and isinstance(record.get("sessionUpdate"), str):
                update = record
            if update is None:
                unknown_records += 1
                continue
            update_type = update.get("sessionUpdate") or update.get("type")
            if update_type == "user_message_chunk":
                _append_text_turn(turns, "user", update.get("content"))
            elif update_type == "agent_message_chunk":
                _append_text_turn(turns, "assistant", update.get("content"))
            elif update_type == "agent_thought_chunk":
                hidden_thoughts += 1
            elif update_type == "hook_execution":
                hook_records += 1
            elif update_type in {"tool_call", "tool_call_update"}:
                call_id_value = update.get("toolCallId")
                call_id = (
                    core._safe_text(call_id_value)
                    if call_id_value is not None
                    else f"grok-call-{index}"
                )
                status = update.get("status")
                if status in {"completed", "failed"}:
                    if call_id in emitted_results:
                        continue
                    emitted_results.add(call_id)
                    turns.append(
                        core._turn(
                            "tool",
                            tool_results=[
                                {
                                    "tool_use_id": call_id,
                                    "content": self._tool_output(update, max_tool_chars, warnings),
                                    "is_error": status == "failed",
                                    "unavailable": False,
                                    "inert": True,
                                }
                            ],
                        )
                    )
                elif status in {None, "pending"} and call_id not in emitted_calls:
                    name, raw_input = self._tool_details(update)
                    emitted_calls.add(call_id)
                    turns.append(
                        core._turn(
                            "assistant",
                            tool_calls=[
                                {
                                    "id": call_id,
                                    "name": name,
                                    "input": core._json_preview(raw_input, max_tool_chars),
                                    "inert": True,
                                }
                            ],
                        )
                    )
            elif update_type == "plan":
                entries = update.get("entries")
                if isinstance(entries, list):
                    plan = [
                        {
                            "content": core._safe_text(entry.get("content")),
                            "status": core._safe_text(entry.get("status") or "pending"),
                            "inert": True,
                        }
                        for entry in entries
                        if isinstance(entry, dict) and entry.get("content")
                    ]
            elif update_type == "turn_completed":
                continue
            else:
                unknown_records += 1

        if malformed:
            core._add_warning(
                warnings,
                "malformed_records_skipped",
                f"Skipped {malformed} malformed Grok update record(s).",
            )
        if hidden_thoughts:
            core._add_warning(
                warnings,
                "hidden_reasoning_skipped",
                f"Excluded {hidden_thoughts} Grok thought update(s).",
            )
        if hook_records:
            core._add_warning(
                warnings,
                "hook_records_skipped",
                f"Excluded {hook_records} Grok hook execution record(s).",
            )
        if hidden_thoughts or hook_records:
            core._add_warning(
                warnings,
                "unsafe_records_skipped",
                "Grok hidden-reasoning or hook records were excluded from inert history.",
            )
        if unknown_records:
            core._add_warning(
                warnings,
                "unknown_records_skipped",
                f"Skipped {unknown_records} unsupported Grok update record(s).",
            )

        created = _as_iso(summary.get("created_at")) or candidate.get("created_at")
        updated = (
            _as_iso(summary.get("last_active_at"))
            or _as_iso(summary.get("updated_at"))
            or candidate.get("updated_at")
        )
        result = {
            "tool": "grok",
            "source": "grok",
            "session_id": candidate.get("session_id"),
            "path": str(session_dir),
            "title": candidate.get("title"),
            "cwd": candidate.get("cwd"),
            "branch": None,
            "created_at": created,
            "updated_at": updated,
            "source_repo_root_path": candidate.get("source_repo_root_path"),
            "model": candidate.get("model"),
            "head_commit": candidate.get("head_commit"),
            "chat_format_version": candidate.get("chat_format_version"),
            "turns": turns,
            "plan": plan,
            "warnings": warnings,
        }
        return core._finalize_result(result)


class PiAdapter(ProviderAdapter):
    tool = "pi"

    @staticmethod
    def _agent_dir() -> Path:
        configured = os.environ.get("PI_CODING_AGENT_DIR")
        return Path(configured).expanduser() if configured else Path.home() / ".pi" / "agent"

    @staticmethod
    def _configured_path(value: str, cwd: str) -> Path:
        path = Path(value).expanduser()
        return path if path.is_absolute() else Path(cwd).expanduser() / path

    @classmethod
    def _settings_session_dir(cls, cwd: str) -> Path | None:
        configured: str | None = None
        for path in (cls._agent_dir() / "settings.json", Path(cwd).expanduser() / ".pi" / "settings.json"):
            settings = _read_json_optional(path)
            if settings is not None and isinstance(settings.get("sessionDir"), str):
                value = settings["sessionDir"].strip()
                if value:
                    configured = value
        return cls._configured_path(configured, cwd) if configured else None

    @classmethod
    def _storage(cls, cwd: str) -> tuple[Path, bool]:
        environment = os.environ.get("PI_CODING_AGENT_SESSION_DIR")
        if environment:
            return cls._configured_path(environment, cwd), True
        settings = cls._settings_session_dir(cwd)
        if settings is not None:
            return settings, True
        # Pi's getDefaultSessionDirPath uses Node path.resolve, which makes the
        # path absolute but does not dereference symlinks.
        resolved = _absolute_cwd(cwd)
        safe_path = re.sub(r"[/\\:]", "-", re.sub(r"^[/\\]", "", resolved))
        return cls._agent_dir() / "sessions" / f"--{safe_path}--", False

    @staticmethod
    def _files_in_root(root: Path, include_nested: bool) -> Iterable[Path]:
        if not root.is_dir() or root.is_symlink():
            return
        seen: set[Path] = set()
        for path in sorted(root.glob("*.jsonl"), key=lambda item: item.name):
            if path.is_file() and not path.is_symlink():
                seen.add(path)
                yield path
        if include_nested:
            for path in sorted(root.glob("*/*.jsonl"), key=str):
                if path.is_file() and not path.is_symlink() and path not in seen:
                    yield path

    @staticmethod
    def _header(records: list[dict[str, Any]]) -> dict[str, Any] | None:
        return next((record for record in records if record.get("type") == "session"), None)

    @staticmethod
    def _visible_text(content: Any) -> str:
        if isinstance(content, str):
            return core._safe_text(content)
        if not isinstance(content, list):
            return ""
        return "\n".join(
            core._safe_text(block.get("text"))
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        )

    @classmethod
    def _candidate_from_file(
        cls,
        path: Path,
        cwd: str,
        *,
        require_cwd: bool,
    ) -> dict[str, Any] | None:
        if not path.is_file() or path.is_symlink() or path.suffix != ".jsonl":
            return None
        try:
            records, _ = core._read_plain_jsonl(path)
        except core.ReaderError:
            return None
        header = cls._header(records)
        if header is None:
            return None
        actual_cwd = header.get("cwd") if isinstance(header.get("cwd"), str) else None
        if require_cwd and not _same_cwd(actual_cwd, cwd):
            return None
        session_id = header.get("id") if isinstance(header.get("id"), str) else path.stem
        title: str | None = None
        model: str | None = None
        version_value = header.get("version")
        version = version_value if isinstance(version_value, int) else 1
        entries = [record for record in records if record is not header and record.get("type") != "session"]
        metadata_records = cls._active_branch(entries, version, [])
        for record in metadata_records:
            if record.get("type") == "session_info" and isinstance(record.get("name"), str):
                title = record["name"]
            if record.get("type") == "model_change" and isinstance(record.get("modelId"), str):
                model = record["modelId"]
            message = record.get("message") if isinstance(record.get("message"), dict) else None
            if message is not None:
                if message.get("role") == "user" and title is None:
                    text = cls._visible_text(message.get("content"))
                    if text:
                        title = core._one_line(text, 120)
                if message.get("role") == "assistant" and isinstance(message.get("model"), str):
                    model = message["model"]
        timestamps = [
            core._timestamp_to_millis(record.get("timestamp"))
            for record in records
        ]
        valid_timestamps = [value for value in timestamps if value is not None]
        updated_ms = valid_timestamps[-1] if valid_timestamps else core._mtime_millis(path)
        return {
            "tool": "pi",
            "source": "pi-coding-agent",
            "session_id": core._safe_text(session_id),
            "path": str(path),
            "title": title,
            "cwd": core._safe_text(actual_cwd) if actual_cwd else None,
            "branch": None,
            "created_at": _as_iso(header.get("timestamp")),
            "updated_at_ms": updated_ms,
            "updated_at": core._iso_from_millis(updated_ms),
            "source_repo_root_path": None,
            "model": model,
            "session_version": header.get("version"),
            "parent_session": (
                header.get("parentSession")
                if isinstance(header.get("parentSession"), str)
                else None
            ),
        }

    def discover(self, cwd: str, within_min: int) -> list[dict[str, Any]]:
        root, custom = self._storage(cwd)
        sessions: list[dict[str, Any]] = []
        for path in self._files_in_root(root, include_nested=custom):
            candidate = self._candidate_from_file(path, cwd, require_cwd=True)
            if candidate is None:
                continue
            if core._within(int(candidate.get("updated_at_ms") or 0), within_min):
                sessions.append(candidate)
        return core._sort_and_dedupe(sessions)

    def candidate_from_path(self, raw_path: str, cwd: str) -> dict[str, Any] | None:
        path = Path(raw_path).expanduser()
        if not path.exists() or path.is_symlink():
            return None
        return self._candidate_from_file(path, cwd, require_cwd=False)

    def find_id(self, session_id: str, cwd: str) -> dict[str, Any] | None:
        root, custom = self._storage(cwd)
        for path in self._files_in_root(root, include_nested=custom):
            candidate = self._candidate_from_file(path, cwd, require_cwd=False)
            if candidate and str(candidate.get("session_id", "")).casefold() == session_id.casefold():
                return candidate
        if custom:
            return None
        all_root = self._agent_dir() / "sessions"
        for path in self._files_in_root(all_root, include_nested=True):
            candidate = self._candidate_from_file(path, cwd, require_cwd=False)
            if candidate and str(candidate.get("session_id", "")).casefold() == session_id.casefold():
                return candidate
        return None

    @staticmethod
    def _active_branch(
        entries: list[dict[str, Any]],
        version: int,
        warnings: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        if version < 2:
            core._add_warning(
                warnings,
                "legacy_session_version",
                f"Pi session version {version} has no reliable branch tree; records were read linearly.",
            )
            return entries
        if not entries:
            return []
        leaf = entries[-1]
        leaf_id = leaf.get("id")
        if not isinstance(leaf_id, str):
            core._add_warning(
                warnings,
                "broken_session_tree",
                "The active Pi leaf had no id; records were read linearly.",
            )
            return entries
        by_id = {
            entry["id"]: entry
            for entry in entries
            if isinstance(entry.get("id"), str)
        }
        branch: list[dict[str, Any]] = []
        seen: set[str] = set()
        current_id: str | None = leaf_id
        while current_id is not None:
            if current_id in seen:
                core._add_warning(
                    warnings,
                    "broken_session_tree",
                    "The Pi session tree contains a cycle; the recovered branch was truncated.",
                )
                break
            seen.add(current_id)
            entry = by_id.get(current_id)
            if entry is None:
                core._add_warning(
                    warnings,
                    "broken_session_tree",
                    f"The Pi session tree is missing parent entry {current_id!r}.",
                )
                break
            branch.append(entry)
            parent = entry.get("parentId")
            current_id = parent if isinstance(parent, str) and parent else None
        branch.reverse()
        inactive = len(entries) - len(branch)
        if inactive > 0:
            core._add_warning(
                warnings,
                "inactive_branch_entries_skipped",
                f"Excluded {inactive} Pi record(s) outside the active branch.",
            )
        return branch

    @staticmethod
    def _message_blocks(
        content: Any,
        warnings: list[dict[str, str]],
    ) -> tuple[str, list[dict[str, Any]], int, int]:
        if isinstance(content, str):
            return core._safe_text(content), [], 0, 0
        if not isinstance(content, list):
            return "", [], 0, 1 if content is not None else 0
        text_parts: list[str] = []
        calls: list[dict[str, Any]] = []
        hidden = 0
        unknown = 0
        for block in content:
            if not isinstance(block, dict):
                unknown += 1
                continue
            block_type = block.get("type")
            if block_type == "text" and isinstance(block.get("text"), str):
                text_parts.append(core._safe_text(block["text"]))
            elif block_type == "toolCall":
                calls.append(block)
            elif block_type == "thinking":
                hidden += 1
            elif block_type in {"image", "image_url"}:
                core._add_warning(
                    warnings,
                    "image_content_unavailable",
                    "Pi image content is not imported into the text handoff.",
                )
            else:
                unknown += 1
        return "\n".join(text_parts), calls, hidden, unknown

    @staticmethod
    def _tool_result_text(
        content: Any,
        max_tool_chars: int,
        warnings: list[dict[str, str]],
    ) -> str:
        if isinstance(content, str):
            return _bounded_text(content, max_tool_chars)
        parts: list[str] = []
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    parts.append(block["text"])
                elif block.get("type") in {"image", "image_url"}:
                    parts.append("[image content unavailable]")
                    core._add_warning(
                        warnings,
                        "image_content_unavailable",
                        "Pi image content is not imported into the text handoff.",
                    )
        return _bounded_text("\n".join(parts), max_tool_chars)

    def read(self, candidate: dict[str, Any], max_tool_chars: int) -> dict[str, Any]:
        path = Path(str(candidate["path"]))
        records, malformed = core._read_plain_jsonl(path)
        header = self._header(records)
        if header is None:
            raise core.ReaderError(f"Pi session header is missing: {path}")
        version_value = header.get("version")
        version = version_value if isinstance(version_value, int) else 1
        warnings: list[dict[str, str]] = []
        if version > 3:
            core._add_warning(
                warnings,
                "future_session_version",
                f"Pi session version {version} is newer than the tested version 3; parsed best-effort.",
            )
        entries = [record for record in records if record is not header and record.get("type") != "session"]
        active_entries = self._active_branch(entries, version, warnings)
        turns: list[dict[str, Any]] = []
        summaries: list[dict[str, Any]] = []
        hidden_blocks = 0
        extension_records = 0
        unknown_records = 0
        model = candidate.get("model")
        title = candidate.get("title")

        for entry in active_entries:
            entry_type = entry.get("type")
            if entry_type == "message":
                message = entry.get("message")
                if not isinstance(message, dict):
                    unknown_records += 1
                    continue
                role = message.get("role")
                if role in {"user", "assistant"}:
                    text, raw_calls, hidden, unknown = self._message_blocks(
                        message.get("content"), warnings
                    )
                    hidden_blocks += hidden
                    unknown_records += unknown
                    calls = [
                        {
                            "id": core._safe_text(call.get("id") or "pi-tool-call"),
                            "name": core._safe_text(call.get("name") or "pi_tool"),
                            "input": core._json_preview(call.get("arguments", {}), max_tool_chars),
                            "inert": True,
                        }
                        for call in raw_calls
                    ]
                    if text or calls:
                        turns.append(core._turn(role, text=text, tool_calls=calls))
                    if role == "assistant" and isinstance(message.get("model"), str):
                        model = message["model"]
                elif role == "toolResult":
                    turns.append(
                        core._turn(
                            "tool",
                            tool_results=[
                                {
                                    "tool_use_id": message.get("toolCallId"),
                                    "content": self._tool_result_text(
                                        message.get("content"), max_tool_chars, warnings
                                    ),
                                    "is_error": message.get("isError") is True,
                                    "unavailable": False,
                                    "inert": True,
                                }
                            ],
                        )
                    )
                elif role in {"hookMessage", "system", "developer"}:
                    extension_records += 1
                else:
                    unknown_records += 1
            elif entry_type in {"compaction", "branch_summary"}:
                summary = entry.get("summary")
                if isinstance(summary, str) and summary:
                    summaries.append(
                        {
                            "kind": entry_type,
                            "content": core._safe_text(summary),
                            "inert": True,
                        }
                    )
            elif entry_type in {"custom", "custom_message"}:
                extension_records += 1
            elif entry_type == "session_info":
                if isinstance(entry.get("name"), str):
                    title = entry["name"]
            elif entry_type == "model_change":
                if isinstance(entry.get("modelId"), str):
                    model = entry["modelId"]
            elif entry_type in {"thinking_level_change", "label"}:
                continue
            else:
                unknown_records += 1

        if malformed:
            core._add_warning(
                warnings,
                "malformed_records_skipped",
                f"Skipped {malformed} malformed Pi session record(s).",
            )
        if hidden_blocks:
            core._add_warning(
                warnings,
                "hidden_reasoning_skipped",
                f"Excluded {hidden_blocks} Pi thinking block(s).",
            )
        if extension_records:
            core._add_warning(
                warnings,
                "extension_records_skipped",
                f"Excluded {extension_records} Pi hook, system, or extension-injected record(s).",
            )
        if hidden_blocks or extension_records:
            core._add_warning(
                warnings,
                "unsafe_records_skipped",
                "Pi hidden-reasoning or extension-injected records were excluded from inert history.",
            )
        if unknown_records:
            core._add_warning(
                warnings,
                "unknown_records_skipped",
                f"Skipped {unknown_records} unsupported Pi record or content block(s).",
            )

        timestamps = [
            core._timestamp_to_millis(entry.get("timestamp"))
            for entry in active_entries
        ]
        valid_timestamps = [value for value in timestamps if value is not None]
        result = {
            "tool": "pi",
            "source": "pi-coding-agent",
            "session_id": core._safe_text(header.get("id") or candidate.get("session_id")),
            "path": str(path),
            "title": core._safe_text(title) if title else None,
            "cwd": (
                core._safe_text(header.get("cwd"))
                if isinstance(header.get("cwd"), str)
                else candidate.get("cwd")
            ),
            "branch": None,
            "created_at": _as_iso(header.get("timestamp")) or candidate.get("created_at"),
            "updated_at": (
                core._iso_from_millis(valid_timestamps[-1])
                if valid_timestamps
                else candidate.get("updated_at")
            ),
            "source_repo_root_path": None,
            "model": core._safe_text(model) if model else None,
            "session_version": version,
            "parent_session": (
                core._safe_text(header.get("parentSession"))
                if isinstance(header.get("parentSession"), str)
                else None
            ),
            "active_leaf_id": (
                active_entries[-1].get("id") if active_entries else None
            ),
            "turns": turns,
            "summaries": summaries,
            "warnings": warnings,
        }
        return core._finalize_result(result)


ADAPTERS: dict[str, ProviderAdapter] = {
    "grok": GrokAdapter(),
    "pi": PiAdapter(),
}


def discover_sessions(tool: str, cwd: str, within_min: int = 0) -> list[dict[str, Any]]:
    adapter = ADAPTERS.get(tool)
    if adapter is None:
        raise core.ReaderError(f"unsupported extended tool: {tool}")
    return adapter.discover(cwd, within_min)


def resolve_session(
    tool: str,
    reference: str | None,
    cwd: str,
    within_min: int = 0,
) -> dict[str, Any]:
    adapter = ADAPTERS.get(tool)
    if adapter is None:
        raise core.ReaderError(f"unsupported extended tool: {tool}")
    ref = (reference or "").strip()
    if not ref or ref.casefold() == "latest":
        ref = "latest"
    path_candidate = adapter.candidate_from_path(ref, cwd)
    if path_candidate is not None:
        return path_candidate
    sessions = adapter.discover(cwd, within_min)
    if ref == "latest":
        if not sessions:
            raise core.ReaderError(f"no {tool} session found for cwd {cwd}")
        return sessions[0]
    exact = [
        item
        for item in sessions
        if str(item.get("session_id", "")).casefold() == ref.casefold()
    ]
    if len(exact) == 1:
        return exact[0]
    found = adapter.find_id(ref, cwd)
    if found is not None:
        return found
    query = " ".join(ref.casefold().split())
    matches = [
        item
        for item in sessions
        if query in " ".join(str(item.get("title") or "").casefold().split())
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise core.AmbiguousReference(ref, matches)
    raise core.ReaderError(f"no {tool} session matched {ref!r} for cwd {cwd}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read foreign coding-agent sessions as inert history."
    )
    parser.add_argument("tool", choices=TOOLS)
    parser.add_argument("action", choices=("list", "show"))
    parser.add_argument("ref", nargs="?")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--within-min", type=int, default=0)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-tool-chars", type=int, default=300)
    return parser


def _core_argv(args: argparse.Namespace) -> list[str]:
    """Grok's parser only accepts the optional ref before flags."""
    forwarded = [args.tool, args.action]
    if args.ref is not None:
        forwarded.append(args.ref)
    forwarded.extend(
        [
            "--cwd",
            args.cwd,
            "--within-min",
            str(args.within_min),
            "--max-tool-chars",
            str(args.max_tool_chars),
        ]
    )
    if args.json:
        forwarded.append("--json")
    return forwarded


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()
    # The DSH tool passes `--json -- <ref>`. Grok's parse_args rejects that order.
    args = parser.parse_intermixed_args(arguments)
    if args.tool in core.TOOLS:
        return core.main(_core_argv(args))
    if args.within_min < 0:
        parser.error("--within-min must be non-negative")
    if args.max_tool_chars < 1:
        parser.error("--max-tool-chars must be positive")
    try:
        adapter = ADAPTERS[args.tool]
        if args.action == "list":
            if args.ref is not None:
                raise core.ReaderError("list does not accept a session reference")
            sessions = adapter.discover(args.cwd, args.within_min)
            if args.json:
                print(
                    json.dumps(
                        {
                            "tool": args.tool,
                            "cwd": args.cwd,
                            "sessions": sessions,
                            "warnings": [],
                        },
                        indent=2,
                        ensure_ascii=True,
                    )
                )
            else:
                print(core._render_list_human(args.tool, args.cwd, sessions), end="")
            return 0
        candidate = resolve_session(args.tool, args.ref, args.cwd, args.within_min)
        result = adapter.read(candidate, args.max_tool_chars)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=True))
        else:
            print(core.render_human(result), end="")
        return 0
    except core.AmbiguousReference as exc:
        print(f"error: {exc}", file=sys.stderr)
        print("Matches (choose a native id or path):", file=sys.stderr)
        for match in exc.matches:
            print(
                f"  {match['session_id']}  [{match.get('source')}]  "
                f"{match.get('title') or '(untitled)'}",
                file=sys.stderr,
            )
        return 2
    except core.ReaderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
