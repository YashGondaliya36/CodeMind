"""
codemind_okf/core/modes.py — Slash Command Modes Engine
=========================================================
Generates IDE-specific slash command files (/plan, /execute, /debug, /review, /ship)
for Antigravity, Claude Code, GitHub Copilot, and Cursor.

Each IDE has its own directory convention:
  Antigravity  → .agents/skills/<name>/SKILL.md
  Claude Code  → .claude/commands/<name>.md
  Copilot      → .github/prompts/<name>.md
  Cursor       → .cursor/rules/<name>.md  (shared prompt format)

All modes share the same 3-file OKF state model:
  .okf/memory.md  — permanent decisions log (never reset)
  .okf/plan.md    — active feature plan (reset on /ship)
  .okf/state.md   — current workflow state (auto-updated)
"""

from __future__ import annotations

import dataclasses
from enum import Enum
from pathlib import Path
from typing import NamedTuple


# ── IDE Identifiers ────────────────────────────────────────────────────────────


class IDE(str, Enum):
    """Supported IDE targets for mode generation."""
    ANTIGRAVITY = "antigravity"
    CLAUDE      = "claude"
    COPILOT     = "copilot"
    CURSOR      = "cursor"


# ── Mode Definitions ───────────────────────────────────────────────────────────


@dataclasses.dataclass(frozen=True)
class ModeDefinition:
    """Describes a single slash command mode."""
    name: str               # slash command name (e.g. "plan")
    emoji: str              # display emoji
    title: str              # human-readable title
    description: str        # one-line description shown in IDE picker


MODES: tuple[ModeDefinition, ...] = (
    ModeDefinition(
        name="plan",
        emoji="🗺️",
        title="The Architect",
        description=(
            "Deep planning mode — understand the problem, discover codebase context, "
            "design solution options, detect conflicts, produce ordered task list"
        ),
    ),
    ModeDefinition(
        name="execute",
        emoji="⚡",
        title="The Builder",
        description=(
            "Codebase-aware implementation — load OKF context, declare changes, "
            "apply Ponytail Ladder (YAGNI-first), implement, self-verify, update plan"
        ),
    ),
    ModeDefinition(
        name="debug",
        emoji="🐛",
        title="The Detective",
        description=(
            "Scientific debugging — identify error, load module context, generate "
            "ranked hypotheses, isolate, fix, log bug to memory"
        ),
    ),
    ModeDefinition(
        name="review",
        emoji="🔍",
        title="The Quality Gate",
        description=(
            "Quality audit — compare implementation to plan, check code quality, "
            "verify architecture, output structured ✅ ⚠️ 🚨 report"
        ),
    ),
    ModeDefinition(
        name="ship",
        emoji="🚀",
        title="The Release Manager",
        description=(
            "Release mode — verify all tasks done, assess risks, generate changelog "
            "from memory, suggest version bump, archive plan"
        ),
    ),
)


# ── Generation Result ──────────────────────────────────────────────────────────


class GeneratedFile(NamedTuple):
    """Represents a single file that was (or will be) generated."""
    path: Path
    ide: IDE
    mode: str
    created: bool   # False if skipped because already exists


@dataclasses.dataclass
class ModesGenerationResult:
    """Summary of what codemind modes generation produced."""
    files: list[GeneratedFile] = dataclasses.field(default_factory=list)

    @property
    def created_count(self) -> int:
        return sum(1 for f in self.files if f.created)

    @property
    def skipped_count(self) -> int:
        return sum(1 for f in self.files if not f.created)

    @property
    def ides_touched(self) -> set[IDE]:
        return {f.ide for f in self.files if f.created}


# ── IDE Detection ──────────────────────────────────────────────────────────────


def detect_ides(project_root: Path) -> set[IDE]:
    """
    Auto-detect which IDEs are configured in a project root.

    Detection rules:
      Antigravity → .agents/ directory exists
      Claude Code → .claude/ directory exists
      Copilot     → .github/ directory exists
      Cursor      → .cursor/ directory exists OR .cursorrules file exists
    """
    detected: set[IDE] = set()

    if (project_root / ".agents").is_dir():
        detected.add(IDE.ANTIGRAVITY)
    if (project_root / ".claude").is_dir():
        detected.add(IDE.CLAUDE)
    if (project_root / ".github").is_dir():
        detected.add(IDE.COPILOT)
    if (project_root / ".cursor").is_dir() or (project_root / ".cursorrules").is_file():
        detected.add(IDE.CURSOR)

    return detected


# ── Destination Path Resolution ───────────────────────────────────────────────


def _mode_dest(project_root: Path, ide: IDE, mode: ModeDefinition) -> Path:
    """Return the destination file path for a mode in a given IDE."""
    if ide == IDE.ANTIGRAVITY:
        return project_root / ".agents" / "skills" / mode.name / "SKILL.md"
    elif ide == IDE.CLAUDE:
        return project_root / ".claude" / "commands" / f"{mode.name}.md"
    elif ide == IDE.COPILOT:
        return project_root / ".github" / "prompts" / f"{mode.name}.md"
    elif ide == IDE.CURSOR:
        return project_root / ".cursor" / "rules" / f"{mode.name}.md"
    else:
        raise ValueError(f"Unknown IDE: {ide}")


# ── Template Loading ───────────────────────────────────────────────────────────


