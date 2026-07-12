---
type: api
title: Repository Analysis API Orchestrator
description: This module provides FastAPI endpoints to manage the asynchronous lifecycle of repository analysis, from cloning and AST parsing to OKF bundle generation. It orchestrates the producer pipeline using background tasks to ensure non-blocking API responses.
resource: app/api/routes/repo.py
tags:
  - fastapi
  - orchestration
  - background-tasks
  - okf
  - repository-analysis
timestamp: 2026-07-12
---

# Repository Analysis API Orchestrator

> **File:** `app/api/routes/repo.py`  
> **Language:** python  
> **Lines:** 216

---

## 📋 Purpose

It enables developers to trigger and monitor automated repository-to-OKF conversion processes without waiting for long-running LLM and parsing operations.

## 🔧 Key Components

### Functions

#### `_update_job(job_id)`
Merge kwargs into the job state dict.

#### `_run_analysis(job_id, request)`
The full Producer pipeline — runs in the background.
Updates _jobs[job_id] at each step so the frontend can poll progress.

#### `⚡ async analyze_repo(request, background_tasks)`
Submit a repository for analysis. Returns immediately with a `job_id`.
Poll `GET /repo/status/{job_id}` to track progress.

The pipeline: clone → crawl → parse → summarize (LLM) → write OKF files → in

#### `⚡ async get_job_status(job_id)`
Returns the current status and progress of a background analysis job.
Poll this every 2–3 seconds from the frontend.

#### `⚡ async list_analyzed_repos()`
Returns all repos that have a generated OKF bundle on disk.

#### `⚡ async delete_repo_bundle(repo_name)`
Permanently deletes the OKF bundle for the given repo.

## 🔗 Dependencies

It relies on the core producer modules for crawling, parsing, and summarization, alongside git utilities for repository management.

**Key imports:**
- `__future__`
- `app.config`
- `app.core.bundle.index_builder`
- `app.core.bundle.manager`
- `app.core.producer.crawler`
- `app.core.producer.okf_writer`
- `app.core.producer.parser`
- `app.core.producer.summarizer`

---

## 🤖 Agent Navigation Hints

_Use these tags to find related concept files:_

`fastapi` · `orchestration` · `background-tasks` · `okf` · `repository-analysis`
