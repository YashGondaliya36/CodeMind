---
type: module
title: Agent LLM Response Orchestrator
description: This module manages the final stage of the agent pipeline by assembling retrieved OKF context and generating LLM responses. It provides full transparency by returning source file metadata alongside the generated answer.
resource: app/core/agent/responder.py
tags:
  - llm
  - context
  - retrieval
  - orchestration
  - prompt-engineering
timestamp: 2026-07-12
---

# Agent LLM Response Orchestrator

> **File:** `app/core/agent/responder.py`  
> **Language:** python  
> **Lines:** 152

---

## 📋 Purpose

It bridges the gap between raw data retrieval and human-readable answers while maintaining provenance for AI-generated content.

## 🔧 Key Components

### Functions

#### `answer_question(request)`
Core agent entrypoint — takes a ChatRequest, runs the full
selective retrieval pipeline, and returns a grounded answer.

Args:
    request: ChatRequest with repo_name, question, and max_files.

Return

#### `_build_context_block(retrieved)`
Format the retrieved OKF files into a clean context block for the prompt.
Each file is clearly delimited so the LLM can reference them separately.

#### `_build_answer_prompt(question, repo_name, context)`
Build the final LLM prompt with injected OKF context.

#### `_answer_without_context(question, repo_name)`
Fallback: answer when no relevant OKF files were found.

## 🔗 Dependencies

Relies on internal retriever and metadata_scanner modules for context gathering and the llm_client for model interaction.

**Key imports:**
- `__future__`
- `app.config`
- `app.core.agent.metadata_scanner`
- `app.core.agent.retriever`
- `app.models.chat`
- `app.utils.llm_client`

---

## 🤖 Agent Navigation Hints

_Use these tags to find related concept files:_

`llm` · `context` · `retrieval` · `orchestration` · `prompt-engineering`