_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "modes"


def _load_template(mode: ModeDefinition, ide: IDE) -> str:
    """
    Load the prompt template for a mode + IDE combination.

    Lookup order:
      1. templates/modes/<ide>/<mode>.md   (IDE-specific override)
      2. templates/modes/shared/<mode>.md  (shared cross-IDE prompt)
    """
    # Try IDE-specific override first
    ide_specific = _TEMPLATES_DIR / ide.value / f"{mode.name}.md"
    if ide_specific.exists():
        return ide_specific.read_text(encoding="utf-8")

    # Fall back to shared template
    shared = _TEMPLATES_DIR / "shared" / f"{mode.name}.md"
    if shared.exists():
        return shared.read_text(encoding="utf-8")

    raise FileNotFoundError(
        f"No template found for mode '{mode.name}' (IDE: {ide.value}). "
        f"Expected at: {shared}"
    )


def _render_antigravity_skill(mode: ModeDefinition, body: str) -> str:
    """Wrap shared prompt body in Antigravity SKILL.md frontmatter format."""
    return (
        f"---\n"
        f"name: {mode.name}\n"
        f"description: {mode.description}\n"
        f"---\n\n"
        f"{body.strip()}\n"
    )


def _render_claude_command(mode: ModeDefinition, body: str) -> str:
    """Wrap shared prompt body in Claude Code command frontmatter format."""
    return (
        f"---\n"
        f"description: {mode.description}\n"
        f"---\n\n"
        f"{body.strip()}\n"
    )


def _render_copilot_prompt(mode: ModeDefinition, body: str) -> str:
    """Wrap shared prompt body in GitHub Copilot prompt frontmatter format."""
    return (
        f"---\n"
        f"mode: agent\n"
        f"description: {mode.description}\n"
        f"---\n\n"
        f"{body.strip()}\n"
    )


def _render_cursor_rule(mode: ModeDefinition, body: str) -> str:
    """Wrap shared prompt body in Cursor rules frontmatter format."""
    return (
        f"---\n"
        f"description: {mode.description}\n"
        f"globs: []\n"
        f"alwaysApply: false\n"
        f"---\n\n"
        f"{body.strip()}\n"
    )


_RENDERERS = {
    IDE.ANTIGRAVITY: _render_antigravity_skill,
    IDE.CLAUDE:      _render_claude_command,
    IDE.COPILOT:     _render_copilot_prompt,
    IDE.CURSOR:      _render_cursor_rule,
}


# ── Core Generation Function ───────────────────────────────────────────────────


def generate_modes(
    project_root: Path,
    ides: set[IDE],
    overwrite: bool = False,
) -> ModesGenerationResult:
    """
    Generate slash command mode files for all requested IDEs.

    Args:
        project_root: Absolute path to the project root directory.
        ides:         Set of IDE targets to generate for.
        overwrite:    If True, overwrite existing mode files. Default skips them.

    Returns:
        ModesGenerationResult summarising what was created/skipped.
    """
    result = ModesGenerationResult()

    for ide in sorted(ides, key=lambda x: x.value):
        renderer = _RENDERERS[ide]

        for mode in MODES:
            dest = _mode_dest(project_root, ide, mode)

            # Skip if exists and overwrite not requested
            if dest.exists() and not overwrite:
                result.files.append(GeneratedFile(dest, ide, mode.name, created=False))
                continue

            # Load shared body + render with IDE-specific wrapper
            try:
                body = _load_template(mode, ide)
                content = renderer(mode, body)
            except FileNotFoundError as exc:
                # Template missing — skip silently, caller can log
                result.files.append(GeneratedFile(dest, ide, mode.name, created=False))
                continue

            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            result.files.append(GeneratedFile(dest, ide, mode.name, created=True))

    return result


# ── OKF State File Initialisation ─────────────────────────────────────────────


_PLAN_TEMPLATE = """\
# Active Plan

> Created by `/plan` mode. Updated by `/execute`. Archived by `/ship`.
> This file is shared across all IDEs. Do NOT edit manually during active work.

## Goal
<!-- /plan will fill this in -->

## Architecture Decision
<!-- /plan will fill this in -->

## Tasks
<!-- Format: - [ ] Task description -->

"""

_STATE_TEMPLATE = """\
# Current Workflow State

> Auto-updated by CodeMind slash command modes. Do not edit manually.

## Status
mode: idle
active_task: none
phase: 0
last_updated: never

## Notes
<!-- /plan, /execute, /debug, /review, /ship update this file automatically -->
"""


def init_okf_state_files(project_root: Path, overwrite: bool = False) -> list[Path]:
    """
    Ensure .okf/plan.md and .okf/state.md exist with starter templates.
    .okf/memory.md is managed by the MCP layer and intentionally not touched here.

    Args:
        project_root: Project root directory.
        overwrite:    If True, reset existing files to blank templates.

    Returns:
        List of paths that were newly created.
    """
    okf_dir = project_root / ".okf"
    okf_dir.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []

    files = {
        okf_dir / "plan.md": _PLAN_TEMPLATE,
        okf_dir / "state.md": _STATE_TEMPLATE,
    }

    for path, template in files.items():
        if not path.exists() or overwrite:
            path.write_text(template, encoding="utf-8")
            created.append(path)

    return created
