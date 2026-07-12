---
type: module
title: Source Code AST Parser
description: This module performs static analysis on source files to extract structured metadata such as classes, functions, and imports. It processes files without LLM intervention to provide efficient, deterministic input for downstream summarization tasks.
resource: app/core/producer/parser.py
tags:
  - static-analysis
  - ast
  - parsing
  - optimization
  - metadata
timestamp: 2026-07-12
---

# Source Code AST Parser

> **File:** `app/core/producer/parser.py`  
> **Language:** python  
> **Lines:** 264

---

## 📋 Purpose

It reduces token consumption and improves LLM context quality by converting raw source code into structured representations.

## 🔧 Key Components

### Functions

#### `parse_file(file_path, relative_path, language)`
Parse a source file and extract structured information.

Args:
    file_path:     Absolute path to the source file.
    relative_path: Relative path from repo root (for display only).
    language:   

#### `_parse_python(source, file_path, line_count)`
Parse Python source using the built-in `ast` module.

#### `_extract_python_function(node)`

#### `_extract_python_class(node)`

#### `_extract_python_imports(tree)`
Extract all import statements from a Python AST.

#### `_parse_js_ts(source, file_path, language, line_count)`
Lightweight regex-based parser for JS/TS files.
Extracts function names, class names, and imports.
Not as precise as AST but covers 90% of practical cases.

#### `_extract_js_functions(source)`
Extract function declarations from JS/TS source.

#### `_extract_js_classes(source)`
Extract class declarations from JS/TS source.

#### `_extract_js_imports(source)`
Extract import/require statements from JS/TS source.

### Classes

#### `FunctionInfo`
Represents a parsed function or method.

#### `ClassInfo`
Represents a parsed class definition.

#### `ParsedFile`
Structured representation of a source file after static analysis.
This is passed to the summarizer to build the LLM prompt.

## 🔗 Dependencies

It relies on the Python standard library's ast module for Python parsing and custom regex patterns for JavaScript/TypeScript analysis.

**Key imports:**
- `__future__`
- `app.utils.file_utils`
- `ast`
- `dataclasses`
- `pathlib`
- `re`

---

## 🤖 Agent Navigation Hints

_Use these tags to find related concept files:_

`static-analysis` · `ast` · `parsing` · `optimization` · `metadata`
