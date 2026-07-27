import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Request

from app.core.bundle.manager import (
    list_repos,
    get_bundle_path,
    bundle_exists,
    get_file_detail,
    get_memory_log,
)
from app.core.bundle.graph_builder import build_graph
from app.utils.file_utils import safe_read, safe_write

router = APIRouter()

MCP_TOOLS = [
    {
        "name": "list_bundles",
        "description": "List all available OKF knowledge bundles stored in the backend.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_project_index",
        "description": "Fetch master index.md architecture map for a repository bundle.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_name": {"type": "string", "description": "Repository bundle name."}
            },
            "required": ["repo_name"],
        },
    },
    {
        "name": "search_bundle",
        "description": "Search OKF modules by keywords or technical concepts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query keywords."},
                "repo_name": {"type": "string", "description": "Repository bundle name."},
                "max_results": {"type": "integer", "description": "Max results (default 5)."},
            },
            "required": ["query", "repo_name"],
        },
    },
    {
        "name": "read_module",
        "description": "Read the full OKF markdown documentation for a specific module.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Module filename (e.g., 'modules/auth-router.md')."},
                "repo_name": {"type": "string", "description": "Repository bundle name."},
            },
            "required": ["filename", "repo_name"],
        },
    },
    {
        "name": "trace_dependencies",
        "description": "Get dependency knowledge graph for a repo bundle.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_name": {"type": "string", "description": "Repository bundle name."}
            },
            "required": ["repo_name"],
        },
    },
    {
        "name": "remember",
        "description": "Persist an AI-generated memory entry to memory.md in the repo bundle.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_name": {"type": "string", "description": "Repository bundle name."},
                "content": {"type": "string", "description": "Memory content to persist."},
                "memory_type": {
                    "type": "string",
                    "enum": ["decision", "task", "context", "bug"],
                    "description": "Category of memory.",
                },
                "ide": {"type": "string", "description": "IDE/Agent label."},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["repo_name", "content"],
        },
    },
    {
        "name": "recall",
        "description": "Search memory.md for past AI-written memory entries in a repo bundle.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_name": {"type": "string", "description": "Repository bundle name."},
                "query": {"type": "string", "description": "Search query."},
                "memory_type": {"type": "string", "enum": ["decision", "task", "context", "bug"]},
                "max_results": {"type": "integer"},
            },
            "required": ["repo_name", "query"],
        },
    },
]


def _execute_backend_tool(name: str, args: dict[str, Any]) -> str:
    repo_name = args.get("repo_name", "")

    if name == "list_bundles":
        return json.dumps(list_repos(), indent=2)

    elif name == "get_project_index":
        if not repo_name or not bundle_exists(repo_name):
            return f"Error: Bundle '{repo_name}' not found."
        index_file = get_bundle_path(repo_name) / "index.md"
        if not index_file.exists():
            return f"Error: index.md missing in bundle '{repo_name}'."
        return safe_read(index_file) or ""

    elif name == "search_bundle":
        if not repo_name or not bundle_exists(repo_name):
            return f"Error: Bundle '{repo_name}' not found."
        query = args.get("query", "").lower()
        modules_dir = get_bundle_path(repo_name) / "modules"
        if not modules_dir.is_dir():
            return "Error: No modules directory found."
        results = []
        for md_file in modules_dir.glob("*.md"):
            raw = safe_read(md_file) or ""
            if query in raw.lower():
                results.append({"file": md_file.name, "snippet": raw[:300]})
        return json.dumps(results[:int(args.get("max_results", 5))], indent=2)

    elif name == "read_module":
        filename = args.get("filename", "")
        detail = get_file_detail(repo_name, filename)
        if not detail:
            return f"Error: File '{filename}' not found in bundle '{repo_name}'."
        return detail.raw

    elif name == "trace_dependencies":
        if not repo_name or not bundle_exists(repo_name):
            return f"Error: Bundle '{repo_name}' not found."
        graph = build_graph(repo_name)
        return json.dumps(graph.model_dump(), indent=2)

    elif name == "remember":
        if not repo_name or not bundle_exists(repo_name):
            return f"Error: Bundle '{repo_name}' not found."
        content = args.get("content", "")
        mtype = args.get("memory_type", "context").lower()
        ide = args.get("ide", "AI IDE")
        tags = args.get("tags") or []
        mem_file = get_bundle_path(repo_name) / "memory.md"
        if not mem_file.exists():
            mem_file.write_text("# 🧠 CodeMind Memory Log\n\n## 📌 Decisions\n\n## ✅ Tasks\n\n## 💬 Context Snapshots\n\n## 🐛 Bug Reports\n", encoding="utf-8")
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        tag_str = ("  \n**Tags:** " + " ".join(f"`{t}`" for t in tags)) if tags else ""
        entry_text = f"\n### [{now}] — {ide}\n{content.strip()}{tag_str}\n\n---"
        mem_raw = safe_read(mem_file) or ""
        safe_write(mem_file, mem_raw + entry_text)
        return json.dumps({"status": "ok", "message": f"Saved memory to {repo_name}"})

    elif name == "recall":
        log = get_memory_log(repo_name)
        if not log:
            return f"Error: No memory log found for '{repo_name}'."
        query = args.get("query", "").lower()
        matched = [e.model_dump() for e in log.entries if query in e.content.lower() or any(query in t for t in e.tags)]
        return json.dumps(matched[:int(args.get("max_results", 5))], indent=2)

    return f"Error: Unknown tool '{name}'."


@router.get("/tools")
async def list_mcp_tools():
    """List all available MCP tools."""
    return {"tools": MCP_TOOLS}


@router.post("")
async def mcp_rpc_handler(request: Request):
    """
    HTTP JSON-RPC 2.0 endpoint for MCP.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    req_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "codemind-backend-mcp", "version": "1.1.0"},
            },
        }

    elif method == "notifications/initialized":
        return {"jsonrpc": "2.0", "result": None}

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": MCP_TOOLS},
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        result_text = _execute_backend_tool(tool_name, args)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {"type": "text", "text": result_text}
                ]
            },
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method '{method}' not found"},
        }
