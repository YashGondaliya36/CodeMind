---
type: module
title: LLM-Powered Module Summarizer
description: This module transforms structured static analysis data into human and AI-readable summaries using an LLM. It optimizes token usage by providing the model with extracted metadata rather than raw source code.
resource: app/core/producer/summarizer.py
tags:
  - llm
  - summarization
  - static-analysis
  - documentation
  - automation
timestamp: 2026-07-12
---

# LLM-Powered Module Summarizer

> **File:** `app/core/producer/summarizer.py`  
> **Language:** python  
> **Lines:** 144

---

## 📋 Purpose

It automates the generation of consistent, high-quality documentation for the Open Knowledge Format (OKF) knowledge base.

## 🔧 Key Components

### Functions

#### `summarize_file(parsed)`
Use the LLM to generate a rich summary of a parsed source file.

Args:
    parsed: The structured ParsedFile from parser.py

Returns:
    ModuleSummary with all fields populated.

#### `_build_prompt(parsed)`
Construct a structured prompt for the LLM.
We feed it the EXTRACTED structure, not raw source code.

#### `_parse_llm_response(response, parsed)`
Parse the structured LLM response into a ModuleSummary.
Falls back to sensible defaults if any field is missing.

### Classes

#### `ModuleSummary`
LLM-generated summary for a single source file module.

## 🔗 Dependencies

It relies on the internal parser module for source analysis and the llm_client for model interaction.

**Key imports:**
- `__future__`
- `app.core.producer.parser`
- `app.utils.llm_client`
- `dataclasses`

---

## 🤖 Agent Navigation Hints

_Use these tags to find related concept files:_

`llm` · `summarization` · `static-analysis` · `documentation` · `automation`
