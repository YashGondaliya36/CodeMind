---
type: module
title: Selective OKF Context Retriever
description: Implements a keyword-based relevance scoring algorithm to filter OKF file metadata. It identifies the most pertinent files for a query to minimize LLM token consumption.
resource: app/core/agent/retriever.py
tags:
  - retrieval
  - optimization
  - keyword
  - metadata
  - agent
  - efficiency
timestamp: 2026-07-12
---

# Selective OKF Context Retriever

> **File:** `app/core/agent/retriever.py`  
> **Language:** python  
> **Lines:** 163

---

## 📋 Purpose

It solves the problem of high token costs by enabling targeted retrieval of relevant context instead of processing entire knowledge bases.

## 🔧 Key Components

### Functions

#### `retrieve_relevant_files(repo_name, question, max_files, min_score)`
Score all OKF files in a bundle against the user's question and return
the most relevant ones with their full content loaded.

Args:
    repo_name: Bundle slug.
    question:  The user's natural langu

#### `_extract_keywords(text)`
Tokenise a question into meaningful keywords.
Lowercases, removes punctuation, strips stop words.

#### `_score_file(meta, keywords)`
Compute a relevance score for an OKF file against a set of keywords.

Score = sum of weighted keyword hits across each metadata field.
Normalised to [0, 1] range.

### Classes

#### `ScoredFile`
A metadata file paired with its relevance score.

## 🔗 Dependencies

Relies on internal metadata scanning and bundle management modules to process repository file structures.

**Key imports:**
- `__future__`
- `app.core.agent.metadata_scanner`
- `app.core.bundle.manager`
- `app.models.bundle`
- `dataclasses`
- `re`

---

## 🤖 Agent Navigation Hints

_Use these tags to find related concept files:_

`retrieval` · `optimization` · `keyword` · `metadata` · `agent` · `efficiency`
