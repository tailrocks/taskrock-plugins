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
# A command whose subcommand is the second word, such as `taskrock pr status`.
TWO_WORD_COMMANDS = {"pr"}
COMMAND_WORDS = rf"(?:{'|'.join(sorted(TWO_WORD_COMMANDS))} [a-z][a-z-]*|[a-z][a-z-]*)"
COMMAND = re.compile(rf"\btaskrock ({COMMAND_WORDS})")
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
                if command.split()[0] not in NOT_COMMANDS:
                    named.setdefault(command, path)
        for command in re.findall(rf"`taskrock ({COMMAND_WORDS})", path.read_text()):
            if command.split()[0] not in NOT_COMMANDS:
                named.setdefault(command, path)
    for command, path in sorted(named.items()):
        try:
            result = subprocess.run(
                ["taskrock", *command.split(), "--help"], capture_output=True, text=True, check=False
            )
        except FileNotFoundError:
            problem(path, "taskrock is not installed, so its commands cannot be checked")
            return
        if result.returncode != 0:
            problem(path, f"names `taskrock {command}`, which the installed taskrock lacks")


GH_ISSUE = re.compile(r"gh issue create|gh issue edit[^\n]*--body")


FLAG = re.compile(r"(?<![\w-])--[a-z][a-z-]*")
TASKROCK_LINE = re.compile(rf"\btaskrock ({COMMAND_WORDS})(.*)")


def flags() -> None:
    """Each flag that a skill passes to a taskrock command is in the --help of that command."""
    named: dict[tuple[str, str], Path] = {}
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        text = path.read_text()
        lines = [line for block in re.findall(r"```sh\n(.*?)```", text, re.S) for line in block.splitlines()]
        lines += re.findall(r"`(taskrock [^`]*)`", text)
        for line in lines:
            match = TASKROCK_LINE.search(line)
            if not match or match.group(1).split()[0] in NOT_COMMANDS:
                continue
            rest = re.split(r"\s(?:\||&&|;)\s", match.group(2))[0]
            for flag in FLAG.findall(rest):
                named.setdefault((match.group(1), flag), path)
    helps: dict[str, str] = {}
    for (command, flag), path in sorted(named.items()):
        if command not in helps:
            try:
                result = subprocess.run(
                    ["taskrock", *command.split(), "--help"], capture_output=True, text=True, check=False
                )
            except FileNotFoundError:
                return
            helps[command] = result.stdout
        if not re.search(rf"(?<![\w-]){re.escape(flag)}(?![\w-])", helps[command]):
            problem(path, f"names `taskrock {command} {flag}`, which the installed taskrock lacks")


def gh_issue() -> None:
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        for match in GH_ISSUE.findall(path.read_text()):
            problem(path, f"names `{match}`. Use taskrock apply or taskrock edit")


GH_MILESTONE_EDIT = re.compile(r"gh issue edit(?:[^\n]*\\\n)*[^\n]*--milestone")
FRONT_MATTER = re.compile(r"^\+\+\+\n(.*?)\n\+\+\+$", re.S | re.M)
TOML_FENCE = re.compile(r"```toml\n(.*?)```", re.S)
FRONT_TYPE = re.compile(r'^type = "([^"]*)"$', re.M)
FRONT_PARENT = re.compile(r'^parent = "(?:https://github\.com/|<link)', re.M)
LEAVE_OUT = re.compile(r"leave out that line", re.I)
STEP_2 = re.compile(r"^### 2\. .*?(?=(?:^### )|(?:\Z))", re.S | re.M)


