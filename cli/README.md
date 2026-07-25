# 🧠 CodeMind OKF CLI

> **Generate AI-ready knowledge bundles for any codebase.**  
> Works with **Cursor**, **Antigravity IDE**, **Claude Desktop**, **GitHub Copilot**, and any **MCP-compatible** AI IDE.

<p align="center">
  <a href="https://pypi.org/project/codemind-okf/"><img src="https://img.shields.io/pypi/v/codemind-okf.svg?color=blue&style=for-the-badge" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/codemind-okf/"><img src="https://img.shields.io/pypi/pyversions/codemind-okf.svg?style=for-the-badge" alt="Python Versions"></a>
  <a href="https://modelcontextprotocol.io/"><img src="https://img.shields.io/badge/MCP-Compatible-green.svg?style=for-the-badge" alt="MCP Compatible"></a>
</p>

---

## 📦 Installation

```bash
pip install codemind-okf
```

---

## 🚀 Quick Usage

### 1. `codemind index` — Index Any Project
Crawls your project files using Tree-sitter & AST parsers to generate a `.okf/` knowledge bundle.

```bash
codemind index .                         # Index current directory
codemind index /path/to/project          # Index a specific directory
codemind index . --lang python           # Only index Python files
codemind index . --overwrite             # Force re-index from scratch
```

* **⚡ SHA-256 Incremental Indexing:** Remembers file hashes. Subsequent runs skip unchanged files in **0.05s**!

---

### 2. `codemind init` — Drop AI IDE Instructions
Creates instruction files so Cursor, Antigravity, and GitHub Copilot use `.okf/index.md` as primary context.

```bash
codemind init                            # Create all AI IDE config files
```

**Files created:**
| File | Compatible Tool |
|---|---|
| `.cursorrules` | Cursor AI IDE |
| `.agents/AGENTS.md` | Antigravity IDE & Open Agents |
| `.github/copilot-instructions.md` | GitHub Copilot |

---

### 3. `codemind audit` — Architecture & Health Audit
Performs an architectural health check evaluating line density, docstring coverage, and layer separation.

```bash
codemind audit                          # Health score (0-100 A+)
```

---

### 4. `codemind watch` — Real-Time Background File Watcher
Watches the project directory for file saves and incrementally updates `.okf/` in under 50ms.

```bash
codemind watch                          # Run watcher in background
```

---

### 5. `codemind mcp` — Model Context Protocol (MCP) Server
Launches the MCP server over STDIO. Connects CodeMind natively to **Cursor**, **Claude Desktop**, **Antigravity**, or **Zed**.

```bash
codemind mcp
```

**Add to Cursor / Claude Desktop / Antigravity (`mcp.json`):**

```json
{
  "mcpServers": {
    "codemind": {
      "command": "uvx",
      "args": [
        "--from",
        "codemind-okf",
        "codemind",
        "mcp"
      ]
    }
  }
}
```

---

## 🔌 Exposed MCP Tools

| MCP Tool | Description |
|---|---|
| 📚 `get_project_index` | Reads the master architecture map (`index.md`) |
| 🔍 `search_bundle(query)` | Sub-word & token search across all project modules |
| 📖 `read_module(slug)` | Reads specific module AST metadata & function signatures |
| 🔗 `trace_dependencies(slug)` | Traces import graphs between components |
| 📁 `list_bundles` | Discovers available `.okf/` knowledge bundles |

---

## 📄 License

MIT License. See repository for details.
