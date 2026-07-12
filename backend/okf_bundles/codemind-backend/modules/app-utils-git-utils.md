---
type: module
title: Git Repository Utility Module
description: This module provides helper functions for validating, cloning, and managing Git repository sources from both remote GitHub URLs and local filesystems. It abstracts Git operations to maintain a clean separation of concerns within the application.
resource: app/utils/git_utils.py
tags:
  - git
  - repository
  - automation
  - utility
  - filesystem
timestamp: 2026-07-12
---

# Git Repository Utility Module

> **File:** `app/utils/git_utils.py`  
> **Language:** python  
> **Lines:** 134

---

## 📋 Purpose

It centralizes repository handling logic to ensure consistent source validation and file management across the application.

## 🔧 Key Components

### Functions

#### `is_github_url(source)`
Return True if the source string looks like a valid GitHub repo URL.

#### `is_local_path(source)`
Return True if the source string is an existing local directory.

#### `validate_source(source)`
Validate the repo source and return its type.

Returns:
    "github" | "local"

Raises:
    ValueError: If source is neither a valid GitHub URL nor a local directory.

#### `clone_repo(github_url, repo_name)`
Clone a GitHub repository into the temp clone directory.

Args:
    github_url: Full GitHub HTTPS URL (e.g. https://github.com/owner/repo)
    repo_name:  Slug used as the local folder name.

Returns:

#### `get_repo_path(source, repo_name)`
Resolve the local filesystem path for a repo source.

- If source is a GitHub URL  → clone (or pull) and return clone path.
- If source is a local path  → return as-is.

#### `extract_repo_name_from_url(url)`
Extract a clean repo name from a GitHub URL.
e.g. https://github.com/openai/gpt-2.git → gpt-2

#### `count_source_files(repo_path)`
Count how many analysable source files exist in the repository.

## 🔗 Dependencies

Relies on the GitPython library for repository operations and internal file utilities for path management.

**Key imports:**
- `__future__`
- `app.config`
- `app.utils.file_utils`
- `git`
- `pathlib`
- `re`

---

## 🤖 Agent Navigation Hints

_Use these tags to find related concept files:_

`git` · `repository` · `automation` · `utility` · `filesystem`