def filing() -> None:
    """A filed issue has a parent, apply sets its milestone, and the goal attaches loose issues."""
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        text = path.read_text()
        if GH_MILESTONE_EDIT.search(text):
            problem(path, "runs `gh issue edit --milestone`. apply sets the milestone of a filed issue from its parent")
        if LEAVE_OUT.search(text):
            problem(path, 'says "leave out that line". A filed issue always has a parent')
        if path.parent.name == "taskrock-plan":
            continue
        for block in FRONT_MATTER.findall(text) + TOML_FENCE.findall(text):
            kind = FRONT_TYPE.search(block)
            if kind and kind.group(1) != "Initiative" and not FRONT_PARENT.search(block):
                problem(path, f'an example of type {kind.group(1)} has no parent as a full link: parent = "https://github.com/<owner>/<repo>/issues/<number>"')
    goal = SKILLS / "taskrock-goal" / "SKILL.md"
    step_2 = STEP_2.search(goal.read_text())
    if not step_2 or "`loose`" not in step_2.group(0):
        problem(goal, "step 2 does not name the key `loose` of taskrock ready")


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
        "has a `Defer:` route. A follow-up is filed under the link and built in the run",
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
        text = path.read_text()
        for sentence in sentences(text):
            found = BUILD_REQUEST.search(sentence)
            if found and not SKILL_NAME.search(sentence):
                at = text.find(sentence.strip()[:20])
                if at < 0:
                    at = max(text.find(found.group(0)), 0)
                line = text.count("\n", 0, at) + 1
                problem(path, f"line {line} tells the user to type `{found.group(0).strip('`')}` without naming a taskrock skill")


CLAIM_RULE = (
    "Write no code for an issue that taskrock claim did not take: its Status is In Progress "
    "and its branch feat/issue-<number> is on GitHub. A blocked task waits until its blockers "
    "close, or until the manager of taskrock-goal takes it with taskrock claim --stacked, and an "
    "issue in Triage waits until taskrock-triage sets it to Todo."
)
CLAIM_SKILLS = ["taskrock-goal", "taskrock-issue", "taskrock-triage"]
TITLE_EXAMPLE = '"taskrock 0.2.1: …"'
TITLE_RULE = (
    "A title starts with a capital letter, a digit or a code span in backticks. A lowercase "
    f"letter is allowed only for the name of the repository, as in {TITLE_EXAMPLE}."
)
TITLE_SKILLS = ["taskrock-goal", "taskrock-issue", "taskrock-plan", "taskrock-triage"]
NEW_BRANCH = re.compile(r"git (?:switch -c|checkout -b|branch )")


def claim_rule() -> None:
    for name in CLAIM_SKILLS:
        path = SKILLS / name / "SKILL.md"
        if CLAIM_RULE not in path.read_text():
            problem(path, "does not state the claim rule: Write no code for an issue that taskrock claim did not take")


STACKED_CLAIM = re.compile(r"\btaskrock claim\b[^\n]*--stacked(?![\w-])")
STACKED_SKILLS = {"taskrock-goal"}


def stacked_claims() -> None:
    """Only the manager in taskrock-goal runs taskrock claim --stacked."""
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        if path.parent.name in STACKED_SKILLS:
            continue
        for block in re.findall(r"```sh\n(.*?)```", path.read_text(), re.S):
            for line in block.splitlines():
                if STACKED_CLAIM.search(line):
                    problem(path, "runs `taskrock claim --stacked`. Only the manager in taskrock-goal stacks a task")


STACK_RULE = (
    "Merge a pull request only when its base is the default branch, and retarget every open "
    "pull request whose base is its branch to the default branch before you merge it."
)


def stack_rule() -> None:
    path = SKILLS / "taskrock-goal" / "SKILL.md"
    if STACK_RULE not in path.read_text():
        problem(path, "does not state the stack rule: Merge a pull request only when its base is the default branch")


GOAL_MUST_NAME = [
    "taskrock pr status",
    "taskrock pr threads",
    "taskrock pr merge",
    "rounds_exhausted",
    "P0",
    "P1",
    "P2",
    "P3",
    "gh pr update-branch",
]
GOAL_MUST_NOT_NAME = {
    "gh pr merge": "merges through `taskrock pr merge`, which retargets, queues and pins the head commit",
    "@codex review": "Codex reviews when the builder marks the pull request ready, so no comment starts it",
    "enqueuePullRequest": "`taskrock pr merge` enqueues the pull request",
}


