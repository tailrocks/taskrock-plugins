#!/usr/bin/env python3
"""Check the taskrock plugin package. Exit 0 when every rule holds.

Run from the repository root: python3 scripts/check.py
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "taskrock"
SKILLS = PLUGIN / "skills"
MANIFESTS = [
    ROOT / ".claude-plugin" / "marketplace.json",
    ROOT / ".agents" / "plugins" / "marketplace.json",
    PLUGIN / ".claude-plugin" / "plugin.json",
    PLUGIN / ".codex-plugin" / "plugin.json",
    PLUGIN / ".muse-plugin" / "plugin.json",
    PLUGIN / ".grok-plugin" / "plugin.json",
    PLUGIN / ".antigravity-plugin" / "plugin.json",
]
# Files where the word may appear: history and the owner's docs.
TAILROCKS_ALLOWED = {"README.md", "CHANGELOG.md"}
COMMAND = re.compile(r"\btaskrock ([a-z][a-z-]*)")
NOT_COMMANDS = {"command", "repository", "issue", "plan", "goal", "plugin", "skills"}

problems: list[str] = []


def problem(path: Path, message: str) -> None:
    problems.append(f"{path.relative_to(ROOT)}: {message}")


def versions(version: str) -> None:
    for path in MANIFESTS:
        data = json.loads(path.read_text())
        found = [data.get("version")] + [p.get("version") for p in data.get("plugins", [])]
        for value in found:
            if value is not None and value != version:
                problem(path, f"version {value} differs from VERSION {version}")
        if all(value is None for value in found):
            problem(path, "has no version")


def front_matter(text: str) -> dict[str, str]:
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    keys = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith(" "):
            keys[key.strip()] = value.strip()
    return keys


def skills() -> list[str]:
    names = sorted(path.name for path in SKILLS.iterdir() if path.is_dir())
    for name in names:
        path = SKILLS / name / "SKILL.md"
        if not path.is_file():
            problem(SKILLS / name, "has no SKILL.md")
            continue
        keys = front_matter(path.read_text())
        if not keys.get("name") or "description" not in keys:
            problem(path, "front matter needs name and description")
        elif keys["name"] != name:
            problem(path, f"name {keys['name']} differs from folder {name}")
    return names


def muse(names: list[str]) -> None:
    path = PLUGIN / ".muse-plugin" / "plugin.json"
    listed = json.loads(path.read_text())["capabilities"]["skills"]
    ids = sorted(entry["id"] for entry in listed)
    for name in sorted(set(names) - set(ids)):
        problem(path, f"skill {name} is not listed")
    for name in sorted(set(ids) - set(names)):
        problem(path, f"skill {name} is listed but has no folder")
    for entry in listed:
        if not (PLUGIN / entry["path"]).is_file():
            problem(path, f"path {entry['path']} does not exist")


def commands() -> None:
    named: dict[str, Path] = {}
    for path in SKILLS.glob("*/SKILL.md"):
        for block in re.findall(r"```sh\n(.*?)```", path.read_text(), re.S):
            for command in COMMAND.findall(block):
                if command not in NOT_COMMANDS:
                    named.setdefault(command, path)
        for command in re.findall(r"`taskrock ([a-z][a-z-]*)", path.read_text()):
            if command not in NOT_COMMANDS:
                named.setdefault(command, path)
    for command, path in sorted(named.items()):
        try:
            result = subprocess.run(
                ["taskrock", command, "--help"], capture_output=True, text=True, check=False
            )
        except FileNotFoundError:
            problem(path, "taskrock is not installed, so its commands cannot be checked")
            return
        if result.returncode != 0:
            problem(path, f"names `taskrock {command}`, which the installed taskrock lacks")


GH_ISSUE = re.compile(r"gh issue create|gh issue edit[^\n]*--body")


def gh_issue() -> None:
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        for match in GH_ISSUE.findall(path.read_text()):
            problem(path, f"names `{match}`. Use taskrock apply or taskrock edit")


def routing() -> None:
    table = (ROOT / "scripts" / "routing.md").read_text()
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        if table not in path.read_text():
            problem(path, "does not contain the text of scripts/routing.md")


BANNED_IN_SKILLS = [
    (
        re.compile(r"(?:do not|don't|never)\s+make\s+this\s+task\s+wait", re.I),
        "a finding must not run outside the goal",
    ),
    (
        re.compile(r"(?:^|\n)\s*(?:[-*]|\d+\.)?\s*defer\b|\bdefer\s*[:\u2013\u2014-]", re.I),
        "has a `Defer` route. A follow-up is filed under the link and built in the run",
    ),
    (
        re.compile(
            r"(?:bugs?|friction)[^.\n]{0,80}?(?:do(?:es)?\s+not|don't|doesn't|never|not)\s+count(?:ed)?\b"
            r"|no\s+milestone,?\s+so\b",
            re.I,
        ),
        "says that Bugs do not count or have no milestone",
    ),
]
BUILD_REQUEST = re.compile(
    r"\b(?:do|implement|build)\s+(?:`?<[^>`]*(?:link|url)[^>`]*>`?|`?https?://\S+)", re.I
)
SKILL_NAME = re.compile(r"taskrock-(?:goal|issue|plan|triage|setup)")
MARKUP = re.compile(r"[*_`]")


def sentences(text: str) -> list[str]:
    """Split Markdown into sentences. A wrapped paragraph and a folded front-matter value join up."""
    units: list[str] = []
    paragraph: list[str] = []
    fenced = False

    def flush() -> None:
        if paragraph:
            units.extend(re.split(r"(?<=[.!?])\s+(?=[A-Z\"`<])", " ".join(paragraph)))
            paragraph.clear()

    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            flush()
            fenced = not fenced
        elif fenced:
            units.append(line)
        elif not line.strip():
            flush()
        elif re.match(r"\s*(?:[-*]\s|\d+\.\s|\||#)", line):
            flush()
            paragraph.append(line.strip())
        else:
            paragraph.append(line.strip())
    flush()
    return units


def scope() -> None:
    """A build request names its skill, and no skill sends a finding outside the goal."""
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        text = MARKUP.sub("", path.read_text())
        flat = re.sub(r"[ \t]+", " ", text)
        for pattern, why in BANNED_IN_SKILLS:
            match = pattern.search(flat)
            if match:
                problem(path, f"contains `{match.group(0).strip()}`: {why}")
    docs = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")), *sorted(SKILLS.glob("*/SKILL.md"))]
    for path in docs:
        for sentence in sentences(path.read_text()):
            if BUILD_REQUEST.search(sentence) and not SKILL_NAME.search(sentence):
                problem(path, f"tells the user to type `{BUILD_REQUEST.search(sentence).group(0)}` without naming a taskrock skill: {sentence.strip()[:80]}")


def tailrocks() -> None:
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if not path.is_file() or relative.parts[0] in {".git", "docs"}:
            continue
        if str(relative) in TAILROCKS_ALLOWED or relative == Path("scripts/check.py"):
            continue
        if "tailrocks-" in path.read_text(errors="ignore"):
            problem(path, "contains `tailrocks-`")


def main() -> int:
    version = (ROOT / "VERSION").read_text().strip()
    versions(version)
    names = skills()
    muse(names)
    commands()
    gh_issue()
    routing()
    scope()
    tailrocks()
    for line in problems:
        print(line)
    if problems:
        print(f"error: {len(problems)} problems")
        return 1
    print(f"OK {len(names)} skills, version {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
