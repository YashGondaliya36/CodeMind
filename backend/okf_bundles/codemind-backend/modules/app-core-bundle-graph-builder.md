---
type: module
title: OKF Knowledge Graph Builder
description: This module parses Markdown links within OKF files to construct a directed graph representing dependency relationships. It provides the structural data required for visualizing repository knowledge connections.
resource: app/core/bundle/graph_builder.py
tags:
  - graph
  - parsing
  - okf
  - visualization
  - dependency
timestamp: 2026-07-12
---

# OKF Knowledge Graph Builder

> **File:** `app/core/bundle/graph_builder.py`  
> **Language:** python  
> **Lines:** 89

---

## 📋 Purpose

It enables the frontend to render interactive dependency maps by mapping file-based relationships into a nodes-and-edges format.

## 🔧 Key Components

### Functions

#### `build_graph(repo_name)`
Build a nodes-and-edges knowledge graph from a bundle's OKF files.

Node IDs are the relative filenames (e.g. "modules/auth-module.md").
Edges come from two sources:
  1. The YAML `depends_on` list in

#### `_resolve_dep(dep, file_set)`
Try to resolve a depends_on entry to an actual filename in the bundle.
Handles both full paths ("modules/auth-module.md") and bare slugs ("auth-module").

## 🔗 Dependencies

It relies on the internal bundle manager and model definitions to retrieve and structure repository file data.

**Key imports:**
- `__future__`
- `app.core.bundle.manager`
- `app.models.bundle`
- `re`

---

## 🤖 Agent Navigation Hints

_Use these tags to find related concept files:_

`graph` · `parsing` · `okf` · `visualization` · `dependency`
