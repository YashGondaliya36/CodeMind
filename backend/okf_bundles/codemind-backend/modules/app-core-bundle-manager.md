---
type: module
title: OKF Bundle Data Access Layer
description: This module provides low-level CRUD operations for managing OKF concept files within repository bundles. It handles file system interactions, metadata parsing, and bundle enumeration without invoking LLM services.
resource: app/core/bundle/manager.py
tags:
  - okf
  - bundle
  - crud
  - filesystem
  - storage
timestamp: 2026-07-12
---

# OKF Bundle Data Access Layer

> **File:** `app/core/bundle/manager.py`  
> **Language:** python  
> **Lines:** 217

---

## 📋 Purpose

It abstracts file system complexity to provide a consistent interface for the application to read and manage structured OKF knowledge files.

## 🔧 Key Components

### Functions

#### `get_bundle_path(repo_name)`
Return the root Path of a repo's OKF bundle directory.

#### `bundle_exists(repo_name)`
Return True if an OKF bundle exists for the given repo.

#### `_parse_okf_file(file_path, bundle_root)`
Parse a single OKF Markdown file and return its frontmatter as OKFFileMeta.
Returns None if the file cannot be parsed (malformed YAML, missing type, etc.).

#### `_parse_okf_file_detail(file_path, bundle_root)`
Parse a single OKF file and return both frontmatter + full body content.

#### `list_bundle_files(repo_name)`
List all OKF files in a bundle and return their metadata.

Args:
    repo_name: The bundle slug.

Returns:
    BundleIndex with all parsed OKF file metadata.

Raises:
    FileNotFoundError: If no bund

#### `get_file_detail(repo_name, filename)`
Retrieve the full content + metadata of one OKF file.

Args:
    repo_name: Bundle slug.
    filename:  Relative path within the bundle (e.g. "modules/auth-module.md").

Returns:
    OKFFileDetail wit

#### `get_all_metadata(repo_name)`
Return frontmatter metadata for ALL files in a bundle.
Used by the agent's metadata scanner for fast relevance scoring.
This is intentionally cheap — NO full file reads.

#### `list_repos()`
Enumerate all repo bundles that exist in the bundles directory.

Returns:
    List of dicts with repo_name, bundle_path, total_okf_files, last_updated.

#### `delete_bundle(repo_name)`
Delete an entire OKF bundle.

Returns:
    True if deleted, False if it didn't exist.

## 🔗 Dependencies

Relies on the frontmatter library for metadata extraction and internal path utilities for file system navigation.

**Key imports:**
- `__future__`
- `app.config`
- `app.models.bundle`
- `app.utils.file_utils`
- `datetime`
- `frontmatter`
- `pathlib`
- `typing`

---

## 🤖 Agent Navigation Hints

_Use these tags to find related concept files:_

`okf` · `bundle` · `crud` · `filesystem` · `storage`