def merge_rule() -> None:
    """taskrock-goal gates and merges with taskrock pr, and states the severity rule."""
    path = SKILLS / "taskrock-goal" / "SKILL.md"
    text = path.read_text()
    for word in GOAL_MUST_NAME:
        if word not in text:
            problem(path, f"does not name `{word}`")
    for word, why in GOAL_MUST_NOT_NAME.items():
        if word in text:
            problem(path, f"names `{word}`: {why}")


def title_rule() -> None:
    for name in TITLE_SKILLS:
        path = SKILLS / name / "SKILL.md"
        if TITLE_RULE not in path.read_text():
            problem(path, "does not state the title rule")


VERSION_SKILLS = ["taskrock-goal", "taskrock-issue", "taskrock-plan", "taskrock-setup", "taskrock-triage"]
VERSION_GATE = (
    "It must print `taskrock {minor}.` followed by a patch number, such as `taskrock {minor}.0`. "
    "If the command is missing or prints an older version, stop and tell the user to install taskrock {minor}.0. "
    "If it prints a newer minor or major version, this plugin is older than the tool: stop and tell the user "
    "to update the plugin with `claude plugin marketplace update taskrock`, then "
    "`claude plugin update taskrock@taskrock` (or the update command of their runtime), and to restart the "
    "session. Do not go on."
)


VERSION_MENTIONS = [
    re.compile(r"version (\d+\.\d+)\.\d+, on PATH"),
    re.compile(r"--tag v(\d+\.\d+)\.\d+"),
    re.compile(r"taskrock (\d+\.\d+)\.(?!\d)"),
    re.compile(r"`?taskrock`? (\d+\.\d+)\.\d+"),
]
VERSION_PAGES = [ROOT / "README.md", ROOT / "docs" / "installation.md"]


def mentioned_versions(path: Path, text: str, minor: str, version: str) -> None:
    for mention in VERSION_MENTIONS:
        for found in mention.findall(text.replace(TITLE_EXAMPLE, "")):
            if found != minor:
                problem(path, f"names taskrock {found}, but VERSION is {version}: name {minor}")


def version_gate(version: str) -> None:
    """Each version skill runs `taskrock --version` and names only the major.minor of VERSION.

    A plugin patch release changes no skill text. Every mention of a full `taskrock X.Y.Z` in a skill, the
    README or the installation page names that major.minor too. The title-rule example is not a version
    mention: it is cut out before the patterns run.
    """
    minor = ".".join(version.split(".")[:2])
    gate = VERSION_GATE.format(minor=minor)
    for path in VERSION_PAGES:
        mentioned_versions(path, path.read_text(), minor, version)
    for name in VERSION_SKILLS:
        path = SKILLS / name / "SKILL.md"
        text = path.read_text()
        mentioned_versions(path, text, minor, version)
        if not VERSION_MENTIONS[0].search(text):
            problem(path, "does not say `version X.Y.Z, on PATH`")
        if "taskrock --version" not in text:
            problem(path, "does not run `taskrock --version`")
        if gate not in text:
            problem(path, f"does not state the version gate: accept only taskrock {minor}.x, and tell the user to update the plugin on a newer minor or major version")


SWITCH = re.compile(r"git (?:switch|checkout|worktree add)\b")
OTHER_TASK_BRANCH = re.compile(r"feat/issue-(?!<number>)")


def branches() -> None:
    """Only `taskrock claim` creates a branch. A builder works only on its own task branch."""
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if NEW_BRANCH.search(line):
                problem(path, f"line {number} creates a branch. Work only on feat/issue-<number>, which taskrock claim creates")
            if SWITCH.search(line) and ("feat/issue-<number>" not in line or OTHER_TASK_BRANCH.search(line)):
                problem(path, f"line {number} works on a branch other than feat/issue-<number>. A stacked task is built on its own branch, which taskrock claim --stacked creates")


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
    flags()
    gh_issue()
    filing()
    routing()
    scope()
    claim_rule()
    stacked_claims()
    stack_rule()
    merge_rule()
    title_rule()
    version_gate(version)
    branches()
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
