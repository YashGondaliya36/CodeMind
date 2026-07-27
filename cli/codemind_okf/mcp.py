"""
codemind_okf/mcp.py — Model Context Protocol (MCP) Server
=========================================================
Implements Anthropic's Model Context Protocol (MCP) over STDIO.
Compatible with Cursor, Claude Desktop, Antigravity, and Zed.

Exposes 7 core tools:
  1. list_bundles()             — List all available OKF knowledge bundles
  2. get_project_index(repo)    — Read master architecture index.md
  3. search_bundle(repo, query) — Rank & retrieve relevant OKF modules
  4. read_module(repo, file)    — Read module YAML frontmatter + AST details
  5. trace_dependencies(repo)   — Map cross-module dependencies
  6. remember(content, type)    — Persist AI decision/task/context to .okf/memory.md
  7. recall(query)              — Retrieve relevant past memory entries
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import frontmatter as fm

# JSON-RPC 2.0 helper constants
JSONRPC_VERSION = "2.0"


def find_okf_root(repo_name_or_path: str | None = None) -> Path | None:
    """Find the .okf directory for a given repo name or current directory."""
    if repo_name_or_path:
        p = Path(repo_name_or_path)
        for cand in [p] + list(p.parents):
            if (cand / ".okf").is_dir():
                return cand / ".okf"
            if cand.name == ".okf" and cand.is_dir():
                return cand
        # Check backend okf_bundles directory
        okf_bundles = Path("okf_bundles") / repo_name_or_path
        if okf_bundles.is_dir():
            return okf_bundles

    # Default: search in current working directory or parents
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        if (parent / ".okf").is_dir():
            return parent / ".okf"

    return None


# ── Core Tool Handlers ────────────────────────────────────────────────────────

def tool_list_bundles() -> str:
    """List all available local OKF knowledge bundles."""
    bundles = []

    # Check cwd/.okf
    cwd_okf = Path.cwd() / ".okf"
    if cwd_okf.is_dir():
        bundles.append({
            "name": Path.cwd().name,
            "path": str(cwd_okf.resolve()),
            "type": "local_project",
        })

    # Check okf_bundles dir
    bundles_dir = Path("okf_bundles")
    if bundles_dir.is_dir():
        for item in bundles_dir.iterdir():
            if item.is_dir():
                bundles.append({
                    "name": item.name,
                    "path": str(item.resolve()),
                    "type": "stored_bundle",
                })

    if not bundles:
        return "No OKF bundles found. Run `codemind index .` to generate one."

    return json.dumps(bundles, indent=2)


def tool_get_project_index(repo_name: str | None = None) -> str:
    """Fetch the master architecture index.md for a project."""
    root = find_okf_root(repo_name)
    if not root:
        return f"Error: No OKF bundle found for '{repo_name or Path.cwd().name}'. Run `codemind index .` first."

    index_file = root / "index.md"
    if not index_file.exists():
        return f"Error: index.md missing in {root}."

    return index_file.read_text(encoding="utf-8", errors="replace")


def tool_search_bundle(query: str, repo_name: str | None = None, max_results: int = 5) -> str:
    """Perform relevance scoring search across all OKF modules."""
    root = find_okf_root(repo_name)
    if not root:
        return f"Error: No OKF bundle found for '{repo_name or Path.cwd().name}'."

    modules_dir = root / "modules"
    if not modules_dir.is_dir():
        return f"Error: No modules directory in {root}."

    # Stop words (English grammar noise words only — keeping programming terms like 'get', 'code', 'file')
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "how", "what", "where", "when", "why", "who", "which", "can", "could",
        "do", "does", "did", "will", "would", "shall", "should", "in", "on",
        "at", "to", "for", "of", "and", "or", "not", "with", "from", "by",
    }

    keywords = {
        t.lower() for t in re.findall(r"\b\w+\b", query)
        if t.lower() not in stop_words and len(t) > 2
    }

    if not keywords:
        return "Query too short or contains only stop words."

    results = []

    for md_path in modules_dir.glob("*.md"):
        try:
            raw = md_path.read_text(encoding="utf-8", errors="replace")
            post = fm.loads(raw)
            meta = post.metadata

            title = str(meta.get("title", "")).lower()
            tags = [str(t).lower() for t in meta.get("tags", [])]
            key_funcs = [str(f).lower() for f in meta.get("key_functions", [])]
            desc = str(meta.get("description", "")).lower()
            resource = str(meta.get("resource", "")).lower()

            score = 0.0
            for kw in keywords:
                # ── 1. Function & Class match (Highest Weight) ──
                for fn in key_funcs:
                    if kw == fn:
                        score += 4.0
                    elif kw in fn or fn in kw:
                        score += 3.0  # Dynamic sub-word match (e.g. 'auth' in 'authenticate_user')

                # ── 2. Title match ──
                if kw in title:
                    score += 3.0
                elif any(kw in word for word in title.split()):
                    score += 2.0

                # ── 3. Dynamic Tag match ──
                for tag in tags:
                    if kw == tag:
                        score += 2.5
                    elif kw in tag or tag in kw:
                        score += 1.5  # Dynamic tag sub-word match

                # ── 4. Description match ──
                if kw in desc:
                    score += 1.5

                # ── 5. Source path match ──
                if kw in resource:
                    score += 1.0

            if score > 0:
                results.append({
                    "score": round(score, 2),
                    "filename": md_path.name,
                    "title": meta.get("title", md_path.stem),
                    "type": meta.get("type", "module"),
                    "resource": meta.get("resource", ""),
                    "description": meta.get("description", ""),
                    "key_functions": meta.get("key_functions", []),
                    "tags": meta.get("tags", []),
                })
        except Exception:
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    top_results = results[:max_results]

    if not top_results:
        # Dynamic Fallback: if zero keywords matched, return the top general modules so AI is never stuck
        fallback_results = []
        for md_path in list(modules_dir.glob("*.md"))[:max_results]:
            try:
                raw = md_path.read_text(encoding="utf-8", errors="replace")
                post = fm.loads(raw)
                meta = post.metadata
                fallback_results.append({
                    "score": 0.1,
                    "filename": md_path.name,
                    "title": meta.get("title", md_path.stem),
                    "type": meta.get("type", "module"),
                    "resource": meta.get("resource", ""),
                    "description": meta.get("description", ""),
                    "key_functions": meta.get("key_functions", []),
                    "tags": meta.get("tags", []),
                })
            except Exception:
                continue

        return json.dumps({
            "query": query,
            "keywords_matched": list(keywords),
            "total_matches": 0,
            "fallback_used": True,
            "note": "No exact keyword matches found. Returning primary project modules for context.",
            "results": fallback_results,
        }, indent=2)

    return json.dumps({
        "query": query,
        "keywords_matched": list(keywords),
        "total_matches": len(results),
        "results": top_results,
    }, indent=2)


def tool_read_module(filename: str, repo_name: str | None = None) -> str:
    """Read a specific OKF module file."""
    root = find_okf_root(repo_name)
    if not root:
        return f"Error: No OKF bundle found."

    # Allow passing filename with or without 'modules/' prefix
    fname = filename.replace("modules/", "").replace("modules\\", "")
    target = root / "modules" / fname

    if not target.exists():
        # Try finding by title or matching slug
        matches = list((root / "modules").glob(f"*{fname}*"))
        if matches:
            target = matches[0]
        else:
            return f"Error: Module file '{filename}' not found."

    return target.read_text(encoding="utf-8", errors="replace")


def tool_trace_dependencies(repo_name: str | None = None) -> str:
    """Map dependencies across all modules in the OKF bundle."""
    root = find_okf_root(repo_name)
    if not root:
        return f"Error: No OKF bundle found."

    modules_dir = root / "modules"
    if not modules_dir.is_dir():
        return "Error: No modules directory found."

    dep_map = {}
    for md_path in modules_dir.glob("*.md"):
        try:
            raw = md_path.read_text(encoding="utf-8", errors="replace")
            post = fm.loads(raw)
            meta = post.metadata
            dep_map[meta.get("title", md_path.stem)] = {
                "resource": meta.get("resource", ""),
                "type": meta.get("type", "module"),
                "key_functions": meta.get("key_functions", []),
                "tags": meta.get("tags", []),
            }
        except Exception:
            continue

    return json.dumps(dep_map, indent=2)


# ── Memory Tool Helpers ───────────────────────────────────────────────────────

_MEMORY_FILENAME = "memory.md"

_SECTION_HEADERS = {
    "decision":  "## 📌 Decisions",
    "task":      "## ✅ Tasks",
    "context":   "## 💬 Context Snapshots",
    "bug":       "## 🐛 Bug Reports",
}

_MEMORY_TEMPLATE = """\
---
type: memory
title: CodeMind AI Memory Log
generated_by: codemind-okf
---

