---
type: module
title: OKF Metadata Frontmatter Scanner
description: This module performs high-speed extraction of YAML frontmatter from OKF files within a bundle. It enables selective retrieval by identifying relevant files without requiring full content parsing.
resource: app/core/agent/metadata_scanner.py
tags:
  - okf
  - metadata
  - scanner
  - optimization
  - retrieval
  - frontmatter
timestamp: 2026-07-12
---

# OKF Metadata Frontmatter Scanner

> **File:** `app/core/agent/metadata_scanner.py`  
> **Language:** python  
> **Lines:** 63

---

## 📋 Purpose

It minimizes computational overhead by allowing the agent to filter files based on metadata before initiating expensive LLM processing.

## 🔧 Key Components

### Functions

#### `scan_all_metadata(repo_name)`
Retrieve the YAML frontmatter of every OKF file in a bundle.

This is intentionally a pure metadata read — NO file bodies are loaded.
Each metadata object is tiny (a few hundred bytes) so scanning hun

#### `get_metadata_summary(repo_name)`
Return a high-level summary of the bundle for diagnostic purposes.
Used by the agent to understand what it's working with.

## 🔗 Dependencies

It relies on the internal bundle manager and bundle data models to locate and parse repository files.

**Key imports:**
- `__future__`
- `app.core.bundle.manager`
- `app.models.bundle`

---

## 🤖 Agent Navigation Hints

_Use these tags to find related concept files:_

`okf` · `metadata` · `scanner` · `optimization` · `retrieval` · `frontmatter`
