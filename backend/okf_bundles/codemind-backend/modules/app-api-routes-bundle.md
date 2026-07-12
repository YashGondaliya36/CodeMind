---
type: api
title: OKF Bundle API Endpoints
description: This module provides a thin HTTP interface for managing and retrieving Open Knowledge Format (OKF) bundles. It acts as a routing layer that delegates business logic to the core bundle services.
resource: app/api/routes/bundle.py
tags:
  - okf
  - bundle
  - fastapi
  - routing
  - knowledge-graph
timestamp: 2026-07-12
---

# OKF Bundle API Endpoints

> **File:** `app/api/routes/bundle.py`  
> **Language:** python  
> **Lines:** 113

---

## 📋 Purpose

It exposes RESTful endpoints to allow clients to interact with OKF bundle content, metadata, and graph structures.

## 🔧 Key Components

### Functions

#### `⚡ async list_files(repo_name)`
Returns metadata (frontmatter) for every OKF concept file in the bundle.
Does NOT return file bodies — use /file/{filename} for that.
This is intentionally lightweight so the frontend can render the f

#### `⚡ async get_file(repo_name, filename)`
Returns the complete content (frontmatter + Markdown body) of one OKF file.

The `filename` parameter supports nested paths, e.g.:
`GET /bundle/my-repo/file/modules/auth-module.md`

#### `⚡ async get_index(repo_name)`
Returns the index.md of the bundle — the auto-generated table of contents
that the agent reads first when answering any question.

#### `⚡ async get_graph(repo_name)`
Returns the OKF knowledge graph as a list of nodes and directed edges.
Edges represent `depends_on` relationships between concept files.
Use this to render the interactive graph visualiser on the fron

#### `⚡ async remove_bundle(repo_name)`
Permanently deletes all OKF files for the given repo.
The repo can be re-analyzed with POST /repo/analyze.

## 🔗 Dependencies

It relies on the FastAPI framework for request handling and delegates core operations to the app.core.bundle module.

**Key imports:**
- `app.core.bundle.graph_builder`
- `app.core.bundle.manager`
- `app.models.bundle`
- `fastapi`

---

## 🤖 Agent Navigation Hints

_Use these tags to find related concept files:_

`okf` · `bundle` · `fastapi` · `routing` · `knowledge-graph`
