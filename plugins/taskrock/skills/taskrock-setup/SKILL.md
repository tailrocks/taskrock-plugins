---
name: taskrock-setup
description: >-
  Interview the owner, write <owner>/.github/taskrock.toml and run taskrock setup so GitHub matches it. Use when the user asks to set up an organization or change its taskrock config.
license: Apache-2.0
---

# Set up an organization

## Use this skill

| The link or request | Skill |
|---|---|
| A project, or an issue of type Initiative or Epic, or any issue that has sub-issues | `taskrock-goal` |
| An issue of type Task, Bug or Feature with no sub-issues and status Todo or In Progress | `taskrock-issue` |
| A Bug or Feature with status Triage | `taskrock-triage` |
| A request to plan work, with no link | `taskrock-plan` |
| A request to set up an organization | `taskrock-setup` |

Find the kind of an issue link with one command:

```sh
gh issue view <link> --json issueType,subIssuesSummary --jq '"\(.issueType.name) \(.subIssuesSummary.total)"'
```

If the link belongs to another skill, load that skill and stop this one.

You describe how an organization works in one file, `<owner>/.github/taskrock.toml`, and make GitHub match it. The owner never opens a browser. You read every fact with a command and ask only what no command can tell you.

Use this skill when the user asks to set up an organization, or to change its taskrock config. The input is an organization name, or a link to the organization or to its `.github` repository.
This skill does not plan or build work. Use `taskrock-plan` to plan, `taskrock-issue` to build one task, and `taskrock-goal` to build a whole plan.

## Before you start

This skill needs the `taskrock` command-line tool, version 0.2.0, on PATH. It also needs the `gh` command with a signed-in GitHub account that can administer the organization, and the `git` command.

This skill changes GitHub. Step 6 opens a pull request to `<owner>/.github`, and creates that repository when it is missing. Step 8 runs `taskrock setup`, which creates and fixes issue types, fields, projects, views, repository links, milestones and workflows.
Do not run step 8 before the owner has merged the pull request and approved.

## Procedure

### 0. Check the taskrock version

```sh
taskrock --version
```

It must print `taskrock 0.2.0` or a newer version. If the command is missing or prints an older version, stop and tell the user to install taskrock 0.2.0 or newer. Do not go on.

### 1. Route the request

When the user gave an issue link, run the `gh issue view` command of the table above. If the table sends that link to another skill, load that skill and stop. A link to an organization or to `<owner>/.github` stays here.

### 2. Read the facts

Find the facts by running commands. Never ask the owner for a fact that a command prints.

```sh
gh api orgs/<owner>/issue-types --jq '.[].name'
gh api orgs/<owner>/issue-fields --jq '.[] | "\(.name): \([(.options // [])[].name] | join(", "))"'
gh project list --owner <owner> --format json
gh repo list <owner> --limit 200 --json name,description,isArchived
gh api -H "Accept: application/vnd.github.raw" repos/<owner>/.github/contents/taskrock.toml
```

The last command prints the current config. HTTP 404 means the organization has none: start a new one. When one exists, start from it and change only what the owner asks.

Tell the owner in a few lines what you found: the issue types, the routing fields, the projects and the repositories.

### 3. Find what this machine can run

```sh
command -v claude codex agy muse grok
```

Each name that prints a path is a runtime this machine can run. Offer only those runtimes. If the current config names another runtime, say so and ask whether to keep it.

Offer only the models that each CLI reports:

```sh
codex debug models
agy models
grok models
```

`claude` and `muse` have no command that lists models. A CLI that is not signed in lists none either. For each of these, offer only the models that the Model field of the organization already holds, from step 2, and the models of the current config that name that runtime.

### 4. Interview in rounds

Ask every question whose answer you cannot find, in rounds. A round holds all questions whose earlier answers are settled.

- Each question is multiple choice. The recommended answer comes first.
- Say that "yes" accepts every recommended answer of the round.
- Ask nothing that a command already told you.

Ask about:

1. **Subagents.** Each subagent, the runtimes that have it installed, and what it can do: `build`, `review`, or both. Offer the Agent values that exist and the subagents of the current config.
2. **Models.** Each model, its runtimes, its efforts, and its `use` text: the words that tell a planner when to pick it. Offer only the models of step 3.
3. **Delivery projects.** Each product or long-lived stream of work, its title, and its repositories. Recommend adopting each existing project by its `number`. Offer the repositories of step 2.
4. **A portfolio project.** Whether the organization wants one, and its title.
5. **Workflows.** Each project keeps the six default workflows. Ask only whether any is to be deleted.
6. **Shared milestones.** For each delivery project, the releases that exist in every repository: title and due date.

### 5. Write the config

Write `taskrock.toml` in a new folder outside any repository. This is the shape of the file. Use the keys exactly. The parser refuses unknown keys.