# 🧠 CodeMind Memory Log

> This file is written automatically by AI IDEs (Antigravity, Cursor, etc.)
> via the CodeMind MCP `remember` tool. Each entry is timestamped and tagged.
> **Do not delete** — it persists context across sessions and IDE switches.

## 📌 Decisions
<!-- AI appends architectural decisions here -->

## ✅ Tasks
<!-- AI appends task progress here -->

## 💬 Context Snapshots
<!-- AI appends working context here -->

## 🐛 Bug Reports
<!-- AI appends bug discoveries here -->
"""


def _get_memory_path(repo_name: str | None = None) -> Path | None:
    """Resolve .okf/memory.md path for a given repo."""
    root = find_okf_root(repo_name)
    return (root / _MEMORY_FILENAME) if root else None


def _ensure_memory_file(memory_path: Path) -> None:
    """Create memory.md with template if it doesn't exist."""
    if not memory_path.exists():
        memory_path.write_text(_MEMORY_TEMPLATE, encoding="utf-8")


def _append_to_section(memory_path: Path, section_header: str, entry: str) -> None:
    """
    Append a new entry directly under the matching section header
    by finding the header line and inserting after it.
    """
    content = memory_path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)

    insert_at = None
    for i, line in enumerate(lines):
        if line.strip() == section_header.strip():
            # Insert after the section header (and skip any comment line beneath)
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("<!--"):
                j += 1
            insert_at = j
            break

    new_block = "\n" + entry.rstrip("\n") + "\n"

    if insert_at is not None:
        lines.insert(insert_at, new_block)
    else:
        # Section not found — append to end
        lines.append(f"\n{section_header}\n{new_block}")

    memory_path.write_text("".join(lines), encoding="utf-8")


