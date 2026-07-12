---
type: config
title: Centralized Application Configuration Management
description: This module utilizes Pydantic-Settings to load and manage application configuration from environment variables or .env files. It serves as the single source of truth for settings, ensuring all other modules access configuration through a unified interface.
resource: app/config.py
tags:
  - pydantic
  - settings
  - environment
  - configuration
  - validation
timestamp: 2026-07-12
---

# Centralized Application Configuration Management

> **File:** `app/config.py`  
> **Language:** python  
> **Lines:** 65

---

## 📋 Purpose

It prevents hardcoded values and scattered environment variable access by providing a type-safe, centralized configuration object.

## 🔧 Key Components

### Classes

#### `Settings` ← `BaseSettings`
All configuration lives here. Pydantic-Settings will:
1. Look for matching environment variables (case-insensitive).
2. Fall back to the .env file if present.
3. Use the default values below as last r
**Methods:** `bundles_path`, `clone_path`, `is_dev`

## 🔗 Dependencies

Relies on pydantic-settings for environment variable parsing and validation.

**Key imports:**
- `pathlib`
- `pydantic_settings`

---

## 🤖 Agent Navigation Hints

_Use these tags to find related concept files:_

`pydantic` · `settings` · `environment` · `configuration` · `validation`