```toml
version = 1

[routing]
runtimes   = ["claude", "codex"]
visibility = "restricted"

[[routing.subagent]]
name     = "<name>"
runtimes = ["claude", "codex"]
can      = ["build", "review"]

[[routing.model]]
name     = "<model>"
runtimes = ["claude"]
efforts  = ["low", "medium", "high"]
use      = "<when the planner picks it>"

[review]
max_rounds = 3

[[project]]
key    = "<key>"
title  = "<title>"
kind   = "delivery"
number = 3
repos  = ["<repository>"]

[project.workflows]
auto_add_sub_issues = true
item_added          = true
item_closed         = true
pr_linked           = true
pr_merged           = true
auto_close_issue    = true

[[project.milestone]]
title = "v1.0.0"
due   = "2026-12-15"

[[project]]
key   = "<key>"
title = "<title>"
kind  = "portfolio"
```

- `number` is optional. Write it only to adopt an existing project.
- A portfolio project has no `repos` and no milestones.
- Also write the five `[[issue_type]]` blocks `Initiative`, `Epic`, `Task`, `Bug` and `Feature`, and the `[owner_task]` table. When the current config has them, keep them as they are. Otherwise write these formats, with `checklist = ["Done when"]` in every block:

| Block | file | build |
|---|---|---|
| Initiative | Outcome, Why, Not yet specified, Out of scope, Done when | same |
| Epic | Outcome, Decisions already made, Not yet specified, Out of scope, Done when | same |
| Task | Outcome, Decisions already made, Steps, Done when, Out of scope | same |
| Bug | What happens, Expected, How to reproduce, Environment | What happens, Expected, How to reproduce, Environment, Cause, Decisions already made, Steps, Done when, Out of scope |
| Feature | Problem, Proposed behavior, Workaround today | Problem, Proposed behavior, Workaround today, Decisions already made, Steps, Done when, Out of scope |
| `[owner_task]` | Outcome, Question, Why it matters, Recommended answer, Done when | same |

Check the file until it prints `OK`:

```sh
taskrock check taskrock.toml
```

Fix each problem it prints and run it again.

### 6. Open the pull request

Write `.github/workflows/taskrock.yml` next to the config. It runs on pull requests and on pushes to main. It installs Rust and taskrock, then checks the config:

```yaml
name: taskrock
on:
  pull_request:
  push:
    branches: [main]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo install --locked --git https://github.com/tailrocks/taskrock --tag v0.2.0 taskrock
      - run: taskrock check taskrock.toml
```

Find out whether the repository exists:

```sh
gh repo view <owner>/.github --json name
```

When it is missing, ask the owner whether to create it, and whether it is private or public. Recommend private. Create it only after the owner says yes:

```sh
gh repo create <owner>/.github --private --add-readme
```

Put the two files in a branch, and open the pull request:

```sh
gh repo clone <owner>/.github <folder>
git -C <folder> switch -c taskrock-config
cp taskrock.toml <folder>/taskrock.toml
mkdir -p <folder>/.github/workflows
cp .github/workflows/taskrock.yml <folder>/.github/workflows/taskrock.yml
git -C <folder> add taskrock.toml .github/workflows/taskrock.yml
git -C <folder> commit -s -m "feat: add the organization config"
git -C <folder> push -u origin taskrock-config
GH_PR_CREATE_DRAFT=0 gh pr create --repo <owner>/.github --head taskrock-config --title "feat: add the organization config" --body-file <file>
```

The body says what the config sets up, and that merging it does not change GitHub: the owner runs `taskrock setup` after the merge.

### 7. Show what setup would change

```sh
taskrock setup <owner> --file taskrock.toml --dry-run
```

Show the output to the owner. Each line starts with `create`, `update`, `delete` or `exists`. Explain each `create`, `update` and `delete` line in one short sentence. Show the link of the pull request, and wait.

### 8. Run setup after approval

Wait until the owner has merged the pull request and approved the run. Then:

```sh
taskrock setup <owner>
taskrock setup <owner> --dry-run
```

The second run must print only `exists` lines and notes. If it prints anything else, show the output to the owner and stop.

Name `--yes` only when the config sets a workflow to `false`. Ask first: a deleted workflow cannot be turned on again.

```sh
taskrock setup <owner> --yes
```

## Result

Print the link of the pull request and the last output of `taskrock setup <owner> --dry-run`. Delete the draft folder.

## Completion checks

Make sure that each item is true:

- `taskrock --version` printed `taskrock 0.2.0` or a newer version.
- You read the facts with commands and did not ask the owner for any of them.
- You offered only the runtimes that `command -v` found, and only the models that a CLI or the Model field reported.
- `taskrock check taskrock.toml` printed `OK`.
- The pull request to `<owner>/.github` holds `taskrock.toml` and `.github/workflows/taskrock.yml`.
- You ran `taskrock setup <owner>` only after the owner merged the pull request and approved.
- You used `--yes` only after the owner agreed to delete a workflow.
- The last `taskrock setup <owner> --dry-run` printed only `exists` lines and notes.