def tool_remember(
    content: str,
    memory_type: str = "context",
    ide: str = "AI IDE",
    tags: list[str] | None = None,
    repo_name: str | None = None,
) -> str:
    """
    Persist an AI-generated memory entry to .okf/memory.md.
    Called by the IDE AI to log decisions, tasks, context, or bugs.
    """
    memory_path = _get_memory_path(repo_name)
    if memory_path is None:
        return json.dumps({
            "status": "error",
            "message": "No .okf directory found. Run `codemind index .` first."
        })

    _ensure_memory_file(memory_path)

    # Normalise type
    memory_type = memory_type.lower().strip()
    if memory_type not in _SECTION_HEADERS:
        memory_type = "context"  # Safe fallback

    section = _SECTION_HEADERS[memory_type]

    # Build timestamp (local + UTC offset)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Build tag line
    tag_str = ""
    if tags:
        tag_str = "  \n**Tags:** " + " ".join(f"`{t}`" for t in tags)

    entry = (
        f"### [{now}] — {ide}\n"
        f"{content.strip()}"
        f"{tag_str}\n"
        f"\n---"
    )

    _append_to_section(memory_path, section, entry)

    return json.dumps({
        "status": "ok",
        "message": f"Memory saved to {memory_path.name} under '{section}'.",
        "type": memory_type,
        "timestamp": now,
    })


