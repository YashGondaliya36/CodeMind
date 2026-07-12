---
type: module
title: Gemini LLM API Wrapper
description: This module provides a centralized interface for interacting with the Google Gemini API. It encapsulates client configuration, text generation, token counting, and connectivity verification.
resource: app/utils/llm_client.py
tags:
  - llm
  - gemini
  - api
  - utility
  - abstraction
timestamp: 2026-07-12
---

# Gemini LLM API Wrapper

> **File:** `app/utils/llm_client.py`  
> **Language:** python  
> **Lines:** 89

---

## 📋 Purpose

It decouples the application logic from specific LLM providers, allowing for seamless model swapping or provider migration.

## 🔧 Key Components

### Functions

#### `_get_client()`
Lazily configure and return a Gemini GenAI Client instance.

#### `generate_text(prompt, temperature)`
Send a prompt to Gemini and return the plain text response.

Args:
    prompt:      The full prompt string.
    temperature: Lower = more deterministic. Use 0.2 for code summaries.

Returns:
    The m

#### `count_tokens(text)`
Estimate token count for a given text string.
Used for transparency reporting in ChatResponse.

Returns:
    Approximate token count (Gemini tokenizer).

#### `check_connectivity()`
Ping the Gemini API with a minimal prompt to verify connectivity.
Used by the /health endpoint.

Returns:
    {"status": "ok", "model": "gemini-1.5-flash"} on success.
    {"status": "error", "message

## 🔗 Dependencies

It relies on the google-genai SDK and the internal app.config module for environment-specific settings.

**Key imports:**
- `app.config`
- `google`
- `google.genai`

---

## 🤖 Agent Navigation Hints

_Use these tags to find related concept files:_

`llm` · `gemini` · `api` · `utility` · `abstraction`
