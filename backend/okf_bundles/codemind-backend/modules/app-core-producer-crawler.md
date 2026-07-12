---
type: module
title: Repository Source File Crawler
description: This module traverses local directories to identify and collect source files suitable for AI analysis. It implements smart filtering to exclude build artifacts, vendored libraries, and test fixtures.
resource: app/core/producer/crawler.py
tags:
  - crawler
  - filesystem
  - automation
  - filtering
  - repository
timestamp: 2026-07-12
---

# Repository Source File Crawler

> **File:** `app/core/producer/crawler.py`  
> **Language:** python  
> **Lines:** 136

---

## 📋 Purpose

It automates the discovery and categorization of relevant source code while ignoring noise to ensure efficient downstream processing.

## 🔧 Key Components

### Functions

#### `crawl_repo(repo_path, languages)`
Walk a repository and collect all analysable source files.

Args:
    repo_path: Absolute path to the cloned/local repository root.
    languages: List of languages to include (e.g. ["python", "javasc

#### `_is_in_skip_dir(file_path, repo_root)`
Return True if any part of the file's path is a skip directory.

#### `_extension_to_language(ext)`
Map a file extension back to its language name.

### Classes

#### `CrawledFile`
Represents a single source file found during crawling.

#### `CrawlResult`
Result of crawling a full repository.
**Methods:** `total_files`

## 🔗 Dependencies

Relies on the standard pathlib library and internal app.utils.file_utils for path manipulation and file system operations.

**Key imports:**
- `__future__`
- `app.utils.file_utils`
- `dataclasses`
- `pathlib`

---

## 🤖 Agent Navigation Hints

_Use these tags to find related concept files:_

`crawler` · `filesystem` · `automation` · `filtering` · `repository`