def tool_recall(
    query: str,
    memory_type: str | None = None,
    max_results: int = 5,
    repo_name: str | None = None,
) -> str:
    """
    Search .okf/memory.md for relevant past entries.
    Returns the top matching entries ranked by keyword overlap.
    """
    memory_path = _get_memory_path(repo_name)
    if memory_path is None or not memory_path.exists():
        return (
            "No memory file found. The AI has not stored any memories yet. "
            "Use the `remember` tool to begin persisting context."
        )

    raw = memory_path.read_text(encoding="utf-8")

    # ── Parse entries — split on `### [` markers ──────────────────────────────
    entries: list[dict] = []
    current_section = "unknown"

    for line in raw.splitlines():
        # Track current section
        for mtype, header in _SECTION_HEADERS.items():
            if line.strip() == header.strip():
                current_section = mtype
                break

    # Split the content into individual entry blocks
    blocks = re.split(r"(?=### \[\d{4}-\d{2}-\d{2})", raw)
    for block in blocks:
        block = block.strip()
        if not block or not block.startswith("### ["):
            continue

        # Determine which section this block belongs to
        # by looking at what section header appears before this block in the raw file
        block_pos = raw.find(block)
        preceding = raw[:block_pos]
        detected_type = "context"
        for mtype, header in _SECTION_HEADERS.items():
            if header in preceding:
                detected_type = mtype  # Last matching section before this block

        entries.append({
            "type": detected_type,
            "text": block,
        })

    if not entries:
        return "Memory file exists but contains no entries yet."

    # ── Keyword scoring ───────────────────────────────────────────────────────
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
        "to", "for", "of", "and", "or", "not", "with", "from", "by", "this",
    }
    keywords = {
        t.lower() for t in re.findall(r"\b\w+\b", query)
        if t.lower() not in stop_words and len(t) > 2
    }

    scored: list[tuple[float, dict]] = []
    for entry in entries:
        # Optional type filter
        if memory_type and entry["type"] != memory_type.lower():
            continue
        text_lower = entry["text"].lower()
        score = sum(2.0 if kw in text_lower else 0.0 for kw in keywords)
        if score > 0:
            scored.append((score, entry))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:max_results]

    if not top:
        # Fallback — return most recent entries of the requested type
        fallback = [
            e for e in entries
            if not memory_type or e["type"] == memory_type
        ][-max_results:]
        return json.dumps({
            "query": query,
            "matched": 0,
            "note": "No keyword matches found. Returning most recent entries.",
            "results": [e["text"] for e in fallback],
        }, indent=2)

    return json.dumps({
        "query": query,
        "keywords": list(keywords),
        "matched": len(top),
        "results": [
            {"score": round(sc, 2), "type": e["type"], "content": e["text"]}
            for sc, e in top
        ],
    }, indent=2)


# ── MCP Tool Definitions (JSON Schema) ────────────────────────────────────────

MCP_TOOLS = [
    {
        "name": "list_bundles",
        "description": "List all available local OKF knowledge bundles and their file paths.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_project_index",
        "description": "Get the master index.md architecture map for a repository bundle. Call this first to understand the full project structure.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_name": {
                    "type": "string",
                    "description": "Optional repository or bundle name. Omit to use local directory.",
                },
            },
        },
    },
    {
        "name": "search_bundle",
        "description": "Search OKF modules by keywords or technical concepts. Returns scored module summaries and key functions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language question or concept query (e.g. 'authentication', 'database schema', 'pipeline').",
                },
                "repo_name": {
                    "type": "string",
                    "description": "Optional repo/bundle name.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 5).",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_module",
        "description": "Read the full OKF markdown documentation for a specific module, including function signatures, AST breakdown, and docstrings.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Module filename (e.g., 'src-auth-router.md' or 'auth_router.py').",
                },
                "repo_name": {
                    "type": "string",
                    "description": "Optional repo/bundle name.",
                },
            },
            "required": ["filename"],
        },
    },
    {
        "name": "trace_dependencies",
        "description": "Get a map of all project modules, their types, key functions, and dependencies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_name": {
                    "type": "string",
                    "description": "Optional repo/bundle name.",
                },
            },
        },
    },
    {
        "name": "remember",
        "description": (
            "Persist an AI-generated memory entry to .okf/memory.md. "
            "Call this after completing important tasks, making architectural decisions, "
            "discovering bugs, or recording working context that should survive IDE restarts "
            "and IDE switches. The memory is stored in human-readable Markdown."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The memory content to persist. Be specific and detailed — future AI sessions will read this.",
                },
                "memory_type": {
                    "type": "string",
                    "enum": ["decision", "task", "context", "bug"],
                    "description": (
                        "Category of memory: "
                        "'decision' for architectural/design choices, "
                        "'task' for work-in-progress / TODO items, "
                        "'context' for general working context snapshots, "
                        "'bug' for discovered issues."
                    ),
                },
                "ide": {
                    "type": "string",
                    "description": "Name of the IDE or agent writing this memory (e.g. 'Antigravity', 'Cursor', 'Claude'). Defaults to 'AI IDE'.",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of short keyword tags (e.g. ['bot_shield', 'ml', 'fastapi']).",
                },
                "repo_name": {
                    "type": "string",
                    "description": "Optional repo/bundle name. Omit to use local directory.",
                },
            },
            "required": ["content"],
        },
    },
    {
        "name": "recall",
        "description": (
            "Search .okf/memory.md for past AI-written memory entries relevant to a query. "
            "Call this at the START of a new session or when switching IDEs to restore context. "
            "Returns ranked memory entries by keyword relevance."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query (e.g. 'bot shield decisions', 'authentication tasks', 'database schema').",
                },
                "memory_type": {
                    "type": "string",
                    "enum": ["decision", "task", "context", "bug"],
                    "description": "Optional filter: only return memories of this type.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of memory entries to return (default 5).",
                },
                "repo_name": {
                    "type": "string",
                    "description": "Optional repo/bundle name. Omit to use local directory.",
                },
            },
            "required": ["query"],
        },
    },
]


