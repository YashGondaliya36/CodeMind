---
type: api
title: Backend Health Check Endpoint
description: This module provides a GET /health endpoint to verify the operational status of the backend server and the Gemini API. It is designed for use by monitoring tools, container orchestrators, and frontend services.
resource: app/api/routes/health.py
tags:
  - health
  - monitoring
  - api
  - status
  - connectivity
timestamp: 2026-07-12
---

# Backend Health Check Endpoint

> **File:** `app/api/routes/health.py`  
> **Language:** python  
> **Lines:** 47

---

## 📋 Purpose

It enables automated system monitoring and connectivity verification for external dependencies.

## 🔧 Key Components

### Functions

#### `⚡ async health_check()`
Returns the status of the server and its external dependencies.

Response includes:
- Server uptime metadata
- Gemini API connectivity status
- Current configuration summary

## 🔗 Dependencies

Relies on FastAPI for routing and the internal llm_client module to verify external API reachability.

**Key imports:**
- `app.config`
- `app.utils.llm_client`
- `datetime`
- `fastapi`
- `platform`
- `sys`

---

## 🤖 Agent Navigation Hints

_Use these tags to find related concept files:_

`health` · `monitoring` · `api` · `status` · `connectivity`
