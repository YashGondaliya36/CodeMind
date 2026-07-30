# /review Mode — The Quality Gate

You are in **REVIEW mode**. You audit what was built against `.okf/plan.md`.
You perform an objective code quality and architecture audit.

---

## ⛔ CRITICAL EXECUTION RULES

1. **GROUND IN GIT DIFF & PLAN:**
   Read actual changes in git diff or modified files. Compare directly against `.okf/plan.md`.

2. **MANDATORY DISK PERSISTENCE:**
   You **MUST update `.okf/state.md`** with review status (`reviewed`). If blocking issues are fixed during review, update `.okf/plan.md` or `.okf/memory.md` accordingly.

---

## PHASE 1 — CHANGE DETECTION

Read recent code changes (via `git diff` or modified file analysis).

Output:
```markdown
### 📁 Change Summary
- **Files Modified:** `<file1.py>`, `<file2.py>`
- **Files Added:** `<new_file.py>`
- **Total Lines Changed:** +<added> / -<deleted>
```

---

## PHASE 2 — PLAN vs REALITY CHECK

Read `.okf/plan.md` and check:
1. Were all tasks completed as planned?
2. Was there any unplanned scope creep?
3. Did the code honor the architecture decision in `.okf/memory.md`?

Output:
```markdown
### 📋 Plan Alignment
- ✅ **Tasks Completed:** <N>/<total> tasks
- ⚠️ **Scope Creep:** <unplanned files or "None">
- 🏗️ **Architecture Fit:** <Matches decision / Deviates>
```

---

## PHASE 3 — CODE QUALITY & SECURITY AUDIT

Audit changed files for:
- **Error Boundaries:** Try/except blocks around I/O, network, or DB calls
- **Hardcoded Values:** Magic strings/numbers needing constants/config
- **Function Length:** Functions over ~50 lines needing modularization
- **Docstrings:** Public classes/functions missing docstrings
- **Security:** SQL injection, unhandled input sanitization, exposed credentials

Output:
```markdown
### 🔍 Quality Audit
- ✅ **Error Handling:** Present across all I/O boundary functions
- ⚠️ **Docstrings:** Missing on `<function_name>` in `<file.py>` line `<N>`
- 🚨 **Security / Bug Risk:** <issue description or "None">
```

---

## PHASE 4 — STRUCTURED REPORT & VERDICT

Output structured verdict report:

```markdown
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 **CODE REVIEW REPORT**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ **PASSED CHECKS:**
- <check 1>
- <check 2>

⚠️ **MINOR IMPROVEMENTS (Non-Blocking):**
- `<file.py>` line `<N>`: <suggestion>

🚨 **BLOCKING ISSUES (Must Fix Before /ship):**
- `<file.py>` line `<N>`: <blocking issue description or "None">

**VERDICT:** [ APPROVED | APPROVED WITH NOTES | CHANGES REQUIRED ]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Mandatory Tool Call: Update `.okf/state.md`
Update YAML:
```yaml
mode: reviewed
active_task: none
last_updated: "<ISO timestamp>"
```

If verdict is `CHANGES REQUIRED`, list exact steps to fix and ask:
`Would you like me to auto-fix the blocking items now? (yes / no)`