# ── MCP Server Loop (STDIO Transport) ────────────────────────────────────────

def run_mcp_server():
    """Main STDIO JSON-RPC 2.0 event loop for Model Context Protocol (MCP)."""
    # Force utf-8 stdout/stdin
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            # ── Initialize ──
            if method == "initialize":
                _reply(req_id, {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                    },
                    "serverInfo": {
                        "name": "codemind-okf-mcp",
                        "version": "1.1.0",
                    },
                })

            elif method == "notifications/initialized":
                pass  # Client notification — no reply needed

            # ── Tools List ──
            elif method == "tools/list":
                _reply(req_id, {"tools": MCP_TOOLS})

            # ── Tools Call ──
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                result_text = _execute_tool(tool_name, args)

                _reply(req_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text,
                        }
                    ]
                })

            elif method == "ping":
                _reply(req_id, {})

            else:
                if req_id is not None:
                    _reply_error(req_id, -32601, f"Method '{method}' not found")

        except json.JSONDecodeError:
            continue
        except Exception as e:
            sys.stderr.write(f"[CodeMind MCP Error] {e}\n")
            sys.stderr.flush()


def _execute_tool(name: str, args: dict[str, Any]) -> str:
    """Route tool call to appropriate handler function."""
    try:
        if name == "list_bundles":
            return tool_list_bundles()
        elif name == "get_project_index":
            return tool_get_project_index(args.get("repo_name"))
        elif name == "search_bundle":
            return tool_search_bundle(
                query=args.get("query", ""),
                repo_name=args.get("repo_name"),
                max_results=int(args.get("max_results", 5)),
            )
        elif name == "read_module":
            return tool_read_module(
                filename=args.get("filename", ""),
                repo_name=args.get("repo_name"),
            )
        elif name == "trace_dependencies":
            return tool_trace_dependencies(args.get("repo_name"))
        elif name == "remember":
            tags_raw = args.get("tags")
            tags = list(tags_raw) if isinstance(tags_raw, list) else None
            return tool_remember(
                content=args.get("content", ""),
                memory_type=args.get("memory_type", "context"),
                ide=args.get("ide", "AI IDE"),
                tags=tags,
                repo_name=args.get("repo_name"),
            )
        elif name == "recall":
            return tool_recall(
                query=args.get("query", ""),
                memory_type=args.get("memory_type"),
                max_results=int(args.get("max_results", 5)),
                repo_name=args.get("repo_name"),
            )
        else:
            return f"Error: Unknown tool '{name}'."
    except Exception as e:
        return f"Tool Execution Error ({name}): {str(e)}"


def _reply(req_id: Any, result: Any):
    if req_id is None:
        return
    msg = {
        "jsonrpc": JSONRPC_VERSION,
        "id": req_id,
        "result": result,
    }
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def _reply_error(req_id: Any, code: int, message: str):
    if req_id is None:
        return
    msg = {
        "jsonrpc": JSONRPC_VERSION,
        "id": req_id,
        "error": {
            "code": code,
            "message": message,
        },
    }
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    run_mcp_server()
