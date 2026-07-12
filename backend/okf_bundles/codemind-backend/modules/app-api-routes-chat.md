---
type: api
title: Chat Agent API Endpoint
description: This module provides the primary FastAPI endpoint for processing natural language queries against analyzed repositories. It acts as a thin interface that delegates request handling to the core agent responder.
resource: app/api/routes/chat.py
tags:
  - chat
  - api
  - fastapi
  - agent
  - interface
timestamp: 2026-07-12
---

# Chat Agent API Endpoint

> **File:** `app/api/routes/chat.py`  
> **Language:** python  
> **Lines:** 53

---

## 📋 Purpose

It exposes a standardized interface for developers to interact with the AI knowledge base via natural language.

## 🔧 Key Components

### Functions

#### `⚡ async ask(request)`
Ask a natural language question about any analyzed repository.

**How it works (the OKF selective retrieval pipeline):**
1. Scans frontmatter of ALL OKF files in the bundle (fast, cheap)
2. Scores eac

## 🔗 Dependencies

It relies on the internal core agent responder and bundle manager modules to process and fulfill chat requests.

**Key imports:**
- `app.core.agent.responder`
- `app.core.bundle.manager`
- `app.models.chat`
- `fastapi`

---

## 🤖 Agent Navigation Hints

_Use these tags to find related concept files:_

`chat` · `api` · `fastapi` · `agent` · `interface`
